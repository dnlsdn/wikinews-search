"""Tests of the search function (owner: Fabio).

Unit tests need nothing; the integration tests run only when Elasticsearch answers on
localhost:9200 and the indices are built (otherwise they are skipped).
"""

import pytest

from wikisearch.schema import Filters, Hit
from wikisearch.search import search
from wikisearch.search.configs import CONFIGS
from wikisearch.search import embed
from wikisearch.search.es import boost_published, client, filters_to_es, knn_query, rrf_fuse, snippet

BM25_CONFIGS = [name for name, cfg in CONFIGS.items() if cfg["mode"] == "bm25"]
VECTOR_CONFIGS = [name for name, cfg in CONFIGS.items() if cfg["mode"] in ("knn", "hybrid")]


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


# --- rrf_fuse -----------------------------------------------------------------------------------


def test_rrf_fuse_hand_computed_example():
    # k = 60. BM25 ranks a, b, c; kNN ranks c, a, d.
    #   a: 1/61 + 1/62 = 0.032522   (1st and 2nd)
    #   c: 1/63 + 1/61 = 0.032266   (3rd and 1st)
    #   b: 1/62        = 0.016129   (2nd, BM25 only)
    #   d: 1/63        = 0.015873   (3rd, kNN only)
    fused = rrf_fuse([["a", "b", "c"], ["c", "a", "d"]], k=60)
    assert [doc for doc, _ in fused] == ["a", "c", "b", "d"]
    assert fused[0][1] == pytest.approx(1 / 61 + 1 / 62)
    assert fused[1][1] == pytest.approx(1 / 63 + 1 / 61)
    assert fused[2][1] == pytest.approx(1 / 62)
    assert fused[3][1] == pytest.approx(1 / 63)


def test_rrf_fuse_breaks_ties_by_id_and_handles_empty_lists():
    # x is 1st in one list, y is 1st in the other: same score, x before y by id
    assert [doc for doc, _ in rrf_fuse([["y"], ["x"]], k=60)] == ["x", "y"]
    assert rrf_fuse([[], []], k=60) == []
    assert rrf_fuse([["a", "b"], []], k=60) == [("a", 1 / 61), ("b", 1 / 62)]


# --- knn_query ----------------------------------------------------------------------------------


def test_knn_query_uses_the_same_filters_as_bm25():
    q = knn_query((0.1, 0.2), k=10, filters=Filters(published=True))
    assert q == {
        "field": "embedding",
        "query_vector": [0.1, 0.2],
        "k": 10,
        "num_candidates": 100,
        "filter": [{"term": {"published": True}}],
    }
    assert "filter" not in knn_query((0.1,), k=50, filters=None)
    assert knn_query((0.1,), k=50, filters=None)["num_candidates"] == 500


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


@needs_es
def test_bm25_does_not_load_the_embedding_model(monkeypatch):
    def fail():
        raise AssertionError("the bm25 configurations must not load the embedding model")

    monkeypatch.setattr(embed, "model", fail)
    embed.embed_query.cache_clear()
    assert search("terremoto abruzzo", "bm25-italian", k=3)


@needs_es
@pytest.mark.parametrize("config", VECTOR_CONFIGS)
def test_every_vector_configuration_returns_hits(config):
    hits = search("terremoto abruzzo", config, k=5)
    assert len(hits) == 5
    assert all(isinstance(h, Hit) and h.id and h.title for h in hits)
    assert len({h.id for h in hits}) == 5
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


@needs_es
def test_knn_finds_the_meaning_without_the_words():
    # Daniel's D4 check: mine explosions, none of them containing the word "disastro"
    titles = " ".join(h.title.lower() for h in search("disastro in una miniera", "knn", k=5))
    assert "miniera" in titles or "minatori" in titles


@needs_es
@pytest.mark.parametrize("config", ["knn", "hybrid-rrf"])
def test_vector_configurations_apply_the_filters(config):
    hidden = search("calcio", config, k=20, filters=Filters(published=False))
    assert len(hidden) == 20 and all(not h.published for h in hidden)
    dated = search("terremoto", config, k=20, filters=Filters(date_from="2009-04-01", date_to="2009-04-30"))
    assert dated and all(h.date and "2009-04-01" <= h.date <= "2009-04-30" for h in dated)


@needs_es
def test_hybrid_score_is_the_rrf_score():
    hits = search("terremoto abruzzo", "hybrid-rrf", k=10)
    # at most 1/61 per list: no hit can score more than 2/61
    assert all(0 < h.score <= 2 / 61 + 1e-12 for h in hits)
