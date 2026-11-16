"""Web API and interface (owner: Fabio), endpoints of docs/contracts.md section 4.

Start:  uv run uvicorn wikisearch.web.app:app --reload   then http://localhost:8000
Fake mode (no Elasticsearch needed): set WIKISEARCH_FAKE=1 before starting
(PowerShell: $env:WIKISEARCH_FAKE=1). Every endpoint then answers with the data of fake.py.
"""

import os
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch import NotFoundError
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from wikisearch.config import index_name
from wikisearch.schema import Filters, Hit
from wikisearch.search import search
from wikisearch.search.configs import CONFIGS, DEFAULT_CONFIG
from wikisearch.web import fake

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_SIZE = 10
MAX_SIZE = 100

app = FastAPI(title="wikinews-search")


def fake_mode() -> bool:
    """Read at every request, so tests can switch it on and off."""
    return os.environ.get("WIKISEARCH_FAKE") == "1"


def _check_config(config: str) -> dict:
    if config not in CONFIGS:
        raise HTTPException(400, f"unknown config {config!r}; see /api/configs")
    return CONFIGS[config]


def _run_search(q: str, config: str, k: int, filters: Filters) -> list[Hit]:
    if fake_mode():
        return fake.HITS[:k]
    try:
        return search(q, config, k=k, filters=filters)
    except NotImplementedError as exc:
        raise HTTPException(501, f"configuration not available yet ({exc})") from exc
    except ESConnectionError as exc:
        raise HTTPException(503, "Elasticsearch is not reachable") from exc


@app.get("/api/configs")
def configs() -> dict:
    return {"default": DEFAULT_CONFIG, "configs": list(CONFIGS)}


@app.get("/api/search")
def api_search(
    q: str = "",
    config: str = DEFAULT_CONFIG,
    page: int = Query(1, ge=1),
    size: int | None = Query(None, ge=1, le=MAX_SIZE),
    k: int | None = Query(None, ge=1, le=MAX_SIZE, description="alias of size (contract name)"),
    date_from: date | None = None,
    date_to: date | None = None,
    category: list[str] = Query([]),
    agency: list[str] = Query([]),
    published: bool | None = None,
) -> dict:
    _check_config(config)
    size = size or k or DEFAULT_SIZE
    filters = Filters(
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        categories=category,
        agencies=agency,
        published=published,
    )
    hits: list[Hit] = []
    took_ms = 0.0
    if q.strip():
        # Pagination: search() has no offset, so ask for every hit up to this page and slice.
        start = time.perf_counter()
        hits = _run_search(q, config, page * size, filters)
        took_ms = (time.perf_counter() - start) * 1000
    return {
        "query": q,
        "config": config,
        "page": page,
        "size": size,
        # Number of hits search() returned for page * size, not the number of matches in the
        # index (search() does not compute it). Decided with Fabio, 16 Nov.
        "total": len(hits),
        "took_ms": round(took_ms, 1),
        "hits": [asdict(h) for h in hits[(page - 1) * size : page * size]],
    }


@app.get("/api/doc/{doc_id}")
def api_doc(doc_id: str) -> dict:
    if fake_mode():
        doc = fake.document(doc_id)
        if doc is None:
            raise HTTPException(404, f"no document {doc_id!r}")
        return doc
    from wikisearch.search.es import client

    index = index_name(CONFIGS[DEFAULT_CONFIG]["analyzer"])
    try:
        resp = client().get(index=index, id=doc_id, source_excludes=["embedding"])
    except NotFoundError as exc:
        raise HTTPException(404, f"no document {doc_id!r}") from exc
    except ESConnectionError as exc:
        raise HTTPException(503, "Elasticsearch is not reachable") from exc
    return resp["_source"]


@app.get("/api/facets")
def api_facets(q: str = "", config: str = DEFAULT_CONFIG) -> dict:
    cfg = _check_config(config)
    if fake_mode():
        return {"query": q, "config": config, **fake.FACETS}
    from wikisearch.search.es import client, multi_match

    # Facets are lexical by design, also for knn configurations: they use the BM25 query on the
    # configuration's index (fields of the default configuration when it has none, e.g. knn).
    fields = cfg.get("fields") or CONFIGS[DEFAULT_CONFIG]["fields"]
    query = multi_match(q, fields, cfg.get("tie_breaker", 0.3)) if q.strip() else {"match_all": {}}
    aggs = {
        "categories": {"terms": {"field": "categories", "size": 15}},
        "agencies": {"terms": {"field": "agencies", "size": 10}},
        "years": {
            "date_histogram": {
                "field": "date",
                "calendar_interval": "year",
                "format": "yyyy",
                "min_doc_count": 1,
            }
        },
    }
    try:
        resp = client().search(index=index_name(cfg["analyzer"]), query=query, aggs=aggs, size=0)
    except ESConnectionError as exc:
        raise HTTPException(503, "Elasticsearch is not reachable") from exc
    out = resp["aggregations"]
    return {
        "query": q,
        "config": config,
        "categories": [{"value": b["key"], "count": b["doc_count"]} for b in out["categories"]["buckets"]],
        "agencies": [{"value": b["key"], "count": b["doc_count"]} for b in out["agencies"]["buckets"]],
        "years": [{"value": b["key_as_string"], "count": b["doc_count"]} for b in out["years"]["buckets"]],
    }


# Mounted last: the /api routes above take precedence, everything else is the static UI.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
