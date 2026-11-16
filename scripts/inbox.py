"""Inbox check, run every time the user sends a message to Claude Code (UserPromptSubmit hook).

Prints something only when there is news since the last check: new GitHub issues addressed to
the user (or blockers and contract changes for everyone), or new commits on GitHub. Otherwise it
prints nothing, so it does not clutter the session. Standard library only; it never fails.
The list of issues already reported is kept in .git/wikisearch-inbox.json (never committed).
"""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / ".git" / f"wikisearch-inbox{os.environ.get('WIKISEARCH_GITHUB', '')}.json"
TEAM = {"dnlsdn": "daniel", "fmdimarco": "fabio", "gioburattii": "gioia"}
REPO = "dnlsdn/wikinews-search"


def run(args: list[str], timeout: int = 10) -> str:
    try:
        out = subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=timeout
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def main() -> None:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    login = os.environ.get("WIKISEARCH_GITHUB") or state.get("login") or run(["gh", "api", "user", "--jq", ".login"])
    me = TEAM.get(login)
    if not me:
        return
    state["login"] = login
    seen = set(state.get("seen", []))

    news = []
    raw = run(["gh", "issue", "list", "-R", REPO, "--state", "open", "--limit", "50",
               "--json", "number,title,labels,author,updatedAt"])
    if raw:
        for issue in json.loads(raw):
            labels = {lab["name"] for lab in issue["labels"]}
            if f"for:{me}" not in labels and not labels & {"blocker", "contract-change"}:
                continue
            key = f"{issue['number']}@{issue['updatedAt']}"
            if key in seen:
                continue
            seen.add(key)
            news.append(f"  #{issue['number']} [{', '.join(sorted(labels))}] {issue['title']} "
                        f"(from {issue['author']['login']}, new or updated)")

    run(["git", "fetch", "--quiet"], timeout=15)
    behind = run(["git", "rev-list", "--count", "HEAD..@{u}"])
    head = run(["git", "rev-parse", "@{u}"])
    new_commits = behind not in ("", "0") and head != state.get("reported_head")
    if new_commits:
        state["reported_head"] = head
        log = run(["git", "log", "--format=  %h %an: %s", "-n", "5", "HEAD..@{u}"])

    state["seen"] = sorted(seen)[-200:]
    try:
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass

    if not news and not new_commits:
        return
    print(f"TEAM INBOX for {me.capitalize()} (scripts/inbox.py). Tell your user about this before "
          "anything else, then follow CLAUDE.md.")
    if news:
        print("GitHub issues new or updated since the last check (read them with `gh issue view <n>`):")
        print("\n".join(news))
    if new_commits:
        print(f"GitHub has {behind} new commit(s) not in your copy; `git pull --rebase` when your "
              "current change is committed, then read the new log entries in STATE.md:")
        print(log)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
