# State

Shared memory of the project. Read it before starting, update it before every push
(rules in `CLAUDE.md`). Newest log entry first.

## Current state

| Part | Owner | State |
|---|---|---|
| Repository, plan, contracts, skeleton | Daniel | done (16 Nov) |
| Data and indexing | Daniel | D1-D4 and D6 done (16 Nov 14:50), D7 slide draft in `slides/daniel.md` (15:05), D5 done (15:45: E8 indices `int8`/`bbq` built, measurement waits for Fabio's configurations and Gioia's runner; no asciifolding variant); queries approved (#9); judgments pushed (17 Nov 14:25: M01-M05 by Daniel, M11-M20 by Claude, see log); blind third-judge grades of the 49 M01-M10 disagreements posted in #13 and #15 (17:05); delivery decided (17:22): pptx only, cover with names and repository link, no emails; final official numbers on `slides/daniel.md` (17:45); consistency check of the three slide files done and first deck draft pushed (18 Nov 09:55); deck redone in the homework 2 style (18 Nov 10:17), decisions on repeated results in #17 (Fabio) and #18 (Gioia); Daniel's speech written (18 Nov 10:22, 5:55 min): notes of `slides/daniel.md` and `slides/discorso-daniel.md`; README final (18 Nov 10:29), setup checked from a fresh clone end to end (10:49); public demo online (18 Nov); deck regenerated with Fabio's #20 changes (18 Nov 16:20); demo GIF in the README (17:35); next: rehearsal; last, just before the upload of the pptx: clean the repository of the tooling files, make it public, upload |
| Search and interface | Fabio | F1-F4 done (16 Nov 16:30); E8 configurations `knn-int8`, `knn-bbq` (16:35, issue #6); F5 work in progress (16:55): `docs/demo.md` and `results/demo/` pushed, rehearsal on Daniel's laptop missing (issue #8); F6 in progress (17:05): README usage done, slide outline decided, `slides/fabio.md` written after the official run (Tue 20:00-22:00); G4 judgments pushed (17 Nov 16:50: M06-M10 by Fabio, M21-M30 by Claude, see log); F5 done (17 Nov 17:35): `docs/demo.md` rewritten as interface actions and checked live; F6 in progress (18:10): `slides/fabio.md` written with the official numbers, Fabio's review before ticking; #17 applied (18 Nov 11:58: RRF diagram on slide 3, latency wording); F6 done (18 Nov 12:05): notes of slides 1-4 cut to about 2:37, F6 ticked; restyle of PR #19 confirmed (#14); next: demo rehearsal on Daniel's laptop |
| Evaluation | Gioia | G1 done (16 Nov 12:30): metrics, TREC files, significance tested; G2 done (16 Nov 15:45), language rule fixed (22:03): `fonti` test set, 7,072 queries; G3 done (ticked 17 Nov 17:05): queries, guidelines, tool and pool done, judging files pushed; queries approved unchanged by Daniel and Fabio (issue #9 closed); G4: all three judgment files merged (17 Nov 17:05), kappa 0.543; 49 disagreements adjudicated blind by Daniel's session (#13, #15), `qrels.txt` final (17:10); G4 ticked; G5 done (17 Nov 17:30): final official run on `fonti` and `manual`, `results/metrics/` and `results/summary.md` pushed, G5 ticked; G6 in progress (17 Nov 17:35): four figures in `results/figures/`, `manual` on M01-M10 in `results/metrics/manual_human*.csv`, reading per experiment in the log; `slides/gioia.md` written (18 Nov 09:30); #18 applied (10:30: who graded `manual`, same wording on slides 1, 3, 8); G6 done (10:36): notes reviewed and cut to about 5:45, G6 ticked; questions for the oral in `slides/domande-gioia.md` (10:38); Gioia's speech in `slides/discorso-gioia.md` (18 Nov 12:16, 5:44 min, same text as the notes); next: rehearsal |

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

### 18 Nov 2026 17:35, Daniel: demo GIF in the README

Added `docs/images/demo.gif` (21 s, 960 px, 2.1 MB, blank first frames trimmed at 17:40) under the online demo link of the README,
so whoever opens the repository sees the interface working without starting anything (and still
sees it when the Azure demo is switched off). It was recorded on the public demo with a headless
browser and shows three steps of `docs/demo.md`: `terremoto in Abruzzo` with `hybrid-rrf`, then
Compare `bm25-italian` against `knn` on `Pontecorvo` and on `il pontefice è deceduto`. Not in the
plan: decided by Daniel. Nothing changes for the others; the recording script is not committed
(tooling). Next: rehearsal, then the steps of Daniel's row.

### 18 Nov 2026 17:26, Fabio: facets on slide 4 are categories and sources only (#20)

`slides/fabio.md` (slide 4 = deck slide 12, subtitle and speaker notes), `slides/discorso-fabio.md`
and `slides/domande-fabio.md`: "le faccette contano per categoria, fonte e anno" becomes "per
categoria e fonte". Reason: `/api/facets` also computes a year histogram, but the interface shows
only the category and source facets (the dates are a range filter, "Da"/"A", with no counts), so
the slide now says what the screenshot shows. Decided by Fabio. Nothing to run, nothing changes
for the others; Daniel regenerates the deck together with the 17:14 changes.

### 18 Nov 2026 17:14, Fabio: two lines removed from his slides 1 and 5 (#20)

`slides/fabio.md` only, to be picked up at the next deck regeneration (Daniel, #20); nothing to
run, nothing changes for the others. Fabio asked:
1. **Slide 1 (deck slide 9)**: the subtitle ends at "una configurazione con un nome"; the words
   ", cioè una manopola dell'ablazione" are removed.
2. **Slide 5 (deck slide 13, Demo)**: no sentence under the title ("Cinque query dal vivo sul
   portatile di Daniel." removed) and no caption at the bottom ("Dal vivo sul portatile;
   screenshot di riserva in results/demo/" removed); the list of the five queries stays as it is.
Speaker notes, numbers and every other slide unchanged. Next: Daniel regenerates; Fabio
checks deck slides 9-13 against `slides/discorso-fabio.md`.

### 18 Nov 2026 16:20, Daniel: deck regenerated with Fabio's #20 changes (D7)

`slides/wikinews-search.pptx` regenerated from the current `.md` files (Fabio's commit 3974fbf);
the uploaded copy (no notes) and its PDF regenerated with it, in Daniel's notes folder. Changes,
the layout of slide 12 approved by Daniel:
1. **Slide 10 (E2)**: the bar chart labels use Fabio's notation too ("3x titolo + 2x lead + 1x
   corpo", "1x titolo + 1x lead + 1x corpo"), not "3-2-1 (nostra)" and "pesi uguali".
2. **Slide 9**: `results/demo/slide-compare-zoom.png`, in the same frame as before.
3. **Slide 12 (E5)**: `results/demo/slide-filters-zoom.png` at full slide width under the title
   (8.1 inches wide, was 4.5), as Fabio asked. To make room, the E5 table and the three text
   blocks (Filtri, Faccette, Spinta x 1,5) are gone: the subtitle already says what filters and
   facets do, and the E5 numbers are one line under the figure ("nDCG@10 su manual da 0,804 a
   0,758 (p 0,029): peggiora, non è nel default"), read from the table of `slides/fabio.md`.
No other slide changed, no number changed (all 22 slides checked visually). For the record on
#20 point 3: the repository copy **does** carry the speaker notes (as decided at 10:56); only the
uploaded copy has none.

No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running). #20 answered. Next:
rehearsal; last, just before the upload: clean the repository of the tooling files, make it
public, upload.

### 18 Nov 2026 14:40, Fabio: weights notation and zoomed screenshots on Fabio's slides

Decided by Fabio, after looking at the deck (commit 457e863); changes in `slides/fabio.md` and
`results/demo/` only, as #20 asks:
1. **Deck slide 10 (Fabio's slide 2, E2)**: the weights are written so that a listener reads
   them at once: "3x titolo + 2x lead + 1x corpo (la nostra)" instead of "titolo^3 + lead^2 +
   corpo", and "1x titolo + 1x lead + 1x corpo (pesi uguali)" instead of "pesi uguali". Numbers
   unchanged.
2. **Deck slides 9 and 12 (Fabio's slides 1 and 4)**: the screenshots were unreadable when
   projected (the whole page shrunk into half a slide). New zoomed crops of the restyled
   screenshots, same pixels, no retake: `results/demo/slide-compare-zoom.png` (the two compare
   columns of "Pontecorvo", `bm25-italian` against `knn`, about 1.9 times larger) and
   `results/demo/slide-filters-zoom.png` (a montage: the "Date" and "Sources" filter blocks of
   the left column, the category list between them left out, next to the three results). The
   `Figura:` lines point to them. The demo fallback screenshots (`1a` ... `6`) are unchanged.
The second crop is wide (1166 x 454): in the current half-slide frame it gains only about 1.2
times; asked Daniel in #20 to place it at full width under the title.
Also asked in #20, by Fabio: remove the speaker notes from the repository copy of the deck too
(the uploaded copy already has none). Daniel decides.

No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running). For Daniel:
regenerate the deck. Next: demo rehearsal.

### 18 Nov 2026 13:31, Daniel: rule for slide changes until the delivery (D7)

Decided by Daniel, issue #20 for Fabio and Gioia: the deck is generated from `slides/<name>.md`
and regenerated at every change, so nobody edits `slides/wikinews-search.pptx` directly (an edit
there is lost at the next regeneration, and a binary file cannot be merged). Text, tables and
notes: change your own `.md` file and tell Daniel; layout or drawing changes: describe them in an
issue for Daniel. Never commit a modified pptx.

### 18 Nov 2026 13:11, Daniel: public demo online, deck regenerated with Fabio's and Gioia's notes (D7)

**Public demo** at https://wikinews-search.denmarkeast.cloudapp.azure.com (link at the top of the
README). Decided by Daniel; files in `deploy/` and `.dockerignore`, no change to the code, the
configurations or the numbers.
1. Where: an Azure virtual machine on Daniel's Azure for Students credit (no credit card),
   Standard_B2als_v2 (2 vCPU, 4 GB, x86) with 2 GB of swap, Ubuntu 24.04, Denmark East. About 40
   dollars a month of credit: online until about February, then switched off, nothing charged.
   Tried and dropped: Hugging Face Spaces (Docker Spaces now need a paid plan), Oracle Cloud
   Always Free (no Ampere capacity in Turin; Pay As You Go needed a 93 euro card authorization).
2. How: `deploy/Dockerfile` builds one image with Elasticsearch 9.5.0 (listening only inside the
   container), the locked dependencies (CPU torch), the embedding model and the indices, built at
   image build from the public dump and the committed vectors; `deploy/compose.yaml` adds Caddy,
   the only service open to the outside, with a Let's Encrypt certificate. At start the indices
   are copied to the container's writable layer (Elasticsearch stops if its lock file changes
   under it, which happened on the first try).
3. Checked on the public link: "Pontecorvo" with `bm25-italian` -> "Si è spento Gillo
   Pontecorvo"; "il pontefice è deceduto" with `knn` -> Benedetto XVI first, with `hybrid-rrf` ->
   Pontecorvo first (as in `results/demo/4b`); `knn-bbq` works; the document view works.
4. Update after a push: copy the code to the machine and rerun `docker compose -f
   deploy/compose.yaml up -d --build` (steps in `deploy/README.md`).
For the class the live demo stays on Daniel's laptop, as planned; the public link is a backup.

**Deck** regenerated from the current `.md` files: Fabio's review (#17 applied, notes cut, F6
done) and Gioia's notes are in. Times from the notes: Daniel 5:55, Fabio 3:07 (of which 0:30 on
the demo slide; the live demo adds about 3:30), Gioia 5:44. #17 closed by Fabio.

### 18 Nov 2026 12:16, Gioia: Gioia's speech for the presentation

Asked by Gioia. `slides/discorso-gioia.md` (Italian, like the rest of `slides/`), in the format of
`slides/discorso-daniel.md` and `slides/discorso-fabio.md`: for each of the nine slides of
`slides/gioia.md` the timing, the gist in one line and the speech, with the key passages in bold.
The speech is **the same text as the "Note del relatore"** of `slides/gioia.md`, word for word
(checked by script, bold removed), so the pptx notes and the printed text agree and the deck does
not need to be regenerated. Timing at 2.4 words per second: 5:44 in total (slide 1 0:37, 2 0:51,
3 0:47, 4 0:37, 5 0:38, 6 0:30, 7 0:40, 8 0:30, 9 0:34), within the 6:00 budget. Likely questions
and the numbers to remember are not repeated: the file points to `slides/domande-gioia.md`.

No code change, no number changed. Tests: 130 passed. Nothing to do for Daniel and Fabio. Next:
rehearsal of Gioia's part with the questions.

### 18 Nov 2026 12:18, Fabio: template-generated pages count fixed in `docs/demo.md`

Decided by Fabio. `docs/demo.md` step 5 now says "2,742 pages, 22% of the corpus, are generated
from templates" instead of "about 2,300", as in `results/data_report.md` (2.6: 76 title patterns
with 5 or more pages) and Daniel's slide 5. Same number as in `slides/discorso-fabio.md`. Nothing
else changed in the demo. No code change. Next: demo rehearsal on Daniel's laptop.

### 18 Nov 2026 12:15, Fabio: Fabio's speech for the oral presentation

`slides/discorso-fabio.md` (Italian; format of `slides/discorso-daniel.md`): Fabio's speech per
slide, with the gist, the timing and the key passages in bold. Slides 1-4: the same words as the
"Note del relatore" of `slides/fabio.md` (checked word by word), 375 words, 0:00-2:37. Slide 5,
the live demo: the five steps of `docs/demo.md` in Italian, with Daniel's actions in square
brackets; 358 spoken words (about 2:30) plus the waits for Daniel's actions, about 3:20, so
Fabio's part is about 6:00. Also the spare query ("rincaro del greggio") and what to do if the
demo fails (screenshots of `results/demo/`). No transition sentence to Gioia (as agreed for every
speaker). The notes of slide 5 in `slides/fabio.md` stay short: the deck does not change.

One number differs between files: `docs/demo.md` step 5 says "about 2,300" template-generated
pages; `results/data_report.md` (2.6) and Daniel's slide say 2,742 (22%, series of 5 or more
pages). The speech uses 2,742; `docs/demo.md` not changed yet (Fabio decides).

No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running). Next: demo rehearsal
on Daniel's laptop with the speech.

