# Instructions for Claude Code (every team member's session)

Three people (Daniel, Fabio, Gioia) build this project in parallel, each with their own Claude Code
session. Sessions do not share memory: **the repository is the only shared memory**. Follow these
rules exactly.

## Before doing anything

1. `git pull --rebase`.
2. Read, in this order: `STATE.md` (current state, last log entries, open requests),
   `PLAN.md` (who owns what, the steps, the deadline), `docs/contracts.md` (the interfaces),
   then the brief of your user in `docs/briefs/` (`daniel.md`, `fabio.md`, `gioia.md`): it says
   exactly what to build, step by step, and when a step is done.
3. Ask your user which person they are if it is not obvious, and work on **that person's next
   unticked step**, unless the user asks otherwise. If the step depends on something not pushed
   yet, the brief says what to do meanwhile.

## While working

1. Stay inside the owner's directories (table in `PLAN.md`). If something outside them must change,
   write it under "Requests" in `STATE.md` instead of editing it, unless it is a one-line fix that
   unblocks you; in that case say so in the log.
2. Never change a contract silently. A change to `docs/contracts.md`, `wikisearch/schema.py` or
   `wikisearch/config.py` goes under "Contract changes" in `STATE.md`, and your user must tell the
   group.
3. The Mac of at least one member has 8 GB of RAM and little disk: Elasticsearch runs with a 1 GB
   heap, never start Kibana, do not run heavy jobs (embeddings) while other heavy things run.
4. Never commit `data/raw/`, `data/processed/`, `results/runs/` or model files (see
   `.gitignore`). Committed on purpose: the sample (`data/sample/`), the shared embeddings
   (`data/shared/`), metrics, figures and reports in `results/`.
5. Everything in the repository is in English: code, comments, README, commit messages, UI text.
   No emoji. **One exception:** `slides/` holds the content of the presentation, which is in
   Italian (see "Slides" in `PLAN.md`).
6. The team uses macOS (Daniel, Gioia) and Windows (Fabio). Code must run on both: open text
   files with `encoding="utf-8"` explicitly (the Windows default is not UTF-8 and the data is
   full of accents), build paths with `pathlib`, no shell scripts (use Python modules run with
   `uv run python -m ...`). When you give a command to a Windows user, give the PowerShell form
   (e.g. `$env:WIKISEARCH_FAKE=1` instead of `WIKISEARCH_FAKE=1 ...`, `curl.exe` instead of
   `curl`).
7. Dependencies are already declared in `pyproject.toml` for every planned step. Do not add new
   ones unless really needed; if you do, use `uv add`, commit `uv.lock` in the same commit, and
   log it under "Contract changes" (the others must run `uv sync`).
8. The presentation must not show code: keep design decisions and their reasons in the log, they
   become the slides.
9. After `git pull`, if the log says the parser, the mapping or the embeddings changed, rebuild
   your local data before measuring anything: `uv run python -m wikisearch.ingest.parse`, then
   `uv run python -m wikisearch.ingest.index`.

## Before every push (mandatory)

1. Run the tests: `uv run pytest -q` (and the step's own check, if any).
2. `git pull --rebase` **before** writing the log, so you write on top of the latest entries.
3. Add an entry at the top of the "Log" in `STATE.md` with: date and time, who, which step,
   what was done, **how to run it**, what changed for the others, the numbers obtained (if any),
   decisions taken and why, next step. Write it so that a session that has never seen this
   project can continue from it.
4. Update your own row of "Current state" in `STATE.md`, and tick the step in `PLAN.md` only if
   its "done when" holds.
5. Small commits with English messages (`ingest: extract news date from the data template`).
   Do not add `Co-Authored-By` trailers.
6. `git push`. If it is rejected, `git pull --rebase` and push again. Never force-push `main`.
7. Conflicts: in `STATE.md` keep **both** log entries (newest first) and every row of the table;
   in `uv.lock` take the incoming version and run `uv lock`; anywhere else, stop and ask your
   user.

## Commands

| What | Command |
|---|---|
| install or update dependencies | `uv sync` |
| start Elasticsearch | `docker compose up -d`, check with `curl localhost:9200` (Windows: `curl.exe localhost:9200`) |
| stop Elasticsearch | `docker compose down` (the index survives in the volume) |
| parse the dump | `uv run python -m wikisearch.ingest.parse` |
| index | `uv run python -m wikisearch.ingest.index` |
| web app | `uv run uvicorn wikisearch.web.app:app --reload`, then http://localhost:8000 |
| experiments | `uv run python -m evaluation.run` |
| tests | `uv run pytest -q` |
