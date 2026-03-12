import argparse
import inspect
import json
import os
import sys

from rag_ingest.embedding_provider import select_embedding_provider
from rag_ingest.file_ingest import scan_files
from rag_ingest.local_folder_pipeline import process_folder_documents
from rag_ingest.observability import build_event, timed_call
from rag_ingest.services.ingest_pipeline import FakeQdrant
from rag_ingest.db.sqlite_session import SQLiteSession, initialize_schema


CLI_WIRING_STUB_ERROR = 'ingest_documents CLI wiring is not complete yet; supply a runner to execute ingestion.'


def _build_parser():
    parser = argparse.ArgumentParser(description='Ingest documents into the configured RAG backend.')
    subparsers = parser.add_subparsers(dest='command')

    def add_common_arguments(command_parser):
        command_parser.add_argument('--source-path')
        command_parser.add_argument('--source-system', default=os.getenv('RAG_SOURCE_SYSTEM', 'localfs'))
        command_parser.add_argument('--chunk-size', type=int, default=int(os.getenv('RAG_CHUNK_SIZE', '500')))
        command_parser.add_argument('--chunk-overlap', type=int, default=int(os.getenv('RAG_CHUNK_OVERLAP', '50')))
        command_parser.add_argument('--db-path', default=os.getenv('RAG_SQLITE_DB_PATH'))

    add_common_arguments(subparsers.add_parser('validate', help='Validate config and source inputs.'))
    add_common_arguments(subparsers.add_parser('ingest', help='Run document ingestion.'))
    add_common_arguments(subparsers.add_parser('smoke', help='Run a lightweight smoke path.'))

    return parser


def _parse_args(argv=None):
    parser = _build_parser()
    argv = list(argv or [])
    if argv and not str(argv[0]).startswith('-'):
        return parser.parse_args(argv)
    return parser.parse_args(['ingest', *argv])


def _config_from_args(args):
    return {
        'source_path': args.source_path,
        'source_system': args.source_system,
        'chunk_size': args.chunk_size,
        'chunk_overlap': args.chunk_overlap,
        'db_path': args.db_path,
    }


def _build_preflight(config, runner_name):
    source_path = config['source_path']
    source_exists = bool(source_path and os.path.exists(source_path))
    supported_files = len(scan_files(source_path)) if source_exists and os.path.isdir(source_path) else 0
    return {
        'source_path': source_path,
        'source_system': config['source_system'],
        'source_exists': source_exists,
        'supported_files': supported_files,
        'runner': runner_name,
    }


def _build_local_runner():
    def run_local_folder_ingest(*, source_path, source_system, chunk_size, chunk_overlap, db_path=None):
        if not db_path:
            raise RuntimeError('Local folder ingest requires --db-path or RAG_SQLITE_DB_PATH.')
        initialize_schema(db_path)
        session = SQLiteSession(db_path)
        qdrant = FakeQdrant()
        provider = select_embedding_provider()
        result = process_folder_documents(
            source_path,
            session,
            qdrant,
            source_system=source_system,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
            embedding_provider=provider,
        )
        return {
            'documents_indexed': result.get('processed', 0),
            'qdrant_points': len(qdrant.points),
            'embedding_provider': getattr(provider, 'name', type(provider).__name__),
            'db_path': db_path,
        }

    return run_local_folder_ingest


def _resolve_runner(runner):
    if runner is not None:
        return runner, 'injected'
    if os.getenv('RAG_INGEST_RUNNER', 'local_folder') == 'local_folder':
        return _build_local_runner(), 'local_folder'
    return None, 'stub'


def _invoke_runner(runner, config):
    kwargs = {
        'source_path': config['source_path'],
        'source_system': config['source_system'],
        'chunk_size': config['chunk_size'],
        'chunk_overlap': config['chunk_overlap'],
    }
    signature = inspect.signature(runner)
    if 'db_path' in signature.parameters:
        kwargs['db_path'] = config['db_path']
    return runner(**kwargs)


def _raise_runtime_dependency_error(exc):
    missing_name = None
    if getattr(exc, 'name', None):
        missing_name = exc.name
    elif exc.args:
        text = str(exc.args[0])
        marker = "No module named '"
        if marker in text:
            missing_name = text.split(marker, 1)[1].split("'", 1)[0]
    if missing_name:
        raise RuntimeError(f'Missing runtime dependency for ingest_documents CLI: {missing_name}') from exc
    raise


def _print_summary(summary):
    print(json.dumps(summary, ensure_ascii=False))


def main(argv=None, runner=None, smoke_runner=None):
    args = _parse_args(argv)
    command = args.command or 'ingest'
    config = _config_from_args(args)
    resolved_runner, runner_name = _resolve_runner(runner if command == 'ingest' else None)
    preflight_runner = 'stub'
    if command == 'ingest':
        preflight_runner = runner_name
    elif command == 'smoke':
        preflight_runner = 'injected' if smoke_runner else 'stub'
    preflight = _build_preflight(config, preflight_runner)

    if command == 'validate':
        summary = {
            'command': 'validate',
            'status': 'ok',
            'config': config,
            'preflight': preflight,
            'summary': {'documents_indexed': 0},
            'timing': {'elapsed_ms': 0.0},
            'event': build_event(
                'ingestion.validate.completed',
                operation='ingest_validate',
                status='ok',
                timing={'elapsed_ms': 0.0},
                summary={'supported_files': preflight['supported_files']},
            ),
        }
        _print_summary(summary)
        return summary

    if command == 'smoke':
        if smoke_runner is None:
            smoke_runner = lambda current_config: {'status': 'ok', 'checks': {'runner': 'stub'}}
        smoke_result, timing = timed_call('ingestion_smoke', lambda: smoke_runner(config))
        summary = {
            'command': 'smoke',
            'status': smoke_result.get('status', 'ok'),
            'config': config,
            'preflight': preflight,
            **smoke_result,
            'timing': {'elapsed_ms': timing['elapsed_ms']},
            'event': build_event(
                'ingestion.smoke.completed',
                operation='ingest_smoke',
                status=smoke_result.get('status', 'ok'),
                timing={'elapsed_ms': timing['elapsed_ms']},
                summary=smoke_result.get('checks', {}),
            ),
        }
        _print_summary(summary)
        return summary

    if resolved_runner is None or not config['source_path']:
        raise RuntimeError(CLI_WIRING_STUB_ERROR)

    try:
        runner_result, timing = timed_call(
            'ingestion_ingest',
            lambda: _invoke_runner(resolved_runner, config),
        )
    except ModuleNotFoundError as exc:
        _raise_runtime_dependency_error(exc)

    summary = {
        'command': 'ingest',
        'status': 'ok',
        'config': config,
        'preflight': preflight,
        'summary': {
            'documents_indexed': runner_result.get('documents_indexed', runner_result.get('processed', 0)),
            **{key: value for key, value in runner_result.items() if key not in {'documents_indexed', 'processed'}},
        },
        'timing': {'elapsed_ms': timing['elapsed_ms']},
    }
    summary['event'] = build_event(
        'ingestion.ingest.completed',
        operation='ingest',
        status=summary['status'],
        timing=summary['timing'],
        summary=summary['summary'],
    )
    summary['documents_indexed'] = summary['summary']['documents_indexed']
    _print_summary(summary)
    return summary


if __name__ == '__main__':
    main(argv=sys.argv[1:])
