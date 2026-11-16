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
4. Never commit `data/raw/`, `data/processed/` or model files (see `.gitignore`). Results
   (`results/`) and the small sample (`data/sample/`) are committed.
5. Everything in the repository is in English: code, comments, README, commit messages, UI text.
   No emoji. The presentation is in Italian and lives outside the repository.
6. The presentation must not show code: keep design decisions and their reasons in the log, they
   become the slides.

## Before every push (mandatory)

1. Run the tests: `uv run pytest -q` (and the step's own check, if any).
2. Append an entry at the top of the "Log" in `STATE.md` with: date and time, who, which step,
   what was done, **how to run it**, what changed for the others, the numbers obtained (if any),
   decisions taken and why, next step. Write it so that a session that has never seen this
   project can continue from it.
3. Update the "Current state" section of `STATE.md` if it changed, and tick the step in `PLAN.md`
   only if its "done when" holds.
4. Small commits with English messages (`ingest: extract news date from the data template`).
   Do not add `Co-Authored-By` trailers.
5. `git pull --rebase`, then `git push`. Never force-push `main`.

## Commands

| What | Command |
|---|---|
| install | `uv sync` (add `--extra embed` for the embedding model) |
| start Elasticsearch | `docker compose up -d`, check with `curl localhost:9200` |
| stop Elasticsearch | `docker compose down` (the index survives in the volume) |
| parse the dump | `uv run python -m wikisearch.ingest.parse` |
| index | `uv run python -m wikisearch.ingest.index` |
| web app | `uv run uvicorn wikisearch.web.app:app --reload`, then http://localhost:8000 |
| experiments | `uv run python -m eval.run` |
| tests | `uv run pytest -q` |
