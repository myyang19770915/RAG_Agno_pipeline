from typing import Any


SOURCE_NAMES = {
    "vector_results": "vector",
    "keyword_results": "keyword",
}


def fuse_ranked_results(
    vector_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
    k: int = 60,
) -> list[dict[str, Any]]:
    fused_by_chunk_id: dict[str, dict[str, Any]] = {}

    for source_name, results in (
        ("vector", vector_results),
        ("keyword", keyword_results),
    ):
        for rank, result in enumerate(results, start=1):
            chunk_id = result["chunk_id"]
            fused = fused_by_chunk_id.setdefault(
                chunk_id,
                {
                    **result,
                    "fused_score": 0.0,
                    "sources": [],
                },
            )
            fused["fused_score"] += 1.0 / (k + rank)
            if source_name not in fused["sources"]:
                fused["sources"].append(source_name)

    return sorted(
        fused_by_chunk_id.values(),
        key=lambda item: item["fused_score"],
        reverse=True,
    )
