from rag_ingest.agent_answers import AgentAnswer


def format_agent_response(answer: AgentAnswer) -> str:
    lines = [answer.answer]

    if answer.citations:
        lines.append('')
        lines.append('Sources:')
        for citation in answer.citations:
            document_key = citation.get('document_key', 'unknown')
            version_id = citation.get('version_id', 'unknown')
            chunk_id = citation.get('chunk_id', 'unknown')
            lines.append(f'- {document_key} (version: {version_id}, chunk: {chunk_id})')

    return '\n'.join(lines)
