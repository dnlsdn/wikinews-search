# Brief: Daniel, data and indexing

You are helping **Daniel Sadun** (GitHub `dnlsdn`). Daniel owns the data pipeline and the indices:
`wikisearch/ingest/` and `docker-compose.yml`. He presents the data challenges and the indexing
choices, and assembles the deck. Read `CLAUDE.md`, `STATE.md`, `PLAN.md` and `docs/contracts.md`
before this file. Daniel's Mac has 8 GB of RAM and little free disk: check `df -h ~` before large
downloads and never run the embedding job while other heavy processes run.

His work is the bottleneck of the first day: Fabio and Gioia wait for the sample (D2, by Monday
15:00) and the indices (D3, by 19:00). Push those first, polish later. Embeddings (D4) Monday
night, so Fabio can do the vector search on Tuesday morning.

## Beyond the code: the whole project, up to the presentation (asked by Daniel, 16 Nov)

Daniel assembles the deck and presents first: follow the whole process, not only his steps.
At every session, besides the next step:

1. Look at the team as a whole: compare everyone's progress with the timeline in `PLAN.md`,
   and tell Daniel early about anything late or missing that the presentation needs (queries,
   judgments, official run, figures, slide files), with a concrete proposal.
2. Keep the story of the presentation coherent: every design choice on Daniel's slides should be
   backed by a number from the experiments, and every experiment should answer a question the
   slides raise. Point out gaps and contradictions between the three slide files.
3. Prepare Daniel for the oral: after each step, the two or three points he must be able to
   explain; once the official results are out, go through E1, E3, E4 (and E8) with him, since
   they test his choices, and the limits to state openly (`docs/course.md`, section 2).
4. Care for the delivery as much as for the code: sober slides with figures and tables, the demo
   rehearsed on Daniel's laptop, README verified from a fresh clone, repository public, names on
   the cover.

## Step D1: Elasticsearch

1. `docker compose up -d` (image `elasticsearch:9.5.0`, about 1.5 GB, pulled once; the image
   exists for arm64 and amd64). Docker Desktop must give its VM at least 3 GB of memory
   (Settings, Resources), since the container is limited to 2 GB. On Daniel's Mac `DOCKER_HOST`
   is set in `~/.zshrc` for Kathara: check that `docker info` talks to Docker Desktop.
2. Done when `curl localhost:9200` answers and the README "Setup" section is verified.

## Step D2: parser (`wikisearch/ingest/parse.py`)

Input `RAW_DUMP`, output `DOCS_JSONL` and the sample `SAMPLE_JSONL` (paths in `wikisearch/config.py`).
Fields exactly as in `docs/contracts.md` section 1.

1. Read the NDJSON line by line (591 MB: never load the whole file in memory at once).
2. Duplicates: same `identifier` -> keep the record with the latest `date_modified`.
3. Plain text from `article_body.html` (Parsoid HTML) with `selectolax` (already a dependency):
   take the paragraphs and lists of the sections, drop the section whose
   heading is "Fonti" or "Fonte" (and "Collegamenti esterni", "Note"; about 1% of pages have no
   "Fonti" heading, check what they use), figures, navigation boxes, tables of
   templates (`{{Dì la tua}}`, `{{Wikinotizie}}` boxes), the first line with the date. Keep the
   text of links. `lead` = first non-empty paragraph after the date.
4. Date: parse `{{data|21 marzo 2008|venerdì}}` from the wikitext (Italian month names), else the
   daily category (`Categoria:21 marzo 2008`), else null; set `date_source`.
5. Categories: drop maintenance categories (list them explicitly: `Pubblicati`,
   `Articoli archiviati`, `Articoli da controllare per l'archiviazione`, `Articoli da archiviare`,
   `Articoli da non elencare`, `Notizie da prima pagina`, the `Articoli con box ...` and
   `Box ...` ones, `Da cancellare subito`, ...) and daily date categories. Remove the `Categoria:`
   prefix.
6. Sources: parse every `{{fonte|...}}` and `{{fonteestera|...}}` from the wikitext into
   `{agency, title, url, date, foreign}`; `foreign = true` for `fonteestera`. Normalise agencies
   with a small mapping table (case, `la Repubblica`/`La Repubblica`, `ANSA`/`Ansa`, `Gazzetta dello
   Sport`/`La Gazzetta dello Sport`) and fill `agencies`. Keep `sources_text` out of `body`.
