# Live demo script (Fabio)

Five queries, in this order, about four minutes in all. **Fabio speaks, Daniel operates the
laptop** (agreed on 17 Nov, `STATE.md` entry of 14:50, issue #8). Everything is done **through the
interface**: the query typed in the search box, the configuration chosen in the menu, the Compare
toggle, the two date fields, the source checkbox, "Clear filters". This shows that the interface
works, not only prepared URLs. Each step lists Daniel's actions, what Fabio points at, and the
sentence Fabio says; the link at the end of each step opens the same state and is only the
fallback, together with the screenshots in `results/demo/`.

The sentences are in English like the rest of the repository; the Italian wording is on the
slides (`slides/fabio.md`).

## Before class (on Daniel's laptop)

1. Close other heavy apps (8 GB of RAM).
2. Start Elasticsearch: `docker compose up -d`, check with `curl localhost:9200`.
3. Start the web app: `uv run uvicorn wikisearch.web.app:app` (no `--reload`), open
   http://localhost:8000.
4. Warm-up: run one `knn` query (any text, configuration `knn` in the menu). The first vector query
   loads the embedding model (about 19 s on Daniel's Mac, but 78 s on Fabio's laptop right after
   starting Docker: do it at least two minutes before the demo); after that every query answers in
   well under a second. Then click "Wikinews search" (top left) to start from an empty page.
5. Keep this file and `results/demo/` open in another window.

## How the interface reacts (for Daniel)

1. The query runs when you press Enter (or "Search"). Changing a menu, the Compare toggle, a date
   or a checkbox **reruns the search at once**: no need to press Enter again.
2. Filters (dates, sources, categories, "Published only") **stay active when you type a new
   query**. Clear them with "Clear filters" (bottom of the left column) before a step without
   filters.
3. When you tick Compare, a second menu appears to the right of the first one: the left column
   uses the first menu, the right column the second one.
4. The date fields show day, month and year in the order of the browser's language (`gg/mm/aaaa`
   in an Italian browser): click the first part of the field and type all the digits without
   stopping, e.g. `06042009`. **While you type the year the list refreshes at every digit** (years
   0002, 0020, 0200, then 2009): this is normal, keep typing; the right results come with the last
   digit.
5. "N results in X ms" counts the results **of the page** (10 per page, "Next" at the bottom), not
   all the matching documents.

## 1. A topical query, and a page that is not published

Actions (Daniel):
1. Type `terremoto in Abruzzo` in the search box.
2. In the menu next to it choose `hybrid-rrf`, press Enter.
3. After Fabio's first sentence, change the menu to `hybrid-rrf-published`. **Use the menu, not the
   "Published only" checkbox**: the checkbox is a filter and would remove the special page, while
   the configuration only ranks it lower (the boost measured by E5).

Show: the result list (title, date, highlighted snippet, categories, agencies, "N results in X ms"),
the facets on the left (categories, sources). With `hybrid-rrf` the first hit is "Speciale
Terremoto in Abruzzo", marked **not published**: an index page, not a news article. With
`hybrid-rrf-published` the special page leaves the top, the first hit is "Nuova fortissima scossa
di terremoto in Abruzzo".

Say: "We kept the pages that are not published, flagged, instead of dropping them. Ranking them
lower is a configuration, a boost of 1.5 on published pages. Here it helps, but experiment E5
says that on average it does not: on the `manual` queries nDCG@10 drops from 0.804 to 0.758,
because the boost also pushes up published pages that are less relevant. So the default
configuration has no boost."

Fallback: http://localhost:8000/?q=terremoto+in+Abruzzo&config=hybrid-rrf, then
http://localhost:8000/?q=terremoto+in+Abruzzo&config=hybrid-rrf-published

## 2. Filters by date and source

Actions (Daniel):
1. Replace the query with `terremoto`, choose `bm25-italian` in the menu, press Enter.
2. Left column, "Date": "From" 6 April 2009 (`06042009`), then "To" 30 April 2009 (`30042009`).
   The list now shows the Abruzzo earthquake articles.
3. Under "Sources", tick `ANSA` (first in the list): three articles are left, "Polemiche sul
   sisma in Abruzzo", "Sisma in Abruzzo: i funerali", "Sisma dell'Abruzzo: le reazioni".
4. At the end of the step click **"Clear filters"**.

Show: the two date fields and the ANSA checkbox; the three articles ("3 results"; with the dates
alone the page is full and "Next" appears). The counts next to the
checkboxes are those of the whole query, without the filters: the facets are computed once per
query and configuration.

