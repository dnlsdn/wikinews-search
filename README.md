# wikinews-search

A search engine with a web interface over the Italian Wikinews news archive (about 12,000 pages,
2004-2025), built on Elasticsearch, with an evaluation of the design choices behind it.

Homework 4 of the Data Engineering course (Ingegneria dei Dati, Roma Tre, 2026/27) by
Gioia Buratti, Fabio Massimo Di Marco and Daniel Sadun.

Status: in progress. See `PLAN.md` and `STATE.md`.

## Requirements

1. Docker Desktop (Elasticsearch runs in a container with a 1 GB heap; give Docker at least 3 GB
   of memory). On Windows Docker Desktop needs WSL 2.
2. [uv](https://docs.astral.sh/uv/): it installs Python 3.12 by itself.
3. git and GitHub CLI (`gh auth login`), with access to the repository.
4. About 5 GB of free disk for the Docker image, the dump, the index and the embedding model.

## Setup

```bash
git clone https://github.com/dnlsdn/wikinews-search.git
cd wikinews-search
uv sync
docker compose up -d
curl localhost:9200
```

Download the dump (73 MB) and extract it into `data/raw/`:

```bash
curl -L -o data/raw/itwikinews.tar.gz https://dumps.wikimedia.org/other/enterprise_html/runs/20250320/itwikinews-NS0-20250320-ENTERPRISE-HTML.json.tar.gz
tar -xzf data/raw/itwikinews.tar.gz -C data/raw
```

On Windows (PowerShell) use `curl.exe` instead of `curl`; `tar` is built in. The result must be
`data/raw/itwikinews_namespace_0_0.ndjson` (591 MB, 12,261 lines).

Elasticsearch takes about a minute to start the first time. `curl localhost:9200` must answer
with `"number" : "9.5.0"`; the container uses about 1.5 GB of memory. `docker compose down` stops
it and keeps the indices (they live in the `esdata` volume).

If it does not answer:

1. `docker logs --tail 30 wikinews-es`.
2. `read past EOF ... elasticsearch.keystore`: the container was created while the disk was full
   and its keystore is truncated. Free some disk, then `docker compose down` and
   `docker compose up -d` (this recreates the container; the data volume is kept).
3. Docker Desktop says "unable to start" with "no space left on device" in its logs: the disk is
   full. Free disk and restart Docker Desktop; on a Mac with 8 GB of RAM, swap also takes disk
   space, so close heavy applications.

## Usage

Sections to be completed as the parts are implemented: parsing and indexing, running the web app,
reproducing the experiments.

### Search and web app

Needs Elasticsearch running and the indices built (parsing and indexing above).

```bash
uv run uvicorn wikisearch.web.app:app
```

Then open http://localhost:8000. The first query of a vector configuration (`knn`, `hybrid-rrf`,
...) loads the embedding model, `intfloat/multilingual-e5-small`: about 25 s, and 471 MB of
download the very first time. Every later query takes well under a second.

What the interface does:

1. **Search** with a configuration chosen next to the search box. Each result shows title, date,
   a snippet with the query words highlighted, categories, source agencies and a "not published"
   label for pages that are not news articles (index pages, tables, drafts).
2. **Filters** in the left column: date range, categories and agencies (with counts for the
   current query), "published only". Every change reruns the search.
3. **Compare** two configurations side by side on the same query: tick "Compare" and pick the
   second one.
4. **Document view**: click a title for the full text, sources, linked Wikipedia entities and a
   link to the original Wikinews page.
5. The query, configurations and filters are kept in the URL, so a search can be shared as a
   link, e.g. http://localhost:8000/?q=terremoto+in+Abruzzo&config=bm25-italian&compare=1&config2=knn.
   The links of the live demo are in `docs/demo.md`.

Configurations (`wikisearch/search/configs.py`; each one is a variant of the experiments in
`PLAN.md`):

| configuration | what it does |
|---|---|
| `bm25-standard` | BM25 on title (weight 3), lead (2) and body, standard analyzer |
| `bm25-italian` | the same with the Italian analyzer (elision, stop words, light stemming) |
| `bm25-italian-title`, `-body`, `-flat` | title only, body only, three fields with equal weights |
| `bm25-italian-leak` | also searches the titles of the cited sources (only to measure leakage) |
| `knn` | nearest neighbours of the query embedding (e5-small, 384 dimensions, HNSW) |
| `knn-int8`, `knn-bbq` | the same on quantized vector indices (8-bit, binary); they need their own indices: `uv run python -m wikisearch.ingest.index --analyzers italian --vector-index int8_hnsw bbq_hnsw` |
| `hybrid-rrf` (default) | BM25 and kNN, 100 hits each, fused with reciprocal rank fusion (k = 60) |
| `hybrid-rrf-published` | the same, with published pages boosted by 1.5 |

