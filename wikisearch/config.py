"""Settings shared by ingestion, search and evaluation. Changing a value here is a contract change."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ES_URL = os.environ.get("ES_URL", "http://localhost:9200")

RAW_DUMP = ROOT / "data" / "raw" / "itwikinews_namespace_0_0.ndjson"
DOCS_JSONL = ROOT / "data" / "processed" / "docs.jsonl"
SAMPLE_JSONL = ROOT / "data" / "sample" / "docs.sample.jsonl"
# Document embeddings are computed once by Daniel (step D4) and committed, so that all three
# laptops index exactly the same vectors (about 17 MB).
EMBEDDINGS_NPY = ROOT / "data" / "shared" / "embeddings.npy"
EMBEDDINGS_IDS = ROOT / "data" / "shared" / "embeddings_ids.json"

INDEX_PREFIX = "wikinews-"
ANALYZER_VARIANTS = ["standard", "italian"]
# Structure of the `embedding` field (experiment E8). `hnsw` keeps the float32 vectors and is the
# structure of the main indices; the others are extra indices with the same documents, named
# with the suffix, e.g. `wikinews-italian-int8`.
VECTOR_INDEX_TYPES = {"hnsw": "", "int8_hnsw": "-int8", "bbq_hnsw": "-bbq"}

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_DIMS = 384
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "


def index_name(analyzer: str, vector_index: str = "hnsw") -> str:
    return f"{INDEX_PREFIX}{analyzer}{VECTOR_INDEX_TYPES[vector_index]}"
