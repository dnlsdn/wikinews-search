"""Elasticsearch helpers shared by search() and the web API (owner: Fabio)."""

from functools import lru_cache

from elasticsearch import Elasticsearch

from wikisearch.config import ES_URL


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
