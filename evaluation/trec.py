"""Read and write the TREC file formats of docs/contracts.md, section 5.

queries.tsv  qid<TAB>text<TAB>meta (meta is JSON)
qrels.txt    qid 0 doc_id grade
run          qid Q0 doc_id rank score tag
"""

import json
from pathlib import Path


def read_queries(path: Path | str) -> dict[str, tuple[str, dict]]:
    """qid -> (text, meta)."""
    queries: dict[str, tuple[str, dict]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        qid, text, meta = line.split("\t")
        queries[qid] = (text, json.loads(meta))
    return queries


def read_qrels(path: Path | str) -> dict[str, dict[str, int]]:
    """qid -> {doc_id: grade}."""
    qrels: dict[str, dict[str, int]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        qid, _, doc_id, grade = line.split()
        qrels.setdefault(qid, {})[doc_id] = int(grade)
    return qrels


def read_run(path: Path | str) -> dict[str, list[str]]:
    """qid -> doc ids sorted by rank (best first)."""
    rows: dict[str, list[tuple[int, str]]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        qid, _, doc_id, rank, _score, _tag = line.split()
        rows.setdefault(qid, []).append((int(rank), doc_id))
    return {qid: [doc_id for _, doc_id in sorted(pairs)] for qid, pairs in rows.items()}


def write_run(path: Path | str, results: dict[str, list[tuple[str, float]]], tag: str) -> None:
    """Write a run. `results` is qid -> [(doc_id, score), ...] already sorted best first;
    ranks are assigned from 1 in that order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for qid, hits in results.items():
            for rank, (doc_id, score) in enumerate(hits, start=1):
                f.write(f"{qid} Q0 {doc_id} {rank} {score:.6f} {tag}\n")
