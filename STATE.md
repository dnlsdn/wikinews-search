# State

Shared memory of the project. Read it before starting, update it before every push
(rules in `CLAUDE.md`). Newest log entry first.

## Current state

| Part | Owner | State |
|---|---|---|
| Repository, plan, contracts, skeleton | Daniel | done (16 Nov) |
| Data and indexing | Daniel | D1-D4 and D6 done (16 Nov 14:50), D7 slide draft in `slides/daniel.md` (15:05), D5 done (15:45: E8 indices `int8`/`bbq` built, measurement waits for Fabio's configurations and Gioia's runner; no asciifolding variant); next: review of Gioia's queries Tue 10:00, deck on Wednesday |
| Search and interface | Fabio | F1-F4 done (16 Nov 16:30); E8 configurations `knn-int8`, `knn-bbq` (16:35, issue #6); F5 work in progress (16:55): `docs/demo.md` and `results/demo/` pushed, rehearsal on Daniel's laptop missing (issue #8); F6 in progress (17:05): README usage done, slide outline decided, `slides/fabio.md` written after the official run (Tue 20:00-22:00) |
| Evaluation | Gioia | G1 done (16 Nov 12:30): metrics, TREC files, significance tested; G2 done (16 Nov 15:45): `fonti` test set, 7,223 queries; G3 in progress (16 Nov 21:30): judging tool, pooling script, guidelines and the 30 `manual` queries pushed; next: review of the queries by Daniel and Fabio (Tue 10:00), then pooling (Tue 12:00) |

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

1. **16 Nov 2026 15:30, Daniel: vector structure variants for E8.** `wikisearch/config.py` has
   `VECTOR_INDEX_TYPES` (`hnsw`, `int8_hnsw`, `bbq_hnsw`) and `index_name(analyzer,
   vector_index="hnsw")`: `wikinews-italian-int8` and `wikinews-italian-bbq`. A configuration may
   have the optional key `"vector_index"` (default `"hnsw"`); `tests/test_contracts.py` checks
   it. Existing calls are unchanged. Fabio: pass the key to `index_name` in `search()` and add the
   two `knn` configurations; Gioia: build the two indices locally before running them
   (`docs/contracts.md` section 2, item 4). Issue `contract-change` opened.

## Messages

Not here: messages between sessions are GitHub issues (`CLAUDE.md`, "Talking to the other
sessions"). The session briefing lists the open ones.

## Log

### 16 Nov 2026 21:30, Gioia: the 30 `manual` queries (G3, work in progress)

The 30 queries of the `manual` test set are in `evaluation/testsets/manual/queries.tsv`
(`qid<TAB>text<TAB>meta`, `meta = {"type", "need"}`, ids `M01`-`M30`). Written before looking at
any result: drafted by Claude without querying the index, approved by Gioia as they are. Nothing
is pooled yet: the pool waits for the review by Daniel and Fabio (Tuesday 10:00, issue opened).

1. **Types**: 7 `topical`, 8 `entity`, 7 `time`, 8 `vague` (8 vague because paraphrases are where
   E3 expects the vectors to help). The types alternate in the file (topical, entity, time,
   vague, ...), so queries 1-10, the doubly judged ones, contain all four types (3, 3, 2, 2).
2. **Years and topics**: most queries are on 2005-2008, the bulk of the corpus; five reach later
   years (Costa Concordia 2012, Rita Levi-Montalcini's death 2012, Papa Francesco 2013+,
   Fukushima 2011, COVID-19 2020), which may have few relevant articles. Topics: politics, sport,
   science, disasters, culture, economy.
3. **Excluded on purpose**: the demo queries of `docs/demo.md` (chosen by looking at results) and
   the two examples of `GUIDELINES.md` ("terremoto in Abruzzo", coal mine accidents), so that the
   judges have not seen graded examples on a test query.
4. **Needs** are in English (repository rule); judges grade against the need, not the words.
5. Two `vague` queries still share one word with their target ("Senato" in M24, "ferrovia" in
   M20): a paraphrase with no word at all in common was too artificial.

Assignment (as proposed at 15:50, to be confirmed in the issue): Gioia M01-M10, Daniel M11-M20
and M01-M05, Fabio M21-M30 and M06-M10. With 20-25 documents per query Daniel and Fabio get
300-375 judgments, Gioia 200-250: if `pool.py` reports more than 350 for someone, the doubly
judged queries are cut first, as the brief says.

How to check: `uv run pytest -q` (the contract test reads every `queries.tsv`): 106 passed,
2 skipped (the E8 indices are not built on Gioia's laptop). Nothing changes for the others
except the review. Next: pooling after the review (Tuesday by 12:00), then judging 12:00-15:00.

### 16 Nov 2026 18:15, Daniel: demo links checked on Daniel's laptop (issue #8), issue #6 closed

Issue #8 (Fabio): every link of `docs/demo.md` checked on Daniel's laptop, through `/api/search`
with the parameters of the links, after pulling cef8d31 (indices and shared embeddings already
built). All results are the ones the script describes: special page first with `hybrid-rrf` and
out of the top 10 with `hybrid-rrf-published`; 3 articles with the date and ANSA filters;
Pontecorvo found by BM25, not by `knn`; Benedetto XVI 1st for `knn`, 78th for BM25 at k=100, 6th
for `hybrid-rrf`; 9 of 10 lottery draws; spare query as described. Screenshot 4b compared by eye:
identical. Timing on this Mac: the first vector query took 19 s (model load), then hybrid
0.2-0.8 s and BM25 under 0.1 s, so the warm-up before class is needed.

Decided by Daniel: the rehearsal with Fabio at Daniel's laptop as soon as possible (today or by
Tuesday afternoon); Fabio proposes the time (asked in #8, which stays open until the rehearsal).
Issue #6 (E8 contract change) closed: Fabio and Gioia acknowledged it.

How to run the check: Elasticsearch running, `uv run uvicorn wikisearch.web.app:app`, then the
links of `docs/demo.md`. No code change; 107 tests passed. Next: D7 (slides with the official
numbers on Tuesday evening, deck on Wednesday), review of Gioia's 30 queries when pushed.

### 16 Nov 2026 17:05, Fabio: F6 README usage, slide outline (work in progress)

F6 in progress. Done: the "Search and web app" subsection of `README.md` (start, what the
interface does, the table of the configurations, command line, fake mode, API). Commands checked
on Fabio's laptop.

Slides, decided by Fabio:
1. **Outline**: four slides and the demo, in about 6 minutes (the demo takes about 3.5):
   1. "Una ricerca, molte configurazioni": one function `search(query, config)` used by the web
      app and the evaluation; every design choice is a named configuration, i.e. a knob of the
      ablation.
   2. "BM25: campi e pesi" (E2): title^3 + lead^2 + body against title only, body only, equal
      weights.
   3. "Lessicale, semantica, ibrida" (E3): BM25, kNN, hybrid; why RRF and not a sum of scores;
      results split by query-title overlap; latencies.
   4. "Filtri, faccette, pagine non pubblicate" (E5): filters as filter clauses (no effect on
      scores, also inside the kNN search), lexical facets, the published boost.
   5. Demo: the five queries of `docs/demo.md`.
2. **When**: `slides/fabio.md` is written on Tuesday evening, after the official run (code
   freeze 20:00, slides due 22:00), with the final numbers of Gioia's G5, not with placeholders
   now. Gioia: Fabio's slides need MRR@10 and R@100 on `fonti` for the E2 and E3 configurations
   (E3 also by overlap bucket), nDCG@10 on `manual` for E5, with confidence intervals and the
   significance tests, as soon as the official run is done.

Nothing changes for the others; no code change, 107 tests passed. Next: rehearsal of the demo
(issue #8), the review of Gioia's queries (Tuesday 10:00), judging (Tuesday 12:00-15:00), then
`slides/fabio.md` on Tuesday evening.

### 16 Nov 2026 16:55, Fabio: F5 demo script and screenshots (work in progress)

F5 work in progress: `docs/demo.md` and the fallback screenshots in `results/demo/` are pushed;
F5 is not ticked because the plan asks for a rehearsal on Daniel's laptop (issue opened to
Daniel). Queries chosen by Claude on the real data and approved by Fabio.

The demo, five queries in this order (links, what to show and the sentence to say in
`docs/demo.md`):

| # | query | configurations | what it shows |
|---|---|---|---|
| 1 | `terremoto in Abruzzo` | `hybrid-rrf`, then `hybrid-rrf-published` | result page and facets; the first hit "Speciale Terremoto in Abruzzo" is not published, the boost moves it out of the top |
| 2 | `terremoto`, 6-30 Apr 2009, agency ANSA | `bm25-italian` | filters: 3 articles left |
| 3 | `Pontecorvo` | `bm25-italian` vs `knn` | exact name, BM25 wins: BM25 finds "Si è spento Gillo Pontecorvo" first; `knn` returns service pages and "crolla un ponteggio" (sub-word look-alikes) |
| 4 | `il pontefice è deceduto` | `bm25-italian` vs `knn`, then `knn` vs `hybrid-rrf` | paraphrase, kNN wins: "Il papa emerito Benedetto XVI è morto" is 1st for `knn`, 78th for BM25 (the article says "papa", never "pontefice"), 6th for the hybrid, which puts "Giovanni Paolo II è morto" 4th |
| 5 | `concorso superenalotto` | `bm25-italian` | near-duplicates: 9 of the top 10 are lottery draw pages (motivates E7) |

Spare query: `rincaro del greggio`, where `knn` fails (unrelated pages) and BM25 and the hybrid
find the oil price records: vectors do not always win.

Decisions, and why:
1. Every step is a link (query, configurations, filters in the URL), so nothing is typed live.
2. The "knn wins" query had to have no **title** word in common with its target (Daniel's note
   of 15:05: "disastro in una miniera" is found by BM25 through "miniera"). The Benedetto XVI
   article contains "deceduto" once in its lead, so the demo says "BM25 ranks it 78th", not "no
   word in common".
3. Two cases against the vectors (3 and the spare query) next to the one in their favour (4):
   the comparison is fair and prepares the question "why hybrid".
4. Screenshots: headless Edge on the real web app, 1400 or 1700 px wide, 8 PNG files, 1.4 MB.

How to run: Elasticsearch and `uv run uvicorn wikisearch.web.app:app`, then the links in
`docs/demo.md` (the first vector query loads the model: 25 s today). Tests: 107 passed, no code
change. Next: F6 (slides in `slides/fabio.md`); rehearsal on Daniel's laptop Tuesday afternoon
or Wednesday morning.

### 16 Nov 2026 16:35, Fabio: E8 configurations `knn-int8` and `knn-bbq` (issue #6)

Issue #6 (contract change by Daniel) handled, decided by Fabio: the E8 configurations are added
now, before F5, because the change is small and Gioia's runner needs their names. E8 stays a
stretch item for the measurement.

1. `search()` queries `index_name(cfg["analyzer"], cfg.get("vector_index", "hnsw"))` (helper
   `_index` in `wikisearch/search/__init__.py`). Every existing configuration still queries the
   same index.
2. Two configurations in `configs.py`, names chosen by Fabio (the ones Daniel proposed):
   `knn-int8` (`vector_index: int8_hnsw`) and `knn-bbq` (`vector_index: bbq_hnsw`). They are
   exactly `knn` plus the `vector_index` key: same model, same `k`, same
   `num_candidates = max(100, 10 * k)`, same filters, so E8 measures the vector structure alone.
   A unit test checks this.
3. The web app lists them like every configuration (selector and compare mode). Facets keep
   using the main index of the analyzer: the documents are the same.
4. Tests: `uv run pytest -q tests/test_search.py`. Two new unit tests (E8 configurations differ
   from `knn` only in `vector_index`; each configuration queries its own index). The integration
   test of the vector configurations **skips** a configuration whose index is not built on that
   laptop, so laptops without the E8 indices still pass. Full suite: 107 passed.

How to run (PowerShell the same), Elasticsearch running: build the two indices once,
`uv run python -m wikisearch.ingest.index --analyzers italian --vector-index int8_hnsw bbq_hnsw --no-csv`
(about 30 s on Fabio's laptop; `--no-csv` so that `results/indexing.csv`, Daniel's official
sizes, is not touched), then
`uv run python -m wikisearch.search "disastro in una miniera" --config knn-bbq`.

Quick sanity check on Fabio's laptop (5 queries, not an evaluation: E8 numbers come from Gioia's
runner on `fonti`): the top 10 of `knn-int8` is the same set as `knn` on 5 / 5 queries, `knn-bbq`
on 4 / 5 (9 of 10 on the fifth). Median latency at k=100: `knn` 57 ms, `knn-int8` 52 ms,
`knn-bbq` 53 ms (warm model). Index size on disk: `wikinews-italian` 52.4 MB, `-int8` 57.0 MB,
`-bbq` 53.1 MB: the quantized indices are not smaller on disk because Elasticsearch keeps the
float vectors next to the quantized ones (for rescoring); the gain is in the memory the graph
search needs (Daniel's memory split in the log of 16 Nov 15:30).

For the others: Gioia, the names are `knn-int8` and `knn-bbq`; build the two indices before
running them (command above). Answered in issue #6. Next: F5 (demo script and screenshots).

### 16 Nov 2026 15:56, Gioia: commit messages without step codes

Decided by Gioia: her commit messages no longer contain the plan's step codes (G1, G2, "wip"),
because GitHub shows the last commit message next to every file. The step stays in the log title
and in `PLAN.md`. Pushed commits are not rewritten (no force-push on `main`); the docstrings of
`build_fonti.py`, `judge.py`, `pool.py` and of their tests no longer name the step either. No code
change, nothing changes for the others.

### 16 Nov 2026 15:50, Gioia: G3 judging tool, pooling script, guidelines (work in progress)

G3 in progress. Pushed what does not depend on the 30 queries; the queries are being written by
Gioia now (before looking at any result) and come in the next push. Nothing is pooled yet.

1. **Judging tool** `evaluation/judge.py`: `uv run python -m evaluation.judge --judge <name>`
   (PowerShell the same). Shows one document at a time (progress `37/310`, query, information
   need, title, date, lead up to 900 characters); type `0`, `1`, `2` and Enter, `o` opens the
   article in the browser, `b` goes back, `q` quits, Enter keeps the grade of a document already
   judged. Every grade is appended at once to `evaluation/testsets/manual/judgments/<name>.tsv`
   (`qid, doc_id, grade, time`), so it can be stopped and resumed; the last grade of a pair wins.
   Line-based `input()`, so it works in the macOS terminal and in PowerShell; stdout is
   reconfigured to UTF-8 for the accents.
2. **Pooling** `evaluation/pool.py`: `uv run python -m evaluation.pool` (Elasticsearch, full
   indices, every configuration: F4 is pushed). Top 10 of `bm25-standard`, `bm25-italian`, `knn`,
   `hybrid-rrf`, `hybrid-rrf-published`, merged, deduplicated, shuffled per query
   (`random.Random("42-<qid>")`). Title, date, lead and URL come from `docs.jsonl`. Writes
   `evaluation/testsets/manual/judging/<name>.tsv` (header `qid, query, doc_id, title, date, lead,
   url`) and prints pool sizes, documents found by one configuration only, and judgments per
   person (flag above 350). Which configuration found each document goes to
   `results/runs/manual/pool_found_by.json`, not committed, so the judges stay blind.
3. **Assignment** (proposed, to be confirmed by the group): queries in file order, 1-10 Gioia,
   11-20 Daniel, 21-30 Fabio; the second judgment of queries 1-10 is split, 1-5 Daniel and 6-10
   Fabio, so that each person has about 300 judgments (a single second judge for all of 1-10
   would get about 450, over the brief's 350).
4. **Guidelines draft** `evaluation/testsets/manual/GUIDELINES.md`: grades 2 / 1 / 0 as in the
   brief, rules (judge the article not the snippet, each article on its own, time matters when the
   need says so, non-news pages judged like any article, when in doubt the lower grade, no
   talking before everyone has finished), illustrative examples on two queries that are not in
   the test set.

Tests: `uv run pytest -q tests/test_judging.py` (5 tests: assignment, pooling with a fake search,
grades saved and resumed, back and regrade, Enter keeps a grade). Nothing changes for the others.
Next: the 30 queries in `evaluation/testsets/manual/queries.tsv`, then an issue to Daniel and
Fabio for the review (Tuesday 10:00) and the assignment.

### 16 Nov 2026 15:45, Gioia: G2 `fonti` test set

Step G2 done: `evaluation/testsets/fonti/queries.tsv` (7,223 queries), `qrels.txt` (one relevant
document per query, grade 1) and `queries_dev.tsv` (fixed subset of 1000, `random.Random(42)`),
built from the full `docs.jsonl`. Committed (1.4 MB).

How to run (needs `data/processed/docs.jsonl`, about 3 s): `uv run python -m evaluation.build_fonti`
(`--show-language 50` also prints 50 titles dropped and 50 kept by the English rule;
`--input data/sample/docs.sample.jsonl --out <dir>` for the sample, 184 queries). Tests:
`uv run pytest -q tests/test_build_fonti.py` (5 tests, hand-made documents, funnel counted by hand).
Before this, Gioia's local data was rebuilt (`parse --no-sample`, `index --no-csv`): same counts
and sizes as Daniel's (12,213 documents, 57.4 MB and 54.9 MB).

Funnel (source titles; filters in this order, each count is what is left):

| step | left |
|---|---|
| candidates (every `sources[i]`) | 17,192 |
| at least 4 words | 15,002 |
| not foreign (`{{fonteestera}}`) | 14,377 |
| not English | 13,842 |
| not ambiguous (same normalised title for 2+ documents) | 13,212 |
| article published | 12,851 |
| **one query per document** (first valid source) | **7,223** |

Buckets (Jaccard overlap of query and article title, Italian stop words removed): **low 2,787**
(< 0.2), **mid 3,580** (0.2-0.5), **high 856** (> 0.5); in the dev subset 400 / 490 / 110. 50 queries
are identical to the article title. Close to the 16 Nov simulation (7,318; 2,969 / 3,549 / 800).

Leakage check (300 random queries, normalised, verbatim in title + lead + body): **5 / 300 (1.7%)**,
below the 4% of the simulation. The five are natural quotes, not leaked sources: a quoted
sentence ("Ha offeso le mie donne"), an exhibition and a book title, "L'Italia vince la Coppa
Davis". No issue for Daniel.

Decisions, and why:
1. Ambiguity is counted over **all** documents, published or not (decided by Gioia): a
   non-published page is in the index too, so a headline shared with one would have a second
   plausible answer.
2. Language rule exactly as in the brief (decided by Gioia, after the eye check): English when a
   title has one of `the of for and with to is` and none of a list of Italian function words.
   Eye check: 50 / 50 dropped titles are English (one, "Sex Crimes and Vatican (sottotitolato)",
   is an English video title); **3 / 50 kept titles are not Italian** (one English kept because
   "I" is also the Italian article "i", one English headline without function words, one German).
   On a sample of 60 final queries without any Italian function word, about 14 were not Italian:
   **about 4-5% of the `fonti` queries are not in Italian** (English agency headlines, a few in
   Cyrillic, Portuguese, Serbian). A stricter rule (drop "i", add about 20 English function words,
   drop non-Latin scripts) would have removed only 56 of them; a real language detector would be
   a new dependency. Kept as a **known limit** for the slides: these queries are harder for the
   `italian` analyzer and favour the multilingual embeddings a little.
3. Normalisation (for ambiguity and the leakage check): lowercase, every non-word character is a
   separator. Titles are put on one line (tabs and newlines become spaces) for the TSV.
4. Overlap stop words: the Italian function words above plus elision fragments (`l`, `d`,
   `dell`, `all`, ...) and a few frequent words; both sets empty gives 0.

Noticed, for the reading of the results: 498 queries point to an article in a series of 5+
near-identical pages (`series_key`: lottery draws, match reports, e.g. "Lotto: Estrazioni del
27-11-2007"). The right page differs from its neighbours only by a date or a number, so these are
hard known-item queries for every configuration; worth a look in the per-query results of G5.

Noted from Fabio's F4 entry: every configuration runs now, so the G3 pool can use all five
configurations. The first knn query downloads the e5-small model (471 MB) on Gioia's laptop.

Nothing changes for the others. Next: G3 (Gioia writes the 30 manual queries, then guidelines,
pooling and judging tool; queries reviewed by Daniel and Fabio Tuesday 10:00).

### 16 Nov 2026 16:30, Fabio: F4 vector and hybrid search

Step F4 done: every configuration in `configs.py` runs, from the CLI, the web API and the UI
(compare mode included). Commit 08054d3. The 501 "configuration not available yet" is gone.

How to run (PowerShell, Elasticsearch running, indices built with the shared embeddings):
`uv run python -m wikisearch.search "disastro in una miniera" --config knn` (also `hybrid-rrf`,
`hybrid-rrf-published`); in the browser
`/?q=disastro+in+una+miniera&config=bm25-italian&compare=1&config2=knn`. Tests:
`uv run pytest -q tests/test_search.py` (unit tests of `rrf_fuse` and `knn_query` with a
hand-computed example, integration tests for every vector configuration, filters, and "bm25 does
not load the model"). First use downloads the model (`intfloat/multilingual-e5-small`, 471 MB in
the Hugging Face cache).

What was built (`wikisearch/search/`):
1. `embed.py`: the model is loaded once and lazily (the bm25 configurations never import
   sentence-transformers or torch); query = `"query: " + text`, `normalize_embeddings=True`.
   Query vectors are cached by text (knn, hybrid-rrf, hybrid-rrf-published and every page of
   the web app embed the same query once).
2. `knn`: Elasticsearch `knn` on `embedding`, `num_candidates = max(100, 10 * k)`, the same
   filters as BM25 inside `knn.filter` (filtered during the graph search, so a filtered query
   still returns k hits). Snippet = start of the lead (no words to highlight).
3. `hybrid`: BM25 and kNN, `depth` = 100 hits each, same filters, fused with
   `rrf_fuse(rankings, k=60)`: `score(d) = sum 1 / (60 + rank)`, ties broken by id. The score
   of a hybrid hit is its RRF score (at most 2/61 = 0.0328). Hit fields and the highlighted
   snippet come from the BM25 side when the document is there.
4. `boost_published` applies after fusion (and after kNN), as in F1: hits are fetched to
   `depth`, the published ones multiplied by 1.5, re-sorted, cut to k.

Decisions, and why:
1. RRF instead of a weighted sum of scores: BM25 scores are unbounded and depend on the query,
   the kNN scores of e5 are compressed (0.934-0.948 for the top 5 of "disastro in una miniera"; Elasticsearch reports (1 + cosine) / 2): a sum would need a
   normalization and a weight to tune. RRF uses only ranks, has one constant (k=60, the value of
   the original paper, Cormack et al. 2009) and is computed in Python so it is visible and tested.
2. Hybrid depth is `max(depth, k)`: equal to 100 for the evaluation (`k=100`); only a web page
   beyond the 10th asks for more.
3. With the published boost (1.5) on RRF scores, a published document beats an unpublished one
   unless the unpublished one is ranked much higher in both lists: E5 measures whether this helps.

Latencies (Fabio's Windows laptop, warm model, median of 10 queries, k=10 / k=100):
`bm25-italian` 68 / 57 ms, `knn` 67 / 88 ms, `hybrid-rrf` 140 / 139 ms,
`hybrid-rrf-published` 191 / 187 ms. Query embedding alone 17 ms. **Loading the model takes
about 23 s** (first query after starting the web app: the API answered in 27.8 s): for the demo,
run one query before class.

Example (E3, for the demo): "disastro in una miniera", `knn` top 5 are mine explosions in Ukraine,
China and Utah; `hybrid-rrf` keeps them in the top 5. As Daniel wrote, BM25 also finds them through
"miniera": the "knn wins" query of the demo still needs no word in common with the article.

For the others: Gioia, every configuration can now be run by the runner (issue #4 asked for this;
the pooling of G3 can use the five configurations). Issues #6 (E8 configurations) and #7 (new
rule) received; #6 needs Fabio's decision. Next: E8 configurations if Fabio agrees, then F5.

### 16 Nov 2026 16:00, Daniel: preparing the presentation and the oral is part of every session

Decided by Daniel: `CLAUDE.md`, "Working with your user", two new rules for every session.
(5) When a result that touches your user's part is pushed (above all Gioia's official results),
go through it with your user: what it shows, how it supports their choices, its limits, the
likely questions at the oral; every choice on the slides is backed by a number or an example.
(6) If something the presentation needs is late or missing, tell your user early, without doing
it in someone else's part. Daniel's brief also has a section "Beyond the code" (he assembles the
deck and keeps the three parts consistent). Nothing else changes: same steps, same scope rules.
Issue opened for Fabio and Gioia so that their running sessions see it.

### 16 Nov 2026 15:45, Daniel: D5 done, no asciifolding variant

Checked whether the optional `italian` + `asciifolding` variant (D5 item 3) is worth a contract
change. Decision (Daniel left it to the evidence): **not built**, D5 ticked (`sources_text` in
D3, E8 indices at 15:30).

Evidence (`_analyze` on `wikinews-italian`, and every non-ASCII word of the corpus and of the
source titles passed through the `italian` analyzer; script not committed):
1. The light Italian stemmer already folds Latin-1 accents on words it stems: "perché" and
   "perche" -> `perc`, "università" and "universita" -> `universit`, "Müller" and "Muller" ->
   `muller`. It leaves short words and other diacritics alone: "città" != "citta", "però" !=
   "pero", "Erdoğan" != "Erdogan", "Gdańsk" != "Gdansk".
2. Corpus: 2,165 distinct words keep an accent after the analyzer, in 7,742 documents; the
   frequent ones are short Italian words (già, così, città, però, può, età), then names
   (José, Petković, Forlì) and ordinals (1ª, 1º).
3. `fonti` queries: 270 of 15,905 published non-foreign source titles write an accent as an
   apostrophe (newspaper capitals: "SARA' DISTRUTTO", "E' una scelta", "Senato da' fiducia"); in
   most of them the word is a stop word anyway (è, sarà, dà, sì).
4. So the variant would help users who type without accents ("citta", "forli"), but neither
   test set has such queries (headlines and our own queries carry accents): it would cost a third
   index on every laptop, a configuration for Fabio and a run for Gioia for a result we expect to
   be null. Recorded as a known limit; one sentence added to the speaker notes of slide 6 in
   `slides/daniel.md`.

Nothing changes for the others. Next: review of Gioia's 30 queries (Tuesday 10:00); deck on
Wednesday.

### 16 Nov 2026 15:30, Daniel: E8 indices (vector quantization), contract change

Decided by Daniel: E8 now instead of Tuesday (the indices do not need F4; only the measurement
does), and a new configuration key rather than new analyzer variants (the analyzer is text
analysis, the vector structure is a separate knob).

Built `wikinews-italian-int8` (`int8_hnsw`) and `wikinews-italian-bbq` (`bbq_hnsw`): same 12,213
documents and vectors as `wikinews-italian`, only `index_options` differs, so E8 isolates the
quantization. How to run (about 1 minute, +115 MB of disk, Elasticsearch running):

    uv run python -m wikisearch.ingest.index --analyzers italian --vector-index int8_hnsw bbq_hnsw

(`--repeat 3` for the timings; the default build is unchanged and builds only `hnsw` indices.)

Numbers (Daniel's Mac, three builds each in `results/indexing.csv`; sizes from `_stats/store`,
the split from `_disk_usage` and `_stats/dense_vector`, which reports the off-heap files):

| index | build s (3 runs) | index size | float32 vectors | quantized vectors | HNSW graph |
|---|---|---|---|---|---|
| `wikinews-italian` (`hnsw`) | 14.0, 14.2, 13.3 | 54.9 MB | 18.76 MB | none | 0.41 MB |
| `wikinews-italian-int8` | 24.0, 13.1, 16.5 | 59.8 MB | 18.76 MB | 4.89 MB (400 B/vector) | 0.41 MB |
| `wikinews-italian-bbq` | 16.6, 14.5, 16.6 | 55.7 MB | 18.76 MB | 0.76 MB (62 B/vector) | 0.41 MB |

What this means (for the slides and the oral):
1. **Quantization makes the index bigger on disk, not smaller**: Elasticsearch keeps the float32
   vectors and adds the quantized copy (+4.9 MB int8, +0.8 MB bbq). The saving is in the memory
   the search needs: the graph walk reads only the quantized vectors and the graph, so the part
   that must stay in RAM goes from 19.2 MB (hnsw) to 5.3 MB (int8, about 4x less) and 1.2 MB
   (bbq, about 16x less). The float32 vectors are read only to rescore the final candidates.
2. Defaults recorded from the mapping: `m` 16, `ef_construction` 100 for all three; `bbq_hnsw`
   gets `rescore_vector.oversample: 3.0` (it fetches 3k candidates and rescores them with the
   float32 vectors), `int8_hnsw` has no rescoring.
3. At 12,213 documents everything fits in memory anyway: E8 shows the quality cost of a
   structure that would matter at millions of vectors, and the slide must say so.

Sanity check, not the E8 result (100 random documents as queries with their own vector, k=10,
num_candidates=100, after a warm-up; script not committed): top-10 overlap with the `hnsw`
index 0.987 for int8 (minimum 0.9) and 0.951 for bbq (minimum 0.2: one query lost most of its
neighbours even with rescoring); the document itself first in 100/100 (int8) and 99/100 (bbq).
Latency p50 about 6 ms for all three on this Mac. The official E8 numbers are Gioia's: MRR@10 and
R@100 of the two new `knn` configurations on `fonti`, and latency.

Contract change (section above, `docs/contracts.md` section 2 item 4): `VECTOR_INDEX_TYPES`,
`index_name(analyzer, vector_index)`, optional configuration key `"vector_index"`. Tests: one
new in `tests/test_index.py`, one check in `tests/test_contracts.py`. Issue `contract-change`
opened for Fabio (configurations `knn-int8`, `knn-bbq` with the same `num_candidates` as `knn`)
and Gioia (build the two indices before the official run).

Next: review of Gioia's 30 queries (Tuesday 10:00, not pushed yet); the `italian` +
`asciifolding` variant only if Daniel wants it; deck on Wednesday.

### 16 Nov 2026 15:15, Fabio: F3b web interface complete

Step F3 done (F3a skeleton + F3b interface): every item of the brief works in fake mode and on the
full indices with the BM25 configurations; with `knn` and `hybrid-*` (including the default
`hybrid-rrf`) a column shows "configuration not available yet" until F4 (Tuesday 11:00).

How to run (PowerShell): `uv run uvicorn wikisearch.web.app:app --reload`, then
http://localhost:8000 (fake mode: `$env:WIKISEARCH_FAKE=1` first). Example links:
`/?q=terremoto+abruzzo&config=bm25-italian&compare=1&config2=bm25-standard` (E1 side by side),
`/?q=elezioni&config=bm25-italian&date_from=2008-01-01&date_to=2008-12-31&agency=ANSA`.
Tests: `uv run pytest -q tests/test_web.py` (11 tests). Checked by hand in the browser on real
data: filters, facets, pagination, browser back, compare mode, document view and back.

What the interface does (`wikisearch/web/static/`, plain HTML, CSS, JS, no build step):
1. Search box, configuration selector, "Compare" toggle with a second selector.
2. Results: rank, title (opens the document view), date, agencies, highlighted snippet,
   category tags, thumbnail, muted "not published"; "N results in X ms".
3. Left column: date range, "Published only", category and source checkboxes with counts from
   `/api/facets`, "Clear filters". Every change reruns the search from page 1.
4. Previous / next. `search()` does not count all matches, so "next" is enabled when a column
   filled the page (10 hits).
5. Document view `#/doc/<id>`: title, date, body, categories, sources with links (foreign ones
   marked), linked Wikipedia entities (links to it.wikipedia.org), link to the original page.
6. Compare mode: same query, filters and page, two configurations in two columns with ranks.
   The second column defaults to `knn` (lexical against semantic is E3).
7. All the state is in the query string (`q`, `config`, `compare`, `config2`, `page`,
   `date_from`, `date_to`, repeated `category` and `agency`, `published`): a demo query opens
   from a link and the browser's back button works. The document view uses the hash, so the
   results stay underneath and "back" does not search again.

Decisions, and why:
1. Facet counts depend on the query and the configuration's index, not on the active filters
   (the endpoint has no filter parameters, as in the contract): the counts say how much each
   value would give for this query. They also count every document matching **any** query word
   (BM25 `multi_match` is an OR): "romano prodi" gives Europa 505. Worth saying in the demo.
2. A checked value stays in the list even when it leaves the top buckets, so it can be unchecked.
3. Responses of an older request are dropped (filters clicked quickly cannot overwrite newer
   results).
4. The 501 message of `/api/search` no longer suggests fake mode: "configuration not available
   yet (...)".

Noted from Daniel's 15:05 entry, for F5: "disastro in una miniera" is not a BM25 failure
(`bm25-italian` finds the mine explosions through "miniera"); the demo's "knn wins" query must
share no word with the article.

Nothing changes for the others. Next: F4 (knn, hybrid RRF, published boost), target Tuesday 11:00.

### 16 Nov 2026 15:05, Daniel: D7 first draft of Daniel's slides

`slides/daniel.md`: seven slides in Italian (corpus; data hidden in templates; categories and
agencies; pages that are not news; leakage; the two indices; embeddings), with the structure of
`PLAN.md`. Every number comes from `results/data_report.md` and `results/indexing.csv`. Figures:
none yet (tables carry the content). D7 stays unticked: the deck, the cover and the publication
come on Wednesday.

Checked while writing (on `wikinews-italian`, Elasticsearch 9.5.0):
1. `_analyze`: "l'Italia" -> `ital`, "elezioni" and "elezione" -> `elezion`.
2. A `dense_vector` with 384 dimensions and no `index_options` gets `bbq_hnsw` (binary
   quantization, rescore oversample 3) by default: this is why the contract sets `hnsw`
   explicitly, and the E8 question.
3. **Correction to the D4 entry**: "disastro in una miniera" is not a query BM25 would miss.
   `bm25-italian` returns the same mine explosions in its top 5 through "miniera"; the knn result
   only shows that the vectors match without the word "disastro". For a BM25 failure, use queries
   that share no word with the article (the low-overlap bucket of `fonti`, E3).
4. e5-small truncates at 512 tokens (`max_seq_length`), one reason to embed title and lead only.

Nothing changes for the others. Next: E8 indices once Fabio's F4 knn configuration exists,
review of Gioia's 30 queries (Tuesday 10:00).

### 16 Nov 2026 14:55, Fabio: F2 ticked

F2 (web API with FastAPI: search, document, facets, configs, highlighted snippets from
Elasticsearch) has no work left: the endpoints were built in F3a and work on real data since F1
(checked on the full indices: `/api/search` with pagination and filters, `/api/facets`,
`/api/doc` without `embedding`). Ticked with Fabio's agreement. Nothing changes for the others.
Next: F3b.

### 16 Nov 2026 14:50, Daniel: D6 data report

Step D6 done: `results/data_report.md`, the challenges of the data with numbers and one real page
each, the indices, the known limits. It is the base of Daniel's slides. It is **generated**, not
written by hand: `uv run python -m wikisearch.ingest.report` (about 12 s, 0.8 GB, needs the dump)
recomputes every number from the dump with the parser's own functions, so rerun it whenever the
parser changes. Examples are fixed page ids; the script stops if one disappears.

Sections: corpus at a glance; 2.1 duplicates; 2.2 date in a template (`{{data}}` 10,918,
`{{luogodata}}` 769, category 40, none 486); 2.3 the dump's abstract is unusable (11,632 start with
the date line, so `lead` comes from the HTML); 2.4 categories (5,963 -> 1,753, dropping 4,188 daily
and 22 maintenance categories); 2.5 agencies (2,965 spellings -> 2,304 names; filtering on the
plain "la Repubblica" would miss 28% of its sources); 2.6 near-duplicate series (76 patterns with
5+ pages, 2,742 documents, 22%); 2.7 non-published pages (1,181: specials, TV schedules, tables,
rugby round reports, drafts); 2.8 tables (36% of the text, 366 documents are only tables); 2.9
leakage; 3 indices (means of the last three builds); 4 known limits.

Found while checking the numbers (worth knowing for the slides and the oral):
1. Leakage example (id 31695): query "Il Dna lo scagiona, ma ha già scontato 24 anni" shares only
   `anni` with the article title, and the `italian` light stemmer does **not** merge "scagiona"
   (`scagion`) and "scagionato" (`scagionat`), checked with `_analyze`. With Fabio's F1:
   `bm25-italian-title` does not find the article in the top 100, `bm25-italian` ranks it 1st
   through the body ("DNA", "24 anni"), `bm25-italian-leak` also 1st with the score from 37 to 63.
2. Sources outside the "Fonti" section: 381 pages (mostly under "Collegamenti esterni"); even
   dropping every section the parser drops by heading would leave sources in 19 pages (no heading,
   inline before "Fonti", "Riferimenti", "Aggiornamenti"). This is why the parser removes every
   source template, wherever it is. (The 631 of the D2 entry counted something else; the report's
   numbers are the ones to use.)
3. Agency normalisation, two small flaws left as known limits (not worth a reparse): the leading
   article is removed even without a space (needed for `ilpost.it`), which wrongly merges `VG`
   with `IVG` and `post.com` with Il Post (one or two sources each); 9 names in Cyrillic or `-`
   (18 sources) get an empty key and stay as written. Because of the second one,
   `distinct_agencies` in `parse_report.json` (2,295) is 9 short of the real 2,304.

Parser change (no effect on the output: `docs.jsonl` regenerated and compared byte by byte,
identical): `html_blocks` also returns the characters of table text, and `read_latest` can count
the lines of each id; both only feed the report. Two tests added in `tests/test_parse.py` for the
"is this source inside a Fonti section" logic. Nothing changes for the others.

Next: the D5 extras (E8 once Fabio's F4 knn configuration exists), the review of Gioia's 30
queries (Tuesday 10:00), then D7 slides.

### 16 Nov 2026 14:40, Fabio: F1 BM25 search

Step F1 done: `search()` (contract section 3) works for every `bm25` configuration
(`bm25-standard`, `bm25-italian`, `bm25-italian-title`, `bm25-italian-body`, `bm25-italian-flat`,
`bm25-italian-leak`), so E1, E2 and E4 can be run. **Gioia: the runner can call it now** (issue
opened). `knn` and `hybrid` raise `NotImplementedError` until F4 (Tuesday 11:00); this includes
the default configuration `hybrid-rrf`, so in the web app pick a `bm25-*` configuration until then.

How to run:
- CLI: `uv run python -m wikisearch.search "terremoto abruzzo" --config bm25-italian` (options
  `-k`, `--date-from`, `--date-to`, `--category` and `--agency` repeatable, `--published`);
  prints rank, score, date, title.
- Web app on real data (PowerShell): `Remove-Item Env:WIKISEARCH_FAKE` if set, then
  `uv run uvicorn wikisearch.web.app:app --reload`; `/api/search`, `/api/facets` and `/api/doc`
  checked on the full indices.
- Tests: `uv run pytest -q tests/test_search.py` (8 unit tests, 8 integration tests skipped when
  Elasticsearch is not running).
- Local data on Fabio's laptop rebuilt after D2-D4 (`parse --no-sample`, `index --no-csv`): same
  counts and sizes as Daniel's (12,213 docs, 57.4 MB and 54.9 MB); `--no-csv` so that Windows
  timings do not mix with Daniel's rows in `results/indexing.csv`.

How it works (`wikisearch/search/__init__.py`, `es.py`):
1. Query: `bool.must = multi_match(best_fields, fields and weights of the configuration,
   tie_breaker 0.3)`, `bool.filter = filters_to_es(filters)`. Filters are in `filter`, not in
   `must`: they restrict the result set without changing the BM25 scores, so a filtered and an
   unfiltered ranking are comparable (and Elasticsearch can cache them).
2. `filters_to_es` (pure function): inclusive `range` on `date`, one `term` per category (all
   must match), one `terms` on `agencies` (any), `term` on `published` when not None. No default
   filter, as the contract requires.
3. Snippet: highlight on `lead` and `body`, one fragment of 160 characters; the first lead
   fragment, else the body fragment, else the first 200 characters of `lead`. Decision (not in
   the brief): highlight `encoder: html` and the fallback escaped too, because the UI inserts the
   snippet as HTML; the only markup in a snippet is `<em>`. Highlighting follows the searched
   fields, so `bm25-italian-title` shows the plain start of the lead (nothing highlighted there).
4. Only the fields of a `Hit` plus `lead` are fetched (`_source` includes), never `body` or
   `embedding`.
5. `boost_published` (none of the BM25 configurations uses it yet; E5 is on the hybrid): fetch
   `max(k, depth)` hits, multiply published scores, re-sort with ties by id, cut to `k`. Pure
   function with a hand-computed unit test, ready for F4.
6. Unknown configuration: `ValueError`; empty query or `k <= 0`: `[]` without calling
   Elasticsearch.

Numbers (Fabio's Windows laptop, 16 GB, Elasticsearch heap 1 GB, warm, k=100, 8 queries x 3,
highlight included): p50 / p95 latency `bm25-standard` 67 / 110 ms, `bm25-italian` 52 / 91 ms,
`bm25-italian-flat` 76 / 83 ms. Indicative only: the official E6 latencies are Gioia's.

Observation for E1 and the slides: "terremoto abruzzo" with `bm25-italian` ranks "Sisma in
Abruzzo: la lista con i dati dei terremoti" 3rd (the stemmer makes terremoti = terremoto); with
`bm25-standard` it is not in the top 5. With `bm25-italian-body` the top 5 changes completely
(the title is the strongest signal for news).

Issues: commented #3 and #4 (read, data rebuilt; left open because they are also for Gioia);
opened one for Gioia (F1 handoff). Next: F3b (filters, pagination, document view, compare mode),
then F4.

### 16 Nov 2026 14:15, Daniel: order of the remaining data steps

Decided by Daniel:
1. D5 item 1 (`sources_text`) is already done inside D3. D5 stays unticked because its extras are
   still wanted.
2. Next: **D6 data report** now (Monday afternoon instead of Tuesday), since it is the base of
   Daniel's slides and needs nothing from the others.
3. Then the D5 extras, in this order: **E8** (same vectors in `int8_hnsw` and `bbq_hnsw` indices)
   on Tuesday late morning, once Fabio's F4 knn configuration exists (open an issue to Fabio and
   Gioia for the matching configurations); the `italian` + `asciifolding` variant only if time is
   left, because it changes a contract on the busiest day.
4. Tuesday 10:00: review Gioia's 30 manual queries (handoff in `PLAN.md`).

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
