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
2. Make git able to read the private repository: install GitHub CLI and run `gh auth login`
   (on Windows, Git Credential Manager also works: it opens the browser at the first clone).
3. `git clone https://github.com/dnlsdn/wikinews-search.git`
4. Open Claude Code **inside** the `wikinews-search` folder, so it reads `CLAUDE.md`.

Installing Docker, uv and the dependencies is Step 0 of your brief: Claude guides you through it.

## First session: paste this into Claude Code

Paste the prompt, replacing `<NAME>` with your name (`Daniel`, `Fabio` or `Gioia`) and
`<name>` with the same name in lowercase:

```text
I am <NAME>, one of the three members of the team that builds this project (Daniel, Fabio, Gioia).
Each of us works with a separate Claude Code session and you have no memory of previous sessions:
the repository is our only shared memory.

1. Run `git pull --rebase`.
2. Read, in this order and completely: CLAUDE.md, STATE.md, PLAN.md, docs/contracts.md,
   docs/briefs/<name>.md.
3. Tell me in a few lines: the state of the project, what the others have already pushed, my next
   step according to my brief, and whether that step is blocked by something not pushed yet
   (in that case, which step of my brief I can do meanwhile).
4. Check my environment (Step 0 of my brief) and tell me what is missing.
5. Then work on my next step following my brief exactly, explaining what you do as you go.
   Stay inside my directories. Before every push follow the "Before every push" rules of
   CLAUDE.md, including the log entry in STATE.md.

Talk to me in Italian. Everything written in the repository stays in English.
```

## Every following session

```text
I am <NAME>. Run `git pull --rebase`, reread CLAUDE.md, STATE.md (new log entries, requests,
contract changes) and docs/briefs/<name>.md, tell me what changed since my last log entry and
whether I must rebuild my local data or run `uv sync`, then continue from my next unticked step.
Same rules as always (CLAUDE.md). Talk to me in Italian.
```

## When a session gets long

Before closing a long session, ask Claude to write the log entry and push, even if the step is
not finished ("work in progress" entry with what remains). The next session starts from there.
