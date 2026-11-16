# Brief: Fabio, search and interface

You are helping **Fabio Massimo Di Marco** (GitHub `fmdimarco`). Fabio owns retrieval and the web
interface: `wikisearch/search/` and `wikisearch/web/`. He presents the retrieval choices and runs
the live demo. Read `CLAUDE.md`, `STATE.md`, `PLAN.md` and `docs/contracts.md` before this file.

Deadline for everything in this brief: **Wednesday 18 November, 20:00** (code freeze).

## What the other two give you, and when

| From | What | Expected | How you know |
|---|---|---|---|
| Daniel | `data/sample/docs.sample.jsonl` (about 300 pages) and `python -m wikisearch.ingest.index --input <file>` | Mon 16 afternoon | log entry D2/D3 in `STATE.md` |
| Daniel | full indices `wikinews-standard`, `wikinews-italian` | Mon 16 evening | log entry D3 |
| Daniel | `embedding` field filled | Tue 17 | log entry D4 |
| Gioia | `evaluation/run.py` that calls your `search()` | Wed 18 | log entry G5 |

Everybody indexes on their own laptop: the dump is downloaded by each person (README), Daniel's
scripts build the indices locally. If a step you need is not pushed yet, do the next step in the
order below that does not need it, and say so in the log.

## Step 0: environment (first session only)

Fabio works on **Windows** (16 GB of RAM). Give him PowerShell commands.

