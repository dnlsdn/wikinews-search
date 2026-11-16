# Plan

Homework 4 of Ingegneria dei Dati (prof. Merialdo): a web search engine over the Italian Wikinews
dump, a test strategy that compares design choices (ablation study), a 20 minute presentation with
a live demo. Official deadline: Thursday 19 November 2026, 18:00 (presentation uploaded through
the course form; presentations in class on Friday 20). **Team target (decided 16 Nov): code
freeze Tuesday 17 at 20:00, delivery Wednesday 18 by 14:00.** Thursday is only a safety margin:
do not plan work on it.

What the course expects, in detail, with references to the slides: `docs/course.md`. Read it.

What the professor asked for, in his words: the technical and methodological challenges, the
solutions (no code on the slides), the test strategy (which datasets, which metrics), the
experimental results and how they support the design choices, a live demo. Code and install
instructions on GitHub.

## Team and ownership

Each person owns a part of the system, the matching part of the presentation, and the directories
below. If something outside your directories must change, open a GitHub issue for its owner
(rules in `CLAUDE.md`, "Talking to the other sessions").

| Person | GitHub | Part | Directories | Presentation |
|---|---|---|---|---|
| Daniel | dnlsdn | data and indexing: parsing the dump, cleaning, Elasticsearch mappings and analyzers, embeddings | `wikisearch/ingest/`, `data/sample/`, `data/shared/`, `docker-compose.yml`, `tests/test_parse.py`, `tests/test_index.py` | the data and its challenges, indexing choices; assembles the deck; the demo runs on his laptop |
| Fabio | fmdimarco | search and interface: BM25, vector and hybrid retrieval, filters, web API and UI, demo | `wikisearch/search/`, `wikisearch/web/`, `tests/test_search.py`, `tests/test_web.py` | retrieval choices and the live demo |
| Gioia | gioburattii | evaluation: test sets, metrics, experiment runner, results | `evaluation/`, `results/`, `tests/test_metrics.py`, `tests/test_evaluation.py` | test strategy and experimental results |

Shared files: `wikisearch/schema.py`, `wikisearch/config.py`, `docs/contracts.md` (change only as
described there), `STATE.md` (everyone appends), `PLAN.md` (everyone ticks their own boxes),
`README.md` (each person writes the "Usage" subsection of their part), `slides/` (one file each).

Laptops: Daniel and Gioia on macOS with 8 GB of RAM, Fabio on Windows with 16 GB. Everything
must run on both systems (rules in `CLAUDE.md`). The live demo and the presentation run on
**Daniel's laptop**.

## Why this split works

1. The only hard dependency is the corpus: search and evaluation need documents. Daniel's first
   job is therefore a **sample** (`data/sample/docs.sample.jsonl`, about 300 pages) pushed within
   Monday by 15:00, and the full parser and indexer the same evening. Until then Fabio builds the
   interface on fake data and Gioia the metrics, which need no documents.
2. Every design choice to compare is a **named configuration** (`wikisearch/search/configs.py`).
   The person who implements a choice exposes it as a configuration; Gioia's runner evaluates all
   configurations with the same `search()` function the web app uses.
3. Each experiment has an owner who implements the knob and Gioia who measures it (table below).

## Handoffs

The moments when one part unblocks another. Whoever completes the left column opens a GitHub
issue to the person on the right (or comments on their open issue), so their session finds it in
the briefing.

| When this is pushed | By | Message to | So that they can |
|---|---|---|---|
| sample `docs.sample.jsonl` and indexer (D2, D3 on the sample) | Daniel | Fabio, Gioia | index the sample locally; Fabio starts F1, Gioia tries G2 on the sample |
| full parser and indexer (D3) | Daniel | Fabio, Gioia | rebuild the full indices locally |
| shared embeddings (D4) | Daniel | Fabio, Gioia | reindex with vectors; Fabio starts F4 |
| BM25 search (F1) | Fabio | Gioia | run the runner on BM25 configurations |
| vector and hybrid search (F4) | Fabio | Gioia | do the pooling (G3) |
| draft of the 30 manual queries (G3) | Gioia | Daniel, Fabio | review them by Tuesday 10:00, before pooling |
| judging assignments and tool (G3) | Gioia | Daniel, Fabio | judge on Tuesday between 12:00 and 15:00 (G4) |
| official results and figures (G5, G6) | Gioia | Daniel, Fabio | write their slides with the final numbers |
| slide content (D7, F6, G6) | everyone | Daniel | build the deck |

## Experiments (the ablation study)

