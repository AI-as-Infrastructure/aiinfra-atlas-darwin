"""
Hybrid search utilities: reciprocal-rank fusion (RRF) and helpers.
"""
from typing import List, Dict, Tuple


def rrf_merge(
    dense: List[Tuple[str, float]],  # list of (doc_id, score/rank)
    lexical: List[Tuple[str, float]],
    k: int = 60,
    top_k: int = 20,
) -> List[str]:
    """
    Reciprocal Rank Fusion merge. Inputs should be already ranked (0..n-1).
    We use position as rank and ignore raw scores to keep it robust.
    Returns ordered list of doc_ids.
    """

    def to_rank_map(items: List[Tuple[str, float]]) -> Dict[str, int]:
        return {doc_id: rank for rank, (doc_id, _) in enumerate(items)}

    d_rank = to_rank_map(dense)
    l_rank = to_rank_map(lexical)
    all_ids = set(d_rank) | set(l_rank)

    fused = []
    for doc_id in all_ids:
        r_dense = d_rank.get(doc_id, 1_000_000)
        r_lex = l_rank.get(doc_id, 1_000_000)
        score = 1.0 / (k + r_dense) + 1.0 / (k + r_lex)
        fused.append((doc_id, score))

    fused.sort(key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in fused[:top_k]]