Say: "Filters are Elasticsearch filter clauses: they restrict the set of documents without
changing the scores. The same filters are passed inside the kNN search, so a filtered vector
query still returns k results."

Fallback: http://localhost:8000/?q=terremoto&config=bm25-italian&date_from=2009-04-06&date_to=2009-04-30&agency=ANSA

## 3. Exact names: BM25 wins

Actions (Daniel), after "Clear filters":
1. Type `Pontecorvo`, keep `bm25-italian` in the menu, press Enter.
2. Tick **Compare**; check that the second menu shows `knn` (choose it if not).

Show: compare mode. Left, BM25 finds "Si è spento Gillo Pontecorvo" first. Right, `knn` returns
service pages ("Inserisci nome della voce", "Lua") and "Latina: crolla un ponteggio".

Say: "A rare proper name is a single token for BM25 and matches exactly. The embedding model
splits it into sub-words and places it near words that look alike, ponte, ponteggio: vectors
are weak on names they have never seen."

Fallback: http://localhost:8000/?q=Pontecorvo&config=bm25-italian&compare=1&config2=knn

## 4. A paraphrase: kNN wins

Actions (Daniel), Compare still on with `bm25-italian` and `knn`:
1. Type `il pontefice è deceduto`, press Enter.
2. After Fabio's first sentence: in the **second** menu choose `hybrid-rrf`, then in the **first**
   menu choose `knn` (in this order, so the two columns never show the same configuration).

Show: with `bm25-italian` against `knn`, left BM25 returns people who "died" (deceduto) but no
pope; right, `knn` puts "Il papa emerito Benedetto XVI è morto" first. That article never says
"pontefice" (it says "papa") and has "deceduto" only once in the text, so BM25 ranks it 78th.
Then with `knn` against `hybrid-rrf`: the hybrid finds "Giovanni Paolo II è morto" at rank 4 and
Benedetto XVI at rank 6.

Say: "The vectors capture the meaning: pontefice is papa, deceduto is morto. Hybrid search
fuses the two rankings with reciprocal rank fusion, which uses only the ranks, because BM25
and cosine scores are on different scales. It is a compromise: it is never the worst, but it is
not always the best, and the evaluation says which is better on average."

Fallback: http://localhost:8000/?q=il+pontefice+%C3%A8+deceduto&config=bm25-italian&compare=1&config2=knn,
then http://localhost:8000/?q=il+pontefice+%C3%A8+deceduto&config=knn&compare=1&config2=hybrid-rrf

## 5. Near-duplicates

Actions (Daniel):
1. Untick **Compare**; choose `bm25-italian` in the menu.
2. Type `concorso superenalotto`, press Enter.

Show: 9 of the top 10 are lottery draw pages that differ only by number and date ("Italia:
concorso n. 134/2007 del SuperEnalotto", "135/2007", ...).

Say: "About 2,300 pages are generated from templates: lottery draws, match reports. They crowd
the result page. Collapsing them by series is the stretch experiment E7."

Fallback: http://localhost:8000/?q=concorso+superenalotto&config=bm25-italian

## Screenshots (fallback)

Taken on 16 Nov 2026 on Fabio's laptop (full indices, shared embeddings), one per fallback link
above, in `results/demo/`: `1a-topical-hybrid.png`, `1b-topical-published-boost.png`,
`2-filters-date-agency.png`, `3-exact-name-bm25-vs-knn.png`, `4a-paraphrase-bm25-vs-knn.png`,
`4b-paraphrase-knn-vs-hybrid.png`, `5-near-duplicates.png`, `6-spare-rare-word-bm25-vs-knn.png`.
The indices and the embeddings are the same on every laptop, so the live results on Daniel's
laptop must match them; if one differs, the indices there are out of date. The links were
checked on Daniel's laptop on 16 Nov 18:10 and 17 Nov (issue #8). Every interface action of this
file was run once on Fabio's laptop on 17 Nov (browser in Italian, date fields `gg/mm/aaaa`):
same results as the links.

## Spare query, if asked whether vectors always win

Actions (Daniel): type `rincaro del greggio`, choose `bm25-italian` in the menu, press Enter;
tick Compare and check that the second menu shows `knn` (choose it if not).

BM25 finds the oil price articles from rank 4 ("Nuovo record per il prezzo della benzina", "il
petrolio sfonda quota 100 dollari"); `knn` starts with unrelated pages ("Vezzano Ligure: riaperta
la Ripa", "Scade il copyright su Braccio di Ferro") and has its first oil article only at rank 5.
A rare word (greggio) is not understood well by a small multilingual model.

Fallback: http://localhost:8000/?q=rincaro+del+greggio&config=bm25-italian&compare=1&config2=knn
