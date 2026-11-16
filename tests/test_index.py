"""Tests of the indexer (step D3). The mapping tests need nothing; the last ones build a small
temporary index from the committed sample and are skipped when Elasticsearch is not running."""

import json

import numpy as np
import pytest

from wikisearch import config
from wikisearch.ingest import index as indexer

FIELDS = {"id", "title", "url", "date", "date_source", "lead", "body", "categories", "sources",
          "sources_text", "agencies", "entities", "wikidata_id", "image_url", "published",
          "series_key", "n_chars", "embedding"}


def test_mapping_follows_the_contract():
    props = indexer.mapping("italian")["mappings"]["properties"]
    assert set(props) == FIELDS
    for field in ("title", "lead", "body", "sources_text"):
        assert props[field] == {**props[field], "type": "text", "analyzer": "italian"}
    assert props["title"]["fields"]["keyword"]["type"] == "keyword"
    for field in ("categories", "agencies", "series_key"):
        assert props[field]["type"] == "keyword"
    assert props["date"]["type"] == "date"
    assert props["published"]["type"] == "boolean"
    assert props["sources"] == {"type": "object", "enabled": False}
    vector = props["embedding"]
    assert vector["dims"] == config.EMBEDDING_DIMS and vector["similarity"] == "cosine"
    assert vector["index_options"] == {"type": "hnsw"}
    assert indexer.mapping("standard")["mappings"]["properties"]["body"]["analyzer"] == "standard"


def test_vector_index_variants_for_e8():
    assert config.index_name("italian") == "wikinews-italian"
    assert config.index_name("italian", "hnsw") == "wikinews-italian"
    assert config.index_name("italian", "int8_hnsw") == "wikinews-italian-int8"
    assert config.index_name("italian", "bbq_hnsw") == "wikinews-italian-bbq"
    for vector_index in config.VECTOR_INDEX_TYPES:
        props = indexer.mapping("italian", vector_index)["mappings"]["properties"]
        assert props["embedding"]["index_options"] == {"type": vector_index}
        assert props["body"]["analyzer"] == "italian"  # only the vector structure changes


def test_sources_text_joins_the_source_titles_and_body_is_untouched():
    doc = {"id": "1", "body": "testo", "sources": [{"title": "Primo titolo"}, {"title": ""}, {"title": "Secondo"}]}
    source = indexer.to_source(doc)
    assert source["sources_text"] == "Primo titolo Secondo"
    assert source["body"] == "testo"
    assert "embedding" not in source
    assert "sources_text" not in doc  # the input document is not modified


def test_embeddings_are_matched_by_id(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "EMBEDDINGS_NPY", tmp_path / "e.npy")
    monkeypatch.setattr(config, "EMBEDDINGS_IDS", tmp_path / "e.json")
    np.save(config.EMBEDDINGS_NPY, np.array([[1.0] * 384, [2.0] * 384], dtype=np.float32))
    config.EMBEDDINGS_IDS.write_text(json.dumps(["b", "a"]), encoding="utf-8")
    vectors = indexer.load_embeddings(["a", "b"])
    assert vectors["a"][0] == 2.0 and vectors["b"][0] == 1.0
    with pytest.raises(ValueError, match="no embedding"):
        indexer.load_embeddings(["a", "c"])


def test_embedded_text_follows_the_contract():
    from wikisearch.ingest.embed import passage

    assert passage({"title": "Titolo ", "lead": " Primo paragrafo."}) == "passage: Titolo. Primo paragrafo."
    assert passage({"title": "Solo titolo", "lead": ""}) == "passage: Solo titolo"


@pytest.fixture(scope="module")
def es_index():
    from wikisearch.search.es import client

    try:
        client().info()
    except Exception as exc:
        pytest.skip(f"Elasticsearch not running: {exc}")
    docs = indexer.read_docs(config.SAMPLE_JSONL)[:50]
    name = "wikinews-pytest-tmp"
    row = indexer.build_index(name, "italian", docs, None)
    yield name, docs, row
    client().indices.delete(index=name, ignore_unavailable=True)


def test_index_holds_every_document(es_index):
    name, docs, row = es_index
    assert row["documents"] == len(docs)
    assert row["size_bytes"] > 0


def test_sources_are_searchable_only_in_sources_text(es_index):
    from wikisearch.search.es import client

    name, docs, _ = es_index
    doc = next(d for d in docs if any(len(s["title"].split()) >= 5 for s in d["sources"]))
    title = next(s["title"] for s in doc["sources"] if len(s["title"].split()) >= 5)
    phrase = lambda field: client().count(index=name, query={"match_phrase": {field: title}})["count"]
    assert phrase("sources_text") >= 1
    assert phrase("body") == 0


def test_italian_analyzer_stems(es_index):
    from wikisearch.search.es import client

    name, _, _ = es_index
    tokens = lambda text: [t["token"] for t in client().indices.analyze(index=name, field="body", text=text)["tokens"]]
    assert tokens("elezioni") == tokens("elezione")
    assert tokens("l'Italia") == tokens("Italia")  # elision
