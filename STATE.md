# State

Shared memory of the project. Read it before starting, update it before every push
(rules in `CLAUDE.md`). Newest log entry first.

## Current state

| Part | Owner | State |
|---|---|---|
| Repository, plan, contracts, skeleton | Daniel | done (16 Nov) |
| Data and indexing | Daniel | not started: next step D1 |
| Search and interface | Fabio | not started: next step F1 (on the sample, once D2 is pushed) |
| Evaluation | Gioia | not started: next step G1 (does not need the corpus) |

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
