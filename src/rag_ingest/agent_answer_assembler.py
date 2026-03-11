from typing import Any

from rag_ingest.agent_answers import AgentAnswer


def assemble_answer(
    query: str,
    retrieve_response: dict[str, Any],
    history_mode: bool = False,
) -> AgentAnswer:
    results = retrieve_response.get('results', [])
    top_result = results[0] if results else {}
    answer_text = top_result.get('text', '') or query
    citations = [result['citation'] for result in results if result.get('citation')]

    notes = None
    if history_mode:
        notes = 'This answer may reference historical document versions.'

    return AgentAnswer(
        answer=answer_text,
        citations=citations,
        used_chunks_count=len(results),
        notes=notes,
    )
