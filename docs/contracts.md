# Contracts

The three parts of the project (ingestion, search, evaluation) are built in parallel by three people.
They meet only at the interfaces below. **Do not change a contract without writing it in the
"Contract changes" section of `STATE.md` and telling the group**: the other two parts depend on it.

## 1. Processed document (`data/processed/docs.jsonl`)

Produced by `wikisearch/ingest` (owner: Daniel). One JSON object per line, one line per page.
A small committed sample lives in `data/sample/docs.sample.jsonl` so the other parts can start
before the full corpus is ready.

| Field | Type | Notes |
|---|---|---|
| `id` | string | MediaWiki page id (`identifier` in the dump), as a string. Unique: duplicated pages are reduced to the most recent version |
| `title` | string | page title (`name`) |
| `url` | string | page URL |
| `date` | string or null | news date, `YYYY-MM-DD`. Taken from the `{{data}}` template, then from the daily category, otherwise null |
| `date_source` | string | `template`, `category` or `none` |
| `lead` | string | first paragraph of plain text, without the date line |
| `body` | string | full plain text of the article **without the "Fonti" section** and without the date line (see "Leakage" below) |
| `categories` | list of strings | topical and geographic categories, prefix `Categoria:` removed. Maintenance categories (e.g. `Pubblicati`, `Articoli archiviati`, `Articoli da controllare per l'archiviazione`) and daily date categories are removed |
| `sources` | list of objects | `{agency, title, url, date, foreign}` from the `{{fonte}}` and `{{fonteestera}}` templates. `agency` is normalized (e.g. `Ansa` -> `ANSA`); `foreign` is true for `{{fonteestera}}` (source in another language) |
| `agencies` | list of strings | the normalized `agency` values, for filtering |
| `entities` | list of strings | titles of the Wikipedia pages linked in the text (`[[w:...]]`) |
| `wikidata_id` | string or null | `main_entity.identifier` |
| `image_url` | string or null | `image.content_url` |
| `published` | bool | true if the page is in `Categoria:Pubblicati`. Non-published pages (tables, specials, drafts) are **kept** and flagged |
| `series_key` | string | title with digits normalized (e.g. `Italia: concorso n. # del SuperEnalotto`), to detect template-generated near-duplicates |
| `n_chars` | int | length of `body` |

**Leakage.** The known-item test set uses the titles of the external sources as queries. Those titles
are written inside the "Fonti" section of each page. If they were searchable, the test would be
trivially easy. So `body` never contains the sources, and `sources` is stored but **not searched**
by default. Searching it is one of the ablations (it shows how much leakage inflates the metrics).

## 2. Elasticsearch indices

Produced by `wikisearch/ingest/index.py` (owner: Daniel).

1. One index per text analysis variant: `wikinews-standard` (standard analyzer) and
   `wikinews-italian` (built-in `italian` analyzer: elision, Italian stop words, light stemmer).
   More variants may be added; their names always start with `wikinews-`.
2. Every index has the same fields as the processed document. Text fields: `title`, `lead`, `body`
   (`text` with the variant's analyzer; `title` also has a `title.keyword` subfield).
   Filter fields: `date` (`date`), `categories`, `agencies`, `series_key` (`keyword`),
   `published` (`boolean`). `sources` is stored (`enabled: false` object) plus a searchable
   `sources_text` field used only by the leakage ablation.
3. Vector field `embedding`: `dense_vector`, 384 dimensions, cosine, HNSW. Model:
   `intfloat/multilingual-e5-small`, text embedded = `"passage: " + title + ". " + lead`.
   The document vectors are computed once and committed in `data/shared/embeddings.npy`
   (float32, rows in the order of `data/shared/embeddings_ids.json`), so every laptop indexes the
   same vectors.
   Queries are embedded as `"query: " + text` with the same model. The model name lives in
   `wikisearch/config.py` (`EMBEDDING_MODEL`): both ingestion and search read it from there.

## 3. Search function (`wikisearch/search`)

Owner: Fabio. Used by both the web app and the evaluation harness, so the web app and the
experiments always measure the same code.

```python
def search(query: str, config: str, k: int = 10, filters: Filters | None = None) -> list[Hit]
```

1. `config` is the name of a configuration in `wikisearch/search/configs.py` (see `CONFIGS`).
   A configuration fixes everything that the experiments compare: index (analyzer), retrieval mode
   (`bm25`, `knn`, `hybrid`), searched fields and their weights, hybrid fusion parameters,
   boosts. Adding a configuration is how a new design choice becomes testable.
2. `Filters` and `Hit` are defined in `wikisearch/schema.py`.
3. The function returns at most `k` hits, best first. It must not apply any default filter
   (the evaluation needs all pages).

## 4. Web API (`wikisearch/web`)

Owner: Fabio. FastAPI on `http://localhost:8000`.

| Endpoint | Returns |
|---|---|
| `GET /api/search?q=&config=&k=&page=&date_from=&date_to=&category=&agency=&published=` | hits with highlighted snippet, total, took (ms) |
| `GET /api/doc/{id}` | the full processed document |
| `GET /api/facets?q=&config=` | top categories, agencies, years for the current query |
| `GET /api/configs` | the list of configuration names, for the UI |
| `GET /` | the web interface |

## 5. Evaluation files (`evaluation/`)

Owner: Gioia. TREC formats, so standard tools can read them too.

1. Queries: `evaluation/testsets/<set>/queries.tsv`, columns `qid<TAB>text<TAB>meta` (meta is JSON,
   e.g. `{"type": "entity", "overlap": 0.21}`).
2. Relevance judgments: `evaluation/testsets/<set>/qrels.txt`, `qid 0 doc_id grade`
   (grade 0, 1, 2; for the known-item set the only relevant document has grade 1).
3. Runs: `results/runs/<set>/<config>.txt`, `qid Q0 doc_id rank score <config>` (not committed:
   large and regenerated by the runner).
4. Metrics: `results/metrics/<set>.csv`, one row per configuration, one column per metric.

Test sets:

1. `fonti`: known-item search. Query = title of an external source of the article, relevant
   document = the article. Built from `docs.jsonl`.
2. `manual`: 30 queries written by the group, judged by the group on the pooled top 10 of the
   five configurations compared in E1, E3 and E5.
