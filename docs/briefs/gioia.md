# Brief: Gioia, evaluation

You are helping **Gioia Buratti** (GitHub `gioburattii`). Gioia owns the evaluation: `evaluation/`,
`results/` and the evaluation tests in `tests/`. She presents the test strategy and the
experimental results. Read `CLAUDE.md`, `STATE.md`, `PLAN.md` and `docs/contracts.md` before this
file.

The professor grades this part most: he asked which datasets, which metrics, and how the results
support the design choices, like an ablation study. Every number on the slides must be
reproducible with one command.

Deadline: all numbers final by **Wednesday 18 November, 20:00** (code freeze).

## What the other two give you, and when

| From | What | Expected | How you know |
|---|---|---|---|
| Daniel | `data/sample/docs.sample.jsonl`, then the full `data/processed/docs.jsonl` (built locally with his parser) | Mon 16 afternoon / evening | log entries D2, D3 in `STATE.md` |
| Daniel | indices on your laptop with `python -m wikisearch.ingest.index` | Mon 16 evening | log entry D3 |
| Fabio | `search(query, config, k, filters)` working for BM25 | Tue 17 | log entry F1 |
| Fabio | `knn` and hybrid configurations | Tue 17 evening | log entry F4 |

If a step you need is not pushed yet, do the next step in the order below that does not need it,
and say so in the log. G1 and the query writing of G3 need nothing.

## Step 0: environment (first session only)

Gioia works on **macOS with 8 GB of RAM**: keep Elasticsearch to the 1 GB heap of the compose
file, do not run the experiments with other heavy apps open.

