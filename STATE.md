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

## Messages

Not here: messages between sessions are GitHub issues (`CLAUDE.md`, "Talking to the other
sessions"). The session briefing lists the open ones.

## Log

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
