# State

Shared memory of the project. Read it before starting, update it before every push
(rules in `CLAUDE.md`). Newest log entry first.

## Current state

| Part | Owner | State |
|---|---|---|
| Repository, plan, contracts, skeleton | Daniel | done (16 Nov) |
| Data and indexing | Daniel | D1-D4 done (16 Nov 14:02): full indices with vectors on Daniel's laptop, embeddings committed in `data/shared/`; next: D5 (Tuesday morning) |
| Search and interface | Fabio | F3a done (16 Nov 12:40): web app and API with fake mode; next: F3b (full UI on fake data), then F1 once D2-D3 are pushed |
| Evaluation | Gioia | G1 done (16 Nov 12:30): metrics, TREC files, significance tested; next: the 30 queries of G3, then G2 on the sample |

How to get the dump (not in git): download
https://dumps.wikimedia.org/other/enterprise_html/runs/20250320/itwikinews-NS0-20250320-ENTERPRISE-HTML.json.tar.gz
(73 MB) and extract it into `data/raw/`: you get `itwikinews_namespace_0_0.ndjson` (591 MB).

## What we know about the dump

Analysed on 16 Nov 2026 before writing the plan.

1. 12,261 lines, one page per line (Wikimedia Enterprise HTML format: `name`, `identifier`, `url`,
   `abstract`, `article_body.html`, `article_body.wikitext`, `categories`, `templates`,
   `main_entity`, `image`, `date_modified`, ...).
2. 25 pages appear twice (same `identifier`, two versions): keep the most recent.
3. 11,066 pages are in `Categoria:Pubblicati`. The other 1,195 are sport tables, "Speciale" pages,
   drafts, pages marked for deletion. Decision (16 Nov): **keep them**, flagged with
   `published: false`; whether to rank them lower is experiment E5.
4. The news date is not a field: it is in the `{{data|21 marzo 2008|venerdì}}` template
   (10,965 pages) and in a daily category. News from 2004 to 2025, almost half in 2005-2008.
