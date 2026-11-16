"""Terminal tool to judge the pooled documents of the `manual` test set.

    uv run python -m evaluation.judge --judge gioia

Shows one document at a time (query, information need, title, date, lead) from
`evaluation/testsets/manual/judging/<name>.tsv` and appends every grade immediately to
`evaluation/testsets/manual/judgments/<name>.tsv` (`qid<TAB>doc_id<TAB>grade<TAB>time`), so it can
be stopped and resumed at any moment: it starts again at the first document without a grade. If a
document is graded twice (after going back), the last grade counts.

Keys (type one, then Enter; works the same in the macOS terminal and in Windows PowerShell):
  0, 1, 2   grade (see GUIDELINES.md)
  Enter     keep the current grade of a document already judged and go on
  o         open the article in the browser
  b         back to the previous document
  q         quit (everything graded so far is saved)
"""

import argparse
import sys
import textwrap
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Callable

from evaluation.trec import read_queries
from wikisearch import config

MANUAL_DIR = config.ROOT / "evaluation" / "testsets" / "manual"
ASSIGNMENT_COLUMNS = ["qid", "query", "doc_id", "title", "date", "lead", "url"]
GRADES = {"0", "1", "2"}
LEAD_CHARS = 900
WIDTH = 100


def read_assignment(path: Path) -> list[dict]:
    """Rows of an assignment file (header line first, tab separated, UTF-8)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    if header != ASSIGNMENT_COLUMNS:
        raise ValueError(f"{path}: unexpected header {header}")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:] if line.strip()]


def read_judgments(path: Path) -> dict[tuple[str, str], int]:
    """(qid, doc_id) -> grade; the last line for a pair wins."""
    judged: dict[tuple[str, str], int] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                qid, doc_id, grade = line.split("\t")[:3]
                judged[(qid, doc_id)] = int(grade)
    return judged


def first_unjudged(items: list[dict], judged: dict, start: int = 0) -> int | None:
    """Index of the first item from `start` (then from the beginning) without a grade."""
    for i in list(range(start, len(items))) + list(range(0, start)):
        if (items[i]["qid"], items[i]["doc_id"]) not in judged:
            return i
    return None


def show(item: dict, need: str, position: int, total: int, current: int | None, out: Callable) -> None:
    out("")
    out("=" * WIDTH)
    out(f"[{position}/{total}]  query {item['qid']}: {item['query']}")
    for line in textwrap.wrap(f"Need: {need}", WIDTH):
        out(line)
    out("-" * WIDTH)
    out(f"{item['title']}   ({item['date'] or 'no date'})")
    lead = item["lead"]
    if len(lead) > LEAD_CHARS:
        lead = lead[:LEAD_CHARS].rsplit(" ", 1)[0] + " ..."
    for line in textwrap.wrap(lead or "(no lead)", WIDTH):
        out(line)
    if current is not None:
        out(f"(already judged: {current})")


def judge_loop(
    items: list[dict],
    needs: dict[str, str],
    out_path: Path,
    ask: Callable[[str], str] = input,
    out: Callable[[str], None] = print,
    open_url: Callable[[str], object] = webbrowser.open,
) -> dict[tuple[str, str], int]:
    """Run the judging session; returns the grades after the session."""
    judged = read_judgments(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    i = first_unjudged(items, judged)
    if i is None:
        out(f"All {len(items)} documents are judged already.")
        return judged
    out(f"{len(judged)} of {len(items)} judged so far; starting at {i + 1}.")
    while i is not None:
        item = items[i]
        key = (item["qid"], item["doc_id"])
        show(item, needs.get(item["qid"], ""), i + 1, len(items), judged.get(key), out)
        try:
            answer = ask("Grade 0/1/2, o = open, b = back, q = quit: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "q"
        if answer == "q":
            out(f"Saved. {len(judged)}/{len(items)} judged.")
            return judged
        if answer == "o":
            open_url(item["url"])
            continue
        if answer == "b":
            i = max(i - 1, 0)
            continue
        if answer == "" and key in judged:
            answer = str(judged[key])
        elif answer not in GRADES:
            out("Type 0, 1 or 2 (or o, b, q).")
            continue
        if judged.get(key) != int(answer) or key not in judged:
            with out_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(f"{key[0]}\t{key[1]}\t{answer}\t{datetime.now().isoformat(timespec='seconds')}\n")
            judged[key] = int(answer)
        if i + 1 < len(items):
            i += 1
        else:
            i = first_unjudged(items, judged)
    out(f"Done: all {len(items)} documents judged. Commit and push {out_path}.")
    return judged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--judge", required=True, help="your name in lowercase: daniel, fabio or gioia")
    parser.add_argument("--dir", type=Path, default=MANUAL_DIR)
    args = parser.parse_args()
    # The data is full of accents: make sure printing them never fails (Windows consoles).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    items = read_assignment(args.dir / "judging" / f"{args.judge}.tsv")
    needs = {qid: meta.get("need", "") for qid, (_, meta) in read_queries(args.dir / "queries.tsv").items()}
    judge_loop(items, needs, args.dir / "judgments" / f"{args.judge}.tsv")


if __name__ == "__main__":
    main()
