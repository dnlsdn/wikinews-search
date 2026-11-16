# State

Shared memory of the project. Read it before starting, update it before every push
(rules in `CLAUDE.md`). Newest log entry first.

## Current state

| Part | Owner | State |
|---|---|---|
| Repository, plan, contracts, skeleton | Daniel | done (16 Nov) |
| Data and indexing | Daniel | not started: next step D1 |
| Search and interface | Fabio | not started: next step F3a (web skeleton with fake search), then F1 once D2-D3 are pushed |
| Evaluation | Gioia | not started: next step G1 (does not need the corpus), then writing the 30 queries of G3 |

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

None yet.

## Requests

None yet.

## Log

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