5. 5,964 distinct categories, mixing geographic (Europa 8,547, Italia 6,765), topical (Sport 4,106,
   Calcio 2,456, Politica e conflitti 2,014) and maintenance ones (Pubblicati, Articoli archiviati,
   Articoli da controllare per l'archiviazione) to drop.
6. 9,767 pages cite at least one source with `{{fonte|autore=|url=|titolo=|agenzia=|data=}}`,
   16,613 sources in all. Top agencies: Corriere della Sera, la Repubblica, ANSA, Gazzetta dello
   Sport; spelling varies (`ANSA`/`Ansa`, `la Repubblica`/`La Repubblica`). `{{Fonteestera}}`
   (400) marks foreign-language sources.
7. 39,765 distinct Wikipedia pages linked from the text with `[[w:...]]`; some are noise
   (`Central European Time`, `Calcio di rigore`).
8. Template-generated near-duplicates: SuperEnalotto draws (230), Lotto (219), prize games (470),
   football match reports (1,418 with `{{Incontro di club}}`).
9. Short texts: median wikitext about 2,200 characters. About 11,000 documents: embeddings with a
   small model take minutes on a laptop CPU.
10. `abstract` exists for 11,995 pages but starts with the date and is empty or very short for
    1,991: build the lead from the HTML instead.

## Contract changes

None yet.

## Messages

Not here: messages between sessions are GitHub issues (`CLAUDE.md`, "Talking to the other
sessions"). The session briefing lists the open ones.

## Log

### 16 Nov 2026 14:02, Daniel: D4 done, shared embeddings and indices with vectors

`wikisearch/ingest/embed.py` computes the e5-small vectors of all documents, committed in
`data/shared/embeddings.npy` (12,213 x 384 float32, 18.8 MB) and `data/shared/embeddings_ids.json`.
**Fabio and Gioia: pull, then reindex** (the indexer loads the vectors by itself when the files
exist): `uv run python -m wikisearch.ingest.index`. Do not recompute the embeddings. Fabio can
start F4.

How to run (only if the corpus changes): `uv run python -m wikisearch.ingest.embed` (downloads
the model once, about 470 MB), then the indexer.

1. Text embedded: `"passage: " + title + ". " + lead` (title alone if the lead is empty),
   `normalize_embeddings=True`, batch 32, CPU. 121 s for 12,213 documents (about 100 docs/s),
   peak memory 1 GB. Elasticsearch was stopped during the job (8 GB Mac).
2. Indices with vectors (`results/indexing.csv`, three builds each): `wikinews-standard` 19.0,
   13.0, 12.7 s, 57.4 MB; `wikinews-italian` 14.0, 14.2, 13.3 s, 54.9 MB. Against the indices
   without vectors: about 3x the time (building the HNSW graph) and +19 MB (the raw float32
   vectors are 18.8 MB; `hnsw` keeps them unquantized).
3. Check (done when): nearest neighbours with `knn` (k=6, num_candidates=100) on
   `wikinews-italian` are sensible.
   - "Strage di Marzabotto: 10 ergastoli e 7 assoluzioni" -> "Strage di Nassiriya: tre rinviati
     a giudizio", "Omicidio Biagi: 5 ergastoli", "Strage di Erba: ...".
   - "Terremoto nel salernitano" -> "Terremoto in Sicilia", "Terremoto nelle Marche: tanta paura
     ma nessun danno", "Terremoto a Palermo, nessun danno rilevante".
   - "Contestata estrazione di Lotto e Superenalotto" -> other SuperEnalotto pages.
   - Query "disastro in una miniera" (embedded as `"query: " + text`) -> "Ucraina: decine di
     vittime in una esplosione in miniera", "Cina: esplosione in miniera, 11 morti", "Cina: 105
     vittime in una esplosione in miniera": none contains "disastro", a paraphrase BM25 would
     miss (useful for the E3 slide and the demo).
   - Query "elezione del presidente degli Stati Uniti" -> Election Day 2008, US elections 2020,
     "Donald Trump è il 47º presidente degli Stati Uniti d'America".
4. Note for whoever reads scores: e5 cosine scores are compressed (0.91-0.96 in the examples
   above), so the absolute score says little; only the ranking matters. This is one more reason
   to fuse rankings with RRF rather than scores in the hybrid configuration.

Next (Tuesday morning): D5. `sources_text` is already indexed (D3), so D5 is only the optional
extra variants; then D6 data report.

### 16 Nov 2026 13:55, Daniel: D3 done, full indices

Both indices hold all 12,213 documents of `data/processed/docs.jsonl`. **Fabio and Gioia: build
them on your laptop** (Elasticsearch running, dump in `data/raw/`):

    uv run python -m wikisearch.ingest.parse --no-sample
    uv run python -m wikisearch.ingest.index

(about 15 s plus 10 s; `--no-sample` avoids rewriting the committed sample, which would be
identical anyway).

Numbers (`results/indexing.csv`, three builds each, without embeddings, Daniel's Mac M-series,
8 GB, Elasticsearch heap 1 GB):

| index | seconds (3 builds) | size |
|---|---|---|
| `wikinews-standard` | 4.69, 3.89, 3.92 | 38.2 MB |
| `wikinews-italian` | 3.84, 3.87, 3.82 | 35.7 MB |

The `italian` index is 6% smaller: stop words removed and stems merge word forms, so fewer
distinct terms and postings. The first build is slower (JVM warm-up), which is why the brief asks
for three runs.

Fix made while measuring: Elasticsearch caches the store size for 10 s
(`index.store.stats_refresh_interval`), so the first measurement read 5.8 MB instead of 38 MB.
The indices are now created with `store.stats_refresh_interval: 0s`, and the CSV was regenerated
with correct rows only. Each row now has its own timestamp.

Next: D4 embeddings (e5-small on the titles and leads, then reindex with vectors).

### 16 Nov 2026 13:50, Daniel: D3 indexer, work in progress (sample indexed)

`wikisearch/ingest/index.py` builds `wikinews-standard` and `wikinews-italian` with the mapping of
contract section 2 and bulk-loads the documents. **Fabio can start F1 now** on the sample:

    uv run python -m wikisearch.ingest.index --input data/sample/docs.sample.jsonl --no-csv

(300 documents per index, under a second each, about 1 MB each). Without `--input` it indexes the
full `data/processed/docs.jsonl` (run the parser first). Other options: `--analyzers italian`,
`--no-embeddings`, `--repeat 3` (timings for E6), `--no-csv`. Each build appends one row per index
to `results/indexing.csv` (timestamp, index, analyzer, input, documents, embeddings, seconds,
size_bytes).

Details:
1. 1 shard, 0 replicas; `refresh_interval: -1` during the load, then `1s`, refresh and flush;
   bulk in chunks of 500. The script fails if any document is rejected or if `count` differs
   from the number of input documents.
2. `"dynamic": "strict"`: a field not in the mapping is an error, so the contract cannot drift
   silently.
3. `_source` holds the whole processed document (the web app's `/api/doc` reads it) plus
   `sources_text` (source titles joined, analyzed, searched only by `bm25-italian-leak`, E4;
   included now so that D5 needs no reindex) and `embedding` when `data/shared/embeddings.npy`
   exists (matched by id, the script stops if a document has no vector).
4. `embedding` is in the mapping already (384 dims, cosine, `index_options: hnsw` explicitly);
   documents without a vector are simply not in the knn graph until D4.
5. Tests (`tests/test_index.py`, 6): mapping against the contract, `sources_text`, vectors
   matched by id; with Elasticsearch running, a temporary index from 50 sample documents checks
   the count, that a source title is found in `sources_text` but never in `body`, and that the
   `italian` analyzer stems (`elezioni` = `elezione`) and removes elision (`l'Italia` = `Italia`).

Next: full corpus, three builds per variant for the timings, then D3 is done.

### 16 Nov 2026 13:48, Daniel: D1 Elasticsearch running

Step D1 done: `docker compose up -d` starts Elasticsearch 9.5.0 on Daniel's Mac (Docker Desktop
VM with 4 GB, container at about 1.5 GB of 2 GB); `curl localhost:9200` answers. The README
"Setup" is verified and now says what to do when it does not answer.

Incident worth knowing (it can happen on the 8 GB Macs): the disk filled up while the image was
being pulled (swap plus an automatic Docker Desktop update), Docker Desktop stopped with "no
space left on device", and the container created in that moment had a truncated
`elasticsearch.keystore` ("read past EOF" at start). Fix: free disk, restart Docker Desktop,
`docker compose down` and `docker compose up -d` (recreates the container, keeps the volume).
Keep at least 5 GB free before indexing.

Next: D3 indexer.

### 16 Nov 2026 13:40, Daniel: D2 parser and sample

Step D2 done: `wikisearch/ingest/parse.py` turns the dump into `data/processed/docs.jsonl`
(contract section 1) and writes the committed sample `data/sample/docs.sample.jsonl` (300 docs).
**Fabio and Gioia can start on the sample now** (G2 on the sample; F1 as soon as the indexer D3
is pushed, or index the sample yourselves once it is).

How to run: `uv run python -m wikisearch.ingest.parse` (about 15 s, 0.8 GB of RAM; needs the dump
in `data/raw/`). It also rewrites the sample (deterministic, seed 42) and
`results/parse_report.json`; `--no-sample` leaves the sample alone. Tests: `uv run pytest -q
tests/test_parse.py` (13 tests on three real pages in `tests/fixtures/pages.json`).

Numbers (`results/parse_report.json`):
1. 12,261 lines read, 48 removed as duplicates (25 identifiers: 22 twice, three 5, 11 and 13
   times; the most recent `date_modified` is kept) -> **12,213 documents**, 11,032 published,
   1,181 not.
2. Date: 11,687 from `{{data}}`/`{{luogodata}}`, 40 from the daily category, 486 none.
3. 9,891 documents with sources, 17,192 sources (655 foreign), 29 without a title.
   Agencies: 2,965 spellings -> 2,295 after normalization.
4. 12,104 with at least one category, 10,247 with entities, 3,653 with an image, 23 with an empty
   body (e.g. "Pagina principale", redirect-like pages). Median body 1,181 characters.
5. Leakage check: in 51 documents the body contains the title of one of its sources verbatim
   (4+ words); checked by hand, they are natural (the name of an exhibition or a play quoted in
   both), not source text left in the body.
6. Sample strata: 180 news spread over the years in proportion, 40 sport pages with tables,
   25 lottery, 15 specials, 40 non-published.

Decisions, and why:
1. Text from the Parsoid HTML (wikitext would need a template expander); date, sources and
   entities from the wikitext, where templates are readable.
2. **Leakage**: sections "Fonti", "Fonte", "Collegamenti esterni", "Note" are dropped, and also
   every `{{fonte}}`/`{{fonteestera}}` transclusion wherever it is: 631 pages have no section
   heading at all, so dropping the section alone would leak their sources.
3. Navigation sections are dropped too ("Articoli correlati", "Notizie correlate", "Notizie
   precedenti", "Altri progetti", "Vedi anche"...): they list other articles' titles, which would
   make a page match queries about its neighbours.
4. Block templates are dropped (archive banners, "Dì la tua", Wikipedia/Wikivoyage boxes,
   "notizia originale", "traduzione", season navigation boxes) except those that carry article
   text: `interv` (interview questions), `quote`, `citazione`, and match reports
   (`incontro di club`, `footballbox`, ...).
5. **Tables are kept** (decided by Daniel): the brief said paragraphs and lists, but 2,832 pages
   have tables (match reports, standings, lottery draws), they are 34% of the corpus text, and
   without them 359 pages (234 published) would have an empty body. One line per table row.
6. Agencies: a key (lowercase, no accents, no leading article, no `.it`/`.com`, no
   "(quotidiano)") plus 14 explicit aliases (`Corriere.it` -> Corriere della Sera, `AGI` = Agenzia
   Giornalistica Italia, ...); the displayed name is the most frequent spelling of the group.
7. `{{fontecarta}}` (159 printed sources) is not in the contract and not parsed; it could be added
   to `sources` later if the `fonti` test set wants more queries.
8. Source `date` is `YYYY-MM-DD` or null (the contract did not fix a format).

Next: D1 (Elasticsearch is starting on Daniel's laptop after a full-disk incident), then D3.

### 16 Nov 2026, Daniel: push and news checks are always automatic

`CLAUDE.md`, new section "Pushing and checking for news: always on your own": every session
pushes by itself at the end of each step and at every working checkpoint inside a long step
(about hourly, with a "work in progress" log entry), and runs `scripts/inbox.py` by itself at the
start, between steps, after every push and before ending a long reply. Users never have to ask.

### 16 Nov 2026 12:40, Fabio: F3a web app skeleton with fake mode

Step F3a done: the web API of `docs/contracts.md` section 4 exists and works without
Elasticsearch, so the interface can be built before the index.

1. `wikisearch/web/app.py`: FastAPI `app` with `/api/search`, `/api/doc/{id}`, `/api/facets`,
   `/api/configs`; the static UI (`wikisearch/web/static/`) is served at `/`. With
   `WIKISEARCH_FAKE=1` every endpoint answers from `wikisearch/web/fake.py` (three hits: one with
   an image, one non-published, one without date; one full document per hit; fake facet counts).
   The variable is read at every request, so tests switch it with `monkeypatch`.
2. `/api/search`: `took_ms` measured in Python around `search()`; pagination asks `search()` for
   `page * size` hits and slices. Page size is `size` (brief) and `k` is accepted as an alias
   (the name in the contract); default 10, max 100. Filters: `date_from`, `date_to` (validated
   `YYYY-MM-DD`, 422 otherwise), repeated `category` and `agency`, `published`. Unknown config:
   400. Empty query: no hits, `search()` not called.
3. Decision (Fabio): the contract lists a `total` that the brief's response did not have, and
   `search()` returns at most k hits with no count of all matches. `total` = number of hits
   `search()` returned for `page * size`, not the number of matches in the index. Cheap, defined
   for every mode (an exact count is not meaningful for knn), and honest about what it is.
4. Real mode, ready for when the index exists (not testable yet): `/api/doc` is a `get` on the
   default configuration's index without `embedding` (404 if missing); `/api/facets` runs the BM25
   `multi_match` of the configuration on its index with terms aggregations on `categories` (15),
   `agencies` (10) and a yearly `date_histogram`; for `knn` it uses the default configuration's
   fields, since facets are lexical by design. Response shape: `{"query", "config",
   "categories": [{"value", "count"}], "agencies": [...], "years": [...]}`. Elasticsearch down:
   503; `search()` still `NotImplementedError` (F1): 501.
5. `wikisearch/search/es.py`: one client per process (`lru_cache`, `ES_URL`) and the
   `multi_match` builder, to be reused by F1.
6. Minimal UI (search box, configuration selector, result list with tags, agencies, thumbnail,
   "not published" label, "N results in X ms"); the rest (filters, pagination, document view,
   compare mode, URL state) is F3b.
7. `tests/test_web.py`: 10 tests in fake mode with `TestClient` (shapes, pagination, `k` alias,
   filters, bad input, 404, facets).

How to run (PowerShell): `$env:WIKISEARCH_FAKE=1; uv run uvicorn wikisearch.web.app:app --reload`,
then http://localhost:8000; `Remove-Item Env:WIKISEARCH_FAKE` for real mode. Tests:
`uv run pytest -q tests/test_web.py`. Nothing changes for the others.
Environment (Step 0): Docker, uv, git, gh ready, Elasticsearch 9.5.0 answers, dump in
`data/raw/`. On Windows `uv` failed with "Missing expected target directory for Python minor
version link"; workaround: `uv sync --python <path to the downloaded python.exe>` once, then
`uv run` works. Next: F3b on fake data, F1 as soon as Daniel's sample and indexer are pushed.

### 16 Nov 2026 12:30, Gioia: G1 metrics, TREC files, significance

Step G1 done: the evaluation can compute every planned metric and test, without any corpus.

1. `evaluation/trec.py`: `read_queries`, `read_qrels`, `read_run` (sorted by numeric rank),
   `write_run` (ranks from 1 in the given order), formats of `docs/contracts.md` section 5.
2. `evaluation/metrics.py`: `precision_at_k`, `recall_at_k`, `reciprocal_rank` (k=10, mean =
   MRR@10), `average_precision` (mean = MAP), `ndcg_at_k`, and `evaluate(qrels, run, metrics)`
   with metric names `P@k`, `R@k`, `MRR@k`, `nDCG@k`, `AP`. Relevant = grade >= 1; unjudged =
   not relevant; queries with no relevant judgment are skipped, judged queries missing from the
   run score 0. Decision not in the brief: a doc id repeated in a run counts only at its first
   rank, so a bug in a run cannot score the same relevant document twice.
3. `evaluation/significance.py`: `paired_randomization_test` (two-sided, sign flips of the
   per-query differences, p = count / n, so p = 0 must be reported as p < 1/n = 0.0001) and
   `bootstrap_ci` (percentile interval of the mean). Both seeded (42) and computed in chunks of
   500 draws: on 7,300 queries x 10,000 draws they take 0.3 s and 0.2 s and stay under 30 MB.
4. `tests/test_metrics.py`: 25 tests, every expected value computed by hand in a comment
   (running example ranked [a, b, c, d], judged {b: 1, d: 2}: P@2 = 0.5, RR = 0.5, AP = 0.5,
   nDCG@4 = 0.52961), edge cases (no relevant retrieved, relevant beyond k, empty run, grade 0,
   repeated doc), a two-query randomization test whose exact p is 0.5.

How to run: `uv run pytest -q tests/test_metrics.py`. Nothing changes for the others.
Environment (Step 0): Docker, uv, git, gh ready; Elasticsearch not started yet and dump not
downloaded yet. Next: G3 query writing (30 `manual` queries with information needs) and G2 as
soon as Daniel's sample is pushed.

### 16 Nov 2026, Daniel: prompt for sessions outside the repository

Daniel works from conversations started outside the repository folder, where `CLAUDE.md` and
the hooks are not active. `docs/briefs/README.md` now has a prompt for that case: it makes the
session run `scripts/briefing.py` and `scripts/inbox.py` by hand, read the same files, and rerun
the inbox between steps. Everything is ready: work starts now, Daniel from D1, Fabio from Step 0
and F3a, Gioia from Step 0 and G1.

### 16 Nov 2026, Daniel: inbox check at every message

New hook (`UserPromptSubmit` in `.claude/settings.json`) that runs `scripts/inbox.py` every time
a user writes to their Claude: if new issues for that user, new blockers or contract changes, or
new commits arrived since the last check, a short "TEAM INBOX" note enters the session, which
tells its user first. Silent when there is no news; about 2 seconds per message. Issues already
reported are remembered in `.git/wikisearch-inbox.json` (never committed). Long autonomous work
also runs the script between steps (`CLAUDE.md`). Tested with a temporary issue for Fabio:
reported once, then silent.

### 16 Nov 2026, Daniel: faster timeline

The team wants to finish earlier than the official deadline. New target: **code freeze Tuesday
17 at 20:00, delivery Wednesday 18 by 14:00**; Thursday is only a safety margin. Every step in
`PLAN.md` and in the briefs has a new date and time ("Timeline" in `PLAN.md`): sample Monday
15:00, full indices Monday 19:00, embeddings Monday night, vector search Tuesday 11:00, pool
Tuesday 12:00, judgments Tuesday 12:00-15:00, slide content Tuesday 22:00, deck Wednesday 11:00.
If on Tuesday at 18:00 something essential is missing, the group decides whether to move the
freeze to Wednesday 12:00. Stretch items are dropped first.

### 16 Nov 2026, Daniel: aligned with the course

Added `docs/course.md`: what the course and the professor expect, in our words, with references
to the slides (assignment, what he values in experiments, IR evaluation from id-02 slides
173-189, text analysis, Elasticsearch, presentations). Every session reads it after `PLAN.md`.
The slides are **not** committed (they are the professor's and the repository becomes public):
each member may copy them into `course/`, which git ignores.

Changes that follow from the course:
1. Statistical robustness: a random ranking as a floor (computed by the runner), 95% bootstrap
   intervals next to every mean, the official `fonti` run on all the queries (about 7,000) with a
   1000-query subset only for development.
2. Each `manual` query has a one-sentence information need (`meta.need`); judges grade against
   it, as the course says (id-02, slide 181).
3. `embedding` uses `index_options: hnsw` explicitly (recent Elasticsearch versions default to a
   quantized structure at 384 dimensions); quantization becomes the stretch experiment E8, from
   the slides on HNSW and quantization.

### 16 Nov 2026, Daniel: the humans stay in control

Added to `CLAUDE.md` two sections. "Working with your user": explain before and after every step
(each of us defends the work alone at the oral exam), ask instead of guessing, ask before
decisions outside the brief and before heavy or destructive actions. "Agreements between
sessions": sessions negotiate through issues, but a change to someone's part, a contract or the
plan is accepted only after asking that person; disagreements go to the humans after one
exchange of reasons. Prompts in `docs/briefs/README.md` updated accordingly.

### 16 Nov 2026, Daniel: sessions talk to each other through GitHub issues

The three Claude Code sessions run on different laptops and accounts and cannot talk directly.
Added a way for them to coordinate without the humans relaying every detail:

1. **Messages = GitHub issues** with labels `for:daniel`, `for:fabio`, `for:gioia`, `blocker`,
   `contract-change` (created on GitHub). Rules in `CLAUDE.md`, "Talking to the other sessions":
   self-contained body, `Closes #n` in the commit that solves it, contract changes always as an
   issue to the other two. Issues never conflict, unlike `STATE.md`; the old "Requests" section
   is gone.
2. **Session briefing**: `.claude/settings.json` has a SessionStart hook that runs
   `scripts/briefing.py` (standard library only). Every session starts knowing who its user is,
   whether the copy is behind GitHub, the latest log entries, the next step, and the open issues
   for its user. It never blocks a session: on any error it prints what to read by hand.
3. **Contract tests** in `tests/test_contracts.py`: sample documents, shared embeddings, test set
   files and `search()` results are checked in everyone's `pytest` as soon as they exist, so a
   push that breaks another part fails before it reaches the others.
4. **Scope rules** in `CLAUDE.md`: only the brief and the issues, no unplanned features, stretch
   items last, check the time against the timeline.
5. **Handoffs** table in `PLAN.md`: who messages whom when a step unblocks someone.
6. GitHub CLI is now required for everyone (`docs/briefs/README.md`).

### 16 Nov 2026, Daniel: second review of the plan before the start

Read every file again looking for steps that would break in practice. Changes:

1. Team machines: Daniel and Gioia on macOS with 8 GB, Fabio on Windows with 16 GB. `CLAUDE.md`
   now has cross-platform rules (UTF-8 explicitly when opening files, pathlib, PowerShell
   commands for Fabio); README and Fabio's Step 0 have the Windows notes (WSL 2, `curl.exe`).
2. All dependencies of every planned step are already in `pyproject.toml` (sentence-transformers,
   selectolax, matplotlib, httpx for tests): `uv sync` is the only install command and nobody
   should need `uv add`, which would cause `uv.lock` conflicts.
3. Package `eval` renamed `evaluation` (it shadowed Python's built-in `eval`).
4. Embeddings computed once by Daniel and committed in `data/shared/` (about 17 MB): all laptops
   index the same vectors and the 8 GB Macs do not compute them. Runs in `results/runs/` are not
   committed (too large); the official numbers are produced once by Gioia at code freeze after
   rebuilding the indices.
5. Push protocol: pull before writing the log entry; conflict rules for `STATE.md` (keep both
   entries) and `uv.lock`.
6. Manual judgments: a terminal tool (`python -m evaluation.judge`) instead of spreadsheets
   (Excel with Italian settings breaks CSV separators and accents); pooling only after the
   vector search exists, otherwise its documents would never be judged.
7. Fake mode for every web endpoint, so Fabio can build the whole interface before the index.
8. Slides: each person writes the content of their slides in `slides/<name>.md` (Italian, the
   only non-English folder) by Wednesday 22:00; Daniel builds the deck. The demo and the
   presentation run on Daniel's laptop. Cover with names, emails and repository link; repository
   made public before the upload.
9. Before the first session: accept the invitation, `gh auth login`, clone, open Claude Code
   inside the folder (`docs/briefs/README.md`).

### 16 Nov 2026, Daniel: pre-flight checks

Checked the assumptions of the plan before anyone starts, so there are no surprises later.

1. `fonti` test set, simulated on the raw dump with the filters of Gioia's brief: 17,190 source
   templates -> 7,318 usable queries (one per published article; low overlap 2,969, mid 3,549,
   high 800). Enough for a sample of 1000. Two findings added to the brief: some `{{fonte}}`
   titles are in English (new language rule), and about 4% of queries appear verbatim in the
   text before "Fonti" (natural overlap, not leakage).
2. Manual judgments were too many: 40 queries pooled from 9 configurations would be well over
   1000 judgments. Now 30 queries pooled from the 5 configurations of E1, E3, E5, 10 queries
   judged twice: about 300 judgments, one hour per person. E2 and E4 are measured on `fonti` only.
3. Elasticsearch 9.5.0 image exists for arm64 and amd64. `uv.lock` resolves torch and
   sentence-transformers for macOS, Windows and Linux on Python 3.12.
4. Parser: about 1% of pages have no "Fonti" heading; the brief says to check the variants.

### 16 Nov 2026, Daniel: personal briefs and session prompts

Added `docs/briefs/` with one detailed brief per person (exact files, functions, checks, "done
when", order of work while waiting for the others) and the prompts to paste into Claude Code at
the first and at every following session (`docs/briefs/README.md`). `CLAUDE.md` now points every
session to its brief. Contract detail added before anyone started: `sources[i].foreign`
(true for `{{fonteestera}}`), needed by Gioia's test set.

How to start: clone, open Claude Code in the repository, paste the first-session prompt from
`docs/briefs/README.md` with your name.

Next: Daniel D1-D3; Fabio step 0, then F3a (web skeleton with fake search) until the sample is
pushed; Gioia step 0, then G1 and the 30 queries of G3.

### 16 Nov 2026, Daniel: repository set up

Created the repository with `PLAN.md` (split of the work, experiments, steps, timeline),
`docs/contracts.md` (document schema, indices, `search()` signature, web API, evaluation file
formats), this file, `CLAUDE.md` (rules for every Claude Code session), `docker-compose.yml`
(Elasticsearch 9.5.0, same image as the course lab, 1 GB heap, security off, no Kibana) and the
package skeleton: `wikisearch/config.py`, `wikisearch/schema.py` (`Filters`, `Hit`),
`wikisearch/search/configs.py` (the list of configurations to compare), empty modules for each
part. Nothing is implemented yet.

Decisions: Elasticsearch rather than plain Lucene (analyzers, filters, vectors, highlighting out of
the box; it is the engine of the course lab); Python for everything; hybrid fusion computed in
Python with RRF so that it is transparent and easy to vary; embedding model
`intfloat/multilingual-e5-small` (384 dimensions, runs on CPU); sources excluded from the searched
text to avoid leakage into the known-item test set.

Next: Daniel D1-D3, Fabio F1 on the sample, Gioia G1.
