"""The `manual` metrics on the human-judged queries only (M01-M10), a robustness check.

    uv run python -m evaluation.manual_human

20 of the 30 `manual` queries (M11-M30) carry grades given by a model (STATE.md, log of 17 Nov,
issue #15); M01-M10 were judged by two people each (disagreements adjudicated by a third judge).
This script recomputes the `manual` means, their 95% bootstrap intervals and the comparisons of
E1, E3 and E5 on M01-M10 only, to show whether the conclusions hold without the model's grades.

No search is run: it reads the per-query scores of the official run
(`results/metrics/manual_per_query.csv`) and writes `results/metrics/manual_human.csv` and
`results/metrics/manual_human_significance.csv`, in the same format as `manual.csv` and
`significance.csv` (Holm correction within each experiment on these 10 queries).
"""

import csv
from pathlib import Path

from evaluation.run import (METRICS, RESULTS, metrics_rows, significance_rows, summarize,
                            write_csv)

HUMAN_QUERIES = {f"M{i:02d}" for i in range(1, 11)}


def read_per_query(path: Path, keep: set[str]) -> dict[str, dict[str, dict[str, float]]]:
    """config -> qid -> {metric: score}, only for the queries in `keep`."""
    out: dict[str, dict[str, dict[str, float]]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["qid"] not in keep:
                continue
            out.setdefault(row["config"], {})[row["qid"]] = {m: float(row[m]) for m in METRICS["manual"]}
    return out


def main() -> None:
    metrics_dir = RESULTS / "metrics"
    per_query_by_config = read_per_query(metrics_dir / "manual_per_query.csv", HUMAN_QUERIES)
    summaries = {name: summarize("manual", pq) for name, pq in per_query_by_config.items()}
    write_csv(metrics_dir / "manual_human.csv", metrics_rows("manual", summaries))
    sig = significance_rows("manual", per_query_by_config)
    write_csv(metrics_dir / "manual_human_significance.csv", sig)

    print(f"manual, human-judged queries only ({len(HUMAN_QUERIES)}):")
    for name, s in summaries.items():
        print("  " + f"{name:22s}" + "  ".join(f"{m} {s[m][0]:.3f} [{s[m][1]:.3f}, {s[m][2]:.3f}]"
                                              for m in METRICS["manual"] if m in s))
    for r in sig:
        print(f"  {r['experiment']} {r['metric']}: {r['variant']} vs {r['baseline']} "
              f"{r['diff']:+.4f} (p {r['p_value']}, Holm p {r['p_holm']})")


if __name__ == "__main__":
    main()