1. Docker Desktop (Settings, Resources: at least 3 GB of memory), `uv`
   (https://docs.astral.sh/uv/), git. Check with `docker --version`, `uv --version`.
2. `uv sync` in the repository (installs Python 3.12 and every dependency: a few minutes).
3. `docker compose up -d`, then `curl localhost:9200` must answer with `"number" : "9.5.0"`.
4. Download and extract the dump into `data/raw/` (README).
5. Done when all four work. Nothing to commit.

## Step G1 (start immediately): metrics and file formats

Files: `evaluation/trec.py`, `evaluation/metrics.py`, `evaluation/significance.py`, `tests/test_metrics.py`.
Formats are in `docs/contracts.md` section 5.

1. `trec.py`: `read_queries(path) -> dict[qid, (text, meta)]`, `read_qrels(path) -> dict[qid, dict[doc_id, grade]]`,
   `read_run(path) -> dict[qid, list[doc_id]]` (sorted by rank), `write_run(path, results, tag)`
   where `results` is `dict[qid, list[tuple[doc_id, score]]]`.
2. `metrics.py`, every function takes the ranked list of one query and its judgments:
   1. `precision_at_k(ranked, rels, k)`: relevant retrieved in the top k / k. Relevant = grade >= 1.
   2. `recall_at_k(ranked, rels, k)`: relevant retrieved in the top k / all relevant judged.
   3. `reciprocal_rank(ranked, rels, k=10)`: 1 / rank of the first relevant within k, else 0.
      Its mean is MRR@10.
   4. `average_precision(ranked, rels)`: mean of precision at the rank of each relevant document,
      divided by all relevant judged (unretrieved relevant count as 0).
   5. `ndcg_at_k(ranked, rels, k=10)`: gain `2**grade - 1`, discount `log2(rank + 1)`, normalised
      by the ideal ordering of the judged grades.
   6. `evaluate(qrels, run, metrics) -> (per_query: dict[qid, dict[metric, float]], mean: dict[metric, float])`.
      Queries without any relevant judgment are skipped; queries missing from the run score 0.
3. `tests/test_metrics.py`: for each metric at least one example computed by hand in a comment
   (e.g. ranked `[a, b, c, d]`, relevant `{b: 1, d: 2}`: P@2 = 0.5, RR = 0.5, AP = (1/2 + 2/4) / 2 = 0.5).
   Include the edge cases: no relevant retrieved, relevant beyond k, empty run.
4. `significance.py`: `paired_randomization_test(scores_a, scores_b, n=10000, seed=42) -> p_value`,
   two-sided, on per-query scores of two configurations over the same queries (randomly swap the
   two scores of each query, count how often the absolute mean difference is at least the
   observed one). Unit test: identical lists give p = 1; a clearly better list gives p < 0.05.
5. Done when `uv run pytest -q` passes.

## Step G2: the `fonti` test set (known-item search)

Idea: each Wikinews article cites external sources with their own headline. That headline,
written by another newspaper about the same event, is a realistic query whose right answer we
already know: the article. Thousands of queries without manual work.

File: `evaluation/build_fonti.py`, output `evaluation/testsets/fonti/queries.tsv` and `qrels.txt`
(committed: they are small).

1. Read `docs.jsonl` (start with the sample, rerun on the full file). For each document, its
   `sources` list gives candidate queries (`sources[i].title`).
2. Drop a candidate if: the title is empty or has fewer than 4 words; the source is foreign
   (`sources[i].foreign`); the title is not in Italian even though the template says nothing
   (some `{{fonte}}` titles are in English, e.g. "Moldova: Direct assignment for Rotterdam"):
   drop titles that contain common English function words (`the`, `of`, `for`, `and`, `with`,
   `to`, `is`) and no Italian ones (`il`, `la`, `di`, `del`, `che`, `per`, `con`, `non`, ...),
   and check the rule by eye on 50 dropped and 50 kept titles; the same normalised title
   (lowercase, punctuation removed) appears for more than one document (ambiguous, e.g.
   "Risultati Serie A"); the document is not `published` (we test news search).
3. Keep **one query per document** (the first valid source), so that articles with many sources
   do not weigh more.
4. `meta` of each query: `{"doc_title": ..., "overlap": ..., "bucket": ...}` where `overlap` is the
   Jaccard similarity between the word sets of query and document title, lowercased, Italian stop
   words removed (use a short fixed list in the script), and `bucket` is `low` (< 0.2), `mid`
   (0.2-0.5) or `high` (> 0.5). Low overlap = paraphrase: that is where semantic search should help.
5. Random sample of **1000 queries** with `random.Random(42)`; ids `F0001`... Print the funnel
   (candidates, after each filter, final) and the bucket sizes: they go on the slides.
6. Leakage check: the contract says `body` does not contain the sources. On 300 random queries
   count how many appear verbatim (normalised) in `title + lead + body`. A simulation on the raw
   dump (16 Nov) found about 4% even before the "Fonti" section, because some articles quote or
   reuse the headline: that is natural overlap, not leakage, and it is fine. A much higher share
   means the parser leaked the sources: write it under "Requests" for Daniel.
7. Expected size (simulation on the raw dump, 16 Nov, before the English-title rule): 17,190
   source templates, 7,318 queries after the filters, buckets low 2,969, mid 3,549, high 800;
   51 queries are identical to the article title. Your numbers should be close.
8. Done when both files exist for the full corpus and the funnel is in the log.

## Step G3: the `manual` test set (judged by us)

The `fonti` set only has one relevant document per query. The `manual` set measures the ranking
of the whole first page, with graded judgments.

1. **Write the 30 queries before looking at any result** (avoid choosing queries the system is
   good at). Four types, 7 or 8 each, mixing years (most news are 2005-2008, some up to 2025) and
   topics (politics, sport, science, disasters, culture):
   1. `topical`: a subject, e.g. "terremoto in Abruzzo";
   2. `entity`: a person, organisation or place, e.g. "Romano Prodi";
   3. `time`: a subject bound to a period, e.g. "elezioni politiche 2008";
   4. `vague`: a paraphrase or description without the key words, e.g. "incidente in una miniera
      di carbone".
   Write them in `evaluation/testsets/manual/queries.tsv` with `meta = {"type": ...}`, and show them to
   the group (Daniel and Fabio can propose changes) before pooling.
2. `evaluation/testsets/manual/GUIDELINES.md`: grade 2 = the article is mainly about what the query
   asks; 1 = it is related or mentions it substantially; 0 = not relevant. Two or three examples
   for each grade. Judge the article, not the snippet.
3. Pooling (`evaluation/pool.py`, needs Fabio's F1 and F4): for every query, the top 10 of the five
   configurations the `manual` set is used for (`bm25-standard`, `bm25-italian`, `knn`,
   `hybrid-rrf`, `hybrid-rrf-published`), merged and deduplicated, shuffled with seed 42 so the
   judge does not know which system found what. Output one assignment file per judge,
   `evaluation/testsets/manual/judging/<name>.tsv` (UTF-8, tab separated) with columns
   `qid, query, doc_id, title, date, lead, url` (committed, so the others get it with `git pull`).
   Assignment: the 30 queries split in three parts of 10; queries 1-10 are also given to a
   second judge, to measure agreement.
   **Do the pooling only after Fabio's F4 is pushed** (otherwise the documents found only by
   `knn` are never judged and the comparison is unfair). If F4 is not there by Tuesday 22:00,
   pool without the vector configurations, and write it in the log as a limit.
4. Workload: expect about 20-25 documents per query after deduplication, so about 300 judgments
   per person. Judge from title and lead, opening the article only when in doubt (about 10
   seconds each): about one hour. `pool.py` must print the judgments per person; if anyone has
   more than 350, cut the doubly judged queries first, then the number of queries, and log it.
   The other configurations (E2, E4) are evaluated on `fonti` only, because their documents are
   not in the pool.
5. Judging tool, `evaluation/judge.py` (no spreadsheets: Excel with Italian settings breaks CSV
   separators and accents). `uv run python -m evaluation.judge --judge <name>` shows one document
   at a time (query, title, date, lead), reads a key (`0`, `1`, `2`; `o` opens the URL in the
   browser with `webbrowser`; `b` goes back; `q` quits) and **appends each grade immediately** to
   `evaluation/testsets/manual/judgments/<name>.tsv`, so it can be stopped and resumed. It prints
   progress (`37/310`). Must work in the macOS terminal and in Windows PowerShell (read a whole
   line with `input()`, do not depend on raw single-key reading).
6. Done when the three assignment files and the tool are pushed and each person has judged two
   documents as a test.

## Step G4: judgments (Wednesday 18 by 13:00)

1. Each person runs the judging tool and pushes their `judgments/<name>.tsv` (each file is
   written by one person only, so no conflicts).
2. `evaluation/merge_judgments.py`: reads the judgment files, computes Cohen's kappa on the
   doubly judged queries (report it: it tells how reliable the judgments are), writes `qrels.txt`.
   Disagreements: the two judges decide together; write in the log how many there were.
3. Documents that enter the ranking after pooling (unjudged) count as not relevant: say this on
   the slides as a limit.

## Step G5: the experiment runner

File: `evaluation/run.py`, `evaluation/experiments.py`. One command, `uv run python -m evaluation.run`,
reproduces every number.

1. For every test set and every configuration in `CONFIGS`: call
   `search(text, config, k=100)` for each query, measure the time of each call, write the run to
   `results/runs/<set>/<config>.txt`.
2. Metrics: `fonti`: MRR@10, R@10, R@100, overall and per `bucket`; `manual`: P@10, nDCG@10, AP
   (MAP), MRR@10. Write `results/metrics/<set>.csv` (one row per configuration) and the
   per-query scores `results/metrics/<set>_per_query.csv` (needed for significance).
3. `experiments.py` lists the comparisons of `PLAN.md` as pairs (baseline, variant):
   E1 `bm25-standard` vs `bm25-italian`; E2 `bm25-italian` vs `bm25-italian-title`,
   `bm25-italian-body`, `bm25-italian-flat` (only on `fonti`); E3 `bm25-italian` vs `knn` vs
   `hybrid-rrf`; E4 `bm25-italian` vs `bm25-italian-leak` (only on `fonti`); E5 `hybrid-rrf` vs
   `hybrid-rrf-published` (only on `manual`). On `manual`, run only the five pooled
   configurations. For each pair: difference of the means and p-value
   of the randomization test, in `results/metrics/significance.csv`.
4. Costs (E6): query latency p50 and p95 per configuration (`results/metrics/latency.csv`);
   indexing time and index size come from Daniel's `results/indexing.csv`.
5. Warm up before timing (run 20 queries and discard them), and run the timing with nothing else
   heavy open.
6. **Official run** (Wednesday, by 20:00): `git pull`, rebuild the data and the indices
   (`python -m wikisearch.ingest.parse`, then `python -m wikisearch.ingest.index`), run
   `python -m evaluation.run`, commit `results/metrics/`, `results/summary.md` and the figures.
   Write in the log the machine used (model, RAM) next to the latencies. Runs (`results/runs/`)
   are not committed.
7. `results/summary.md`: generated tables, one per experiment, with a one-line reading each.
8. Done when one command produces everything above on the full corpus.

## Step G6: figures and reading of the results (Wednesday)

1. `evaluation/figures.py` (matplotlib is already a dependency) writes PNGs into
   `results/figures/`: E3 bars of MRR@10 per bucket (low/mid/high overlap) for BM25, kNN and
   hybrid, the key figure of the presentation; E1/E2 bars with p-values; E6 latency against
   quality (one point per configuration, a trade-off chart).
2. For each experiment write in the log one sentence of conclusion with the numbers: it becomes
   the slide text. A difference that is not significant is a result too: say it ("the Italian
   analyzer does not change MRR in a significant way, p = 0.4").
3. Limits to state honestly on the slides: `fonti` has one relevant document per query; the
   manual pool is judged by us, the authors of the system; unjudged documents count as non
   relevant.

## Slides and README

1. `slides/gioia.md`, in Italian, with the structure in `PLAN.md` ("Slides"), by Wednesday
   22:00: the test strategy (the two test sets, how they were built, the funnel, the metrics,
   significance), the results per experiment with the figures, the limits, the conclusions.
2. The "Usage" subsection of `README.md` for the evaluation (how to rebuild the test sets, how to
   reproduce every number).

## What to write in the log

For every push: what you built, how to run it, the numbers (funnel of the test set, kappa,
metrics), what you noticed in the results, and anything you need from Daniel or Fabio under
"Requests".
