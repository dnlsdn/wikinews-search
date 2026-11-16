"""Settings shared by ingestion, search and evaluation. Changing a value here is a contract change."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ES_URL = os.environ.get("ES_URL", "http://localhost:9200")

RAW_DUMP = ROOT / "data" / "raw" / "itwikinews_namespace_0_0.ndjson"
DOCS_JSONL = ROOT / "data" / "processed" / "docs.jsonl"
SAMPLE_JSONL = ROOT / "data" / "sample" / "docs.sample.jsonl"
EMBEDDINGS_NPY = ROOT / "data" / "processed" / "embeddings.npy"

INDEX_PREFIX = "wikinews-"
ANALYZER_VARIANTS = ["standard", "italian"]

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_DIMS = 384
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "


def index_name(analyzer: str) -> str:
    return f"{INDEX_PREFIX}{analyzer}"
