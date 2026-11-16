"""Web API tests in fake mode (WIKISEARCH_FAKE=1): no Elasticsearch needed."""

import pytest
from fastapi.testclient import TestClient

from wikisearch.search.configs import CONFIGS, DEFAULT_CONFIG
from wikisearch.web.app import app

HIT_FIELDS = {"id", "score", "title", "url", "date", "snippet", "categories", "agencies", "image_url", "published"}
DOC_FIELDS = {
    "id", "title", "url", "date", "date_source", "lead", "body", "categories", "sources", "agencies",
    "entities", "wikidata_id", "image_url", "published", "series_key", "n_chars",
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("WIKISEARCH_FAKE", "1")
    return TestClient(app)


def test_index_page_is_served(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<html" in resp.text
    assert client.get("/app.js").status_code == 200
    assert client.get("/style.css").status_code == 200


def test_configs(client):
    data = client.get("/api/configs").json()
    assert data["default"] == DEFAULT_CONFIG
    assert data["configs"] == list(CONFIGS)


def test_search_returns_three_fake_hits(client):
    data = client.get("/api/search", params={"q": "governo"}).json()
    assert data["query"] == "governo"
    assert data["config"] == DEFAULT_CONFIG
    assert (data["page"], data["size"], data["total"]) == (1, 10, 3)
    assert data["took_ms"] >= 0
    assert len(data["hits"]) == 3
    for hit in data["hits"]:
        assert set(hit) == HIT_FIELDS


def test_search_pagination(client):
    # 3 fake hits, 2 per page: page 1 has 2, page 2 has 1, page 3 is empty.
    pages = [client.get("/api/search", params={"q": "x", "size": 2, "page": p}).json() for p in (1, 2, 3)]
    assert [len(p["hits"]) for p in pages] == [2, 1, 0]
    assert pages[0]["hits"][0]["id"] != pages[1]["hits"][0]["id"]


def test_search_accepts_k_as_page_size(client):
    data = client.get("/api/search", params={"q": "x", "k": 1}).json()
    assert data["size"] == 1 and len(data["hits"]) == 1


def test_search_with_filters_and_other_config(client):
    params = {
        "q": "governo", "config": "bm25-italian", "date_from": "2008-01-01", "date_to": "2009-12-31",
        "category": ["Italia", "Abruzzo"], "agency": "ANSA", "published": "true",
    }
    resp = client.get("/api/search", params=params)
    assert resp.status_code == 200
    assert resp.json()["config"] == "bm25-italian"


def test_empty_query_returns_no_hits(client):
    data = client.get("/api/search", params={"q": "  "}).json()
    assert data["hits"] == [] and data["total"] == 0


def test_search_rejects_bad_input(client):
    assert client.get("/api/search", params={"q": "x", "config": "nope"}).status_code == 400
    assert client.get("/api/search", params={"q": "x", "date_from": "21/03/2008"}).status_code == 422
    assert client.get("/api/search", params={"q": "x", "page": 0}).status_code == 422


def test_doc_has_every_contract_field(client):
    doc = client.get("/api/doc/fake-1").json()
    assert set(doc) >= DOC_FIELDS
    assert "embedding" not in doc
    assert client.get("/api/doc/does-not-exist").status_code == 404


def test_facets(client):
    data = client.get("/api/facets", params={"q": "governo", "config": "knn"}).json()
    assert data["config"] == "knn"
    for key in ("categories", "agencies", "years"):
        assert data[key] and all(set(b) == {"value", "count"} for b in data[key])
    assert client.get("/api/facets", params={"config": "nope"}).status_code == 400
