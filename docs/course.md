# What the course expects

The project is graded at the oral exam of Ingegneria dei Dati (prof. Paolo Merialdo, Roma Tre). This
file summarises, in our own words, what the course teaches and asks that matters for this
homework, with references to the course material. **The slides themselves are not in the
repository** (they belong to the professor and this repository becomes public): every member has
them; to let your Claude read the originals, copy them into `course/` (ignored by git).

Use this file to keep the work aligned with the course: use the course's terms and methods, and
when a choice departs from them, say why.

## 1. The assignment (slides "Homework 4", lecture of 6 Nov 2026)

1. A search system with a web interface over the Italian Wikinews dump, with Elasticsearch or
   Lucene. The kind of queries to offer is up to us: "a lot of creativity" is welcome.
2. A test strategy: which datasets and which metrics. The design alternatives must be compared
   with each other, like an **ablation study**, showing that a choice brings a real advantage or
   that there is a **trade-off** (one is better for one goal, the other for another).
3. Code and install instructions on GitHub.
4. A presentation of about 20 minutes: technical and methodological challenges; the solutions,
   **without code** ("we are raising the level"; it is taken for granted that you master your
   code); the test strategy; the experimental results and how they support the design choices;
   a **live demo**.
5. LLMs are allowed and recommended, as long as we keep control of all the code they produce.

## 2. What the professor values (lectures of 16 Oct and 6 Nov, mail of 12 Nov)

1. **The experimental evaluation comes first.** At the exam he starts from the delivered material
   and asks above all about the experimental part, and before that whether we understood the
   problem.
2. **Statistical robustness.** He insists that many published results are fragile: a single run,
   fixed seeds, comparisons never tested statistically, even bugs in the code that computes the
   metrics, and "improvements" over a random baseline that vanish under a proper analysis. So:
   1. test metric code on hand-computed examples;
   2. include trivial baselines (a random ranking) as a floor that shows the pipeline works;
   3. report significance (paired randomization test) and confidence intervals, not only means;
   4. when something depends on a random choice (e.g. which queries are sampled), repeat it with
      different seeds or use all the data.
3. **Reproducibility**: anyone must be able to rerun the experiments and get the same numbers
   (one command, fixed seeds, data construction documented).
4. **Critical spirit**: state the limits of our own evaluation openly; it is appreciated, not
   penalised.
5. From his mail on homework 3 reports: test on **many documents**; explain **how the test
   dataset was built**; use **evaluation metrics**, paying attention to **recall**; put the
   authors' **email addresses** in the delivered material.

## 3. Evaluation of a search system (slides id-02, 173-189, from Manning, Raghavan, Schütze)

1. A benchmark has three elements: a document collection, a suite of queries, relevance
   judgments for query-document pairs (174-175).
2. Judgments can be binary or graded (0, 1, 2, ...). Judging everything is impossible at scale
   (176): hence pooling, which we use for the `manual` set.
3. Test queries must be representative of real information needs; **random terms taken from the
   documents are not a good idea** (178). Our `fonti` queries are headlines written by other
   newspapers, not terms sampled from the article: say so when presenting them.
4. **Relevance is judged against the information need, not against the words of the query**
   (181, the "pool cleaner" example). Every `manual` query therefore comes with a one-sentence
   information need, and the judges use that.
5. Unranked: precision and recall (182). Ranked, binary: P@K, R@K, MAP, MRR; graded: NDCG (183).
6. MAP: average of the precision at the rank of each relevant document; a relevant document
   never retrieved contributes zero; macro-average over queries; it assumes users want many
   relevant documents and needs many judgments (186-189). MRR fits known-item search (one right
   answer), like our `fonti` set.

## 4. Text analysis and ranking (slides id-02 41-67 and 129-171; Lucene slides 20-31, 46-49)

1. Tokenisation, stop words, normalisation (case folding, accents), stemming and lemmatisation
   depend on the language; documents and queries must go through the same analysis.
2. Analyzers are a tokenizer plus a chain of token filters; one analyzer per field is possible.
3. Phrase queries need positional information.
4. Ranking: tf-idf and the vector space model in the theory slides; BM25 is the default
   similarity of Lucene and Elasticsearch.

## 5. Elasticsearch (Lucene and Elasticsearch slides, 50-80)

1. Elasticsearch is a distributed engine built on Lucene: an index is split into shards, each a
   Lucene index made of segments; replicas for availability. We run one node, one shard.
2. Mapping types: `text` (analysed, full text), `keyword` (exact values, filters, aggregations),
   `date`, numbers, `boolean`, `nested`, `dense_vector`.
3. Bulk indexing; refresh makes new documents visible (like Lucene's commit).
4. Query families: `match_all`, `match`, `multi_match`, `match_phrase`, `bool` with `range`
   filters, `knn`.
5. Vector search: `knn` needs a `dense_vector` field; `num_candidates` must exceed `k`, and more
   candidates cost more but find more. `index_options` choose the structure: `flat` (brute
   force), `int8_flat`, `hnsw`, `int8_hnsw`, `bbq_hnsw` (binary quantization), `bbq_disk`. HNSW
   and quantization trade quality for speed and memory: a natural experiment (E8 in `PLAN.md`).
6. Course lab: https://github.com/tteofili/lucenex, folder `es/` (notebook and docker compose
   for Elasticsearch 9.5.0, the version we use).

## 6. Presentations (experience of homework 1 and 2)

1. Sober slides: a label and one line, figures and tables carry the content; no "AI style"
   decks; names only on the cover, in alphabetical order by surname.
2. Each speaker presents their own part; no transition sentences between speakers.
3. The discussion in class is not graded; the exam is.
