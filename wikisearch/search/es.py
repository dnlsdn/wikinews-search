"""Elasticsearch helpers shared by search() and the web API (owner: Fabio)."""

import html
from dataclasses import replace
from functools import lru_cache

from elasticsearch import Elasticsearch

from wikisearch.config import ES_URL
from wikisearch.schema import Filters, Hit

# Only the fields a Hit needs: never `body` (large) or `embedding` (384 floats per hit).
# `lead` is fetched for the snippet fallback.
HIT_SOURCE = ["id", "title", "url", "date", "lead", "categories", "agencies", "image_url", "published"]
SNIPPET_CHARS = 200

# One fragment of about 160 characters from the lead or the body. The html encoder escapes the
# document text, so the only markup in a snippet is the <em> tags (the UI inserts it as HTML).
HIGHLIGHT = {
    "pre_tags": ["<em>"],
    "post_tags": ["</em>"],
    "encoder": "html",
    "fields": {
        "lead": {"fragment_size": 160, "number_of_fragments": 1},
        "body": {"fragment_size": 160, "number_of_fragments": 1},
    },
}


@lru_cache(maxsize=1)
def client() -> Elasticsearch:
    """One client for the whole process (it keeps a connection pool)."""
    return Elasticsearch(ES_URL, request_timeout=30)


def multi_match(query: str, fields: list[str], tie_breaker: float = 0.3) -> dict:
    """The lexical (BM25) query used by the bm25 configurations and by the facets."""
    return {
        "multi_match": {
            "query": query,
            "fields": fields,
            "type": "best_fields",
            "tie_breaker": tie_breaker,
        }
    }


def filters_to_es(filters: Filters | None) -> list[dict]:
    """Translate Filters into Elasticsearch filter clauses (they restrict, they do not score).

    Date range inclusive; every category must match (one term each); any agency may match (one
    terms); published only when not None. No filters -> empty list.
    """
    if filters is None:
        return []
    clauses: list[dict] = []
    if filters.date_from or filters.date_to:
        bounds = {}
        if filters.date_from:
            bounds["gte"] = filters.date_from
        if filters.date_to:
            bounds["lte"] = filters.date_to
        clauses.append({"range": {"date": bounds}})
    for category in filters.categories:
        clauses.append({"term": {"categories": category}})
    if filters.agencies:
        clauses.append({"terms": {"agencies": list(filters.agencies)}})
    if filters.published is not None:
        clauses.append({"term": {"published": filters.published}})
    return clauses


def bm25_query(query: str, cfg: dict, filters: Filters | None) -> dict:
    """bool query: multi_match in `must` (scored), filters in `filter` (not scored)."""
    return {
        "bool": {
            "must": [multi_match(query, cfg["fields"], cfg.get("tie_breaker", 0.3))],
            "filter": filters_to_es(filters),
        }
    }


def snippet(highlight: dict | None, lead: str | None) -> str:
    """First highlighted fragment (lead, then body); otherwise the start of the lead, escaped."""
    for field in ("lead", "body"):
        fragments = (highlight or {}).get(field)
        if fragments:
            return fragments[0]
    return html.escape((lead or "")[:SNIPPET_CHARS])


def to_hit(es_hit: dict) -> Hit:
    src = es_hit["_source"]
    return Hit(
        id=str(src.get("id") or es_hit["_id"]),
        score=float(es_hit["_score"]),
        title=src.get("title", ""),
        url=src.get("url", ""),
        date=src.get("date"),
        snippet=snippet(es_hit.get("highlight"), src.get("lead")),
        categories=src.get("categories", []),
        agencies=src.get("agencies", []),
        image_url=src.get("image_url"),
        published=bool(src.get("published", True)),
    )


def boost_published(hits: list[Hit], boost: float, k: int) -> list[Hit]:
    """Multiply the score of published hits by `boost`, re-sort (ties by id), keep the top k."""
    boosted = [replace(h, score=h.score * boost) if h.published else h for h in hits]
    boosted.sort(key=lambda h: (-h.score, h.id))
    return boosted[:k]
