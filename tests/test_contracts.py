"""Contract tests: they check the interfaces of docs/contracts.md, so that a change in one part
that breaks another part fails here, in everyone's `uv run pytest -q`, before the push.

Tests on files that do not exist yet are skipped, and start to run as soon as the file is pushed.
"""

import json
from pathlib import Path

import pytest

from wikisearch import config
from wikisearch.schema import Hit
from wikisearch.search.configs import CONFIGS, DEFAULT_CONFIG

DOC_FIELDS = {
    "id": str, "title": str, "url": str, "date": (str, type(None)), "date_source": str,
    "lead": str, "body": str, "categories": list, "sources": list, "agencies": list,
    "entities": list, "wikidata_id": (str, type(None)), "image_url": (str, type(None)),
    "published": bool, "series_key": str, "n_chars": int,
}
SOURCE_FIELDS = {"agency", "title", "url", "date", "foreign"}
TESTSETS = config.ROOT / "evaluation" / "testsets"


def test_configs_are_well_formed():
    assert DEFAULT_CONFIG in CONFIGS
    for name, cfg in CONFIGS.items():
        assert cfg["analyzer"] in config.ANALYZER_VARIANTS, name
        assert cfg.get("vector_index", "hnsw") in config.VECTOR_INDEX_TYPES, name
        assert cfg["mode"] in {"bm25", "knn", "hybrid"}, name
        if cfg["mode"] in {"bm25", "hybrid"}:
            assert cfg["fields"], name
        if cfg["mode"] == "hybrid":
            assert cfg["rrf_k"] > 0 and cfg["depth"] > 0, name


def test_sample_documents_follow_the_contract():
    if not config.SAMPLE_JSONL.exists():
        pytest.skip("sample not pushed yet (step D2)")
    lines = config.SAMPLE_JSONL.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 100
    ids = set()
    for line in lines:
        doc = json.loads(line)
        assert set(doc) >= set(DOC_FIELDS), set(DOC_FIELDS) - set(doc)
        for field, kind in DOC_FIELDS.items():
            assert isinstance(doc[field], kind), (doc["id"], field)
        for source in doc["sources"]:
            assert set(source) >= SOURCE_FIELDS, (doc["id"], source)
        if doc["date"]:
            assert len(doc["date"]) == 10 and doc["date"][4] == "-", (doc["id"], doc["date"])
        assert not any(c.startswith("Categoria:") for c in doc["categories"]), doc["id"]
        assert "Pubblicati" not in doc["categories"], doc["id"]
        assert doc["id"] not in ids, ("duplicate id", doc["id"])
        ids.add(doc["id"])
    assert any(not json.loads(line)["published"] for line in lines), "sample has no non-published page"


def test_shared_embeddings_match_their_ids():
    if not config.EMBEDDINGS_NPY.exists():
        pytest.skip("embeddings not pushed yet (step D4)")
    import numpy as np

    vectors = np.load(config.EMBEDDINGS_NPY)
    ids = json.loads(config.EMBEDDINGS_IDS.read_text(encoding="utf-8"))
    assert vectors.shape == (len(ids), config.EMBEDDING_DIMS)
    assert vectors.dtype == np.float32
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("path", sorted(TESTSETS.glob("*/queries.tsv")), ids=lambda p: p.parent.name)
def test_queries_files(path: Path):
    qids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        qid, text, meta = line.split("\t")
        assert text.strip(), qid
        json.loads(meta)
        assert qid not in qids, qid
        qids.add(qid)


@pytest.mark.parametrize("path", sorted(TESTSETS.glob("*/qrels.txt")), ids=lambda p: p.parent.name)
def test_qrels_files(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        qid, zero, doc_id, grade = line.split()
        assert zero == "0" and int(grade) in {0, 1, 2}, line


def test_search_returns_hits_when_implemented():
    from wikisearch.search import search

    try:
        hits = search("governo", DEFAULT_CONFIG, k=3)
    except NotImplementedError:
        pytest.skip("search not implemented yet (step F1)")
    except Exception as exc:  # Elasticsearch not running or index not built on this laptop
        pytest.skip(f"search not available here: {exc}")
    assert len(hits) <= 3
    assert all(isinstance(h, Hit) for h in hits)
