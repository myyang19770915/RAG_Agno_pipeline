import argparse
import json
import os
import sys


CLI_WIRING_STUB_ERROR = 'ingest_documents CLI wiring is not complete yet; supply a runner to execute ingestion.'


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Ingest documents into the configured RAG backend.')
    parser.add_argument('--source-path')
    parser.add_argument('--source-system', default=os.getenv('RAG_SOURCE_SYSTEM'))
    parser.add_argument('--chunk-size', type=int, default=int(os.getenv('RAG_CHUNK_SIZE', '500')))
    parser.add_argument('--chunk-overlap', type=int, default=int(os.getenv('RAG_CHUNK_OVERLAP', '50')))
    return parser.parse_args(argv)


def main(argv=None, runner=None):
    args = _parse_args(argv)
    if runner is None:
        raise RuntimeError(CLI_WIRING_STUB_ERROR)

    config = {
        'source_path': args.source_path,
        'source_system': args.source_system,
        'chunk_size': args.chunk_size,
        'chunk_overlap': args.chunk_overlap,
    }
    summary = runner(
        source_path=args.source_path,
        source_system=args.source_system,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    summary = {
        'config': config,
        'preflight': {
            'source_path': args.source_path,
            'source_system': args.source_system,
        },
        **summary,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return summary


if __name__ == '__main__':
    main(argv=sys.argv[1:])
