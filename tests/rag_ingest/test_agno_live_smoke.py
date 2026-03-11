from rag_ingest.agno_live_smoke import run_agno_live_smoke


class FakeAgent:
    def __init__(self):
        self.runs = []

    def run(self, query):
        self.runs.append(query)
        return {'answer': f'agent:{query}', 'citations': [{'document_key': 'doc1'}]}


def test_run_agno_live_smoke_wires_backend_then_agent_then_response():
    calls = []
    agent = FakeAgent()

    def backend_factory():
        calls.append('backend')
        return {'backend': 'ok'}

    def agent_factory(backend):
        calls.append(('agent', backend))
        return agent

    result = run_agno_live_smoke(
        'reset password',
        backend_factory=backend_factory,
        agent_factory=agent_factory,
    )

    assert calls == ['backend', ('agent', {'backend': 'ok'})]
    assert agent.runs == ['reset password']
    assert result['query'] == 'reset password'
    assert result['backend'] == {'backend': 'ok'}
    assert result['response']['answer'] == 'agent:reset password'
