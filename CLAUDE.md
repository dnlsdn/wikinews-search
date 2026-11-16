# Instructions for Claude Code (every team member's session)

Three people (Daniel, Fabio, Gioia) build this project in parallel, each with their own Claude Code
session on their own laptop and account. Sessions cannot talk to each other directly and do not
share memory. They share two things, and only these:

1. **the repository** (`STATE.md`, `PLAN.md`, `docs/`): the shared memory, what is true now;
2. **GitHub issues** of `dnlsdn/wikinews-search`: the messages between sessions, what someone
   needs from someone else.

Follow these rules exactly.

## Before doing anything

1. At session start a hook runs `scripts/briefing.py` and puts a **session briefing** in your
   context: who your user is, whether the local copy is behind, the latest log entries, your next
   step, the issues addressed to you. If you do not see it, run
   `uv run python scripts/briefing.py` yourself.
2. `git pull --rebase` if the briefing says you are behind.

   A second hook runs `scripts/inbox.py` **every time your user sends a message**: if new issues
   for your user (or new blockers and contract changes) or new commits arrived since the last
   check, a "TEAM INBOX" note appears in your context. Tell your user about it before anything
   else, and deal with it as described below. When it prints nothing, there is no news.
3. Read, in this order: `STATE.md`, `PLAN.md`, `docs/course.md` (what the course and the
   professor expect: methods, metrics, statistical robustness), `docs/contracts.md`, then the
   brief of your user
   in `docs/briefs/` (`daniel.md`, `fabio.md`, `gioia.md`): it says exactly what to build, step
   by step, and when a step is done.
4. Read every open issue addressed to your user (`gh issue view <n>`) and deal with it **before**
   continuing your step (answer, fix, or say in the issue when it will be done).
5. Work on your user's **next unticked step**. If it depends on something not pushed yet, the
   brief says what to do meanwhile.

## Working with your user

Your user is a student who will **defend this work alone at the oral exam**: the professor asks
about the design choices and above all about the experimental evaluation. A result your user
cannot explain is worth nothing. So:

1. **Before** each step, say in a few lines what you are about to do and why, in plain words.
2. **After** each step, explain what was built, the decisions taken and their reasons, and what
   your user should know to explain it at the exam (two or three key points).
3. **When in doubt, ask. Never guess.** Ask your user before: any decision the brief does not
   settle, any change to the plan or to a contract, deleting or overwriting data, anything that
   takes long or uses a lot of disk or memory (downloads, the embedding job, rebuilding indices).
   Pushing and opening issues as described here need no extra permission, but tell your user
   each time.
4. Talk to your user in Italian, briefly and concretely; no walls of text.

## Agreements between sessions

The sessions negotiate with each other through issues, but **the humans decide**.

1. A session may propose anything in an issue. The receiving session never accepts a request
   that changes its user's part, a contract or the plan without asking its user first; it
   explains the request to its user, then answers in the issue with the decision and who took it
   ("Accepted by Fabio", "Fabio prefers X because ...").
2. When two sessions disagree, they do not go back and forth: each writes its reasons once in
   the issue and tells its user, and the humans decide.
3. Every agreement that changes something for the others is written in the log of `STATE.md`
   (and under "Contract changes" if it touches a contract).

## Scope: stay on the plan

Follow the course: use the methods, terms and metrics of `docs/course.md`, and when a choice
   departs from them, write why in the log. If the course material is in `course/` (local only),
   you may read it; never commit it.

1. Do only what your user's brief and the issues addressed to them ask. Do not add features,
   pages, configurations or refactorings that are not in the plan, even if they look useful:
   propose them to your user, and if the group agrees they go in `PLAN.md` first.
2. Stretch items (marked "stretch" or "optional") only after every other step of your brief is
   ticked.
3. Do not edit files owned by another person (table in `PLAN.md`). If something there must
   change, open an issue for that person (below). A one-line fix that unblocks you is allowed
   only if you say it in the issue and in the log.
4. If your user asks for something outside the plan or outside their part, say so clearly and
   ask whether to proceed; if it affects others, it needs an issue.
5. Check the date and time against the timeline in `PLAN.md`. If your user is late on a
   milestone, tell them, and drop stretch items before anything else.
6. When unsure what the plan means, do not guess: ask your user, or open an issue to the owner.

## Talking to the other sessions (GitHub issues)

Use `gh` (GitHub CLI). Labels: `for:daniel`, `for:fabio`, `for:gioia`, `blocker`,
`contract-change`.

1. **Ask someone for something**: `gh issue create --label for:<name> --title "<short>" --body "<message>"`.
   The body must be self-contained, because the other session knows nothing of yours: what you
   need, why, which files or fields, an example, by when, and what you will do meanwhile. Add the
   label `blocker` if you cannot continue without it.
2. **Answer**: `gh issue comment <n> --body "..."`. When the work is pushed, put
   `Closes #<n>` in the commit message (the issue closes itself on push) or close it with a
   comment saying which commit fixed it.
