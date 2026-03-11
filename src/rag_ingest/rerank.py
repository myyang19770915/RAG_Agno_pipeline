def _tokenize(text):
    return {token for token in text.lower().split() if token}


def rerank_candidates(query, candidates, strategy='lightweight'):
    if strategy == 'none':
        return list(candidates)

    if strategy == 'lightweight':
        query_tokens = _tokenize(query)
        return sorted(
            candidates,
            key=lambda candidate: (
                len(query_tokens & _tokenize(candidate.get('text', ''))),
                candidate.get('score', 0),
            ),
            reverse=True,
        )

    raise ValueError(f'Unsupported rerank strategy: {strategy}')
