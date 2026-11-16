"""Merge the judgments of the `manual` test set into `qrels.txt` and measure the agreement.

    uv run python -m evaluation.merge_judgments

Reads every assignment `evaluation/testsets/manual/judging/<name>.tsv` and the grades
`judgments/<name>.tsv` written by `python -m evaluation.judge`, then:

1. reports, per judge, how many assigned documents are still without a grade (they are left out of
   `qrels.txt`, so the metrics count them as not relevant: finish them before the official run);
2. on the documents graded by two judges (queries 1-10), Cohen's kappa on the three grades and on
   relevant / not relevant (grade >= 1), overall and per pair of judges;
3. writes the disagreements to `judgments/disagreements.tsv`, for the two judges to decide
   together. The agreed grade goes in `judgments/resolved.tsv` (`qid<TAB>doc_id<TAB>grade`); a
   disagreement not resolved there gets the lower of the two grades (GUIDELINES.md, rule 5: when
   in doubt, the lower grade), and the command says how many are still open;
4. writes `qrels.txt` (`qid 0 doc_id grade`) and prints the grade distribution and the queries
   without any relevant document (no metric is defined for them: they are skipped).
"""

import argparse
from collections import Counter
from pathlib import Path

from evaluation.judge import MANUAL_DIR, read_assignment, read_judgments
from evaluation.pool import JUDGES

GRADES = [0, 1, 2]


def cohen_kappa(a: list[int], b: list[int], labels: list[int]) -> float:
    """(p_o - p_e) / (1 - p_e): observed agreement corrected by the agreement expected by chance
    from the two judges' own grade distributions."""
    if len(a) != len(b) or not a:
        raise ValueError("need two non-empty lists of grades of the same documents")
    n = len(a)
    p_o = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    p_e = sum(ca[label] * cb[label] for label in labels) / (n * n)
    return 1.0 if p_e == 1 else (p_o - p_e) / (1 - p_e)


def binary(grades: list[int]) -> list[int]:
    return [1 if g >= 1 else 0 for g in grades]


def read_resolved(path: Path) -> dict[tuple[str, str], int]:
    resolved = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("qid\t"):
                qid, doc_id, grade = line.split("\t")[:3]
                resolved[(qid, doc_id)] = int(grade)
    return resolved


def merge(grades_by_judge: dict[str, dict[tuple[str, str], int]], resolved: dict[tuple[str, str], int]):
    """Returns (qrels, double, disagreements, unresolved).

    double: (qid, doc_id) -> [(judge, grade), (judge, grade)] in the order of JUDGES;
    disagreements: the keys of `double` with two different grades; unresolved: those not in
    `resolved`, which got the lower grade."""
    by_pair: dict[tuple[str, str], list[tuple[str, int]]] = {}
    order = {j: i for i, j in enumerate(JUDGES)}
    for judge in sorted(grades_by_judge, key=lambda j: order.get(j, len(order))):
        for key, grade in grades_by_judge[judge].items():
            by_pair.setdefault(key, []).append((judge, grade))
    qrels: dict[str, dict[str, int]] = {}
    double, disagreements, unresolved = {}, [], []
    for key, graded in sorted(by_pair.items()):
        values = [g for _, g in graded]
        if len(graded) >= 2:
            double[key] = graded[:2]
        if len(set(values)) > 1:
            disagreements.append(key)
            if key in resolved:
                grade = resolved[key]
            else:
                unresolved.append(key)
                grade = min(values)
        else:
            grade = values[0]
        qid, doc_id = key
        qrels.setdefault(qid, {})[doc_id] = grade
    return qrels, double, disagreements, unresolved


def agreement(double: dict) -> dict[str, tuple[int, float, float, float]]:
    """Group ("all" and each pair of judges) -> (documents, raw agreement, kappa on the three
    grades, kappa on relevant / not relevant)."""
    groups: dict[str, list[tuple[int, int]]] = {"all": []}
    for graded in double.values():
        (ja, ga), (jb, gb) = graded
        groups["all"].append((ga, gb))
        groups.setdefault(f"{ja}-{jb}", []).append((ga, gb))
    out = {}
    for name, pairs in groups.items():
        if not pairs:
            continue
        a, b = [x for x, _ in pairs], [y for _, y in pairs]
        raw = sum(x == y for x, y in pairs) / len(pairs)
        out[name] = (len(pairs), raw, cohen_kappa(a, b, GRADES), cohen_kappa(binary(a), binary(b), [0, 1]))
    return out


def write_qrels(path: Path, qrels: dict[str, dict[str, int]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for qid in sorted(qrels):
            for doc_id in sorted(qrels[qid]):
                f.write(f"{qid} 0 {doc_id} {qrels[qid][doc_id]}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=Path, default=MANUAL_DIR)
    args = parser.parse_args()

    assigned, grades_by_judge = {}, {}
    for path in sorted((args.dir / "judging").glob("*.tsv")):
        judge = path.stem
        assigned[judge] = read_assignment(path)
        grades_by_judge[judge] = read_judgments(args.dir / "judgments" / f"{judge}.tsv")

    print("Judgments per person:")
    titles = {}
    for judge, items in assigned.items():
        todo = {(it["qid"], it["doc_id"]) for it in items}
        titles.update({(it["qid"], it["doc_id"]): it["title"] for it in items})
        # grades for documents not assigned to this judge (a wrong --judge) are ignored
        grades_by_judge[judge] = {k: g for k, g in grades_by_judge[judge].items() if k in todo}
        missing = len(todo) - len(grades_by_judge[judge])
        flag = f"  {missing} STILL TO JUDGE (they count as not relevant)" if missing else ""
        print(f"  {judge:7s} {len(grades_by_judge[judge]):4d} / {len(todo):4d}{flag}")

    resolved = read_resolved(args.dir / "judgments" / "resolved.tsv")
    qrels, double, disagreements, unresolved = merge(grades_by_judge, resolved)

    print(f"Agreement on the {len(double)} documents graded by two judges:")
    for name, (n, raw, k3, k2) in agreement(double).items():
        print(f"  {name:13s} {n:4d} documents  raw agreement {raw:.3f}  "
              f"kappa (0/1/2) {k3:.3f}  kappa (relevant or not) {k2:.3f}")

    dis_path = args.dir / "judgments" / "disagreements.tsv"
    dis_path.parent.mkdir(parents=True, exist_ok=True)
    with dis_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("qid\tdoc_id\ttitle\tjudge_a\tgrade_a\tjudge_b\tgrade_b\tresolved\n")
        for key in disagreements:
            (ja, ga), (jb, gb) = double[key]
            f.write(f"{key[0]}\t{key[1]}\t{titles.get(key, '')}\t{ja}\t{ga}\t{jb}\t{gb}\t"
                    f"{resolved.get(key, '')}\n")
    print(f"Disagreements: {len(disagreements)}, resolved {len(disagreements) - len(unresolved)}, "
          f"still open {len(unresolved)} (they get the lower grade); list in {dis_path.name}")

    write_qrels(args.dir / "qrels.txt", qrels)
    dist = Counter(g for rels in qrels.values() for g in rels.values())
    print(f"qrels.txt: {len(qrels)} queries, {sum(dist.values())} judged documents, "
          f"grades 0: {dist[0]}, 1: {dist[1]}, 2: {dist[2]}")
    empty = sorted(q for q, rels in qrels.items() if not any(g >= 1 for g in rels.values()))
    if empty:
        print(f"Queries without any relevant document (skipped by the metrics): {', '.join(empty)}")


if __name__ == "__main__":
    main()