3. **Change a contract** (`docs/contracts.md`, `wikisearch/schema.py`, `wikisearch/config.py`,
   `wikisearch/search/configs.py` names, `pyproject.toml` dependencies): open an issue with the
   label `contract-change` and the three `for:` labels except your own, describing the change
   and what the others must do (e.g. `uv sync`, rebuild the indices); write it also under
   "Contract changes" in `STATE.md`. Close the issue when the others have acknowledged it with a
   comment.
4. Never wait idle for an answer: continue with another step of your brief.
5. Tell your user in chat about every issue you open or receive: the humans also talk to each
   other directly.

`STATE.md` is not for messages: it says what is true now (state, log, contract changes).

## While working

1. The Macs (Daniel, Gioia) have 8 GB of RAM and little disk: Elasticsearch runs with a 1 GB
   heap, never start Kibana, do not run heavy jobs while other heavy things run.
2. Never commit `data/raw/`, `data/processed/`, `results/runs/` or model files (see
   `.gitignore`). Committed on purpose: the sample (`data/sample/`), the shared embeddings
   (`data/shared/`), metrics, figures and reports in `results/`.
3. Everything in the repository is in English: code, comments, README, commit messages, issues,
   UI text. No emoji. **One exception:** `slides/` holds the content of the presentation, which is
   in Italian (see "Slides" in `PLAN.md`).
4. The team uses macOS (Daniel, Gioia) and Windows (Fabio). Code must run on both: open text
   files with `encoding="utf-8"` explicitly (the Windows default is not UTF-8 and the data is
   full of accents), build paths with `pathlib`, no shell scripts (use Python modules run with
   `uv run python -m ...`). When you give a command to a Windows user, give the PowerShell form
   (e.g. `$env:WIKISEARCH_FAKE=1` instead of `WIKISEARCH_FAKE=1 ...`, `curl.exe` instead of
   `curl`).
5. Dependencies are already declared in `pyproject.toml` for every planned step. Do not add new
   ones unless really needed; if you do, use `uv add`, commit `uv.lock` in the same commit, and
   treat it as a contract change.
6. `tests/test_contracts.py` checks the interfaces between the parts (sample documents, shared
   embeddings, test set files, `search()` results). Never weaken or skip it to make your push
   pass: if it fails, either your change breaks a contract (fix it) or the contract must change
   (issue `contract-change`).
7. The presentation must not show code: keep design decisions and their reasons in the log, they
   become the slides.
8. After `git pull`, if the log says the parser, the mapping or the embeddings changed, rebuild
   your local data before measuring anything: `uv run python -m wikisearch.ingest.parse`, then
   `uv run python -m wikisearch.ingest.index`.

## Before every push (mandatory)

1. Run the tests: `uv run pytest -q` (and the step's own check, if any).
2. `git pull --rebase` **before** writing the log, so you write on top of the latest entries.
3. Add an entry at the top of the "Log" in `STATE.md` with: date and time, who, which step,
   what was done, **how to run it**, what changed for the others, the numbers obtained (if any),
   decisions taken and why, issues opened or closed, next step. Write it so that a session that
   has never seen this project can continue from it.
4. Update your own row of "Current state" in `STATE.md`, and tick the step in `PLAN.md` only if
   its "done when" holds.
5. Small commits with English messages (`ingest: extract news date from the data template`).
   Do not add `Co-Authored-By` trailers.
6. `git push`. If it is rejected, `git pull --rebase` and push again. Never force-push `main`.
7. Conflicts: in `STATE.md` keep **both** log entries (newest first) and every row of the table;
   in `uv.lock` take the incoming version and run `uv lock`; anywhere else, stop and ask your
   user.
8. If what you pushed unblocks someone, comment on their issue or open one for them
   (`for:<name>`): "the sample is pushed, you can start F1" (see "Handoffs" in `PLAN.md`).
9. After pushing, and between steps when you work for a long time without messages from your
   user, run `uv run python scripts/inbox.py`: messages may have arrived while you worked (the
   hook only fires when your user writes). Tell your user about anything it prints.

## Commands

| What | Command |
|---|---|
| session briefing | `uv run python scripts/briefing.py` |
| news since the last check | `uv run python scripts/inbox.py` (prints nothing if there is none) |
| messages for me | `gh issue list --label for:<name>` |
| install or update dependencies | `uv sync` |
| start Elasticsearch | `docker compose up -d`, check with `curl localhost:9200` (Windows: `curl.exe localhost:9200`) |
| stop Elasticsearch | `docker compose down` (the index survives in the volume) |
| parse the dump | `uv run python -m wikisearch.ingest.parse` |
| index | `uv run python -m wikisearch.ingest.index` |
| web app | `uv run uvicorn wikisearch.web.app:app --reload`, then http://localhost:8000 |
| experiments | `uv run python -m evaluation.run` |
| tests | `uv run pytest -q` |
