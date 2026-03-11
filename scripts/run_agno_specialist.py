import argparse
import json
import os
import sys

from rag_ingest.agno_backend_factory import create_backend_from_env
from rag_ingest.agno_live_smoke import run_agno_live_smoke
from rag_ingest.agno_runtime import create_agno_specialist_agent


DEFAULT_AGENT_INSTRUCTIONS = (
    'You are a RAG specialist. Always use the retrieve_knowledge tool before answering '
    'questions about available documents. Base your answer only on retrieved results and '
    'cite the source document_key when possible.'
)


def _serialize_response(response):
    if isinstance(response, dict):
        return response
    content = getattr(response, 'content', None)
    if content is not None:
        return {'content': content}
    return {'repr': repr(response)}


def main(query=None, argv=None):
    if query is None and argv is not None:
        parser = argparse.ArgumentParser(description='Run the Agno specialist against the configured live backend.')
        parser.add_argument('query', nargs='?', default='reset password')
        args = parser.parse_args(argv)
        query = args.query
    if query is None:
        query = 'reset password'

    model_name = os.environ.get('AGNO_MODEL')
    result = run_agno_live_smoke(
        query,
        backend_factory=create_backend_from_env,
        agent_factory=lambda backend: create_agno_specialist_agent(
            backend=backend,
            model=model_name,
            instructions=DEFAULT_AGENT_INSTRUCTIONS,
        ),
    )
    result['response'] = _serialize_response(result['response'])
    print(json.dumps(result['response'], ensure_ascii=False))
    return result


if __name__ == '__main__':
    main(argv=sys.argv[1:])