| # | Question | Variants | Knob owner | Metrics |
|---|---|---|---|---|
| E1 | Does Italian text analysis help? | standard vs italian analyzer | Daniel | MRR@10, R@100 on `fonti`; nDCG@10 on `manual` |
| E2 | Which fields to search, with which weights? | title only, body only, title+lead+body, title^3+lead^2+body | Fabio | MRR@10, R@100 on `fonti` |
| E3 | Lexical, semantic or both? | BM25, kNN (e5-small), hybrid with RRF | Fabio (query), Daniel (embeddings) | MRR@10, R@100 on `fonti`, split by query-title overlap (low overlap = paraphrase); nDCG@10 on `manual` |
| E4 | How much does leakage inflate results? | with and without the sources field | Daniel (field), Gioia (analysis) | MRR@10 on `fonti` |
| E5 | Should published pages rank higher? | no boost vs boost on `published` | Fabio | nDCG@10 on `manual` |
| E6 | What does each choice cost? | all of the above | Gioia | indexing time, index size, query latency p50/p95 |
| E8 (stretch) | What does vector quantization cost in quality? | `dense_vector` with `hnsw` vs `int8_hnsw` vs `bbq_hnsw` (course slides on HNSW and quantization) | Daniel | MRR@10 of `knn` on `fonti`, index size, latency |
| E7 (stretch) | Do near-duplicates hurt the result page? | collapse on `series_key` off/on | Fabio | distinct series in the top 10 of the `manual` queries |

Statistical robustness, which the professor insists on (`docs/course.md`, section 2): a random
ranking as a floor; paired randomization test between configurations and 95% bootstrap
confidence intervals, reported with every comparison on the slides; the official `fonti` run
uses all the queries, not a sample.

## Steps

Summary of the steps. The detailed instructions (files, functions, checks, what to do while
waiting for someone else) are in the personal briefs: `docs/briefs/daniel.md`,
`docs/briefs/fabio.md`, `docs/briefs/gioia.md`. Prompts to start a Claude Code session are in
`docs/briefs/README.md`.

Everyone runs Elasticsearch and builds the indices on their own laptop with Daniel's scripts
(the dump and the indices are not in git; the embeddings are, so all laptops index the same
vectors). The **official numbers** are produced once, at code freeze, by Gioia on her laptop,
after pulling and rebuilding the indices.

Tick a box only when the "done when" is true, and log it in `STATE.md`.

### Daniel: data and indexing

- [x] **D1, Mon 16 now.** Elasticsearch running locally with `docker compose up -d` (single node, 1 GB
  heap, no Kibana; the laptop has 8 GB). Done when `curl localhost:9200` answers and the README
  says how.
- [x] **D2, Mon 16 (sample by 15:00).** Parser `wikisearch/ingest/parse.py`: dump -> `data/processed/docs.jsonl`
  following `docs/contracts.md` section 1 (dedupe the 25 double pages, date extraction, clean
  categories, sources and agencies, entities, body without "Fonti", `published`, `series_key`).
  Commit `data/sample/docs.sample.jsonl` (about 300 pages, mixed: news, sport tables, lottery,
  specials). Done when the sample is pushed and the parser reports coverage numbers (pages, dated
  pages, pages with sources).
- [x] **D3, Mon 16 by 19:00.** Indexer `wikisearch/ingest/index.py`: creates `wikinews-standard`
  and `wikinews-italian` with the mapping of section 2 and bulk-loads the corpus, measuring time
  and size. Accepts `--input` so the sample can be indexed too. Done when both indices hold all
  documents and the numbers are in `results/indexing.csv`.
- [x] **D4, Mon 16 night.** Embeddings: `wikisearch/ingest/embed.py` computes e5-small vectors for all
  documents into `data/shared/embeddings.npy` (committed, about 17 MB, so nobody else has to
  compute them) and the indexer loads them into `embedding`. Done when a `knn` query returns
  sensible neighbours for a few test articles.
- [ ] **D5, Tue 17 morning.** `sources_text` field for E4, any further analyzer variant worth testing.
- [x] **D6, Tue 17 afternoon.** Data report for the slides: counts, cleaning decisions with numbers,
  examples of hard pages (`results/data_report.md`).
- [ ] **D7, Tue 17 evening - Wed 18 morning.** Own slides (challenges of the data, indexing choices) in
  `slides/daniel.md`; assembly of the whole deck from the three files; cover with names,
  institutional emails and the repository link (the professor asked for emails in homework 3);
  repository made public before the upload.

### Fabio: search and interface

- [x] **F1, Mon 16 evening.** `wikisearch/search/`: `search()` with BM25 configurations over
  `multi_match` (fields and weights from the configuration) and the filters of `Filters`. Until
  D3 is done, index the sample with `python -m wikisearch.ingest.index --input data/sample/...`.
  Done when every BM25 configuration of E1 and E2 runs.
- [ ] **F2, Mon 16.** Web API (contracts section 4) with FastAPI: search, document, facets,
  configs. Highlighted snippets from Elasticsearch.
- [ ] **F3, Mon 16 (on fake data) - Tue 17 morning.** Web UI (`wikisearch/web/static/`): search box, result list (title, date,
  snippet, categories, source agencies, image), filters (date range, category, agency,
  published), pagination, document page, **compare mode** (two configurations side by side,
  useful in the demo to show E3). Plain HTML, CSS and JS served by FastAPI: no build step.
