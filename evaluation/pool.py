"""Pool the documents to judge for the `manual` test set.

    uv run python -m evaluation.pool

For every query of `evaluation/testsets/manual/queries.tsv`: the top 10 of each of the five
configurations the `manual` set compares (E1, E3, E5), merged, deduplicated and shuffled (seed 42
and the qid), so the judge cannot tell which system found what. Writes one assignment file per
judge, `evaluation/testsets/manual/judging/<name>.tsv` (`qid, query, doc_id, title, date, lead,
url`, header line, tab separated, UTF-8), read by `python -m evaluation.judge`.

Assignment: the queries in file order are split in three parts of 10, one per judge; queries 1-10
are also judged by a second judge (1-5 by the second judge of the list, 6-10 by the third), to
measure agreement. Needs Elasticsearch, the full indices and every configuration (F4).
"""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from evaluation.judge import ASSIGNMENT_COLUMNS, MANUAL_DIR
from evaluation.trec import read_queries
from wikisearch import config

POOL_CONFIGS = ["bm25-standard", "bm25-italian", "knn", "hybrid-rrf", "hybrid-rrf-published"]
DEPTH = 10
SEED = 42
JUDGES = ["gioia", "daniel", "fabio"]
PART = 10
DOUBLE = 10  # the first DOUBLE queries get a second judge
MAX_PER_JUDGE = 350


def assign(qids: list[str], judges: list[str] = JUDGES) -> dict[str, list[str]]:
    """judge -> qids to judge, in query order. See the module docstring."""
    out: dict[str, list[str]] = {j: [] for j in judges}
    for i, qid in enumerate(qids):
        out[judges[min(i // PART, len(judges) - 1)]].append(qid)
    double = qids[:DOUBLE]
    half = (len(double) + 1) // 2
    for qid in double[:half]:
        out[judges[1]].append(qid)
    for qid in double[half:]:
        out[judges[2]].append(qid)
    order = {qid: i for i, qid in enumerate(qids)}
    return {j: sorted(q, key=order.get) for j, q in out.items()}


def pool(queries: dict[str, tuple[str, dict]], search, configs: list[str] = POOL_CONFIGS,
         depth: int = DEPTH) -> tuple[dict[str, list[str]], dict[str, dict[str, list[str]]]]:
    """qid -> shuffled doc ids; and qid -> doc_id -> configurations that retrieved it."""
    pooled: dict[str, list[str]] = {}
    found_by: dict[str, dict[str, list[str]]] = {}
    for qid, (text, _) in queries.items():
        by_doc: dict[str, list[str]] = defaultdict(list)
        for cfg in configs:
            for hit in search(text, cfg, k=depth):
                by_doc[hit.id].append(cfg)
        docs = sorted(by_doc)
        random.Random(f"{SEED}-{qid}").shuffle(docs)
        pooled[qid] = docs
        found_by[qid] = dict(by_doc)
    return pooled, found_by


def one_line(text: str | None) -> str:
    return " ".join((text or "").split())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=Path, default=MANUAL_DIR)
    parser.add_argument("--configs", nargs="+", default=POOL_CONFIGS,
                        help="only if a configuration is missing (log it as a limit)")
    args = parser.parse_args()

    from wikisearch.search import search

    queries = read_queries(args.dir / "queries.tsv")
    pooled, found_by = pool(queries, search, args.configs)

    docs = {}
    needed = {d for ids in pooled.values() for d in ids}
    with config.DOCS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            if doc["id"] in needed:
                docs[doc["id"]] = doc

    assignment = assign(list(queries))
    (args.dir / "judging").mkdir(parents=True, exist_ok=True)
    for judge, qids in assignment.items():
        path = args.dir / "judging" / f"{judge}.tsv"
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(ASSIGNMENT_COLUMNS) + "\n")
            for qid in qids:
                for doc_id in pooled[qid]:
                    d = docs[doc_id]
                    row = [qid, queries[qid][0], doc_id, d["title"], d["date"] or "", d["lead"], d["url"]]
                    f.write("\t".join(one_line(v) for v in row) + "\n")

    sizes = [len(ids) for ids in pooled.values()]
    print(f"{len(queries)} queries, {sum(sizes)} pooled documents "
          f"(per query: min {min(sizes)}, mean {sum(sizes) / len(sizes):.1f}, max {max(sizes)})")
    only = Counter()
    for by_doc in found_by.values():
        for cfgs in by_doc.values():
            if len(cfgs) == 1:
                only[cfgs[0]] += 1
    print("Documents found by one configuration only:")
    for cfg in args.configs:
        print(f"  {cfg:22s} {only[cfg]:5d}")
    print("Judgments per person:")
    for judge, qids in assignment.items():
        n = sum(len(pooled[q]) for q in qids)
        flag = "  MORE THAN %d: cut the doubly judged queries first" % MAX_PER_JUDGE if n > MAX_PER_JUDGE else ""
        print(f"  {judge:7s} {len(qids):3d} queries {n:5d} documents{flag}")

    # Which configuration found what: kept out of the repository (results/runs/ is ignored),
    # so that the judges stay blind; used later to see what each system adds to the pool.
    out = config.ROOT / "results" / "runs" / "manual" / "pool_found_by.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(found_by, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {args.dir / 'judging'} and {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
