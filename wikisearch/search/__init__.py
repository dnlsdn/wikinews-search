"""Search (owner: Fabio). The one function used by both the web app and the evaluation."""

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
    if cfg["mode"] == "bm25":
        hits = _bm25(query, cfg, k, filters)
    else:
        raise NotImplementedError(f"mode {cfg['mode']!r} is step F4")
    return hits


def _bm25(query: str, cfg: dict, k: int, filters: Filters | None) -> list[Hit]:
    from wikisearch.search import es

    boost = cfg.get("boost_published", 1.0)
    # With a boost the order changes after Elasticsearch: fetch a deeper list, then re-rank.
    size = max(k, cfg.get("depth", 100)) if boost != 1.0 else k
    resp = es.client().search(
        index=index_name(cfg["analyzer"]),
        query=es.bm25_query(query, cfg, filters),
        highlight=es.HIGHLIGHT,
        source_includes=es.HIT_SOURCE,
        size=size,
    )
    hits = [es.to_hit(h) for h in resp["hits"]["hits"]]
    if boost != 1.0:
        hits = es.boost_published(hits, boost, k)
    return hits
