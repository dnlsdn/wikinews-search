# Plan

Homework 4 of Ingegneria dei Dati (prof. Merialdo): a web search engine over the Italian Wikinews
dump, a test strategy that compares design choices (ablation study), a 20 minute presentation with
a live demo. **Deadline: Thursday 19 November 2026, 18:00** (presentation uploaded through the course
form). Presentations in class on Friday 20.

What the professor asked for, in his words: the technical and methodological challenges, the
solutions (no code on the slides), the test strategy (which datasets, which metrics), the
experimental results and how they support the design choices, a live demo. Code and install
instructions on GitHub.

## Team and ownership

Each person owns a part of the system, the matching part of the presentation, and the directories
below. Work outside your directories only after writing it in `STATE.md` ("Requests").

| Person | GitHub | Part | Directories | Presentation |
|---|---|---|---|---|
| Daniel | dnlsdn | data and indexing: parsing the dump, cleaning, Elasticsearch mappings and analyzers, embeddings | `wikisearch/ingest/`, `docker-compose.yml` | the data and its challenges, indexing choices; assembles the deck |
| Fabio | fmdimarco | search and interface: BM25, vector and hybrid retrieval, filters, web API and UI, demo | `wikisearch/search/`, `wikisearch/web/` | retrieval choices and the live demo |
| Gioia | gioburattii | evaluation: test sets, metrics, experiment runner, results | `eval/`, `results/` | test strategy and experimental results |

Shared files: `wikisearch/schema.py`, `wikisearch/config.py`, `docs/contracts.md` (change only as
described there), `STATE.md` (everyone appends), `PLAN.md` (everyone ticks their own boxes),
`README.md` (Daniel keeps it current, the others send their sections).

## Why this split works

1. The only hard dependency is the corpus: search and evaluation need documents. Daniel's first
   job is therefore a **sample** (`data/sample/docs.sample.jsonl`, about 300 pages) pushed within
   the first afternoon, and the full index the same evening. Until then Fabio and Gioia work on
   the sample.
2. Every design choice to compare is a **named configuration** (`wikisearch/search/configs.py`).
   The person who implements a choice exposes it as a configuration; Gioia's runner evaluates all
   configurations with the same `search()` function the web app uses.
3. Each experiment has an owner who implements the knob and Gioia who measures it (table below).

## Experiments (the ablation study)

| # | Question | Variants | Knob owner | Metrics |
|---|---|---|---|---|
| E1 | Does Italian text analysis help? | standard vs italian analyzer | Daniel | MRR@10, R@100 on `fonti`; nDCG@10 on `manual` |
| E2 | Which fields to search, with which weights? | title only, body only, title+lead+body, title^3+lead^2+body | Fabio | MRR@10, R@100 on `fonti` |
| E3 | Lexical, semantic or both? | BM25, kNN (e5-small), hybrid with RRF | Fabio (query), Daniel (embeddings) | same, plus results split by query-title overlap (low overlap = paraphrase) |
| E4 | How much does leakage inflate results? | with and without the sources field | Daniel (field), Gioia (analysis) | MRR@10 on `fonti` |
| E5 | Should published pages rank higher? | no boost vs boost on `published` | Fabio | nDCG@10 on `manual` |
| E6 | What does each choice cost? | all of the above | Gioia | indexing time, index size, query latency p50/p95 |
| E7 (stretch) | Do near-duplicates hurt the result page? | collapse on `series_key` off/on | Fabio | distinct series in top 10, nDCG@10 |

Statistical significance: paired randomization test between configurations (as in homework 3),
reported with every comparison on the slides.

## Steps

Summary of the steps. The detailed instructions (files, functions, checks, what to do while
waiting for someone else) are in the personal briefs: `docs/briefs/daniel.md`,
`docs/briefs/fabio.md`, `docs/briefs/gioia.md`. Prompts to start a Claude Code session are in
`docs/briefs/README.md`.

Everyone runs Elasticsearch and builds the indices on their own laptop with Daniel's scripts
(the dump and the indices are not in git).

Tick a box only when the "done when" is true, and log it in `STATE.md`.

### Daniel: data and indexing

- [ ] **D1, Mon 16.** Elasticsearch running locally with `docker compose up -d` (single node, 1 GB
  heap, no Kibana; the laptop has 8 GB). Done when `curl localhost:9200` answers and the README
  says how.
- [ ] **D2, Mon 16.** Parser `wikisearch/ingest/parse.py`: dump -> `data/processed/docs.jsonl`
  following `docs/contracts.md` section 1 (dedupe the 25 double pages, date extraction, clean
  categories, sources and agencies, entities, body without "Fonti", `published`, `series_key`).
  Commit `data/sample/docs.sample.jsonl` (about 300 pages, mixed: news, sport tables, lottery,
  specials). Done when the sample is pushed and the parser reports coverage numbers (pages, dated
  pages, pages with sources).
