"""Tests of the search function (owner: Fabio).

Unit tests need nothing; the integration tests run only when Elasticsearch answers on
localhost:9200 and the indices are built (otherwise they are skipped).
"""

import pytest

from wikisearch.schema import Filters, Hit
from wikisearch.search import search
from wikisearch.search.configs import CONFIGS
from wikisearch.search.es import boost_published, client, filters_to_es, snippet

BM25_CONFIGS = [name for name, cfg in CONFIGS.items() if cfg["mode"] == "bm25"]


# --- filters_to_es -----------------------------------------------------------------------------


def test_no_filters_means_no_clauses():
    assert filters_to_es(None) == []
    assert filters_to_es(Filters()) == []


def test_every_filter_becomes_one_clause():
    clauses = filters_to_es(
        Filters(
            date_from="2008-01-01",
            date_to="2008-12-31",
            categories=["Italia", "Politica e conflitti"],
            agencies=["ANSA", "la Repubblica"],
            published=True,
        )
    )
    assert clauses == [
        {"range": {"date": {"gte": "2008-01-01", "lte": "2008-12-31"}}},
        {"term": {"categories": "Italia"}},  # all categories must match: one term each
        {"term": {"categories": "Politica e conflitti"}},
        {"terms": {"agencies": ["ANSA", "la Repubblica"]}},  # any agency: one terms
        {"term": {"published": True}},
    ]


def test_open_date_range_and_published_false():
    assert filters_to_es(Filters(date_to="2005-06-30", published=False)) == [
        {"range": {"date": {"lte": "2005-06-30"}}},
        {"term": {"published": False}},
    ]


# --- snippet ------------------------------------------------------------------------------------


def test_snippet_prefers_the_lead_fragment():
    hl = {"body": ["nel <em>body</em>"], "lead": ["nel <em>lead</em>"]}
    assert snippet(hl, "lead text") == "nel <em>lead</em>"
    assert snippet({"body": ["nel <em>body</em>"]}, "lead text") == "nel <em>body</em>"


def test_snippet_falls_back_to_the_escaped_start_of_the_lead():
    lead = "L'Italia <b>" + "x" * 300
    out = snippet(None, lead)
    assert out.startswith("L&#x27;Italia &lt;b&gt;")  # no markup from the document text
    assert "<" not in out
    assert snippet({}, None) == ""


# --- boost_published ----------------------------------------------------------------------------


def _hit(doc_id: str, score: float, published: bool) -> Hit:
    return Hit(id=doc_id, score=score, title=doc_id, url="", published=published)


def test_boost_reorders_and_cuts_to_k():
    # a: 10 (not published), b: 8 * 1.5 = 12, c: 6 * 1.5 = 9, d: 9 (not published)
    hits = [_hit("a", 10, False), _hit("b", 8, True), _hit("d", 9, False), _hit("c", 6, True)]
    out = boost_published(hits, 1.5, k=3)
    assert [h.id for h in out] == ["b", "a", "c"]  # c and d tie at 9: broken by id
    assert out[0].score == 12
    assert hits[1].score == 8  # the input is not modified


# --- search() without Elasticsearch -------------------------------------------------------------


def test_unknown_configuration_is_an_error():
    with pytest.raises(ValueError):
        search("governo", "no-such-config")


def test_empty_query_returns_nothing_without_calling_elasticsearch():
    assert search("   ", "bm25-italian") == []
    assert search("governo", "bm25-italian", k=0) == []


# --- integration (Elasticsearch running, indices built) ----------------------------------------


def _es_ready() -> bool:
    try:
        return bool(client().ping())
    except Exception:
        return False


needs_es = pytest.mark.skipif(not _es_ready(), reason="Elasticsearch not running on this laptop")


@needs_es
@pytest.mark.parametrize("config", BM25_CONFIGS)
def test_every_bm25_configuration_returns_hits(config):
    hits = search("terremoto abruzzo", config, k=5)
    assert 1 <= len(hits) <= 5
    assert all(isinstance(h, Hit) and h.id and h.title for h in hits)
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


@needs_es
def test_filters_are_applied():
    hits = search(
        "terremoto",
        "bm25-italian",
        k=50,
        filters=Filters(date_from="2009-04-01", date_to="2009-04-30", published=True),
    )
    assert hits
    assert all(h.published and h.date and "2009-04-01" <= h.date <= "2009-04-30" for h in hits)
    hidden = search("calcio", "bm25-italian", k=20, filters=Filters(published=False))
    assert hidden and all(not h.published for h in hidden)


@needs_es
def test_italian_stemming_matches_plural_forms():
    # "terremoti" (plural) is found by the singular query only with the italian analyzer (E1)
    titles = [h.title for h in search("terremoto abruzzo", "bm25-italian", k=5)]
    assert any("terremoti" in t for t in titles)
