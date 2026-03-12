import pytest

from scripts import run_agno_specialist


def test_run_agno_specialist_module_exposes_main():
    assert callable(run_agno_specialist.main)


def test_run_agno_specialist_main_fails_clearly_when_runtime_prerequisites_missing(monkeypatch):
    def fail_backend_factory():
        raise RuntimeError('Missing required Agno backend settings: RAG_QDRANT_URL')

    monkeypatch.setattr(run_agno_specialist, 'create_backend_from_env', fail_backend_factory)

    with pytest.raises(RuntimeError, match='Missing required Agno backend settings'):
        run_agno_specialist.main()


def test_run_agno_specialist_main_returns_useful_result_when_factories_are_patched(monkeypatch, capsys):
    class FakeAgent:
        def run(self, query):
            return {'answer': f'agent:{query}', 'citations': []}

    monkeypatch.setattr(run_agno_specialist, 'create_backend_from_env', lambda: {'backend': 'ok'})
    monkeypatch.setattr(run_agno_specialist, 'create_agno_specialist_agent', lambda backend, **kwargs: FakeAgent())

    result = run_agno_specialist.main(query='reset password')

    assert result['query'] == 'reset password'
    assert result['backend'] == {'backend': 'ok'}
    assert result['response']['answer'] == 'agent:reset password'
    assert 'agent:reset password' in capsys.readouterr().out


def test_run_agno_specialist_main_passes_model_and_serializes_run_output(monkeypatch, capsys):
    captured = {}

    class FakeRunOutput:
        def __init__(self, content):
            self.content = content

    class FakeAgent:
        def run(self, query):
            return FakeRunOutput(f'agent:{query}')

    monkeypatch.setattr(run_agno_specialist, 'create_backend_from_env', lambda: {'backend': 'ok'})
    monkeypatch.setattr(
        run_agno_specialist,
        'load_policy_from_env',
        lambda: {
            'rewrite_mode': 'multi_query',
            'history_mode': True,
            'rerank_provider': 'none',
            'embedding_provider': 'fastembed',
        },
    )

    def fake_create_agent(backend, **kwargs):
        captured['backend'] = backend
        captured['kwargs'] = kwargs
        return FakeAgent()

    monkeypatch.setattr(run_agno_specialist, 'create_agno_specialist_agent', fake_create_agent)
    monkeypatch.setenv('AGNO_MODEL', 'gpt-5-mini')

    result = run_agno_specialist.main(query='reset password')

    assert captured['kwargs']['model'] == 'gpt-5-mini'
    assert captured['kwargs']['default_rewrite_mode'] == 'multi_query'
    assert captured['kwargs']['default_history_mode'] is True
    assert 'retrieve_knowledge' in captured['kwargs']['instructions']
    assert result['response'] == {'content': 'agent:reset password'}
    assert 'agent:reset password' in capsys.readouterr().out