1. Docker Desktop with the WSL 2 backend (the installer may ask to enable WSL and reboot), `uv`
   (https://docs.astral.sh/uv/, PowerShell installer), git. Check with `docker --version`,
   `uv --version`, `git --version`.
2. `uv sync` in the repository (it installs Python 3.12 and every dependency, including the
   embedding library: a few minutes).
3. `docker compose up -d`, then `curl.exe localhost:9200` must answer with a JSON containing
   `"number" : "9.5.0"`. If the container stops, `docker logs wikinews-es` says why.
4. Download and extract the dump into `data/raw/` (README, Windows notes).
5. Done when all four work. Nothing to commit.

## Step F3a (can start immediately): web app skeleton with a fake search

Goal: the interface exists before the index does.

1. `wikisearch/web/app.py`: FastAPI `app`. Serve `wikisearch/web/static/` at `/` (`index.html`)
   and implement the endpoints of `docs/contracts.md` section 4 with the response shapes below.
2. Environment variable `WIKISEARCH_FAKE=1` makes **every** endpoint answer without
   Elasticsearch: `/api/search` returns three hard-coded `Hit`s, `/api/doc/{id}` a fake document
   with all the fields of the contract, `/api/facets` a few fake counts. So the UI can be built
   before the index exists. Keep the fake mode: `tests/test_web.py` uses it with FastAPI's
   `TestClient` (httpx is already a dev dependency).
3. Response of `/api/search`:
   ```json
   {"query": "...", "config": "hybrid-rrf", "page": 1, "size": 10, "took_ms": 42,
    "hits": [{"id": "...", "score": 1.0, "title": "...", "url": "...", "date": "2008-03-21",
              "snippet": "... <em>governo</em> ...", "categories": ["Europa"], "agencies": ["ANSA"],
              "image_url": null, "published": true}]}
   ```
   `took_ms` is measured in Python around the `search()` call. Pagination: `page` and `size`
   (default 10), implemented by asking `search()` for `page * size` hits and slicing.
4. `/api/doc/{id}`: the full document from Elasticsearch (`get` on the default index), without
   `embedding`. 404 if missing.
5. `/api/configs`: `{"default": DEFAULT_CONFIG, "configs": [names...]}` from `configs.py`.
6. `/api/facets`: terms aggregations on `categories` (size 15), `agencies` (size 10) and a
   `date_histogram` on `date` per year, computed with the BM25 query of the selected
   configuration's index (also when the configuration is `knn`: facets are lexical by design).
7. Done when the app started in fake mode shows the UI with the three fake results
   (PowerShell: `$env:WIKISEARCH_FAKE=1; uv run uvicorn wikisearch.web.app:app --reload`, then
   http://localhost:8000; `Remove-Item Env:WIKISEARCH_FAKE` to go back to real mode).

## Step F3b: the interface (`wikisearch/web/static/`)

Plain `index.html`, `style.css`, `app.js`. No framework, no build step, no CDN needed. UI text in
English. Sober look: white background, one accent colour, system font, no gradients, no emoji,
no rounded "cards everywhere" style.

1. Search box with the configuration selector (from `/api/configs`) next to it.
2. Result list: title (link to the document view), date, snippet with highlights, categories as
   small tags, source agencies, thumbnail if `image_url`, a muted "not published" label when
   `published` is false. Show "N results in X ms".
3. Filters in a left column: date range (two date inputs), categories and agencies from
   `/api/facets` (checkboxes with counts), "published only" toggle. Changing a filter reruns the
   search.
4. Pagination (previous/next).
5. Document view (`#/doc/<id>`): title, date, body, categories, sources with links, linked
   Wikipedia entities, link to the original Wikinews page.
6. **Compare mode**: a toggle that shows two result columns for the same query with two
   configurations chosen by the user (e.g. `bm25-italian` against `knn`). This is the core of
   the demo: it makes the experiments visible.
7. The query and filters are kept in the URL (`?q=...&config=...`), so a demo query can be
   opened from a link.
8. Done when every item above works in fake mode and, once Daniel's index exists, on real data.

## Step F1: BM25 search (needs Daniel's D3, or the sample indexed with his script)

Files: `wikisearch/search/__init__.py` (keep the `search()` signature), helpers in
`wikisearch/search/es.py`.

1. One Elasticsearch client for the process (`functools.lru_cache`), URL from
   `wikisearch.config.ES_URL`.
2. Index: `wikisearch.config.index_name(cfg["analyzer"])`.
3. Query for `mode == "bm25"`:
   `bool.must = multi_match(query, fields=cfg["fields"], type="best_fields", tie_breaker=cfg.get("tie_breaker", 0.3))`,
   `bool.filter = filters_to_es(filters)`.
4. `filters_to_es(filters) -> list[dict]`, a pure function: `range` on `date` (`gte`/`lte`), one
   `term` per category (all must match), one `terms` on `agencies` (any), `term` on `published`
   if not None.
5. Highlighting on `lead` and `body`: one fragment of about 160 characters, `<em>` tags. Snippet =
   the first fragment found, otherwise the first 200 characters of `lead`.
6. Request only the fields a `Hit` needs (`_source` includes), never `body` or `embedding`.
7. `boost_published` (if present and not 1.0): ask for `cfg.get("depth", 100)` hits, multiply the
   score of published hits by the boost, re-sort, cut to `k`.
8. Command line for quick checks: `uv run python -m wikisearch.search "terremoto abruzzo" --config bm25-italian`
   prints rank, score, date, title (`wikisearch/search/__main__.py`).
9. Tests (`tests/test_search.py`): unit tests for `filters_to_es`; an integration test that runs
   every BM25 configuration on one query, marked to skip when `localhost:9200` does not answer.
10. Done when every BM25 configuration in `configs.py` returns results from the CLI and the web
    app works on real data.

## Step F4: vector and hybrid search (needs Daniel's D4)

1. Query embedding: `SentenceTransformer(EMBEDDING_MODEL)` loaded once (`lru_cache`),
   `encode(QUERY_PREFIX + query, normalize_embeddings=True)`. Constants from `wikisearch.config`.
   Load the model lazily: BM25-only use must not load it.
2. `mode == "knn"`: Elasticsearch `knn` search on `embedding`, `k`, `num_candidates = max(100, 10 * k)`,
   the same filters passed as the `knn.filter`. Snippet = start of `lead` (no highlight).
3. `mode == "hybrid"`: run BM25 and kNN, each with `cfg["depth"]` hits and the same filters, and
   fuse with reciprocal rank fusion: `score(d) = sum over lists of 1 / (cfg["rrf_k"] + rank(d))`,
   ranks from 1, ties broken by document id. Write the fusion as a pure function
   `rrf_fuse(rankings: list[list[str]], k: int) -> list[tuple[str, float]]` with a unit test on a
   hand-computed example. Snippets from the BM25 side when available.
4. `boost_published` applies after fusion, as in F1.
5. Stretch (E7), only if F1-F5 are done: optional `collapse` on `series_key` (config key
   `"collapse": true`), keeping the best hit per series.
6. Done when `knn`, `hybrid-rrf` and `hybrid-rrf-published` run from the CLI and in the UI,
   including compare mode.

## Step F5: demo (Wednesday)

1. `docs/demo.md`: 5-6 queries in the order you will run them, each with what to show and the
   sentence to say. Cover: a plain topical query, a filter by date and agency, a query where
   BM25 wins (exact names), a paraphrase where `knn`/hybrid wins (compare mode), a sport or lottery
   query that shows near-duplicates, a non-published page.
2. Screenshots of each step in `results/demo/` as a fallback if the live demo fails in class.
3. The demo runs on **Daniel's laptop** (macOS, 8 GB), not on Fabio's: rehearse it there at
   least once on Wednesday or Thursday morning. Before class: Elasticsearch started, the web app
   started, each demo query run once (the first query loads the embedding model, a few seconds),
   other heavy apps closed.

## Step F6: slides and README

1. `slides/fabio.md`, in Italian, with the structure in `PLAN.md` ("Slides"), by Wednesday 22:00:
   the retrieval choices (BM25 fields and weights, why vectors, why RRF, filters and facets) with
   the numbers from Gioia's results, then the demo.
2. The "Usage" subsection of `README.md` for the web app (start, open, configurations).

## What to write in the log

For every push: what you built, how to run it, any configuration added or changed (the
experiments depend on `configs.py`: never rename a configuration without a "Contract changes"
entry), observed latencies, and design decisions with their reason, e.g. why RRF instead of a
weighted sum of scores (BM25 and cosine scores are on different scales; RRF only uses ranks).
These reasons become your slides.
