# Brief: Daniel, data and indexing

You are helping **Daniel Sadun** (GitHub `dnlsdn`). Daniel owns the data pipeline and the indices:
`wikisearch/ingest/` and `docker-compose.yml`. He presents the data challenges and the indexing
choices, and assembles the deck. Read `CLAUDE.md`, `STATE.md`, `PLAN.md` and `docs/contracts.md`
before this file. Daniel's Mac has 8 GB of RAM and little free disk: check `df -h ~` before large
downloads and never run the embedding job while other heavy processes run.

His work is the bottleneck of the first day: Fabio and Gioia wait for the sample (D2) and the
indices (D3). Push those first, polish later.

## Step D1: Elasticsearch

1. `docker compose up -d` (image `elasticsearch:9.5.0`, about 1.5 GB, pulled once).
2. Done when `curl localhost:9200` answers and the README "Setup" section is verified.

## Step D2: parser (`wikisearch/ingest/parse.py`)

Input `RAW_DUMP`, output `DOCS_JSONL` and the sample `SAMPLE_JSONL` (paths in `wikisearch/config.py`).
Fields exactly as in `docs/contracts.md` section 1.

1. Read the NDJSON line by line (591 MB: never load the whole file in memory at once).
2. Duplicates: same `identifier` -> keep the record with the latest `date_modified`.
3. Plain text from `article_body.html` (Parsoid HTML) with an HTML parser (`selectolax` or `lxml`,
   add it with `uv add`): take the paragraphs and lists of the sections, drop the section whose
   heading is "Fonti" (and "Collegamenti esterni", "Note"), figures, navigation boxes, tables of
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
   in a sidecar `embeddings_ids.json` to check the order.
2. Measure the time; then rerun D3 so the vectors are indexed.
3. Done when a `knn` query on `embedding` returns sensible neighbours for two or three test
   articles (write them in the log).

## Step D5: leakage field and extra variants

1. `sources_text` (titles of the sources joined) indexed as `text` with the variant's analyzer,
   used only by `bm25-italian-leak`.
2. Optional, only if time allows: a third analyzer variant (e.g. `italian` plus `asciifolding`
   for accents) as `wikinews-italian-folding`, added to `ANALYZER_VARIANTS` with a "Contract
   changes" entry.

## Step D6: data report (Wednesday)

`results/data_report.md`: the challenges of the data with numbers and one real example each
(date hidden in a template, maintenance categories, inconsistent agency names, near-duplicate
series, non-published pages, leakage of the sources). It is the base of Daniel's slides.

## Step D7: slides

Italian, sober style (not "AI style"), no code on the slides. Daniel's part: the data and its
challenges, the indexing choices. Then assemble the deck from the parts of Fabio and Gioia.
