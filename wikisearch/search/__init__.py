"""Search (owner: Fabio). The one function used by both the web app and the evaluation."""

from dataclasses import replace

from wikisearch.config import index_name
from wikisearch.schema import Filters, Hit
from wikisearch.search.configs import CONFIGS


def search(query: str, config: str, k: int = 10, filters: Filters | None = None) -> list[Hit]:
    """Return at most k hits for the query, best first, using the named configuration.

    See docs/contracts.md, section 3. Must not apply default filters.
    """
    if config not in CONFIGS:
        raise ValueError(f"unknown configuration {config!r}; known: {', '.join(CONFIGS)}")
    cfg = CONFIGS[config]
    if k <= 0 or not query.strip():
        return []
    mode = cfg["mode"]
    if mode not in ("bm25", "knn", "hybrid"):
        raise ValueError(f"configuration {config!r} has unknown mode {mode!r}")

    from wikisearch.search import es

    boost = cfg.get("boost_published", 1.0)
    # With a boost the order changes after Elasticsearch: fetch a deeper list, then re-rank.
    size = max(k, cfg.get("depth", 100)) if boost != 1.0 else k
    if mode == "bm25":
        hits = _bm25(query, cfg, size, filters)
    elif mode == "knn":
        hits = _knn(query, cfg, size, filters)
    else:
        hits = _hybrid(query, cfg, size, filters)
    if boost != 1.0:
        hits = es.boost_published(hits, boost, k)
    return hits[:k]


def _bm25(query: str, cfg: dict, size: int, filters: Filters | None) -> list[Hit]:
    from wikisearch.search import es

    resp = es.client().search(
        index=index_name(cfg["analyzer"]),
        query=es.bm25_query(query, cfg, filters),
        highlight=es.HIGHLIGHT,
        source_includes=es.HIT_SOURCE,
        size=size,
    )
    return [es.to_hit(h) for h in resp["hits"]["hits"]]


def _knn(query: str, cfg: dict, size: int, filters: Filters | None) -> list[Hit]:
    """Semantic search: nearest document vectors to the query vector. Snippet = start of lead."""
    from wikisearch.search import es
    from wikisearch.search.embed import embed_query

    resp = es.client().search(
        index=index_name(cfg["analyzer"]),
        knn=es.knn_query(embed_query(query), size, filters),
        source_includes=es.HIT_SOURCE,
        size=size,
    )
    return [es.to_hit(h) for h in resp["hits"]["hits"]]


def _hybrid(query: str, cfg: dict, size: int, filters: Filters | None) -> list[Hit]:
    """BM25 and kNN with the same filters, `depth` hits each, fused with reciprocal rank fusion.

    The score of a hit is its RRF score. Hit fields (and the highlighted snippet) come from the
    BM25 side when the document is there, otherwise from the kNN side.
    """
    from wikisearch.search import es

    depth = max(size, cfg["depth"])  # a deep page of the web app may ask for more than depth
    lexical = _bm25(query, cfg, depth, filters)
    semantic = _knn(query, cfg, depth, filters)
    by_id = {h.id: h for h in semantic}
    by_id.update({h.id: h for h in lexical})
    fused = es.rrf_fuse([[h.id for h in lexical], [h.id for h in semantic]], cfg["rrf_k"])
    return [replace(by_id[doc_id], score=score) for doc_id, score in fused[:size]]
