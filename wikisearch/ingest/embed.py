"""Compute the document embeddings once, for everyone (step D4, contract: docs/contracts.md
section 2).

Model `config.EMBEDDING_MODEL` (multilingual-e5-small, 384 dimensions). Text embedded:
`"passage: " + title + ". " + lead` (e5 models are trained with the "passage: " and "query: "
prefixes; the search side embeds queries with "query: "). Vectors are L2-normalized, so cosine
similarity is a dot product.

Output, committed so that the other laptops index the same vectors without computing them:
`data/shared/embeddings.npy` (float32, one row per document) and `data/shared/embeddings_ids.json`
(the document id of each row). The indexer matches rows to documents by id.

Run: `uv run python -m wikisearch.ingest.embed` (downloads the model once, about 470 MB), then
`uv run python -m wikisearch.ingest.index` to load the vectors into the indices.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np

from wikisearch import config

BATCH_SIZE = 32


def passage(doc: dict) -> str:
    title = doc["title"].strip()
    lead = doc["lead"].strip()
    return config.PASSAGE_PREFIX + (f"{title}. {lead}" if lead else title)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute the shared document embeddings (step D4).")
    parser.add_argument("--input", type=Path, default=config.DOCS_JSONL)
    parser.add_argument("--device", default="cpu", help="cpu (default) or mps on Apple silicon")
    args = parser.parse_args()

    from sentence_transformers import SentenceTransformer

    with open(args.input, encoding="utf-8") as f:
        docs = [json.loads(line) for line in f if line.strip()]
    texts = [passage(d) for d in docs]

    model = SentenceTransformer(config.EMBEDDING_MODEL, device=args.device)
    start = time.perf_counter()
    vectors = model.encode(texts, batch_size=BATCH_SIZE, normalize_embeddings=True,
                           show_progress_bar=True, convert_to_numpy=True).astype(np.float32)
    seconds = time.perf_counter() - start
    if vectors.shape != (len(docs), config.EMBEDDING_DIMS):
        raise RuntimeError(f"unexpected shape {vectors.shape}")

    config.EMBEDDINGS_NPY.parent.mkdir(parents=True, exist_ok=True)
    np.save(config.EMBEDDINGS_NPY, vectors)
    config.EMBEDDINGS_IDS.write_text(json.dumps([d["id"] for d in docs]) + "\n", encoding="utf-8")
    print(f"{len(docs)} documents embedded in {seconds:.0f} s on {args.device} "
          f"({len(docs) / seconds:.0f} docs/s); wrote {config.EMBEDDINGS_NPY} "
          f"({config.EMBEDDINGS_NPY.stat().st_size / 1e6:.1f} MB) and {config.EMBEDDINGS_IDS}")


if __name__ == "__main__":
    main()