- [ ] **F4, Tue 17 by 11:00.** kNN configuration (query embedded with `EMBEDDING_MODEL`) and hybrid with
  reciprocal rank fusion computed in Python (k=60, parameters in the configuration); boost on
  `published` (E5). Stretch: collapse on `series_key` (E7).
- [ ] **F5, Tue 17 afternoon.** Demo script: 5-6 queries that show the features and the differences between
  configurations; screenshots as a fallback if the live demo fails in class. The demo runs on
  Daniel's laptop: rehearse it there.
- [ ] **F6, Tue 17 evening.** Own slides (retrieval choices) in `slides/fabio.md`, and the demo.

### Gioia: evaluation

- [x] **G1, Mon 16 now.** `evaluation/metrics.py`: P@k, R@k, MRR, AP, nDCG@k from TREC qrels and runs, with
  unit tests on hand-computed examples (`tests/`). `evaluation/significance.py`: paired randomization
  test.
- [ ] **G2, Mon 16 evening.** `fonti` test set (`evaluation/build_fonti.py`): one query per source
  title, relevant document = the article. Drop titles in foreign languages, titles under 4 words,
  generic titles that occur for many articles (e.g. "Risultati Serie A"), duplicates. Store the
  word overlap between query and article title in `meta` (to split results into easy and
  paraphrase queries). Keep a fixed random sample of 1000 queries (seed in the script). Start on
  the sample, rerun on the full corpus.
- [ ] **G3, Mon 16 (queries and tool) - Tue 17 by 12:00 (pooling).** `manual` test set: 30 queries in four types: topical ("terremoto in
  Abruzzo"), entity ("Romano Prodi"), time-bound ("elezioni 2008"), vague or paraphrased
  ("disastro in una miniera"). Pooling: top 10 of the five configurations of E1, E3 and E5,
  merged and shuffled, one file per judge; grades 0 (not relevant), 1 (partly), 2 (relevant),
  given with a small terminal tool (`python -m evaluation.judge`), with written guidelines in
  `evaluation/testsets/manual/GUIDELINES.md`.
- [ ] **G4, Tue 17, 12:00-15:00.** Judgments: all three judge (about one hour each, about 300
  judgments per person; 10 queries judged by two people to measure agreement).
- [ ] **G5, Mon 16 (runner on BM25) - Tue 17 20:00 (official run).** `evaluation/run.py`: runs every configuration on every test set, writes runs,
  metrics CSV, significance tests and latency; one command reproduces all numbers.
- [ ] **G6, Tue 17 evening.** Tables and plots for the slides (`results/figures/`), reading of
  the results, own slides (test strategy, results) in `slides/gioia.md`.

## Slides

The presentation is in Italian, about 20 minutes: about 6 minutes each, Fabio's demo included in
his time. No code on the slides. Sober style, not "AI style" (as in homework 2: label plus one
line, figures and tables carry the content).

Each person writes the content of their slides in `slides/<name>.md`, in Italian, by **Tuesday
17, 22:00**, with this structure for every slide:

```markdown
## Slide N: <title>
Contenuto: <one or two short lines, or the table>
Figura: <path in the repository, e.g. results/figures/e3_buckets.png, or "nessuna">
Note del relatore: <what to say, a few sentences>
```

Order: Daniel (the data and its challenges, indexing choices), Fabio (retrieval choices, demo),
Gioia (test strategy, results, conclusions). Daniel builds the deck from the three files on
Wednesday morning.

## Timeline

| When | Milestone |
|---|---|
| Mon 16, 15:00 | sample pushed (Daniel); metrics module ready (Gioia); web app running on fake data (Fabio) |
| Mon 16, 19:00 | full corpus parsed and indexed on every laptop; BM25 search and `fonti` test set |
| Mon 16, night | embeddings pushed (Daniel); 30 manual queries drafted and judging tool ready (Gioia) |
| Tue 17, 10:00 | queries reviewed by Daniel and Fabio |
| Tue 17, 11:00 | vector and hybrid search pushed (Fabio) |
| Tue 17, 12:00 | pool ready (Gioia) |
| Tue 17, 15:00 | judgments done (each person blocks one hour between 12:00 and 15:00) |
| Tue 17, 20:00 | **code freeze**: official run, numbers final |
| Tue 17, 22:00 | slide content of each person in `slides/` |
| Wed 18, 11:00 | deck complete; rehearsal with timing (about 6 minutes each), demo on Daniel's laptop |
| Wed 18, 14:00 | README final, repository made public, PDF and pptx uploaded |

If on Tuesday at 18:00 something essential is missing, the group decides together whether to move
the code freeze to Wednesday 12:00 and the delivery to Wednesday evening. Stretch items (E7, E8)
are dropped first.