### 18 Nov 2026 12:08, Fabio: questions for the oral on the retrieval part

`slides/domande-fabio.md` (Italian, like the rest of `slides/`; same format as
`slides/domande-gioia.md`): 29 questions the professor may ask on Fabio's part, with short
answers and their numbers (one `search()` and the named configurations, BM25 fields and weights,
kNN, RRF, filters and facets, E5, latency, the demo), four points to be careful about, and the
numbers to remember. Every number is from `results/summary.md` (run of 17 Nov 17:27), the code
of `wikisearch/search/` or earlier log entries; nothing was rerun. Not part of the deck: Daniel
does not need to do anything with it.

Two points found while checking, for whoever presents the numbers:
1. `hybrid-rrf` is the best configuration on `fonti` only among those without the published
   boost: `hybrid-rrf-published` has MRR@10 0.814 against 0.811 (not tested, and favoured by
   construction on `fonti`). On `manual` the hybrid is the best by nDCG@10, but `knn` has the
   higher MRR@10 (0.925 against 0.911).
2. The reason given for E5 (published pages that are less relevant pushed up, unpublished
   specials that answer the query pushed down) is an interpretation, not counted per query.

No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running). Next: demo rehearsal
on Daniel's laptop with the new look.

### 18 Nov 2026 12:05, Fabio: speaker notes cut to about 2:30, F6 done

Fabio's review of `slides/fabio.md`, decided by Fabio. Only the "Note del relatore" of slides 1-4
changed; titles, tables, figures and numbers are the same as in the 11:58 version (slide 5 and the
header unchanged). The notes of slides 1-4 went from 568 to 375 words, about 4:00 down to 2:37 at
2.4 words per second, within the budget of Daniel's entry of 10:22 (about 2:30 for slides 1-4,
then 3:30 of live demo). Cut, with the same rule as Gioia's: what the table on the same slide
already shows, and details that stay as answers for the oral questions, not on the slides:
title-only BM25 -0.104 (slide 2 table), kNN R@100 0.942 against 0.958 and the hybrid +0.086 on
paraphrases (slide 3 table), the E3b numbers (+0.011 overall, Holm p 0.003; -0.036 on paraphrases,
Holm p 0.0008: the limit is still said, without numbers). Every number left was checked against
`results/summary.md` (run of 17 Nov 17:27).

Also for the record (#14): Fabio confirmed the restyle merged from PR #19 by Daniel (commit
441b1f1), as it is, before the class presentation.

