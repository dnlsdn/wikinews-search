# Live demo script (Fabio)

Five queries, in this order, about four minutes in all. Each step has a link that opens the web
app in the exact state to show (the query, the configurations and the filters are in the URL),
what to point at, and the sentence to say. The demo runs on Daniel's laptop; screenshots of every
step are in `results/demo/` as a fallback if the live demo fails.

The sentences are in English like the rest of the repository; the Italian wording is on the
slides (`slides/fabio.md`).

## Before class (on Daniel's laptop)

1. Close other heavy apps (8 GB of RAM).
2. Start Elasticsearch: `docker compose up -d`, check with `curl localhost:9200`.
3. Start the web app: `uv run uvicorn wikisearch.web.app:app` (no `--reload`), open
   http://localhost:8000.
4. **Open every link below once.** The first vector query loads the embedding model (about 23 s
   on Fabio's laptop); after that every query answers in well under a second.
5. Keep this file and `results/demo/` open in another window.

## 1. A topical query, and a page that is not published

http://localhost:8000/?q=terremoto+in+Abruzzo&config=hybrid-rrf

Show: the result list (title, date, highlighted snippet, categories, agencies, "N results in X ms"),
the facets on the left (categories, agencies, years). The first hit is "Speciale Terremoto in
Abruzzo", marked **not published**: an index page, not a news article.

Then switch the configuration to `hybrid-rrf-published`
(http://localhost:8000/?q=terremoto+in+Abruzzo&config=hybrid-rrf-published): the special page
leaves the top, the first hit is "Nuova fortissima scossa di terremoto in Abruzzo".

Say: "We kept the 1,195 pages that are not published, flagged, instead of dropping them. Ranking
them lower is a configuration, a boost of 1.5 on published pages, and experiment E5 measures
whether it helps."

## 2. Filters by date and agency

http://localhost:8000/?q=terremoto&config=bm25-italian&date_from=2009-04-06&date_to=2009-04-30&agency=ANSA

Show: the two date inputs and the ANSA checkbox; three articles left, among them "Sisma in
Abruzzo: i funerali". Uncheck ANSA to show how many there were.

Say: "Filters are Elasticsearch filter clauses: they restrict the set of documents without
changing the scores. The same filters are passed inside the kNN search, so a filtered vector
query still returns k results."

## 3. Exact names: BM25 wins

http://localhost:8000/?q=Pontecorvo&config=bm25-italian&compare=1&config2=knn

Show: compare mode. Left, BM25 finds "Si è spento Gillo Pontecorvo" first. Right, `knn` returns
service pages ("Inserisci nome della voce", "Lua") and "Latina: crolla un ponteggio".

Say: "A rare proper name is a single token for BM25 and matches exactly. The embedding model
splits it into sub-words and places it near words that look alike, ponte, ponteggio: vectors
are weak on names they have never seen."

## 4. A paraphrase: kNN wins

http://localhost:8000/?q=il+pontefice+%C3%A8+deceduto&config=bm25-italian&compare=1&config2=knn

Show: left, BM25 returns people who "died" (deceduto) but no pope. Right, `knn` puts "Il papa
emerito Benedetto XVI è morto" first. That article never says "pontefice" (it says "papa") and
has "deceduto" only once in the text, so BM25 ranks it 78th.

Then compare with the hybrid
(http://localhost:8000/?q=il+pontefice+%C3%A8+deceduto&config=knn&compare=1&config2=hybrid-rrf):
`hybrid-rrf` finds "Giovanni Paolo II è morto" at rank 4 and Benedetto XVI at rank 6.

Say: "The vectors capture the meaning: pontefice is papa, deceduto is morto. Hybrid search
fuses the two rankings with reciprocal rank fusion, which uses only the ranks, because BM25
and cosine scores are on different scales. It is a compromise: it is never the worst, but it is
not always the best, and the evaluation says which is better on average."

## 5. Near-duplicates

http://localhost:8000/?q=concorso+superenalotto&config=bm25-italian

Show: 9 of the top 10 are lottery draw pages that differ only by number and date ("Italia:
concorso n. 134/2007 del SuperEnalotto", "135/2007", ...).

Say: "About 2,300 pages are generated from templates: lottery draws, match reports. They crowd
the result page. Collapsing them by series is the stretch experiment E7."

## Screenshots (fallback)

Taken on 16 Nov 2026 on Fabio's laptop (full indices, shared embeddings), one per link above, in
`results/demo/`: `1a-topical-hybrid.png`, `1b-topical-published-boost.png`,
`2-filters-date-agency.png`, `3-exact-name-bm25-vs-knn.png`, `4a-paraphrase-bm25-vs-knn.png`,
`4b-paraphrase-knn-vs-hybrid.png`, `5-near-duplicates.png`, `6-spare-rare-word-bm25-vs-knn.png`.
The indices and the embeddings are the same on every laptop, so the live results on Daniel's
laptop must match them; if one differs, the indices there are out of date.

## Spare query, if asked whether vectors always win

http://localhost:8000/?q=rincaro+del+greggio&config=bm25-italian&compare=1&config2=knn

BM25 and the hybrid find the oil price records ("il petrolio sfonda quota 100 dollari"); `knn`
returns unrelated pages ("Vezzano Ligure: riaperta la Ripa"). A rare word (greggio) is not
understood by a small multilingual model.