From the command line, for quick checks:

```bash
uv run python -m wikisearch.search "terremoto abruzzo" --config bm25-italian
```

Without Elasticsearch, the web app can run on three fake results (used by the tests and to work
on the interface): `WIKISEARCH_FAKE=1 uv run uvicorn wikisearch.web.app:app` (PowerShell:
`$env:WIKISEARCH_FAKE=1; uv run uvicorn wikisearch.web.app:app`, then
`Remove-Item Env:WIKISEARCH_FAKE`).

The API used by the interface (`docs/contracts.md`, section 4): `/api/search`, `/api/doc/{id}`,
`/api/facets`, `/api/configs`.

### Evaluation

Every command below is the same in PowerShell. They need the parsed corpus
(`data/processed/docs.jsonl`); all but the first also need Elasticsearch and the indices.

**Test sets** (`evaluation/testsets/`, committed, so rebuilding them is only needed to check them):

1. `fonti`, known-item search: the query is the headline of an external source cited by an
   article, the only relevant document is the article. 7,072 queries, one per article, and a
   fixed subset of 1,000 (`queries_dev.tsv`, seed 42). Rebuild it and print the funnel, the
   overlap buckets and the leakage check with:

   ```bash
   uv run python -m evaluation.build_fonti
   ```

   `--show-language 50` also prints 50 titles dropped and 50 kept by the language rule, for an
   eye check.
2. `manual`: 30 queries written by the group (`queries.tsv`, each with its type and information
   need), the top 10 of the five configurations compared on it pooled and judged 0 / 1 / 2 by
   the three authors (`GUIDELINES.md`). The steps, in order:

   ```bash
   uv run python -m evaluation.pool
   uv run python -m evaluation.judge --judge <name>
   uv run python -m evaluation.merge_judgments
   ```

   `pool` writes one blind assignment file per judge in `judging/`; `judge` shows one document at
   a time and saves every grade at once in `judgments/<name>.tsv` (stop with `q`, resume later);
   `merge_judgments` computes Cohen's kappa on the queries judged twice (M01-M10), lists the
   disagreements and writes `qrels.txt`.

**Reproducing every number** (an estimated 20 minutes on a laptop; close other heavy applications, the
latencies depend on it):

```bash
uv run python -m evaluation.run
```

For every test set and configuration it searches each query (k = 100), writes the run to
`results/runs/` (not committed), and computes from the runs:

| file | content |
|---|---|
| `results/metrics/fonti.csv`, `manual.csv` | one row per configuration and the `random` baseline: MRR@10, R@10, R@100 (`fonti`, also per overlap bucket); P@10, nDCG@10, MAP, MRR@10 (`manual`); each with its 95% bootstrap interval |
| `results/metrics/<set>_per_query.csv` | the per-query scores behind the intervals and the tests |
| `results/metrics/significance.csv` | each comparison of the experiments E1-E5 (and E8): difference of the means, p-value of the paired randomization test, p-value corrected with Holm-Bonferroni within the experiment |
| `results/metrics/latency.csv` | query latency p50 / p95 per configuration (E6), measured on 500 `fonti` queries with the configurations in random order |
| `results/summary.md` | all the tables above, with the machine and the commit |

Seeds are fixed (42), so the same corpus and indices give the same numbers; latencies depend on
the machine. Options: `--dev` runs on the 1,000 dev queries of `fonti` and writes under
`results/runs/dev/` (a few minutes, for development); `--configs <name> ...` reruns only some
configurations and reuses the other runs; the `manual` set is skipped until `qrels.txt` exists;
the E8 configurations are skipped where their indices are not built.

Tests of the metrics (hand-computed examples), the significance tests, the test-set builders and
the runner, all without Elasticsearch: `uv run pytest -q tests/test_metrics.py
tests/test_build_fonti.py tests/test_judging.py tests/test_merge_judgments.py tests/test_run.py`.