F6 ticked in `PLAN.md`: `slides/fabio.md` reviewed, README "Usage" for the web app done (16 Nov),
demo script done (F5). No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running).
For Daniel: regenerate the deck from `slides/fabio.md` (comment in #17). Next: rehearsal of the
demo on Daniel's laptop with the new look.

### 18 Nov 2026 12:02, Daniel: web restyle merged before the presentation, deck regenerated (D7)

Change of plan decided by Daniel (issue #14): the restyle of the interface is done **before** the
class presentation, to show it there. Done by Daniel's session on the branch `web-restyle`,
pull request #19, approved by Fabio (reported by Daniel) and merged:
1. `wikisearch/web/static/style.css` rewritten (light grey page, square corners, dark header with
   the search form, results in white panels); the compare column headers use the colours of the
   slides for the three families (BM25 dark slate, kNN teal, hybrid orange; `app.js`: a
   `data-family` attribute, no logic change); `index.html`: a tagline and a footer with the
   licence of the texts (Wikinotizie, CC BY 4.0; CC BY 2.5 before 25 Sep 2005) and the code link;
   on a phone the results come before the filters.
2. Every element id, menu and button is unchanged: `docs/demo.md` is valid step by step. No
   change to `search()` or the configurations: no number changes. Tests: 130 passed.
3. `results/demo/`: the eight fallback screenshots retaken with the new style (same links and
   sizes, headless Chrome). The deck is regenerated with them (Fabio's slides 1 and 4).
For the rehearsal: the demo on Daniel's laptop now shows the new look.

Also prepared, not on `main` yet: branch `deploy-server` (`deploy/`, `.dockerignore`), a public
demo on a free Oracle Cloud Always Free machine (one container with Elasticsearch and the web app,
Caddy for HTTPS). Details when it is online. Hugging Face Spaces was the first idea, but Docker
Spaces now need a paid plan.

### 18 Nov 2026 11:58, Fabio: issue #17 applied on `slides/fabio.md` (F6, work in progress)

Issue #17 (Daniel), accepted by Fabio. Two changes on slide 3 of `slides/fabio.md`, nothing else:
1. `Figura:` is now "schema di RRF (disegnato nel deck)": `e3_buckets.png` stays only on Gioia's
   slide 5; Daniel's deck draws the RRF diagram (two ranked lists, 1/(60 + rank) summed).
2. Latency wording, same as Gioia's slide 7: the hybrid "resta sotto i 60 ms anche al 95°
   percentile" (p95 53.4 ms in `results/summary.md`, E6), instead of "sotto i 100 ms".
No number changed. No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running).
For Daniel: regenerate the deck from `slides/fabio.md`. Next: Fabio's review of the whole file
(the speaker notes of slides 1-4 are about 568 words, about 4:00 at 2.4 words per second, against
the 2:30 budget), then F6 ticked.

### 18 Nov 2026 10:56, Daniel: where the deck is built (D7)

The deck script and Daniel's speech script moved from `slides/build/` (local, not committed) to
Daniel's notes folder, next to his copies of the presentation, as for homework 2. One command,
`costruisci.py` there, writes: `slides/wikinews-search.pptx` in the repository (with notes, the
team's copy, to commit as before), a copy with notes, a copy **without notes** (the one to
upload: the speech stays out of the handed-in file, as for homework 2) and its PDF. Nothing
changes for Fabio and Gioia: they edit their `.md` files and Daniel regenerates.

### 18 Nov 2026 10:51, Daniel: deck regenerated with Gioia's review (D7)

`slides/wikinews-search.pptx` regenerated from the current `.md` files (commit dc70372): Gioia's
changes of #18 (who graded `manual`, same wording on slides 1, 3, 8) and her shorter notes are in
the deck. Times from the notes: Daniel 5:55, Gioia 5:44, Fabio 4:27 (his notes before his
review; the live demo adds about 3:30). Changed slides checked visually. #18 closed. Waiting for
Fabio (#17: slide 3 figure line, latency wording, his review), then the last regeneration.

### 18 Nov 2026 10:49, Daniel: fresh clone checked end to end, with Elasticsearch (D7)

Continuation of the 10:29 entry, the part that needed Elasticsearch (Docker started for it):
1. From the fresh clone, `uv run python -m wikisearch.ingest.index`: `wikinews-standard` 17.5 s,
   57.4 MB, `wikinews-italian` 17.0 s, 54.9 MB, 12,213 documents each, with the shared vectors
   (same sizes as `results/indexing.csv`). The indices on Daniel's laptop were rebuilt by this,
   from an identical `docs.jsonl` and the same vectors; the E8 indices were not touched.
2. `uv run pytest -q`: 130 passed (the 22 that need Elasticsearch included).
3. Command line: "Pontecorvo" with `bm25-italian` -> "Si è spento Gillo Pontecorvo" first;
   "il pontefice è deceduto" with `knn` -> "Il papa emerito Benedetto XVI è morto" first (as in
   `docs/demo.md`). Web app: `/`, `/api/configs` (11 configurations, default `hybrid-rrf`) and
   `/api/search` answer.
4. `uv run python -m evaluation.run --configs bm25-italian knn`: the rows of `bm25-italian` and
   `knn` in `fonti.csv` and `manual.csv` are identical to the official ones (16 minutes).
README "Requirements" now states this check. Elasticsearch and Docker stopped again afterwards.
Nothing committed from the fresh clone.

Next: Fabio's and Gioia's reviews (#17, #18), regenerate the deck, rehearsal, repository public,
upload.

### 18 Nov 2026 10:38, Gioia: questions for the oral on the evaluation part

`slides/domande-gioia.md` (Italian, like the rest of `slides/`; same idea as the questions in
`slides/discorso-daniel.md`): 23 questions the professor may ask on the evaluation, with short
answers and their numbers (test sets and metrics, `manual` and the kappa, statistics, results),
three points to be careful about, and the numbers to remember. Every number is from
`results/summary.md` (run of 17 Nov 17:27) or from earlier log entries; nothing was rerun.
Not part of the deck: Daniel does not need to do anything with it.

Two points found while checking, for whoever presents the numbers:
1. Slide 4 of `slides/gioia.md` says "E3 fa 27 confronti": they are 24 on `fonti` and 3 on
   `manual`, and Holm corrects the two families separately (the smallest E3 Holm p on `fonti` is
   0.0024 = 24 x 1/10,000). The slide stays as it is; the answer is in the file.
2. The 49 disagreements of the kappa are 1-2: 21, 0-1: 14, 0-2: 14, so "1 against 2" is the most
   frequent kind, not "almost all" of them (the wording of the 17 Nov 17:05 entry).

No code change. Tests: 130 passed. Next: rehearsal with timing.

### 18 Nov 2026 10:36, Gioia: speaker notes cut to 6 minutes, G6 done

Gioia's review of `slides/gioia.md`, decided by Gioia. Only the "Note del relatore" changed; titles,
tables and numbers are the same as in the 09:30 version. The notes went from 1,016 to 827 words,
about 7:04 down to 5:44 at 2.4 words per second, within the 6:00 budget (Daniel's entry of 10:22).
What was cut, and why: sentences that a table on the same slide already shows, or that another
slide says (slide 2 no longer anticipates the E3 result; slide 5 no longer repeats the intervals);
the definition of Holm on slide 4 (the example p 0.03 -> 0.18 stays); on slide 3, the detail
that the disagreements are about "how" relevant; on slide 7, the machine used for latency
(MacBook Air M4, 16 GB: in the log of the official run). These stay as answers for the questions,
not on the slides. Slide 9 is unchanged.

G6 ticked in `PLAN.md`: figures in `results/figures/`, reading of the results in the log of
17 Nov 17:35, slides reviewed. No code change. Tests: 130 passed. For Daniel: regenerate the
deck from `slides/gioia.md` (comment in #18). Next: rehearsal with timing.

### 18 Nov 2026 10:30, Gioia: who graded `manual`, same wording on every slide (G6, work in progress)

Issue #18 (Daniel), accepted by Gioia. `slides/gioia.md` now says the same thing everywhere about
who graded `manual`:
1. Slide 1, table: "573 documenti graduati 0/1/2: 10 query da due di noi, 20 da un modello (vedi
   Limiti)"; speaker note: "giudicato con tre gradi, in parte da noi e in parte da un modello".
2. Slide 3, speaker note: the blind third judge of the 49 disagreements is named as a model.
3. Slide 8, limits: the row "giudizi di `manual` dati da noi" becomes "10 query di `manual`
   giudicate da noi, autori del sistema", so it no longer reads as a contradiction with the next
   row (20 of 30 queries graded by a model).
Point 2 of #18 (`e3_buckets.png` only on Gioia's slide 5) needs no change on Gioia's side.

No code change, no number changed. Tests: 130 passed. For Daniel: regenerate the deck from
`slides/gioia.md`. Next: Gioia's review of the whole file (speaker notes are about 7:00 at 2.4
words per second, the budget is 6:00), then G6 ticked.

### 18 Nov 2026 10:29, Daniel: final README, setup checked from a fresh clone (D7, work in progress)

`README.md` is now the final version for the delivery:
1. Status line replaced by what the repository contains at delivery; new section "What it does,
   in brief" (the three parts, who did what) with a table of the main results, one row per
   experiment, numbers from `results/summary.md`, and the limit of `manual` (20 of 30 queries
   graded by a model).
2. Requirements: GitHub CLI is no longer needed to use the repository (it will be public).
3. New section "Data: parsing and indexing" (the missing usage part): `parse`, `index`, `embed`,
   the E8 indices, the data report, the sample. Evaluation section: `evaluation.figures` and
   `evaluation.manual_human` added. New "Repository layout" table.
4. **Checked from a fresh clone** (macOS, 18 Nov): `git clone`, `uv sync`, `uv run pytest -q`
   (108 passed, 22 skipped: they need Elasticsearch), `python -m wikisearch.ingest.parse` on the
   dump: 12,213 documents in 12 s, `docs.jsonl` identical byte for byte (same SHA-1) to the one
   of the official run. Not checked from the fresh clone: indexing and search, because Docker was
   not running; to do when Elasticsearch is started for the rehearsal.

No code change. Tests: 108 passed, 22 skipped. Next: indexing and search check with Elasticsearch
up, Fabio's and Gioia's reviews (#17, #18), regenerate the deck, rehearsal, repository public,
upload.

### 18 Nov 2026 10:22, Daniel: Daniel's speech, the same text in the notes (D7, work in progress)

As in homework 2, each speaker has a written speech, and the speech is the "Note del relatore"
of their `.md` file, so the pptx notes and the printed text are the same words.
1. `slides/daniel.md`: the notes of slides 1-7 are now Daniel's speech, shorter than before
   (the longest notes, slides 6 and 7, were about 1:45 each; now 0:43 and 0:51). The cover speech
   (names, the project, the demo query on the cover, who presents what) is in the deck script,
   since the cover is not in any `.md` file.
2. `slides/discorso-daniel.md`: the speech per slide with the gist, the timing and the key
   passages in bold, then 13 questions the professor may ask on the data and indexing part, with
   the answers, and the numbers to remember. Total 5:55 at 2.4 words per second.
3. If Fabio or Gioia want the same for their part, the format is in `slides/discorso-daniel.md`
   (not requested: their notes stay theirs). Time budget: Daniel 6:00, Fabio about 2:30 for slides 1-4 plus 3:30 of demo, Gioia
   6:00 for her nine slides. No transition sentences between speakers (`docs/course.md`).

No code change. Tests: 108 passed, 22 skipped. Next: Fabio's and Gioia's reviews
(#17, #18), regenerate the deck, rehearsal, README, repository public, upload.

### 18 Nov 2026 10:17, Daniel: deck in the homework 2 style, decisions on repeated results (D7, work in progress)

Decided by Daniel (he assembles the deck and keeps the three parts consistent):
1. **E3 figure once.** `e3_buckets.png` stays only on Gioia's slide 5 (the key result). Fabio's
   slide 3 shows instead a diagram of how RRF works (two ranked lists, 1/(60 + rank) summed).
   Issue #17 for Fabio (also: latency wording "sotto i 60 ms anche al 95° percentile", as Gioia).
2. **Who graded `manual`.** Gioia's slide 1 says "da noi", her slide 8 says 20 of 30 queries were
   graded by a model: issue #18 asks her to make slide 1 say the same. #16 closed (her slides are
   in the deck).
3. **E5 and E8 not repeated by Daniel.** `slides/daniel.md`: slide 4 notes only say that E5
   measures the boost and Fabio shows it; slide 7 shows only the memory side of E8 (19.2, 5.3,
   1.2 MB), the quality numbers stay on Gioia's slide 7.

**Deck** `slides/wikinews-search.pptx`, 22 slides, 16:9 (10 x 5.625 in), same style as the homework
2 deck: dark title band, orange progress bar, booktabs tables, blocks, Calibri, footer with the
three parts (Dati, Retrieval, Valutazione; the current one in orange) and the slide number.
Choices and why:
1. One colour per retrieval family on every slide: BM25 dark, kNN teal, hybrid orange. A listener
   who has seen one chart reads the next one.
2. The PNGs of `results/figures/` are redrawn as native charts or drawn shapes from the same
   numbers (`results/summary.md`, `results/data_report.md`): E2 bars, E3 per bucket, `manual`
   nDCG@10 as means with their 95% intervals, the latency-quality scatter of E6. They are crisp on
   the projector and use the deck's colours. The PNGs stay the reference in the repository.
3. Cover: one query of the demo ("il pontefice è deceduto"), BM25 against kNN, the top 3 of each
   from `results/demo/4a-paraphrase-bm25-vs-knn.png`: the project in one picture.
4. Real examples instead of text where the `.md` notes had one: the `{{luogodata}}` template
   turned into a date, the 14 spellings of "la Repubblica" merged by one key, the leakage pair
   (source title, article), stemming examples, the five demo queries.
5. Speaker notes = "Note del relatore" of the `.md` files, headed by the speaker and an estimate of
   the time (words / 2.4 per second). Estimates: Daniel about 6:45, Fabio about 4:30 plus the live
   demo, Gioia about 7:00: Daniel's slides 7 and 8 have the longest notes (about 1:45 each).
The deck is generated by a script on Daniel's laptop (`slides/build/`, not committed: Node and
`pptxgenjs` are not project dependencies). Titles, tables and notes are read from the three
`.md` files at every build; the drawings are in the script. So: change the `.md` files, then
Daniel regenerates; do not edit the pptx.

No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running). Next: Fabio's and
Gioia's reviews (#17, #18), regenerate, rehearsal with timing, README, repository public, upload.

### 18 Nov 2026 09:55, Daniel: consistency check of the three slide files, first deck draft (D7, work in progress)

**Consistency check.** Every number in `slides/daniel.md`, `fabio.md` and `gioia.md` was checked
against `results/summary.md` (run of 17 Nov 17:27): all match (rounding only, e.g. E3b -0.0359 is
"-0,036" for Fabio and "0,646 contro 0,611" for Gioia; E1 manual p 0.0379 is "0,038" for Daniel
and "0,04" for Gioia). Points that are not errors but must be decided before the rehearsal:
1. E3 appears twice with the same table and figure: Fabio slide 3 and Gioia slide 5
   (`e3_buckets.png`); E5 three times (Daniel 4, Fabio 4, Gioia 6); E8 twice (Daniel 7, Gioia 7).
   Gioia's header says E2, E3, E5 details stay on Fabio's slides, but her slide 5 is a full E3
   slide. 22 slides for 20 minutes is tight.
2. Gioia slide 1 says the `manual` grades are "da noi", her slide 8 says 20 of 30 queries were
   graded by a model: the two lines should say the same thing.
3. Latency: Fabio slide 3 "resta sotto i 100 ms", Gioia slide 7 "sotto i 60 ms" (p95 53.4 ms): both
   true, one wording is enough.

**Deck.** `slides/wikinews-search.pptx`, 22 slides, 16:9: cover (title, the three names in
alphabetical order by surname, course, repository link, no emails), then Daniel 7, Fabio 5,
Gioia 9, in the order of `PLAN.md`. Each slide: the title of the `.md` file, the "Contenuto" line
as subtitle, the table, the figure; "Note del relatore" go into the speaker notes, prefixed with
the speaker's name. Sober style: white slides, one dark red for the best values (the bold cells
of the `.md` files), no divider slides, no names on the content slides. The deck is generated
from the three `.md` files by a script on Daniel's laptop (`slides/build/`, not committed:
it uses Node and `pptxgenjs`, which are not project dependencies), so changes to the `.md` files
go into the deck by regenerating it, not by editing the pptx. Not changed: the content of
Fabio's and Gioia's files (their reviews are still open, F6 and G6 not ticked).

No code change. Tests: 108 passed, 22 skipped (Elasticsearch not running). Next: decide the three
points above with Fabio and Gioia, regenerate the deck after their reviews (Gioia: before 11:00),
rehearsal with timing, README, repository public, upload.

### 18 Nov 2026 09:30, Gioia: `slides/gioia.md` written (G6, work in progress)

`slides/gioia.md`, in Italian, with the structure of `PLAN.md` ("Slides"), nine short slides
(about 6 minutes), structure decided by Gioia: (1) how we evaluate, the two test sets side by
side; (2) `fonti`: the idea and the funnel 17,192 -> 7,072, buckets, language rule and leakage
check; (3) `manual`: 30 queries with needs, pool of 573 documents (95 found only by `knn`), grades,
kappa 0.543 / 0.674, blind third judge; (4) statistical checks: bootstrap intervals, paired
randomization test, Holm, `random` baseline at 0, metrics tested by hand; (5) E3 per bucket
(`e3_buckets.png`, the key figure); (6) `manual` nDCG@10 with intervals (`manual_ndcg.png`) and
the human-judged subset; (7) costs, E6 and E8 (`e6_tradeoff.png`); (8) limits; (9) conclusions,
one row per experiment (confirmed: E1, E3, E4; contradicted: E2, E5).

Every number is from `results/summary.md` and `results/metrics/` of the final run (17 Nov 17:27);
nothing was rerun. To avoid repeating the other parts, E1 and E4 details stay on Daniel's slides,
E2, E3 and E5 on Fabio's; Gioia's slides only recall them in the final table, with the same
numbers. Late against the plan (Tuesday 22:00): written this morning, before the deck.

No code change. Tests: 130 passed. For Daniel: `slides/gioia.md` is ready for the deck; the four
figures are in `results/figures/` (`e3_buckets.png` is also on Fabio's slide 3: in the deck it
can be shown once). G6 not ticked yet: Gioia reviews the text first. Next: Gioia's review, then
G6 ticked, then the rehearsal.

### 17 Nov 2026 18:10, Fabio: `slides/fabio.md` with the official numbers (F6, work in progress)

`slides/fabio.md` written in Italian with the structure of `PLAN.md` ("Slides"), numbers from the
final run (`results/summary.md`, 17:27), Holm p everywhere. Five slides, as in the outline of
16 Nov 17:05: (1) one `search()`, eleven named configurations, one per experiment (figure: compare
mode screenshot); (2) E2 fields and weights (`results/figures/e1_e2_bm25.png`); (3) E3 lexical,
semantic, hybrid, with latencies and E3b (`e3_buckets.png`); (4) filters, facets and E5
(screenshot of the filters); (5) the demo. Not ticked yet: Fabio reviews the text first.

How the results read for Fabio's part, decided with Fabio:
1. **E2 contradicts our default weights**: equal weights (`-flat`) 0.800 against `title^3 lead^2
   body` 0.768 (+0.032, Holm p 0.0006), almost all on paraphrases (0.646 against 0.525). Said
   openly on slide 2. Why E3 and E5 still use 3-2-1: the configurations were fixed before the
   results, and changing them after seeing the test set would tune the engine on the queries that
   evaluate it.
2. **E3 confirms RRF**: hybrid best on `fonti` (0.811; paraphrases 0.611), on `manual` only hybrid
   against BM25 is significant (+0.103, p 0.010); cost 43 ms p50 against 15. E3b is stated as a
   limit: against equal-weights BM25 the hybrid loses on paraphrases (-0.036); a hybrid on equal
   weights was not tested (next step, not done after the freeze).
3. **E5 contradicts the published boost** (`manual` nDCG@10 0.804 -> 0.758, p 0.029), so the
   default configuration stays without boost. Why E5 is not measured on `fonti`: its target is
   always a published article, so the test would favour the boost by construction.
`docs/demo.md` step 1: the sentence now gives the E5 result instead of "E5 measures whether it
helps".

No code change. Tests: 130 passed. For Daniel (deck): the figures used are Gioia's
`e1_e2_bm25.png` and `e3_buckets.png` and two screenshots of `results/demo/`; Gioia may show the
same figures in her results part, to be kept consistent in the deck. Next: Fabio's review, then
F6 ticked.

### 17 Nov 2026 17:35, Gioia: figures, `manual` on the human-judged queries, reading of the results (G6, work in progress)

**Figures**, `uv run python -m evaluation.figures` (reads `results/metrics/`, no search, a few
seconds), into `results/figures/`; the script is the draft of commit `e2a4fe2` (reverted on 16 Nov)
brought back and updated:
1. `e3_buckets.png`: MRR@10 of BM25, kNN, hybrid on all queries and per overlap bucket, 95%
   intervals (the key figure);
2. `e1_e2_bm25.png`: MRR@10 of the five BM25 variants, each with its difference and Holm p;
3. `e6_tradeoff.png`: p50 latency against MRR@10; kNN with its int8/BBQ variants and the hybrid
   with and without the published boost nearly coincide and share one label;
4. `manual_ndcg.png` (**added, decided by Gioia**): nDCG@10 of the five pooled configurations on
   `manual` with E1, E3, E5 differences and Holm p, so the `manual` results are not only a table.
Decided by Gioia: titles and labels of the figures are **in Italian**, because they go on the
Italian slides (an exception to the English rule of the repository, like `slides/`). p-values on
the figures are the Holm-corrected ones.

**`manual` on M01-M10 only** (the 10 human-judged queries, promised in #15),
`uv run python -m evaluation.manual_human` (reads `manual_per_query.csv`, writes
`results/metrics/manual_human.csv` and `manual_human_significance.csv`). nDCG@10: standard 0.756,
Italian 0.818, kNN 0.787, hybrid 0.867, hybrid-published 0.788. Same direction as on the 30
queries for E1 (+0.062), hybrid against BM25 (+0.050) and E5 (-0.079), but **nothing is
significant** on 10 queries (Holm p 0.35 to 0.85); kNN is below BM25 here (-0.031, p 0.74), while
it is above on the 30. Reading: the `manual` conclusions rest on the 30 queries, 20 with model
grades; on the human-judged subset alone the test has too little power to confirm or deny them.

**Reading of the results** (one sentence per experiment, for the slides; all from
`results/summary.md`, Holm p):
1. E1: the Italian analyzer is better on both test sets (`fonti` MRR@10 +0.025, p 0.0002;
   `manual` nDCG@10 +0.052, p 0.04) and also faster (p50 14.6 against 19.2 ms).
2. E2: searching only the title (-0.104) or only the body (-0.042) loses; equal field weights
   beat our boosted weights (+0.032, p 0.0006), mostly on paraphrases (low bucket 0.646 against
   0.525): the title boost hurts when the query does not reuse the title's words.
3. E3: the hybrid is the best on `fonti` (MRR@10 0.811 against 0.768 BM25 and 0.781 kNN, all
   significant) and the gain is largest on paraphrases (low bucket 0.611 against 0.525); kNN alone
   loses recall (R@100 0.942 against 0.958). On `manual` only hybrid against BM25 is significant
   (nDCG@10 +0.103, p 0.010).
4. E3b: against the stronger lexical baseline (equal weights) the hybrid still wins overall
   (MRR@10 +0.011, p 0.003) but loses on the low bucket (-0.036, p 0.0008).
5. E4: indexing the sources would inflate MRR@10 from 0.768 to 0.900 (+17%): the leakage check
   of the test set is needed.
6. E5: boosting published pages makes `manual` worse (nDCG@10 -0.046, p 0.03).
7. E6: quality costs latency: BM25 about 15 ms, kNN 26 ms (query embedding included), hybrid
   43 ms (p50); every configuration stays well under 100 ms.
8. E8 (stretch): int8 and BBQ quantization cost no measurable MRR@10 (-0.0004, p 0.95); BBQ loses
   a little R@100 (-0.003, p 0.03); latency unchanged.
Limits for the slides: `fonti` has one relevant document per query; `manual` is judged by us, 20
of 30 queries by a model, disagreements adjudicated by a model; unjudged documents count as not
relevant; `manual` has 30 queries, so its intervals are wide.

Tests: 130 passed (new: `tests/test_figures.py`, `tests/test_manual_human.py`). Nothing changes
for the others; Daniel and Fabio can use the figures. Next: `slides/gioia.md` (by 22:00), then
G6 ticked.

### 17 Nov 2026 17:45, Daniel: final official numbers on Daniel's slides (D7, work in progress)

`slides/daniel.md` updated with Gioia's final run (entry of 17:30, `results/summary.md`):
1. slide 6 (E1): `manual` nDCG@10 0.648 -> 0.701 (+0.052, p 0.038; one test, so Holm p = p);
   latency p50 now 19.2 against 14.6 ms (the final latency pass; the `fonti` means are unchanged).
2. slide 7 (embeddings): `knn` latency 25.8 against 14.6 ms ("almost twice", was "twice"); new
   row and notes for E8: `int8` and `bbq` lose 0.0004 MRR@10 (Holm p 0.95), `bbq` loses R@100
   0.003 (Holm p 0.026), latency unchanged (25-26 ms); the gain is memory (19.2 -> 5.3 -> 1.2 MB in
   RAM, entry of 16 Nov 15:30), which at 12,213 documents does not matter.
3. slide 4 (non-published pages): the answer of E5, the published boost lowers `manual` nDCG@10
   from 0.804 to 0.758 (p 0.029), so keeping those pages unpenalised was right.
For the deck: Fabio's E5 slide and Gioia's results should say the same (the boost hurts). No code
change; tests 125 passed. Next: read `slides/fabio.md` and `slides/gioia.md` when pushed (22:00)
for consistency; the deck last, on Wednesday morning.

### 17 Nov 2026 17:30, Gioia: final official run, numbers frozen (G5 done, G4 done)

`uv run python -m evaluation.run` (full, every configuration, both test sets; started 16:56,
ended 17:27, commit `216e862`), Apple M4, 16 GB RAM, Elasticsearch 1 GB heap. `manual` uses the
final qrels (merge of 17:10). Committed: `results/metrics/` (`fonti.csv`, `manual.csv`, both
`_per_query.csv`, `significance.csv`, `latency.csv`) and `results/summary.md`. These are the
official numbers; nothing is rerun after this unless the code changes. The `fonti` means are
identical to the 09:35 run (same index and code): only `manual`, E8 and the latencies are new.

Headline numbers (95% bootstrap interval in `summary.md`, Holm-corrected p):
1. E1 analyzer: `fonti` MRR@10 0.743 -> 0.768 (Holm p 0.0002); `manual` nDCG@10 0.648 -> 0.701
   (p 0.038): the Italian analyzer helps on both sets.
2. E3 `fonti` MRR@10: BM25 0.768, `knn` 0.781, hybrid 0.811 (all pairs significant); low
   bucket 0.525 / 0.557 / 0.611. `knn` loses recall (R@100 0.942 against 0.958). `manual`
   nDCG@10: 0.701 / 0.764 / 0.804; only hybrid against BM25 is significant (Holm p 0.010).
3. E3b: hybrid against `bm25-italian-flat`: MRR@10 +0.011 (Holm p 0.003), but worse on the low
   bucket (-0.036): the equal-weights BM25 is the stronger lexical baseline on paraphrases.
4. E4 leakage: MRR@10 0.768 -> 0.900 with the sources searchable.
5. E5 published boost on `manual`: nDCG@10 0.804 -> 0.758, **worse** (p 0.029): the boost pushes
   up published but less relevant pages.
6. E8 quantization: `knn-int8` and `knn-bbq` MRR@10 -0.0004 (not significant); `bbq` loses
   R@100 -0.003 (Holm p 0.026); latency unchanged (p50 25-26 ms, all three).
7. E6 latency p50: BM25 14.6 ms, `knn` 25.8 ms (query embedding included), hybrid 43.1 ms.
8. `random` scores 0 everywhere: the floor holds, the metric code is sane.

G4 ticked (judgments merged, kappa reported, disagreements adjudicated) and G5 ticked (one
command reproduces every number on the full corpus). Tests: 125 passed. For Daniel and Fabio:
the official numbers are in `results/summary.md`, you can put them on your slides. #12 closed
(E8). Next: G6, figures and one-sentence reading per experiment; the `manual` numbers also on
M01-M10 only (the human-judged queries, as promised in #15).

### 17 Nov 2026 17:22, Daniel: delivery is the pptx only, cover without emails (D7)

Decided by Daniel:
1. **Only the pptx is uploaded**, no PDF: the professor never asked for a PDF (`docs/course.md`
   has no such request; "PDF and pptx" was our own line in the timeline of `PLAN.md`).
2. **The cover carries the three names and the repository link, no emails.** The professor asked
   for the authors' emails in the homework 3 reports (`docs/course.md`, section 2, item 5), not
   for the presentation.
3. **The deck is the last thing**: it is built only when the code and all the numbers are final
   (after the official run), as already planned for Wednesday morning.

`PLAN.md` (D7 and the timeline row of Wednesday 14:00) and `docs/briefs/daniel.md` updated. No
code change; tests 125 passed. Nothing changes for Fabio and Gioia (their slide files are due as
before, Tuesday 22:00). Next: E1 nDCG@10 on `manual` and the E8 numbers in `slides/daniel.md` as
soon as Gioia's final run is pushed.

### 17 Nov 2026 17:10, Gioia: disagreements adjudicated, final `manual` qrels (G4)

`evaluation/testsets/manual/judgments/resolved.tsv` written from the 49 blind third-judge grades
of Daniel's session (25 in #13 for M01-M05, 24 in #15 for M06-M10; same 49 keys as the
disagreements), then `uv run python -m evaluation.merge_judgments`. `qrels.txt` is now **final**:
30 queries, 573 judged documents, grades 0: 279, 1: 76, 2: 218 (provisional: 293 / 83 / 197).
No query is left without relevant documents: **M05 is back** in the metrics (3060 and 4964
graded 2). `disagreements.tsv` is pushed now that the adjudication is closed: it shows both
judges' grades and the third grade.

Kappa unchanged (computed on the original human grades): 0.543 on 0/1/2, 0.674 binary, 178
documents. How the third judge decided the 49: the higher of the two grades 27 times, the lower
16, the middle grade 1 on 6 pairs 0-2. Pairs: 1-2: 21, 0-1: 14, 0-2: 14.

Timing: the full official run (`uv run python -m evaluation.run`, started 16:56) was still on the
`fonti` configurations when the merge ran; it loads the `manual` qrels only when it reaches that
set, so it uses the final qrels and **no second run is needed** (Daniel's suggestion in #15 of a
rerun with `--configs random` becomes unnecessary). Tests: 125 passed. Nothing changes for the
others. #13 and #15 closed. Next: finish the official run, commit `results/metrics/` and
`results/summary.md`, close #12 (E8), then G6.

### 17 Nov 2026 17:35, Fabio: demo script as interface actions, F5 done

`docs/demo.md` rewritten as Daniel asked in the entry of 14:50 (issue #8): every step is now a
list of **interface actions for Daniel** (query typed in the box, configuration menu, Compare and
the second menu, the two date fields, the ANSA checkbox, "Clear filters"), then what Fabio shows
and the sentence he says; the links stay at the end of each step as the fallback, with the
screenshots of `results/demo/`. Order and sentences unchanged. New section "How the interface
reacts", for Daniel.

Checked live on Fabio's laptop (Elasticsearch, the web app, the app's browser in Italian): every
action of the file run once through the interface, results identical to the links. Found and
written in the file:
1. **Dates**: typing the year, the list refreshes at every digit (years 0002, 0020, 0200, then
   2009), because each complete date fires a new search; it is harmless, keep typing.
2. **"N results"** counts the results of the page (10 per page), not all the matching documents:
   the old line "untick ANSA to show how many there were" is removed, the step says only that the
   page fills up again and "Next" appears.
3. **Filters stay active** when a new query is typed: "Clear filters" is now an explicit action at
   the end of step 2 (otherwise "Pontecorvo" would run with the April 2009 dates and ANSA).
4. Step 1 uses the configuration menu (`hybrid-rrf-published`), not the "Published only"
   checkbox, as agreed with Daniel; step 4 changes the second menu before the first so the two
   columns never show the same configuration.
5. Warm-up: the first `knn` query took **78 s** on Fabio's laptop right after starting Docker
   (19 s on Daniel's Mac on 16 Nov): the file asks to run it at least two minutes before the demo.
6. Spare query: `knn` does find an oil article at rank 5, so the sentence now says "starts with
   unrelated pages, first oil article only at rank 5" instead of "returns unrelated pages".

Decided by Fabio: **F5 ticked** in `PLAN.md`. The plan asked for a rehearsal on Daniel's laptop;
Daniel and Fabio agreed at 14:50 that a joint rehearsal is not needed (links checked twice on
Daniel's Mac, Daniel practises the actions alone, same indices and code everywhere).

No code change. Tests: 124 passed, 0 skipped (Elasticsearch and the E8 indices up). For Daniel:
please practise from the new `docs/demo.md`, above all the dates. Next: `slides/fabio.md` (F6)
with the official numbers, by 22:00.

### 17 Nov 2026 17:20, Daniel: experiment results on Daniel's slides (D7, work in progress)

`slides/daniel.md`: each indexing choice now carries its number from Gioia's official `fonti` run
(`results/summary.md`, 09:35), which the final run reproduces (same index and code):
1. slide 5, leakage (E4): MRR@10 0.768 -> 0.900 with the sources searchable (+17%; low bucket
   0.525 -> 0.808);
2. slide 6, analyzer (E1): MRR@10 +0.025, R@100 +0.013 (Holm p 0.0002), and cheaper (p50 13.9
   against 18.3 ms): better on every count, not a trade-off;
3. slide 7, embeddings: `knn` over BM25 on the low-overlap bucket +0.032 MRR@10 (Holm p 0.002),
   but lower R@100 (0.942 against 0.958) and twice the latency: the reason to combine them, shown
   by Fabio (E3). Daniel's slide gives one number; the full E3 comparison stays on Fabio's slides,
   the full tables on Gioia's.
Still to add after the final run: E1 nDCG@10 on `manual` and E8 (quality and latency of `knn-int8`,
`knn-bbq`). No code change; tests 125 passed. Next: those numbers, then the deck on Wednesday.

### 17 Nov 2026 17:05, Daniel: blind third-judge grades for the 49 disagreements of M01-M10 (G4)

Daniel's session graded the 49 disagreements as the blind third judge agreed in #13 (M01-M05,
proposed by Daniel, accepted by Gioia) and #15 (M06-M10, proposed by Gioia, accepted by Fabio and,
at 17:00, by Daniel). Grades posted in the issues as `qid<TAB>doc_id<TAB>grade` (25 in #13, 24 in
#15): 2 = 21, 1 = 14, 0 = 14. M05 gets two documents of grade 2 (3060, 4964), so it stays in the
metrics once the merge is rerun.

How: Claude read only the qid, the `need` in `queries.tsv`, `GUIDELINES.md` and the article in
`docs.jsonl`; it never opened `judgments/{gioia,daniel,fabio}.tsv`, and Daniel was not asked about
any document (he is one of the two judges of M01-M05). Rules applied, for consistency: rule 3
strictly on the `time` queries (other elections in M03, the Club World Cup in M07: 0); events
closely connected but not the need itself are 1 (qualifying play-offs and squad lists of the 2006
World Cup, procedural pages on the 2006 election, Pavarotti leaving hospital, the removal of the
Costa Concordia wreck in 2013); special pages carrying the results are 2 (rule 4); entity needs
read as written (a tax case of Valentino Rossi is 0 for "races, championships and results").
Limit for the slides (already agreed): the disagreements of M01-M10 were resolved by a model as
third judge; the kappa stays on the original human grades.

For Gioia: write `judgments/resolved.tsv` from the two comments and rerun the merge and the run
before 19:15. No code change; tests 125 passed. Next: D7 (slides with the official numbers).

### 17 Nov 2026 17:05, Gioia: all judgments merged, provisional `manual` qrels (G4, work in progress)

`uv run python -m evaluation.merge_judgments` run with the three files (Gioia 178, Daniel 287,
Fabio 286, none missing). `evaluation/testsets/manual/qrels.txt` committed: 30 queries, 573
judged documents, grades 0: 293, 1: 83, 2: 197. It is **provisional**: the 49 disagreements are
still open and get the lower grade (GUIDELINES.md, rule 5) until Daniel's session sends its blind
grades (#13 for M01-M05, #15 for M06-M10); then `judgments/resolved.tsv` is written and the merge
run again.

Agreement on the 178 doubly judged documents (original human grades, before any resolution; this
is the number for the slides):
1. all: raw agreement 0.725, Cohen's kappa 0.543 on 0/1/2, 0.674 on relevant / not relevant;
2. Gioia-Daniel (M01-M05, 90 documents): 0.722, kappa 0.527 and 0.711;
3. Gioia-Fabio (M06-M10, 88 documents): 0.727, kappa 0.549 and 0.619.
Moderate agreement on three grades, substantial on binary relevance (Landis and Koch): most
disagreements are 1 against 2, i.e. on how relevant, not whether. They cluster on two `time`
queries, M03 (13) and M07 (11), where rule 3 (other year or other election) applies.

Note: with the lower grade for every open disagreement, **M05 has no relevant document** and is
skipped by the metrics (29 queries); the third judge's grades on its 4 disputed documents decide
whether it comes back.

`disagreements.tsv` is **not** pushed until the adjudication is done (it shows both judges'
grades, the third judge must stay blind). Blind list for M06-M10 posted in #15 (24 documents);
deadline given to Daniel: 19:15, after that the open disagreements keep the lower grade and the
full run starts. G3 ticked: its "done when" holds (assignment files and tool pushed, everyone has
judged). Tests: 125 passed. Nothing changes for the others, except Daniel's session: grades in
#13 and #15. Next: the full official run `uv run python -m evaluation.run` once the grades are
in (or at 19:15), then G6.

### 17 Nov 2026 16:50, Fabio: Fabio's judgments of the `manual` pool (G4), M21-M30 graded by Claude

`evaluation/testsets/manual/judgments/fabio.tsv`: 286 of 286 assigned documents, none missing
(checked against `judging/fabio.tsv`). One line per document, in the order of the assignment file.

**Who judged what (decided by Fabio, to state as a limit):**
1. **M06-M10** (88 documents, the doubly judged queries): judged by Fabio himself. Claude showed
   him the documents in chat in blocks of one query (title, date, start of the lead, the need
   translated into Italian, the grade definitions) and wrote down the grades Fabio typed; Claude
   never suggested a grade. Three times the number of grades typed did not match the number of
   documents of the block: Claude saved nothing and asked Fabio to type the block again. As agreed
   in #10, Fabio was not shown `judgments/gioia.tsv` or per-query counts before judging. So the kappa on M06-M10 is between two humans.
   Grades: 0 = 32, 1 = 14, 2 = 42.
2. **M21-M30** (198 documents, judged by one person only): **graded by Claude**, at Fabio's request
   (16:45), the same arrangement as Daniel's M11-M20 (entry of 14:25): from title, date and lead
   following `GUIDELINES.md`, reading the body when the lead was not enough (e.g. an article on
   environment and conflicts that quotes an analysis of Darfur over several sentences: 1). Rules
   applied: rule 3 for the `time` queries (for M27, the 2009 flu and COVID news about other
   countries or later years score 0, world-wide overviews of 2020 score 1); a scheduled event or follow-up of the right subject is 1
   (e.g. the 2008 elections called after the fall of Prodi for M24); fan-against-fan deaths are 1
   for M28, whose need asks for fans against police. Grades: 0 = 107, 1 = 28, 2 = 63. While
   recording, one block of M30 was shifted by one position; Claude noticed it from the count and
   re-recorded those seven documents before the push.

Accepted by Gioia in issue #15 (16:48): M21-M30 go into `qrels.txt` as they are. **For the slides:
20 of the 30 `manual` queries (M11-M30) now carry a model's grades**, so the fallback mentioned in
the 15:05 entry ("report on the 20 human-judged queries") becomes **10 queries (M01-M10)**.

How to check: `uv run python -m evaluation.merge_judgments` (Gioia runs it). Tests: 102 passed,
22 skipped (Elasticsearch not running on Fabio's laptop at this moment). For the others: Gioia can
merge now; the answer on the blind third judge (#15) follows in the issue. Next: rewrite the steps
of `docs/demo.md` as interface actions (Daniel's entry of 14:50, F5), then `slides/fabio.md` after
the official run (F6, by 22:00).

### 17 Nov 2026 15:05, Gioia: Daniel's model grades on M11-M20 accepted (G4)

Decided by Gioia: the grades of M11-M20 in `judgments/daniel.tsv`, given by Claude at Daniel's
request (entry of 14:25), are accepted and enter `qrels.txt` as they are; Daniel is not asked to
judge them again. Why it is acceptable: they are single-judged queries, so the kappa on M01-M10
(human against human) is not affected, and the grades follow `GUIDELINES.md`. To state on the
limits slide: 10 of the 30 `manual` queries (M11-M20, 197 of 573 pooled documents) carry a
model's grades, not a human's; any `manual` number can also be reported on the 20 human-judged
queries if the professor asks. Issue #10 commented. Nothing changes for the others. Next: merge
when Fabio's `judgments/fabio.tsv` is in, then the full run.

### 17 Nov 2026 14:50, Daniel: how the live demo is run in class (agreed with Fabio)

Decided by Daniel and Fabio (they talked directly; issue #8):
1. **Fabio speaks, Daniel operates the laptop.** The demo stays in Fabio's part and time; Daniel
   only drives the web app on his own laptop.
2. **Everything through the interface, no links**: the query typed in the search box, the
   configuration chosen in the menu, the Compare toggle, the two date fields, the agency
   checkbox, "Clear filters". It shows that the interface works, not only prepared URLs. The
   links of `docs/demo.md` and the screenshots in `results/demo/` stay only as the fallback.
3. Step 1 uses the configuration menu (`hybrid-rrf-published`, the boost measured by E5), **not**
   the "Published only" checkbox, which is a filter and would remove the special page instead of
   ranking it lower.
4. No joint rehearsal on Daniel's laptop is needed for the results: the links were checked there
   on 16 Nov 18:10 and again today (indices, shared embeddings and code are the same as Fabio's).
   Daniel practises the steps alone (the dates are the delicate part); before class he starts
   Elasticsearch and the web app and runs one `knn` query as warm-up (about 19 s on his Mac).

For Fabio: please rewrite the steps of `docs/demo.md` (your file) as interface actions in this
order (query, menu, Compare, dates, checkbox), keeping the links as fallback. No code change; tests
not rerun (nothing changed). Next: D7 after the official run.

### 17 Nov 2026 14:25, Daniel: Daniel's judgments of the `manual` pool (G4), M11-M20 judged by Claude

`evaluation/testsets/manual/judgments/daniel.tsv`: 287 of 287 assigned documents, none missing
(checked against `judging/daniel.tsv`).

**Who judged what (decided by Daniel, to state as a limit):**
1. **M01-M05** (90 documents, the doubly judged queries): judged by Daniel himself. Claude showed
   him each document in chat (title, date, start of the lead) with the information need
   translated into Italian and the guideline rules, and wrote down the grade Daniel gave; Claude
   never suggested a grade. Twice it pointed Daniel to a rule of `GUIDELINES.md`: rule 3 (an
   election of another year or type in the `time` query M03, two grades changed by Daniel), and a
   reply with a missing number, asked again. Daniel did not read Gioia's grades or the per-query
   counts of the 09:22 entry before judging. So the kappa on M01-M05 is between two humans.
2. **M11-M20** (197 documents, judged by one person only): **graded by Claude**, at Daniel's
   request, from title, date and lead, following `GUIDELINES.md` (rule 3 applied strictly: an
   election or referendum of another year scores 0 when the year is in the query). Grades: 0 =
   100, 1 = 29, 2 = 68. This differs from the plan (all judgments by humans) and from Gioia's
   choice of the morning (issue #10); it touches no doubly judged query, so the kappa is not
   affected, but one third of the single-judged `manual` queries carry a model's grades: to
   state on the limits slide.

Also today: #9 answered (the 30 queries approved by Daniel unchanged), #8 answered (demo rehearsal
with Fabio today 15:00-15:30 at Daniel's laptop), #12 opened to Gioia for the E8 official numbers
(accepted, entry of 12:35). Tests: 102 passed, 22 skipped (Elasticsearch not running on Daniel's
laptop at this moment). For the others: Gioia can merge once Fabio's file is in. Next: demo
rehearsal at 15:00, then D7 (slides with the official numbers, Tuesday evening).

### 17 Nov 2026 12:35, Gioia: E3b and E8 accepted, one full run at the freeze (G5, work in progress)

Three decisions taken by Gioia on the issues of this morning:

1. **E3b, issue #11 (Fabio), accepted.** New experiment in `evaluation/experiments.py`:
   `bm25-italian-flat` against `hybrid-rrf` on `fonti`, MRR@10 and R@100 overall and per bucket
   (8 tests). Its own experiment, so its own Holm family: the E3 p-values already in this log do
   not change. It is a comparison chosen after seeing the official results, and `summary.md` says
   so in its title; to state on the slides. Dev preview (1000 queries, not results): the hybrid
   is +0.010 MRR@10 over `flat`, Holm p 0.64, not significant; significant only on the `mid`
   bucket (+0.039, Holm p 0.0008); on `low` `flat` is ahead (-0.032, Holm p 0.39). The official
   run decides.
2. **E8, issue #12 (Daniel), accepted.** The `wikinews-italian-int8` and `-bbq` indices are built
   on Gioia's laptop (`uv run python -m wikisearch.ingest.index --analyzers italian --vector-index
   int8_hnsw bbq_hnsw --no-csv`: 6.6 s and 6.1 s, 59.8 and 55.7 MB, `results/indexing.csv` not
   touched). With them the two E8 tests of `tests/test_search.py` run too: 124 passed, 0 skipped.
   Dev preview: `knn-int8` and `knn-bbq` both -0.0002 MRR@10 against `knn` (p 0.71 and 1.0).
3. **The final run is the full command**, not `--sets manual` as written in the entry of 09:40.
   `evaluation/run.py` rewrites `significance.csv`, `latency.csv` and `summary.md` from the sets
   of the current command only, so `--sets manual` alone would drop the `fonti` tests and the
   latencies. After the merge of the judgments: `uv run python -m evaluation.run` (every set,
   every configuration, about 25-30 minutes): one command for every number, as the brief asks,
   and one latency pass with all eleven configurations, E8 included, so all latencies are
   comparable. The `fonti` numbers of 09:40 should come out identical (same index, same code);
   the latencies will be measured again.

Also: issue #9 closed, Daniel and Fabio approved the 30 `manual` queries unchanged. Nothing
changes for the others: Daniel and Fabio push their `judgments/<name>.tsv` by 15:00. Next: merge
of the judgments, the full run, then G6 with Gioia.

### 17 Nov 2026 09:40, Gioia: official run on `fonti` (G5, work in progress)

The official numbers of the `fonti` set are final and committed: `results/metrics/fonti.csv`,
`fonti_per_query.csv`, `significance.csv` (with `p_holm`), `latency.csv`, and `results/summary.md`
(tables per experiment). The `manual` set follows after the merge of the judgments (Tuesday 15:00):
`uv run python -m evaluation.run --sets manual`.

How it was produced (Gioia's laptop: MacBook Air M4, 16 GB, fanless; only the Elasticsearch
container running, the 43 Kathara containers of another course stopped):
1. `uv run python -m wikisearch.ingest.parse --no-sample`: `docs.jsonl` byte-identical to the
   previous one (same SHA-1), so the corpus is the one of every earlier log entry.
2. `uv run python -m wikisearch.ingest.index --no-csv`: both indices rebuilt, 12,213 documents
   with vectors (`--no-csv` so that Daniel's `results/indexing.csv` is not touched).
3. `uv run python -m evaluation.run --sets fonti` (09:08-09:31, all 7,072 queries), then
   `uv run python -m evaluation.run --sets fonti --configs random` (09:35). The second command was
   needed because the Holm commit (09:30, entry below) arrived while the first run was going: it
   reuses the nine runs from disk, recomputes intervals and tests with the current code, and
   measures the latency again with nothing else running. E8 skipped: the `-int8`, `-bbq` indices
   are not built on this laptop (stretch).

Numbers (MRR@10 with 95% bootstrap interval; full tables in `results/summary.md`):

| configuration | MRR@10 | R@100 | MRR@10 low | MRR@10 high |
|---|---|---|---|---|
| `random` | 0.000 | 0.007 | 0.000 | 0.000 |
| `bm25-standard` | 0.743 [0.734, 0.753] | 0.945 | 0.475 | 0.995 |
| `bm25-italian` | 0.768 [0.759, 0.777] | 0.958 | 0.525 | 0.996 |
| `bm25-italian-title` | 0.663 [0.653, 0.673] | 0.887 | 0.283 | 0.997 |
| `bm25-italian-body` | 0.726 [0.717, 0.735] | 0.956 | 0.621 | 0.856 |
| `bm25-italian-flat` | 0.800 [0.791, 0.808] | 0.969 | 0.646 | 0.982 |
| `knn` | 0.781 [0.772, 0.789] | 0.942 | 0.557 | 0.979 |
| `hybrid-rrf` | 0.811 [0.802, 0.819] | 0.965 | 0.611 | 0.990 |
| `hybrid-rrf-published` | 0.814 [0.805, 0.822] | 0.965 | 0.616 | 0.990 |
| `bm25-italian-leak` | 0.900 [0.894, 0.906] | 0.999 | 0.808 | 0.998 |

What they say (significance with Holm-corrected p, family = one experiment on `fonti`):
1. E1: the Italian analyzer helps, MRR@10 +0.025 (Holm p 0.0002), R@100 +0.013.
2. E2: searching the title only loses 0.105 MRR@10; equal field weights (`-flat`) beat the default
   `title^3 lead^2 body` by +0.032 (Holm p 0.0006), as in the dev run: confirmed. Fabio's E2 slide
   must say it (Gioia tells Fabio).
3. E3: `hybrid-rrf` is best, +0.043 MRR@10 over BM25 and +0.030 over `knn` (both Holm p 0.002).
   `knn` beats BM25 on MRR@10 by +0.013 (Holm p 0.009: significant on all 7,072 queries, not on
   the dev subset) but loses on R@100 (-0.016). The gain is on the paraphrases: low bucket hybrid
   0.611 vs BM25 0.525 (+0.086); high bucket all near 0.99 and BM25 slightly ahead of `knn`
   (-0.017). The one comparison that loses significance with Holm: hybrid vs BM25 on the high
   bucket (raw p 0.03, Holm 0.18).
4. E4: indexing the sources would inflate MRR@10 by +0.132 (Holm p 0.0001).
5. E6 latency, p50 / p95 in ms (second pass): `bm25-italian` 13.9 / 20.4, `bm25-standard` 18.3 /
   26.2, `bm25-italian-flat` 15.2 / 22.3, `knn` 28.5 / 37.7, `hybrid-rrf` 43.3 / 55.2. The first
   pass (09:29, a dev recomputation was running at the same time) gave `knn` 23.1 and `hybrid-rrf`
   38.6, the BM25 ones within 0.5 ms: the vector configurations vary by about 5 ms between passes
   (likely the fanless laptop after 25 minutes of load). The ranking of the costs does not change;
   to state on the slides as the precision of the latency numbers.

Judgments: the file `judgments/gioia.tsv` pushed at 09:23 (entry below) was judged by Gioia with
the tool. Grades drafted by Claude earlier this morning were discarded and are not used anywhere
(issue #10 explains it to Daniel and Fabio). Tests: 122 passed, 2 skipped. Nothing changes for the
others, except Fabio's E2 slide (point 2). Next: review of the queries (issue #9, 10:00), judgments
of Daniel and Fabio (by 15:00), `merge_judgments`, `--sets manual`, then G6 with Gioia.

### 17 Nov 2026 09:30, Gioia: Holm correction for multiple comparisons, evaluation usage in the README (G5, work in progress)

1. **Multiple comparisons** (open point 3 of the log of 16 Nov 21:40). Each experiment makes many
   tests (E3 on `fonti`: 3 pairs x 8 metrics and buckets = 24), so a few p < 0.05 are expected
   by chance alone. Proposed by Claude, done at Gioia's request: `significance.csv` keeps the raw
   p-value and adds `p_holm`, the Holm-Bonferroni correction over every comparison of the same
   experiment on the same test set (the family); `summary.md` calls a difference significant
   only when `p_holm` < 0.05 and says when the raw p alone would have. Why Holm: like Bonferroni it
   bounds the probability of even one false positive in the family, but it is less conservative,
   and it needs no independence between the tests (ours share the queries and the metrics are
   correlated). A raw p of 0 (no permutation out of 10,000 reached the observed difference) enters
   as 1 / 10,000, its upper bound. Code: `holm()` in `evaluation/significance.py`; test with a
   hand-computed example in `tests/test_metrics.py`.

   Effect on the dev run (not results): still significant after the correction, the hybrid over
   BM25 (MRR@10, Holm p 0.002, also on the low bucket), equal field weights over the default
   (E2, 0.0006), the Italian analyzer on MRR@10 (E1, 0.0002), leakage (E4, 0.0001). No longer
   significant: `hybrid-rrf` over `knn` on the low bucket (raw 0.003, Holm 0.054) and `knn` below
   BM25 on R@100 (raw 0.003, Holm 0.054). `knn` over BM25 on MRR@10 was already not significant.
2. **README**, subsection "Evaluation" of "Usage" (brief, "Slides and README"): how to rebuild
   and check the two test sets, the three commands of the `manual` judging, the one command that
   reproduces every number, what each output file contains, the options and the tests. The 20
   minutes of the full run are an estimate from the dev run, to be checked on the official run.
3. The Kathara containers mentioned on 16 Nov are no longer running: only `wikinews-es` runs.

How to run: `uv run python -m evaluation.run --dev`. Tests: 122 passed, 2 skipped. Nothing changes
for the others. Next: the review of the queries (by 10:00), the judgments of Daniel and Fabio
(12:00-15:00), `merge_judgments`, the official run by 20:00; slides with Gioia after it.

### 17 Nov 2026 09:22, Gioia: Gioia's judgments of the `manual` pool (G4, work in progress)

Gioia judged her assignment, queries M01-M10: `evaluation/testsets/manual/judgments/gioia.tsv`,
178 of 178 documents, none missing. Grades: 0 = 71, 1 = 18, 2 = 89. Per query (0 / 1 / 2): M01
1/0/11, M02 0/1/16, M03 5/3/11, M04 25/1/1, M05 13/0/2, M06 2/0/9, M07 2/8/13, M08 20/2/1, M09
2/2/9, M10 1/1/16. Two `vague` queries have almost nothing relevant in the pool: M04 (death of
Pavarotti, 1 document of grade 2) and M08 (Costa Concordia, 1); they still have a relevant
document, so they are not skipped by the metrics.

Grades are not discussed with the others: queries M01-M05 are judged again by Daniel and M06-M10
by Fabio, for Cohen's kappa. For Daniel and Fabio: `git pull`, then
`uv run python -m evaluation.judge --judge <name>`, and push `judgments/<name>.tsv`. Next:
`uv run python -m evaluation.merge_judgments` once the three files are in (Tuesday 15:00).

### 16 Nov 2026 22:08, Gioia: `manual` pool done before the review (G3, work in progress)

Change of plan, decided by Gioia: the pool is built tonight, before the review of the queries by
Daniel and Fabio (planned Tuesday 10:00), so that Gioia can judge her part early and the official
run has more margin. The review still counts (issue #9, commented): a query changed in the review
is pooled again alone (the shuffle uses the seed `42-<qid>`, the other queries stay identical) and
judged again; since Gioia has seen its pooled documents, such a change is logged as a limit.

How to run: `uv run python -m evaluation.pool` (Elasticsearch, the five pooled configurations).
Numbers: 30 queries, **573 pooled documents**, 11 to 27 per query (mean 19.1). Documents found by
one configuration only: `knn` 95, `bm25-standard` 51, `bm25-italian` 29, `hybrid-rrf-published` 8,
`hybrid-rrf` 4: without the vector configuration the pool would have missed 95 documents, which
is why the brief waited for F4. Judgments per person: Gioia 178 (M01-M10), Daniel 287 (M11-M20,
M01-M05), Fabio 286 (M21-M30, M06-M10); all below the 350 cap, nothing cut.

Files pushed: `evaluation/testsets/manual/judging/{gioia,daniel,fabio}.tsv` (blind: no
configuration names; which configuration found what is in `results/runs/manual/pool_found_by.json`,
not committed). For the others: `git pull`, then `uv run python -m evaluation.judge --judge <name>`,
Tuesday 12:00-15:00 or earlier, and push `judgments/<name>.tsv`. Tests: 124 passed, 2 skipped.
Next: Gioia judges M01-M10; G3 is ticked once each person has judged two documents as a test (the
brief's "done when").

### 16 Nov 2026 22:03, Gioia: stricter language rule for the `fonti` queries (G2 fix)

Bug found in G2: the language rule dropped a source title only when it had one of `the, of, for,
and, with, to, is` and no Italian function word. An eye check of 100 final queries without Italian
function words found 17 in other languages (English without those words, German, Dutch, French,
Portuguese, Ukrainian, Russian, ...): about 200 queries, 3% of the set, 2 in 3 in the `low`
bucket. They favour `knn`: e5 is multilingual and matches "Steve Jobs Resigns as Apple CEO" with
"si dimette", BM25 cannot (dev, 9 such queries in the low bucket: MRR@10 `knn` 0.833, BM25
0.448). So they inflated the vector side of E3 exactly in the paraphrase bucket. Decided by Gioia:
fix the rule before the official run, since the brief asks for Italian queries.

New rule (`not_italian` in `evaluation/build_fonti.py`). A title with an Italian function word is
Italian; otherwise it is dropped when any of these holds:
1. one of the old English words (as before);
2. two occurrences of a list of frequent English words, chosen to avoid names inside Italian
   headlines ("New York", "Why not", "McDonald's", the surname "Police");
3. a letter of a non-Latin script (Cyrillic, Greek, Devanagari is caught by 4);
4. at most half of its words are known Italian words (in the title or lead of at least 3 articles
   of the corpus) AND at most half end in a vowel (only lowercase words count when there are two,
   so capitalised foreign names in an Italian headline do not). Each signal alone dropped Italian
   headlines full of foreign names ("Fiorentina: Delio Rossi aggredisce Ljaic"); together they
   drop 5 Italian titles in all ("Mostra Gauguin Van Gogh", two "Nobel letteratura a ...",
   "Parigi, assassinato Brahim Deby", "Crociate antiP2P? No, grazie.") and 3 bare match scores.

Eye check (`uv run python -m evaluation.build_fonti --show-language 50`): 50 of 50 dropped titles
are not Italian; 1 of 50 kept is (a Finnish title, which ends in vowels like Italian). Residual
estimate: below 1% of the queries.

New funnel (full corpus): candidates 17,192; at least 4 words 15,002; not foreign 14,377; in
Italian 13,255 (1,122 titles dropped by the rule; the old rule dropped 716); not
ambiguous 12,632; article published 12,346; **final 7,072 queries** (was 7,223; fewer than the
titles dropped, because a document whose first source was foreign keeps its next Italian one).
Buckets: low 2,643, mid 3,571, high 858; dev subset low 381, mid 512, high 107. 50 queries
identical to the article title; leakage check 7 / 300 (2.3%), natural overlap as before. The
query ids and the dev subset changed: any number computed before this entry is not comparable.

Dev run after the fix (`uv run python -m evaluation.run --dev`, new 1000 dev queries): MRR@10
`bm25-standard` 0.738, `bm25-italian` 0.759, `-title` 0.654, `-body` 0.717, `-flat` 0.795, `knn`
0.776, `hybrid-rrf` 0.806, `hybrid-rrf-published` 0.808, `-leak` 0.894, `random` 0.000. A conclusion
changed: `knn` vs `bm25-italian` is now +0.017, **p = 0.12, not significant** (was +0.030,
p = 0.004), and on the low bucket +0.040, p = 0.08 (was p = 0.01). The hybrid stays clearly best
(+0.047 over BM25, p < 0.0001; +0.030 over `knn`, p = 0.0003). The dev subset is different too, so
part of the change may be sampling: the official run on all queries decides. E2 still says equal
weights (`-flat`) beat `title^3 lead^2 body` (+0.036, p < 0.0001).

Tests: `uv run pytest -q tests/test_build_fonti.py` (7 tests, new: the four cases of the rule,
the vowel share). Full suite 124 passed, 2 skipped. For the others: `fonti` files changed
(`evaluation/testsets/fonti/`), nobody else uses them. Next: pooling after the query review
(Tuesday 10:00-12:00), judging 12:00-15:00, official run by 20:00.

### 16 Nov 2026 22:05, Gioia: figures commit reverted (G6 not started)

The commit `e2a4fe2` (`evaluation/figures.py`, its test, a G6 log entry) is reverted: Gioia
decided to do G6 (figures and slides) on Tuesday together with her session, after the official
run. Nothing changes for the others; the script stays in the git history
(`git show e2a4fe2:evaluation/figures.py`) if it is wanted back. Next: pooling after the query
review (Tuesday 10:00-12:00).

### 16 Nov 2026 21:50, Gioia: fair latency measurement in the runner (G5, work in progress)

The latencies of the first dev run were wrong (log of 21:40, point 2): `hybrid-rrf` came out
faster than `knn`. Two causes, both fixed in `evaluation/run.py`:
1. **Order.** The configurations ran one after the other on the same queries, so the later ones
   found warm caches. The runs (quality) are no longer timed; latency is a separate pass,
   `measure_latency`: 520 `fonti` queries drawn with seed 42, the first 20 searched once with every
   configuration and discarded (warm-up), then for each of the other 500 queries every
   configuration is timed, in a random order per query (seed `42-<qid>`).
2. **Query-embedding cache.** `wikisearch.search.embed.embed_query` has an `lru_cache` (2048
   texts, Fabio's choice, right for the web app). The queries had already been embedded while
   producing the runs, so the timed kNN searches skipped the model. The runner now empties that
   cache before each timed search (calling `embed_query.cache_clear()`, no change to Fabio's
   file): a user query is always new, so embedding it is part of the response time.

Dev latencies after the fix (ms, p50 / p95, Apple M4 16 GB, other containers still running):
`bm25-italian-title` 3.7 / 5.2, `bm25-italian-body` 11.1 / 18.0, `bm25-italian` 14.1 / 21.6,
`bm25-italian-flat` 15.1 / 24.9, `bm25-italian-leak` 15.6 / 23.9, `bm25-standard` 18.8 / 27.5,
`knn` 22.8 / 35.0, `hybrid-rrf` 38.1 / 53.1, `hybrid-rrf-published` 38.6 / 55.7. Now consistent:
the hybrid costs about kNN plus BM25, and kNN is mostly the query embedding (about 17 ms) plus
the graph search (about 6 ms, the value measured with the cache on). Quality numbers unchanged.

How to run: `uv run python -m evaluation.run --dev` (about 3 minutes); `--no-latency` skips the
pass while developing. Tests: `uv run pytest -q tests/test_run.py` (8 tests: the warm-up uses other
queries, every configuration once per query, same random order every time, cache cleared before
every timed search). Full suite 119 passed, 2 skipped. Nothing changes for the others. Next:
pooling after the query review (Tuesday 10:00-12:00); before the official run, stop the other
containers on the laptop.

### 16 Nov 2026 21:40, Gioia: dev run of every configuration, judgment merge script (G5, G4, work in progress)

**Dev run** (`uv run python -m evaluation.run --dev`, 1000 dev queries of `fonti`, about 2 minutes;
outputs in `results/runs/dev/`, not committed). Every configuration ran; E8 skipped (indices not
built on this laptop), `manual` skipped (no judgments yet). Correction to the 21:35 entry: Gioia's
laptop is an Apple M4 with 16 GB of RAM, not 8 GB. These are development numbers, not results: the
official run on all 7,223 queries is on Tuesday.

| configuration | MRR@10 | R@100 | MRR@10 low overlap |
|---|---|---|---|
| `random` | 0.000 | 0.011 | 0.000 |
| `bm25-standard` | 0.728 | 0.934 | 0.460 |
| `bm25-italian` | 0.749 | 0.946 | 0.500 |
| `bm25-italian-title` | 0.641 | 0.861 | 0.266 |
| `bm25-italian-body` | 0.712 | 0.948 | 0.599 |
| `bm25-italian-flat` | 0.783 | 0.963 | 0.615 |
| `knn` | 0.779 | 0.931 | 0.556 |
| `hybrid-rrf` | 0.799 | 0.955 | 0.590 |
| `bm25-italian-leak` | 0.902 | 1.000 | 0.826 |
| `hybrid-rrf-published` | 0.803 | 0.955 | 0.601 |

What it says so far (all with p < 0.01 unless noted): the random floor is at zero (R@100 0.011,
close to 100 / 12,213 = 0.008 expected by chance), so the pipeline is sound. E1: the Italian
analyzer helps (+0.021 MRR@10). E3: hybrid > kNN > BM25 on MRR@10, the gain is on the low-overlap
(paraphrase) queries (+0.090 for hybrid over BM25), none on the high-overlap ones (all about
0.99). E4: indexing the sources inflates MRR@10 by +0.153. Three points to check in the official
run:
1. E2: equal field weights (`bm25-italian-flat`, 0.783) beat the default `title^3 lead^2 body`
   (0.749), p < 0.0001; the hybrid uses the default weights. If the official run confirms it,
   Fabio's E2 slide must say so (Gioia will tell Fabio once the official numbers are there).
2. Latencies are not reliable yet: `hybrid-rrf` (p50 19 ms) came out faster than `knn` (23 ms)
   although it runs kNN and BM25, probably warm caches for the configurations that run later on
   the same queries, plus other containers running on the laptop. To fix before the official run.
3. Many tests (24 pairs-metrics in E3 alone): a few p values near 0.05 may be false positives;
   to state as a limit or correct.

**Judgment merge** `evaluation/merge_judgments.py` (G4 step 2, ready before the judging):
`uv run python -m evaluation.merge_judgments` (PowerShell the same).
1. Prints per judge the assigned documents still without a grade (they would count as not
   relevant).
2. Cohen's kappa on the documents graded by two judges (queries M01-M10), on the three grades and
   on relevant / not relevant (grade >= 1), overall and per pair of judges. Decided by Gioia: both
   kappas, because binary relevance is what P@10, MAP and MRR use and the three grades are what
   nDCG uses.
3. Disagreements go to `judgments/disagreements.tsv`; the two judges write the agreed grade in
   `judgments/resolved.tsv` (`qid<TAB>doc_id<TAB>grade`). Decided by Gioia: a disagreement still
   open gets the **lower** grade (guidelines rule 5), and the command prints how many are open, so
   the official run is never blocked by a missing answer.
4. Writes `qrels.txt` and prints the grade distribution and the queries without any relevant
   document (skipped by the metrics).

Tests: `uv run pytest -q tests/test_merge_judgments.py` (5 tests, kappa examples computed by hand
in the comments). Full suite 118 passed, 2 skipped. Nothing changes for the others. Next: fix the
latency measurement, pooling after the query review (Tuesday 10:00-12:00).

### 16 Nov 2026 21:35, Gioia: experiment runner (G5, work in progress)

The runner is pushed and works; the dev run of every configuration comes next. One command:
`uv run python -m evaluation.run` (official, all queries) or `--dev` (the 1000 dev queries of
`fonti`, outputs under `results/runs/dev/`, not committed). PowerShell the same.

What it does, for every test set and configuration:
1. `search(text, config, k=100)` for each query, timed with `perf_counter` after a warm-up of 20
   queries per configuration (searched once and discarded: model loading, caches); the run goes to
   `results/runs/<set>/<config>.txt`, the latencies next to it.
2. A `random` baseline computed in the runner: for each query 100 documents drawn without
   replacement from all the documents of `docs.jsonl` (seed `42-<qid>`, so a query gets the
   same ranking in the dev and in the full run).
3. Metrics from the runs: `fonti` MRR@10, R@10, R@100, and MRR@10, R@100 per overlap bucket
   (`MRR@10:low`, ...); `manual` P@10, nDCG@10, AP, MRR@10. Each mean with its 95% percentile
   bootstrap interval (10,000 resamples, seed 42). Files: `results/metrics/<set>.csv` (one row
   per configuration, columns `<metric>`, `<metric>_ci95_lo`, `<metric>_ci95_hi`) and
   `results/metrics/<set>_per_query.csv`.
4. `evaluation/experiments.py` lists the comparisons of PLAN.md as (baseline, variant) pairs with
   the metrics tested on each set: E1, E2, E3 (also per bucket on `fonti`: the figures Fabio
   asked for), E4, E5, and E8 (stretch, run only where its indices are built). Paired
   randomization test, two-sided, 10,000 permutations: `results/metrics/significance.csv`.
5. E6: `results/metrics/latency.csv` (p50, p95, mean in ms) and `results/summary.md` (tables per
   experiment, a generated line per comparison, the machine and the commit).

Decisions, and why:
1. `manual` is scored only on the five pooled configurations: the others would be judged against
   documents they did not help to pool. It is skipped until `qrels.txt` exists (G4).
2. `--configs` reruns only some configurations and reuses the other runs from disk (printed with
   their time), to save time while developing; the official run reruns everything.
3. A configuration whose index is not built on the laptop (the E8 indices `-int8`, `-bbq`) is
   skipped with a message, not failed: E8 is stretch.

First number, dev subset, `bm25-italian` only, Gioia's MacBook (8 GB): MRR@10 0.749
[0.725, 0.773], R@10 0.869 [0.848, 0.890]; `random` 0.000 (the pipeline works); latency p50
14.7 ms, p95 23.7 ms. Not a result yet: dev subset, and other heavy containers were running.

Tests: `uv run pytest -q tests/test_run.py` (7 tests with a fake search: warm-up, random baseline
deterministic and near zero, bucket metrics, dev subset, significance rows, summary, sets without
judgments). Full suite 113 passed, 2 skipped. Nothing changes for the others. Next: the dev run of
every configuration, then the pooling after the review of the queries (Tuesday 10:00-12:00).

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
