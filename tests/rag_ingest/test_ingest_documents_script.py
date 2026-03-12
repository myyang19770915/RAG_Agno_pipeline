import json
from pathlib import Path

import pytest

from scripts import ingest_documents


def test_ingest_documents_module_exposes_main():
    assert callable(ingest_documents.main)


def test_ingest_documents_main_fails_clearly_when_full_inputs_are_not_supplied():
    with pytest.raises(RuntimeError, match='ingest_documents CLI wiring is not complete yet'):
        ingest_documents.main(['ingest'])


def test_ingest_documents_main_uses_env_defaults_when_cli_values_are_omitted(monkeypatch, capsys):
    monkeypatch.setenv('RAG_SOURCE_SYSTEM', 'env-source')
    monkeypatch.setenv('RAG_CHUNK_SIZE', '777')
    monkeypatch.setenv('RAG_CHUNK_OVERLAP', '88')
    captured = {}

    def fake_runner(*, source_path, source_system, chunk_size, chunk_overlap):
        captured['source_path'] = source_path
        captured['source_system'] = source_system
        captured['chunk_size'] = chunk_size
        captured['chunk_overlap'] = chunk_overlap
        return {
            'source_path': source_path,
            'source_system': source_system,
            'documents_indexed': 3,
        }

    result = ingest_documents.main(['ingest', '--source-path', '/tmp/docs'], runner=fake_runner)

    assert captured == {
        'source_path': '/tmp/docs',
        'source_system': 'env-source',
        'chunk_size': 777,
        'chunk_overlap': 88,
    }
    assert result['config']['source_path'] == '/tmp/docs'
    assert result['config']['source_system'] == 'env-source'
    assert result['config']['chunk_size'] == 777
    assert result['config']['chunk_overlap'] == 88
    assert result['documents_indexed'] == 3
    assert json.loads(capsys.readouterr().out) == result


def test_ingest_documents_main_includes_stable_config_summary_before_runner_execution(capsys):
    def fake_runner(*, source_path, source_system, chunk_size, chunk_overlap):
        assert source_path == '/tmp/docs'
        assert source_system == 'local-folder'
        assert chunk_size == 512
        assert chunk_overlap == 64
        return {'documents_indexed': 3}

    result = ingest_documents.main(
        [
            'ingest',
            '--source-path', '/tmp/docs',
            '--source-system', 'local-folder',
            '--chunk-size', '512',
            '--chunk-overlap', '64',
        ],
        runner=fake_runner,
    )

    assert result['command'] == 'ingest'
    assert result['config'] == {
        'source_path': '/tmp/docs',
        'source_system': 'local-folder',
        'chunk_size': 512,
        'chunk_overlap': 64,
        'db_path': None,
    }
    assert result['preflight']['source_path'] == '/tmp/docs'
    assert result['preflight']['source_system'] == 'local-folder'
    assert result['preflight']['source_exists'] is False
    assert result['documents_indexed'] == 3
    assert json.loads(capsys.readouterr().out) == result


def test_validate_command_returns_preflight_summary_without_runner_execution(tmp_path, capsys):
    docs_dir = tmp_path / 'docs'
    docs_dir.mkdir()
    (docs_dir / 'a.md').write_text('hello world', encoding='utf-8')

    result = ingest_documents.main(['validate', '--source-path', str(docs_dir)])

    assert result['command'] == 'validate'
    assert result['status'] == 'ok'
    assert result['preflight']['source_exists'] is True
    assert result['preflight']['supported_files'] == 1
    assert result['preflight']['runner'] == 'stub'
    assert result['summary']['documents_indexed'] == 0
    assert result['event']['event'] == 'ingestion.validate.completed'
    assert json.loads(capsys.readouterr().out) == result


def test_smoke_command_returns_runner_summary_with_timing(capsys):
    def fake_smoke_runner(config):
        assert config['source_path'] == '/tmp/docs'
        return {'status': 'ok', 'checks': {'backend': 'stubbed'}}

    result = ingest_documents.main(['smoke', '--source-path', '/tmp/docs'], smoke_runner=fake_smoke_runner)

    assert result['command'] == 'smoke'
    assert result['status'] == 'ok'
    assert result['checks'] == {'backend': 'stubbed'}
    assert result['timing']['elapsed_ms'] >= 0.0
    assert result['event']['event'] == 'ingestion.smoke.completed'
    assert json.loads(capsys.readouterr().out) == result


def test_ingest_command_reports_missing_runtime_dependency_clearly(monkeypatch):
    def missing_dependency_runner(**kwargs):
        raise ModuleNotFoundError("No module named 'qdrant_client'")

    with pytest.raises(RuntimeError, match='Missing runtime dependency for ingest_documents CLI: qdrant_client'):
        ingest_documents.main(['ingest', '--source-path', '/tmp/docs'], runner=missing_dependency_runner)


def test_ingest_command_can_resolve_default_local_runner(tmp_path, monkeypatch, capsys):
    docs_dir = tmp_path / 'docs'
    docs_dir.mkdir()
    (docs_dir / 'note.md').write_text('文件編號: SOP-100\nhello world ' * 10, encoding='utf-8')
    db_path = tmp_path / 'ingest.db'

    class FakeProvider:
        name = 'fake-embed'

        def embed_texts(self, chunks):
            return [[float(index + 1)] for index, _chunk in enumerate(chunks)]

    monkeypatch.setattr(ingest_documents, 'select_embedding_provider', lambda: FakeProvider())

    result = ingest_documents.main(
        ['ingest', '--source-path', str(docs_dir), '--db-path', str(db_path), '--chunk-size', '10', '--chunk-overlap', '0']
    )

    assert result['command'] == 'ingest'
    assert result['status'] == 'ok'
    assert result['summary']['documents_indexed'] == 1
    assert result['summary']['qdrant_points'] >= 1
    assert result['preflight']['runner'] == 'local_folder'
    assert Path(db_path).exists() is True
    assert result['timing']['elapsed_ms'] >= 0.0
    assert result['event']['event'] == 'ingestion.ingest.completed'
    assert json.loads(capsys.readouterr().out) == result