7. Entities: targets of `[[w:...]]` links in the wikitext, deduplicated.
8. `published`, `series_key` (title with every digit run replaced by `#`), `n_chars`,
   `wikidata_id`, `image_url`.
9. Print a coverage report: pages read, duplicates removed, published, with date per
   `date_source`, with sources, with at least one category, empty body. Save it to
   `results/parse_report.json`.
10. Sample: 300 documents chosen with `random.Random(42)`, stratified so it contains news from
    several years, sport tables, lottery pages, specials and non-published pages. Commit it.
11. Tests (`tests/test_parse.py`) on two or three real records copied as fixtures: date
    extraction, sources and foreign flag, "Fonti" not in `body`.
12. Done when the full `docs.jsonl` is built, the report numbers are plausible against
    `STATE.md` ("What we know about the dump"), and the sample is pushed.

## Step D3: indexer (`wikisearch/ingest/index.py`)

1. For each analyzer in `ANALYZER_VARIANTS`, delete and create `index_name(analyzer)` with the
   mapping of `docs/contracts.md` section 2: 1 shard, 0 replicas (single node).
2. Bulk-load with `elasticsearch.helpers.bulk` in chunks of 500, `refresh_interval: -1` during the
   load, then restore it and refresh.
3. `--input` (default `DOCS_JSONL`), `--analyzers` (default all), `--no-embeddings`
   (default: load embeddings if `EMBEDDINGS_NPY` exists, in the same order as `docs.jsonl`).
4. Measure and append to `results/indexing.csv`: analyzer, documents, seconds, index size in bytes
   (`_stats/store`), with or without embeddings. Run each configuration three times and keep all
   rows (as in homework 3, timings vary with the state of the machine).
5. Done when both indices hold every document and `count` matches the parser report.

## Step D4: embeddings (`wikisearch/ingest/embed.py`)

1. `SentenceTransformer(EMBEDDING_MODEL)`, text `PASSAGE_PREFIX + title + ". " + lead`,
   `normalize_embeddings=True`, batch size 32, saved as float32 to `EMBEDDINGS_NPY` with the ids
   in `EMBEDDINGS_IDS` (both in `data/shared/`, **committed**: about 17 MB, so Fabio and Gioia
   do not compute them). The indexer matches vectors to documents by id, not by position, and
   fails loudly if an id is missing.
2. Measure the time; then rerun D3 so the vectors are indexed.
3. Done when a `knn` query on `embedding` returns sensible neighbours for two or three test
   articles (write them in the log).

## Step D5: leakage field and extra variants

Note for D3/D4: set `index_options: {"type": "hnsw"}` on `embedding` explicitly (contract
section 2), otherwise Elasticsearch may choose a quantized structure by default.


1. `sources_text` (titles of the sources joined) indexed as `text` with the variant's analyzer,
   used only by `bm25-italian-leak`.
2. Stretch E8, only if time allows: the same vectors indexed with `int8_hnsw` and `bbq_hnsw`
   in extra indices (e.g. `wikinews-italian-int8`), with sizes in `results/indexing.csv`; open an
   issue to Fabio and Gioia to add the matching `knn` configurations.
3. Optional, only if time allows: a third analyzer variant (e.g. `italian` plus `asciifolding`
   for accents) as `wikinews-italian-folding`, added to `ANALYZER_VARIANTS` with a "Contract
   changes" entry.

## Step D6: data report (Tuesday afternoon)

`results/data_report.md`: the challenges of the data with numbers and one real example each
(date hidden in a template, maintenance categories, inconsistent agency names, near-duplicate
series, non-published pages, leakage of the sources). It is the base of Daniel's slides.

## Step D7: slides, README, publication

1. `slides/daniel.md` by Tuesday 22:00 (structure in `PLAN.md`, "Slides"): the data and its
   challenges, the indexing choices.
2. Wednesday morning (deck ready by 11:00, upload by 14:00): build the deck from `slides/daniel.md`, `fabio.md`, `gioia.md`. Italian,
   sober style (not "AI style"), no code. Cover with the three names and the repository link (no
   emails, decided by Daniel on 17 Nov). Only the pptx is uploaded (no PDF).
3. README: setup verified from a fresh clone, "Usage" sections of the three parts merged.
4. Make the repository public (`gh repo edit dnlsdn/wikinews-search --visibility public --accept-visibility-change-consequences`)
   before uploading the presentation, then check the link from a private browser window.
5. The demo and the presentation run on Daniel's laptop: Elasticsearch and the web app started
   and warmed up before class.
