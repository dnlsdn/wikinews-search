"""Build the Elasticsearch indices from the processed documents (step D3, contract:
docs/contracts.md section 2).

One index per text analysis variant (`config.ANALYZER_VARIANTS`): same documents, same fields,
different analyzer on the text fields. Comparing them is experiment E1.

Run:
    uv run python -m wikisearch.ingest.index                      # full corpus, all variants
    uv run python -m wikisearch.ingest.index --input data/sample/docs.sample.jsonl
    uv run python -m wikisearch.ingest.index --repeat 3           # timings for E6

Every build appends one row per index to `results/indexing.csv` (time, documents, size).
"""

import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path

from elasticsearch import helpers

from wikisearch import config
from wikisearch.search.es import client

INDEXING_CSV = config.ROOT / "results" / "indexing.csv"
CSV_FIELDS = ["timestamp", "index", "analyzer", "input", "documents", "embeddings", "seconds", "size_bytes"]
CHUNK_SIZE = 500


def mapping(analyzer: str, vector_index_type: str = "hnsw") -> dict:
    """Settings and mappings of one index. `analyzer` is an Elasticsearch built-in analyzer name."""
    text = {"type": "text", "analyzer": analyzer}
    keyword = {"type": "keyword"}
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            # the store size is cached for 10 s by default: measure the real size after the load
            "store.stats_refresh_interval": "0s",
        },
        "mappings": {
            "dynamic": "strict",  # a field not listed here is an error, not a silent new mapping
            "properties": {
                "id": keyword,
                "title": {**text, "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
                "url": {"type": "keyword", "index": False},
                "date": {"type": "date", "format": "yyyy-MM-dd"},
                "date_source": keyword,
                "lead": text,
                "body": text,
                "categories": keyword,
                "sources": {"type": "object", "enabled": False},  # stored, never searched
                "sources_text": text,  # searched only by the leakage ablation (E4)
                "agencies": keyword,
                "entities": keyword,
                "wikidata_id": keyword,
                "image_url": {"type": "keyword", "index": False},
                "published": {"type": "boolean"},
                "series_key": keyword,
                "n_chars": {"type": "integer"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": config.EMBEDDING_DIMS,
                    "index": True,
                    "similarity": "cosine",
                    # explicit: recent versions default to a quantized structure (that is E8)
                    "index_options": {"type": vector_index_type},
                },
            },
        },
    }


def read_docs(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_embeddings(ids: list[str]) -> dict[str, list[float]]:
    """Vectors of the shared embeddings file, matched to documents by id (never by position).
    Fails if a document has no vector: the index would silently miss it in the knn search."""
    import numpy as np

    vectors = np.load(config.EMBEDDINGS_NPY)
    vector_ids = json.loads(config.EMBEDDINGS_IDS.read_text(encoding="utf-8"))
    if len(vector_ids) != len(vectors):
        raise ValueError(f"{config.EMBEDDINGS_IDS} has {len(vector_ids)} ids for {len(vectors)} vectors")
    row = {doc_id: i for i, doc_id in enumerate(vector_ids)}
    missing = [doc_id for doc_id in ids if doc_id not in row]
    if missing:
        raise ValueError(f"{len(missing)} documents have no embedding (first: {missing[:5]}); "
                         "recompute them with `python -m wikisearch.ingest.embed`")
    return {doc_id: vectors[row[doc_id]].tolist() for doc_id in ids}


def to_source(doc: dict, embedding: list[float] | None = None) -> dict:
    """The indexed document: the processed document plus the derived search fields."""
    source = dict(doc)
    source["sources_text"] = " ".join(s["title"] for s in doc["sources"] if s.get("title"))
    if embedding is not None:
        source["embedding"] = embedding
    return source


def build_index(name: str, analyzer: str, docs: list[dict], vectors: dict | None) -> dict:
    """Delete and recreate one index, bulk-load the documents, return the measurements."""
    es = client()
    es.indices.delete(index=name, ignore_unavailable=True)
    body = mapping(analyzer)
    es.indices.create(index=name, settings=body["settings"], mappings=body["mappings"])
    es.indices.put_settings(index=name, settings={"index": {"refresh_interval": "-1"}})

    actions = ({"_index": name, "_id": d["id"], "_source": to_source(d, vectors[d["id"]] if vectors else None)}
               for d in docs)
    start = time.perf_counter()
    ok, errors = helpers.bulk(es.options(request_timeout=300), actions, chunk_size=CHUNK_SIZE,
                              raise_on_error=False)
    es.indices.put_settings(index=name, settings={"index": {"refresh_interval": "1s"}})
    es.indices.refresh(index=name)
    es.indices.flush(index=name)
    seconds = time.perf_counter() - start
    if errors:
        raise RuntimeError(f"{len(errors)} documents failed in {name}, first: {errors[0]}")

    count = es.count(index=name)["count"]
    if count != len(docs):
        raise RuntimeError(f"{name} holds {count} documents, expected {len(docs)}")
    size = es.indices.stats(index=name, metric="store")["indices"][name]["primaries"]["store"]["size_in_bytes"]
    return {"timestamp": datetime.now().isoformat(timespec="seconds"), "index": name, "analyzer": analyzer, "documents": count, "embeddings": vectors is not None,
            "seconds": round(seconds, 2), "size_bytes": size}


def append_csv(rows: list[dict], input_path: Path) -> None:
    INDEXING_CSV.parent.mkdir(parents=True, exist_ok=True)
    new = not INDEXING_CSV.exists()
    with open(INDEXING_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            writer.writeheader()
        for row in rows:
            try:
                shown = input_path.resolve().relative_to(config.ROOT).as_posix()
            except ValueError:
                shown = input_path.name
            writer.writerow({"input": shown, **row})


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Elasticsearch indices (step D3).")
    parser.add_argument("--input", type=Path, default=config.DOCS_JSONL)
    parser.add_argument("--analyzers", nargs="+", default=config.ANALYZER_VARIANTS,
                        choices=config.ANALYZER_VARIANTS)
    parser.add_argument("--no-embeddings", action="store_true",
                        help="index without vectors even if data/shared/embeddings.npy exists")
    parser.add_argument("--repeat", type=int, default=1, help="build each index this many times (timings)")
    parser.add_argument("--no-csv", action="store_true", help="do not append to results/indexing.csv")
    args = parser.parse_args()

    docs = read_docs(args.input)
    vectors = None
    if not args.no_embeddings and config.EMBEDDINGS_NPY.exists():
        vectors = load_embeddings([d["id"] for d in docs])
    print(f"{len(docs)} documents from {args.input}, embeddings: {'yes' if vectors else 'no'}")

    rows = []
    for run in range(args.repeat):
        for analyzer in args.analyzers:
            row = build_index(config.index_name(analyzer), analyzer, docs, vectors)
            rows.append(row)
            print(f"run {run + 1}/{args.repeat} {row['index']}: {row['documents']} docs in "
                  f"{row['seconds']} s, {row['size_bytes'] / 1e6:.1f} MB")
    if not args.no_csv:
        append_csv(rows, args.input)
        print(f"appended {len(rows)} rows to {INDEXING_CSV}")


if __name__ == "__main__":
    main()
