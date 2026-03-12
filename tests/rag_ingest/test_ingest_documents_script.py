import json

import pytest

from scripts import ingest_documents


def test_ingest_documents_module_exposes_main():
    assert callable(ingest_documents.main)


def test_ingest_documents_main_fails_clearly_when_full_inputs_are_not_supplied():
    with pytest.raises(RuntimeError, match='ingest_documents CLI wiring is not complete yet'):
        ingest_documents.main([])


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

    result = ingest_documents.main(['--source-path', '/tmp/docs'], runner=fake_runner)

    assert captured == {
        'source_path': '/tmp/docs',
        'source_system': 'env-source',
        'chunk_size': 777,
        'chunk_overlap': 88,
    }
    assert result == {
        'config': {
            'source_path': '/tmp/docs',
            'source_system': 'env-source',
            'chunk_size': 777,
            'chunk_overlap': 88,
        },
        'preflight': {
            'source_path': '/tmp/docs',
            'source_system': 'env-source',
        },
        'source_path': '/tmp/docs',
        'source_system': 'env-source',
        'documents_indexed': 3,
    }
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
            '--source-path', '/tmp/docs',
            '--source-system', 'local-folder',
            '--chunk-size', '512',
            '--chunk-overlap', '64',
        ],
        runner=fake_runner,
    )

    assert result == {
        'config': {
            'source_path': '/tmp/docs',
            'source_system': 'local-folder',
            'chunk_size': 512,
            'chunk_overlap': 64,
        },
        'preflight': {
            'source_path': '/tmp/docs',
            'source_system': 'local-folder',
        },
        'documents_indexed': 3,
    }
    assert json.loads(capsys.readouterr().out) == result
