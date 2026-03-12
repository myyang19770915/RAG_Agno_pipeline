import builtins
import sys
import types

import pytest

from rag_ingest.agno_runtime import build_agno_tools, create_agno_specialist_agent


class FakeBackend:
    def vector_search(self, query, limit):
        return [
            {
                'chunk_id': 'v1:0000',
                'text': f'Vector hit for {query}',
                'score': 0.9,
                'document_key': 'doc1',
                'version_id': 'v1',
                'metadata': {'source': 'vector'},
                'is_latest': True,
                'is_active': True,
            }
        ]

    def keyword_search(self, query, limit):
        return [
            {
                'chunk_id': 'v1:0000',
                'text': f'Keyword hit for {query}',
                'score': 2.0,
                'document_key': 'doc1',
                'version_id': 'v1',
                'metadata': {'source': 'keyword'},
                'is_latest': True,
                'is_active': True,
            }
        ]


class FakeAgent:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def test_build_agno_tools_returns_callable_tool_that_delegates_to_retrieve_knowledge():
    tools = build_agno_tools(backend=FakeBackend())

    assert len(tools) == 1
    tool = tools[0]
    assert callable(tool)

    response = tool(query='reset password')

    assert response['retrieval_mode'] == 'hybrid'
    assert response['applied_query'] == 'reset password'


def test_build_agno_tools_tool_returns_plain_dict_response_shape():
    tool = build_agno_tools(backend=FakeBackend())[0]

    response = tool(query='reset password', top_k=3)

    assert isinstance(response, dict)
    assert set(response.keys()) == {
        'results',
        'applied_query',
        'applied_queries',
        'retrieval_mode',
        'debug',
    }
    assert isinstance(response['results'], list)
    assert response['results'][0]['version_id'] == 'v1'


def test_build_agno_tools_tolerates_missing_or_unknown_rewrite_mode_values():
    tool = build_agno_tools(backend=FakeBackend())[0]

    response_none = tool(query='reset password', rewrite_mode=None)
    response_unknown = tool(query='reset password', rewrite_mode='summarize_only')

    assert response_none['applied_query'] == 'reset password'
    assert response_unknown['applied_query'] == 'reset password'


def test_build_agno_tools_can_enable_debug_by_default_for_operator_runs():
    tool = build_agno_tools(backend=FakeBackend(), default_include_debug=True)[0]

    response = tool(query='reset password')

    assert response['debug']['event']['event'] == 'retrieval.completed'
    assert response['debug']['event']['operation'] == 'retrieve'


def test_create_agno_specialist_agent_raises_clear_error_when_agno_unavailable(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'agno.agent':
            raise ImportError('no agno')
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, 'agno', raising=False)
    monkeypatch.delitem(sys.modules, 'agno.agent', raising=False)
    monkeypatch.setattr(builtins, '__import__', fake_import)

    with pytest.raises(RuntimeError, match='Agno'):
        create_agno_specialist_agent(backend=FakeBackend())


def test_create_agno_specialist_agent_instantiates_agent_with_tools_and_options(monkeypatch):
    agno_module = types.ModuleType('agno')
    agno_agent_module = types.ModuleType('agno.agent')
    agno_agent_module.Agent = FakeAgent
    agno_module.agent = agno_agent_module

    monkeypatch.setitem(sys.modules, 'agno', agno_module)
    monkeypatch.setitem(sys.modules, 'agno.agent', agno_agent_module)

    agent = create_agno_specialist_agent(
        backend=FakeBackend(),
        instructions='Be helpful.',
        markdown=False,
        name='RAG Specialist',
    )

    assert isinstance(agent, FakeAgent)
    assert agent.kwargs['instructions'] == 'Be helpful.'
    assert agent.kwargs['markdown'] is False
    assert agent.kwargs['name'] == 'RAG Specialist'
    assert len(agent.kwargs['tools']) == 1
    assert callable(agent.kwargs['tools'][0])
