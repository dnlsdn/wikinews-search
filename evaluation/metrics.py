"""Ranked retrieval metrics (course slides id-02, 182-189).

Every metric takes the ranked list of one query (doc ids, best first) and its judgments
(`rels`: doc_id -> grade 0, 1, 2). For binary metrics a document is relevant when grade >= 1.
Unjudged documents count as not relevant. A doc id repeated in the ranking is counted only at
its first position, so a buggy run cannot score the same relevant document twice.
"""

import math
import re


def _dedupe(ranked: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for doc_id in ranked:
        if doc_id not in seen:
            seen.add(doc_id)
            out.append(doc_id)
    return out


def _relevant(rels: dict[str, int]) -> set[str]:
    return {doc_id for doc_id, grade in rels.items() if grade >= 1}


def precision_at_k(ranked: list[str], rels: dict[str, int], k: int) -> float:
    """Relevant documents in the top k, divided by k (not by the length of the list)."""
    relevant = _relevant(rels)
    return sum(1 for d in _dedupe(ranked)[:k] if d in relevant) / k


def recall_at_k(ranked: list[str], rels: dict[str, int], k: int) -> float:
    """Relevant documents in the top k, divided by all the relevant documents judged."""
    relevant = _relevant(rels)
    if not relevant:
        return 0.0
    return sum(1 for d in _dedupe(ranked)[:k] if d in relevant) / len(relevant)


def reciprocal_rank(ranked: list[str], rels: dict[str, int], k: int = 10) -> float:
    """1 / rank of the first relevant document within the top k, else 0. Mean = MRR@k."""
    relevant = _relevant(rels)
    for rank, doc_id in enumerate(_dedupe(ranked)[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def average_precision(ranked: list[str], rels: dict[str, int]) -> float:
    """Mean of the precision at the rank of each relevant document, over all the relevant
    documents judged: a relevant document never retrieved contributes 0. Mean = MAP."""
    relevant = _relevant(rels)
    if not relevant:
        return 0.0
    hits = 0
    total = 0.0
    for rank, doc_id in enumerate(_dedupe(ranked), start=1):
        if doc_id in relevant:
            hits += 1
            total += hits / rank
    return total / len(relevant)


def _dcg(grades: list[int]) -> float:
    return sum((2**g - 1) / math.log2(rank + 1) for rank, g in enumerate(grades, start=1))


def ndcg_at_k(ranked: list[str], rels: dict[str, int], k: int = 10) -> float:
    """DCG of the top k (gain 2**grade - 1, discount log2(rank + 1)), divided by the DCG of the
    ideal ordering of the judged grades."""
    ideal = _dcg(sorted((g for g in rels.values() if g > 0), reverse=True)[:k])
    if ideal == 0:
        return 0.0
    return _dcg([rels.get(d, 0) for d in _dedupe(ranked)[:k]]) / ideal


_METRIC = re.compile(r"^(P|R|MRR|nDCG)@(\d+)$|^AP$")


def score(name: str, ranked: list[str], rels: dict[str, int]) -> float:
    """Compute a metric by name: `P@k`, `R@k`, `MRR@k` (reciprocal rank), `nDCG@k`, `AP`."""
    m = _METRIC.match(name)
    if not m:
        raise ValueError(f"unknown metric {name!r}")
    if name == "AP":
        return average_precision(ranked, rels)
    kind, k = m.group(1), int(m.group(2))
    fn = {"P": precision_at_k, "R": recall_at_k, "MRR": reciprocal_rank, "nDCG": ndcg_at_k}[kind]
    return fn(ranked, rels, k)


def evaluate(
    qrels: dict[str, dict[str, int]], run: dict[str, list[str]], metrics: list[str]
) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    """Per-query scores and their mean (macro-average over queries).

    Queries without any relevant judgment are skipped (no metric is defined for them).
    Queries judged but missing from the run score 0. Queries in the run but not in the qrels
    are ignored.
    """
    per_query: dict[str, dict[str, float]] = {}
    for qid in sorted(qrels):
        rels = qrels[qid]
        if not _relevant(rels):
            continue
        ranked = run.get(qid, [])
        per_query[qid] = {name: score(name, ranked, rels) for name in metrics}
    n = len(per_query)
    mean = {name: (sum(s[name] for s in per_query.values()) / n if n else 0.0) for name in metrics}
    return per_query, mean
