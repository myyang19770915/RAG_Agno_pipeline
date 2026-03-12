import json

import pytest

from scripts import ingest_documents


def test_ingest_documents_module_exposes_main():
    assert callable(ingest_documents.main)


def test_ingest_documents_main_fails_clearly_when_full_inputs_are_not_supplied():
    with pytest.raises(RuntimeError, match='ingest_documents CLI wiring is not complete yet'):
        ingest_documents.main([])


def test_ingest_documents_main_returns_summary_and_prints_json_when_runner_is_patched(capsys):
    captured = {}

    def fake_runner(*, source_path, source_system):
        captured['source_path'] = source_path
        captured['source_system'] = source_system
        return {
            'source_path': source_path,
            'source_system': source_system,
            'documents_indexed': 3,
        }

    result = ingest_documents.main(
        ['--source-path', '/tmp/docs', '--source-system', 'local-folder'],
        runner=fake_runner,
    )

    assert captured == {
        'source_path': '/tmp/docs',
        'source_system': 'local-folder',
    }
    assert result == {
        'source_path': '/tmp/docs',
        'source_system': 'local-folder',
        'documents_indexed': 3,
    }
    assert json.loads(capsys.readouterr().out) == result
