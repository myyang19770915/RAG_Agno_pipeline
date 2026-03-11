def run_agno_live_smoke(query, *, backend_factory, agent_factory):
    backend = backend_factory()
    agent = agent_factory(backend)
    response = agent.run(query)
    return {
        'query': query,
        'backend': backend,
        'response': response,
    }