- [ ] **D3, Mon 16 evening.** Indexer `wikisearch/ingest/index.py`: creates `wikinews-standard`
  and `wikinews-italian` with the mapping of section 2 and bulk-loads the corpus, measuring time
  and size. Accepts `--input` so the sample can be indexed too. Done when both indices hold all
  documents and the numbers are in `results/indexing.csv`.
- [ ] **D4, Tue 17.** Embeddings: `wikisearch/ingest/embed.py` computes e5-small vectors for all
  documents (cached in `data/processed/embeddings.npy`, not committed) and the indexer loads them
  into `embedding`. Done when a `knn` query from Kibana-less curl returns sensible neighbours.
- [ ] **D5, Tue 17.** `sources_text` field for E4, any further analyzer variant worth testing.
- [ ] **D6, Wed 18.** Data report for the slides: counts, cleaning decisions with numbers,
  examples of hard pages (`results/data_report.md`).
- [ ] **D7, Wed 18 - Thu 19.** Own slides (challenges of the data, indexing choices) and assembly
  of the whole deck.

### Fabio: search and interface

- [ ] **F1, Mon 16 - Tue 17.** `wikisearch/search/`: `search()` with BM25 configurations over
  `multi_match` (fields and weights from the configuration) and the filters of `Filters`. Until
  D3 is done, index the sample with `python -m wikisearch.ingest.index --input data/sample/...`.
  Done when every BM25 configuration of E1 and E2 runs.
- [ ] **F2, Tue 17.** Web API (contracts section 4) with FastAPI: search, document, facets,
  configs. Highlighted snippets from Elasticsearch.
- [ ] **F3, Tue 17.** Web UI (`wikisearch/web/static/`): search box, result list (title, date,
  snippet, categories, source agencies, image), filters (date range, category, agency,
  published), pagination, document page, **compare mode** (two configurations side by side,
  useful in the demo to show E3). Plain HTML, CSS and JS served by FastAPI: no build step.
- [ ] **F4, Tue 17.** kNN configuration (query embedded with `EMBEDDING_MODEL`) and hybrid with
  reciprocal rank fusion computed in Python (k=60, parameters in the configuration); boost on
  `published` (E5). Stretch: collapse on `series_key` (E7).
- [ ] **F5, Wed 18.** Demo script: 5-6 queries that show the features and the differences between
  configurations; screenshots as a fallback if the live demo fails in class.
- [ ] **F6, Wed 18 - Thu 19.** Own slides (retrieval choices) and the demo.

### Gioia: evaluation

- [ ] **G1, Mon 16.** `eval/metrics.py`: P@k, R@k, MRR, AP, nDCG@k from TREC qrels and runs, with
  unit tests on hand-computed examples (`tests/`). `eval/significance.py`: paired randomization
  test.
- [ ] **G2, Mon 16 - Tue 17.** `fonti` test set (`eval/build_fonti.py`): one query per source
  title, relevant document = the article. Drop titles in foreign languages, titles under 4 words,
  generic titles that occur for many articles (e.g. "Risultati Serie A"), duplicates. Store the
  word overlap between query and article title in `meta` (to split results into easy and
  paraphrase queries). Keep a fixed random sample of 1000 queries (seed in the script). Start on
  the sample, rerun on the full corpus.
- [ ] **G3, Tue 17.** `manual` test set: 30 queries in four types: topical ("terremoto in
  Abruzzo"), entity ("Romano Prodi"), time-bound ("elezioni 2008"), vague or paraphrased
  ("disastro in una miniera"). Pooling: top 10 of the five configurations of E1, E3 and E5,
  merged and shuffled, in one CSV per judge; grades 0 (not relevant), 1 (partly), 2 (relevant),
  with written guidelines in `eval/testsets/manual/GUIDELINES.md`.
- [ ] **G4, Wed 18 morning.** Judgments: all three judge (about one hour each, about 300
  judgments per person; 10 queries judged by two people to measure agreement).
- [ ] **G5, Wed 18.** `eval/run.py`: runs every configuration on every test set, writes runs,
  metrics CSV, significance tests and latency; one command reproduces all numbers.
- [ ] **G6, Wed 18 - Thu 19.** Tables and plots for the slides (`results/figures/`), reading of
  the results, own slides (test strategy, results).

## Timeline

| When | Milestone |
|---|---|
| Mon 16 evening | Elasticsearch up, sample and full corpus indexed, metrics module ready |
| Tue 17 evening | all configurations searchable, web UI usable, both test sets built, pool ready |
| Wed 18, 13:00 | judgments done (each person blocks about one hour in the morning) |
| Wed 18, 20:00 | **code freeze**: all experiments run, numbers final |
| Thu 19, 12:00 | deck complete; rehearsal with timing (about 7 minutes each) |
| Thu 19, 16:00 | README final, repository made public, PDF and pptx uploaded (2 hours of margin) |
