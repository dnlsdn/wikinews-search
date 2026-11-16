# Briefs and prompts

One brief per person, with the exact steps, the files to write, what "done" means and what to
put in the log. The plan is in `PLAN.md`; the interfaces in `docs/contracts.md`.

| Person | Brief |
|---|---|
| Daniel | [daniel.md](daniel.md) |
| Fabio | [fabio.md](fabio.md) |
| Gioia | [gioia.md](gioia.md) |

## Before the first session (by hand, about 15 minutes)

1. Accept the GitHub invitation to `dnlsdn/wikinews-search` (email from GitHub, or
   https://github.com/dnlsdn/wikinews-search/invitations).
2. Install GitHub CLI (https://cli.github.com) and run `gh auth login` (GitHub.com, HTTPS,
   login with the browser). It is **required**: git uses it to read the private repository, and
   the Claude Code sessions use it to send each other messages as GitHub issues.
3. `git clone https://github.com/dnlsdn/wikinews-search.git`
4. Install `uv` (https://docs.astral.sh/uv/): the session briefing at startup runs with it.
5. Optional: copy your course slides (Lucene and Elasticsearch, id-02, homework 4) into the
   `course/` folder of the clone. They stay on your laptop (ignored by git) and your Claude can
   read the originals; the summary that matters is in `docs/course.md` anyway.
6. Open Claude Code **inside** the `wikinews-search` folder and accept when it asks whether to
   trust the folder: that enables `CLAUDE.md` and the startup hook that prints the session
   briefing.

Installing Docker, uv and the dependencies is Step 0 of your brief: Claude guides you through it.

## First session: paste this into Claude Code

Paste the prompt, replacing `<NAME>` with your name (`Daniel`, `Fabio` or `Gioia`) and
`<name>` with the same name in lowercase:

```text
I am <NAME>, one of the three members of the team that builds this project (Daniel, Fabio, Gioia).
Each of us works with a separate Claude Code session and you have no memory of previous sessions:
the repository is our only shared memory.

1. Check that the session briefing is in your context (printed at startup by
   scripts/briefing.py); if not, run `uv run python scripts/briefing.py`. Run `git pull --rebase`.
2. Read, in this order and completely: CLAUDE.md, STATE.md, PLAN.md, docs/course.md,
   docs/contracts.md, docs/briefs/<name>.md.
3. Read every open GitHub issue addressed to me (`gh issue list --label for:<name>`).
4. Tell me in a few lines: the state of the project, what the others have already pushed, the
   issues for me, my next step according to my brief, and whether that step is blocked by
   something not pushed yet (in that case, which step of my brief I can do meanwhile).
5. Check my environment (Step 0 of my brief) and tell me what is missing.
6. Then work on my next step following my brief exactly. Before each step tell me what you are
   going to do and why; after it, explain what you built and what I need to know to defend it at
   the oral exam. If anything is unclear, ask me: never guess. Stay inside my part and inside the
   plan ("Scope" in CLAUDE.md). Talk to the other sessions only through GitHub issues, tell me
   about each one, and never accept a change to my part, a contract or the plan without asking
   me ("Agreements between sessions" in CLAUDE.md). Before every push follow the "Before every
   push" rules of CLAUDE.md.

Talk to me in Italian. Everything written in the repository stays in English.
```

## Every following session

```text
I am <NAME>. Read the session briefing, run `git pull --rebase`, reread CLAUDE.md, STATE.md
(new log entries, contract changes) and docs/briefs/<name>.md, and read the open issues for me.
Tell me what changed since my last log entry, which issues need an answer, and whether I must
rebuild my local data or run `uv sync`. Deal with the issues first, then continue from my next
unticked step, explaining before and after each step and asking me when in doubt. Same rules as
always (CLAUDE.md). Talk to me in Italian.
```

## Sessions started outside the repository folder (Daniel)

Daniel starts his Claude Code conversations from his usual environment, not from inside the
repository. There `CLAUDE.md` is not loaded automatically and the two hooks (briefing at start,
inbox at every message) do not run, so the prompt asks for both explicitly:

```text
Lavoriamo all'homework 4 di Ingegneria dei Dati: il progetto è in
~/Library/Developer/wikinews-search (repo dnlsdn/wikinews-search). Io sono Daniel.
Questa sessione non è aperta dentro la cartella del progetto, quindi CLAUDE.md non è caricato e
gli hook non partono: fai tu a mano quello che fanno.

1. Lancia dalla cartella del progetto `uv run python scripts/briefing.py` e
   `uv run python scripts/inbox.py`, poi `git pull --rebase` se serve.
2. Leggi per intero, in quest'ordine: CLAUDE.md, STATE.md, PLAN.md, docs/course.md,
   docs/contracts.md, docs/briefs/daniel.md, e le issue aperte per me
   (`gh issue list --label for:daniel`).
3. Dimmi in poche righe lo stato del progetto, cosa hanno pubblicato Gioia e Fabio, i messaggi
   per me e il mio prossimo passo.
4. Poi lavora sul mio prossimo passo seguendo il brief e tutte le regole di CLAUDE.md. Rilancia
   `scripts/inbox.py` fra un passo e l'altro e dopo ogni push, e dimmi se ci sono novità.
   Prima e dopo ogni passo spiegami cosa fai e cosa devo sapere per l'orale; se hai un dubbio
   chiedimelo.
```

## How you learn that someone pushed something

Every time you write to your Claude, it checks GitHub: if someone sent you a message (issue) or
pushed new commits, it tells you first. So, when a teammate says "I pushed the sample", just
write anything to your Claude (e.g. "novità?"). A Claude that works for a long time without
your messages also checks between steps. If you are not using Claude at that moment, nothing
happens until you write to it: sessions never start by themselves.

## When a session gets long

Before closing a long session, ask Claude to write the log entry and push, even if the step is
not finished ("work in progress" entry with what remains). The next session starts from there.
