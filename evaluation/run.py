"""Experiment runner: one command reproduces every number of the evaluation.

    uv run python -m evaluation.run            # official: every query of every test set
    uv run python -m evaluation.run --dev      # development: the 1000 dev queries of `fonti`

For every test set and configuration: `search(text, config, k=100)` for each query, and the run
written to `results/runs/<set>/<config>.txt`. Then, from the runs:

1. `results/metrics/<set>.csv`: one row per configuration (plus the `random` baseline), each mean
   with its 95% bootstrap interval (`<metric>_ci95_lo`, `<metric>_ci95_hi`); on `fonti` also per
   overlap bucket (`MRR@10:low`, ...).
2. `results/metrics/<set>_per_query.csv`: the per-query scores the intervals and tests use.
3. `results/metrics/significance.csv`: the pairs of `evaluation/experiments.py`, difference of the
   means and two-sided p-value of the paired randomization test.
4. `results/metrics/latency.csv`: p50 and p95 of the query latency, from a separate pass on 500
   `fonti` queries with the configurations in random order per query (`measure_latency`).
5. `results/summary.md`: the tables, with the machine the latencies were measured on.

`--dev` writes everything under `results/runs/dev/` (not committed). `--configs` reruns only some
configurations; the metrics are then computed from every run present for the set, the others
reused from disk (the command prints which). The `manual` set is skipped until its `qrels.txt`
exists (step G4). A configuration whose index is not built on this laptop (the E8 indices) is
skipped with a message.
"""

import argparse
import csv
import json
import os
import platform
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from evaluation.experiments import (BUCKET_METRICS, BUCKETS, EXPERIMENTS, MANUAL_CONFIGS, METRICS,
                                    RANDOM, TEST_SETS)
from evaluation.metrics import evaluate
from evaluation.significance import bootstrap_ci, paired_randomization_test
from evaluation.trec import read_qrels, read_queries, read_run, write_run
from wikisearch import config
from wikisearch.search.configs import CONFIGS

K = 100
WARMUP = 20
LATENCY_QUERIES = 500  # timed queries of `fonti` per configuration (E6)
LATENCY_SET = "fonti"
SEED = 42
N_RESAMPLES = 10000
ALPHA = 0.05
TESTSETS = config.ROOT / "evaluation" / "testsets"
RESULTS = config.ROOT / "results"


# --- inputs ------------------------------------------------------------------------------------


def load_set(name: str, dev: bool = False, root: Path = TESTSETS):
    """(queries, qrels) of a test set, or None when its judgments do not exist yet."""
    folder = root / name
    qrels_path = folder / "qrels.txt"
    if not qrels_path.exists():
        return None
    queries_file = "queries_dev.tsv" if dev and (folder / "queries_dev.tsv").exists() else "queries.tsv"
    return read_queries(folder / queries_file), read_qrels(qrels_path)


def all_doc_ids() -> list[str]:
    """Ids of every document of the corpus, the population of the random baseline."""
    ids = []
    with config.DOCS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            ids.append(json.loads(line)["id"])
    return sorted(ids)


def configs_for(set_name: str) -> list[str]:
    """`manual` is scored only on the configurations whose documents were pooled and judged."""
    return list(MANUAL_CONFIGS) if set_name == "manual" else list(CONFIGS)


def index_built(name: str) -> bool:
    from wikisearch.search import es

    cfg = CONFIGS[name]
    return bool(es.client().indices.exists(index=config.index_name(cfg["analyzer"], cfg.get("vector_index", "hnsw"))))


# --- runs --------------------------------------------------------------------------------------


def random_run(queries: dict, doc_ids: list[str], k: int = K) -> dict[str, list[tuple[str, float]]]:
    """For each query, k documents drawn at random without replacement (seed 42 and the qid, so a
    query gets the same ranking in the dev and in the full run)."""
    out = {}
    for qid in queries:
        docs = random.Random(f"{SEED}-{qid}").sample(doc_ids, min(k, len(doc_ids)))
        out[qid] = [(d, float(k - i)) for i, d in enumerate(docs)]
    return out


def run_config(queries: dict, name: str, search, k: int = K):
    """Search every query with one configuration (not timed: see `measure_latency`)."""
    results = {}
    for i, (qid, (text, _)) in enumerate(queries.items(), start=1):
        results[qid] = [(h.id, h.score) for h in search(text, name, k=k)]
        if i % 500 == 0:
            print(f"    {name}: {i}/{len(queries)}", flush=True)
    return results


def measure_latency(queries: dict, configs: list[str], search, n: int = LATENCY_QUERIES,
                    warmup: int = WARMUP, k: int = K, before_each=None) -> dict[str, list[float]]:
    """Latency in milliseconds of every configuration, measured in conditions that are the same
    for all of them. Measuring while producing the runs is unfair: the configurations run one after
    the other on the same queries, so the later ones find the caches warm (a first dev run timed
    `hybrid-rrf`, which runs kNN and BM25, faster than `knn` alone).

    So: `warmup + n` queries drawn at random (seed 42); the first `warmup` are searched once with
    every configuration and discarded (model loading, Elasticsearch and disk caches); then for each
    of the other `n` queries every configuration is timed, in a random order per query (seed 42 and
    the qid), so that no configuration always comes first or last.

    `before_each` is called before every timed search, untimed: the runner passes the clearing of
    the query-embedding cache of `wikisearch.search.embed`, which would otherwise hold the vectors
    computed while producing the runs and hide the cost of the model (a user query is always new)."""
    qids = sorted(queries)
    drawn = random.Random(SEED).sample(qids, min(len(qids), warmup + n))
    warm, timed = drawn[:warmup], drawn[warmup:]
    for qid in warm:
        for name in configs:
            search(queries[qid][0], name, k=k)
    latencies: dict[str, list[float]] = {name: [] for name in configs}
    for qid in timed:
        order = list(configs)
        random.Random(f"{SEED}-{qid}").shuffle(order)
        for name in order:
            if before_each is not None:
                before_each()
            t0 = time.perf_counter()
            search(queries[qid][0], name, k=k)
            latencies[name].append((time.perf_counter() - t0) * 1000)
    return latencies


# --- scores ------------------------------------------------------------------------------------


def score_run(set_name: str, queries: dict, qrels: dict, run: dict[str, list[str]]):
    """Per-query scores: qid -> {metric: score}. On `fonti` the bucket metrics (`MRR@10:low`) are
    present only for the queries of that bucket. Only the queries of `queries` are scored (the dev
    subset uses the full qrels)."""
    qrels = {qid: rels for qid, rels in qrels.items() if qid in queries}
    per_query, _ = evaluate(qrels, run, METRICS[set_name])
    if set_name == "fonti":
        for qid, scores in per_query.items():
            bucket = queries[qid][1].get("bucket")
            for m in BUCKET_METRICS:
                if bucket in BUCKETS:
                    scores[f"{m}:{bucket}"] = scores[m]
    return per_query


def metric_names(set_name: str) -> list[str]:
    names = list(METRICS[set_name])
    if set_name == "fonti":
        names += [f"{m}:{b}" for m in BUCKET_METRICS for b in BUCKETS]
    return names


def values(per_query: dict, metric: str) -> tuple[list[str], list[float]]:
    qids = sorted(q for q, s in per_query.items() if metric in s)
    return qids, [per_query[q][metric] for q in qids]


def summarize(set_name: str, per_query: dict, n_resamples: int = N_RESAMPLES) -> dict:
    """metric -> (mean, ci_low, ci_high, n queries)."""
    out = {}
    for m in metric_names(set_name):
        _, xs = values(per_query, m)
        if not xs:
            continue
        low, high = bootstrap_ci(xs, n=n_resamples, seed=SEED, alpha=ALPHA)
        out[m] = (float(np.mean(xs)), low, high, len(xs))
    return out


def significance_rows(set_name: str, per_query_by_config: dict, n_resamples: int = N_RESAMPLES):
    rows = []
    for exp in EXPERIMENTS:
        for metric in exp.metrics.get(set_name, []):
            for base, variant in exp.pairs:
                if base not in per_query_by_config or variant not in per_query_by_config:
                    continue
                qa, a = values(per_query_by_config[base], metric)
                qb, b = values(per_query_by_config[variant], metric)
                assert qa == qb, f"{base} and {variant} are not scored on the same queries"
                if not a:
                    continue
                p = paired_randomization_test(b, a, n=n_resamples, seed=SEED)
                rows.append({
                    "experiment": exp.name, "set": set_name, "metric": metric,
                    "baseline": base, "variant": variant, "queries": len(a),
                    "baseline_mean": round(float(np.mean(a)), 4),
                    "variant_mean": round(float(np.mean(b)), 4),
                    "diff": round(float(np.mean(b) - np.mean(a)), 4),
                    "p_value": p,
                })
    return rows


def latency_row(set_name: str, name: str, latencies: list[float]) -> dict:
    x = np.asarray(latencies)
    return {"set": set_name, "config": name, "queries": len(x),
            "p50_ms": round(float(np.percentile(x, 50)), 1),
            "p95_ms": round(float(np.percentile(x, 95)), 1),
            "mean_ms": round(float(x.mean()), 1)}


# --- outputs -----------------------------------------------------------------------------------


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        if not rows:
            return
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def metrics_rows(set_name: str, summaries: dict) -> list[dict]:
    rows = []
    for name, summary in summaries.items():
        row = {"config": name, "queries": max((v[3] for v in summary.values()), default=0)}
        for m in metric_names(set_name):
            mean, low, high, _ = summary.get(m, (float("nan"),) * 3 + (0,))
            row[m], row[f"{m}_ci95_lo"], row[f"{m}_ci95_hi"] = round(mean, 4), round(low, 4), round(high, 4)
        rows.append(row)
    return rows


def per_query_rows(set_name: str, queries: dict, per_query_by_config: dict) -> list[dict]:
    rows = []
    for name, per_query in per_query_by_config.items():
        for qid in sorted(per_query):
            row = {"config": name, "qid": qid}
            if set_name == "fonti":
                row["bucket"] = queries[qid][1].get("bucket", "")
            row.update({m: round(per_query[qid][m], 4) for m in METRICS[set_name]})
            rows.append(row)
    return rows


def machine() -> str:
    cpu = platform.processor() or platform.machine()
    if platform.system() == "Darwin":
        try:
            cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                 text=True, timeout=5).stdout.strip() or cpu
        except Exception:
            pass
    try:
        ram = f"{os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 2**30:.0f} GB RAM"
    except (AttributeError, ValueError, OSError):
        ram = "RAM unknown"
    return f"{platform.system()} {platform.release()}, {cpu}, {ram}"


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=config.ROOT,
                              capture_output=True, text=True, timeout=5).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def fmt_p(p: float, n_resamples: int = N_RESAMPLES) -> str:
    return f"< {1 / n_resamples:g}" if p == 0 else f"{p:.4f}"


def reading(row: dict) -> str:
    """One generated line per comparison; the conclusions in words are written by hand (G6)."""
    sig = "significant" if row["p_value"] < ALPHA else "not significant"
    sign = "+" if row["diff"] >= 0 else ""
    return (f"`{row['variant']}` vs `{row['baseline']}`: {row['metric']} {sign}{row['diff']:.4f} "
            f"(p {fmt_p(row['p_value'])}, {sig} at {ALPHA})")


def write_summary(path: Path, info: dict, summaries_by_set: dict, sig_rows: list[dict],
                  lat_rows: list[dict], bucket_sizes: dict) -> None:
    lines = ["# Evaluation summary", "",
             "Generated by `uv run python -m evaluation.run`" + (" --dev" if info["dev"] else "")
             + f" on {info['date']}, commit `{info['commit']}`.",
             f"Machine (latencies): {info['machine']}.", "",
             f"Every mean has its 95% bootstrap interval ({N_RESAMPLES} resamples, seed {SEED}); "
             f"p-values are two-sided paired randomization tests ({N_RESAMPLES} permutations). "
             f"`{RANDOM}` is a random ranking (the floor: it must score near zero).", ""]
    for set_name, summaries in summaries_by_set.items():
        names = metric_names(set_name)
        n = max((v[3] for s in summaries.values() for v in s.values()), default=0)
        lines += [f"## Test set `{set_name}` ({n} queries)", ""]
        if set_name == "fonti" and bucket_sizes:
            lines += ["Queries per overlap bucket: " + ", ".join(f"{b} {bucket_sizes.get(b, 0)}" for b in BUCKETS) + ".", ""]
        main = [m for m in names if ":" not in m]
        lines += ["| configuration | " + " | ".join(main) + " |", "|---|" + "---|" * len(main)]
        for cfg, s in summaries.items():
            cells = [f"{s[m][0]:.3f} [{s[m][1]:.3f}, {s[m][2]:.3f}]" if m in s else "-" for m in main]
            lines.append(f"| `{cfg}` | " + " | ".join(cells) + " |")
        lines.append("")
        bucketed = [m for m in names if ":" in m]
        if bucketed:
            lines += ["Per overlap bucket (low overlap = paraphrase):", "",
                      "| configuration | " + " | ".join(bucketed) + " |", "|---|" + "---|" * len(bucketed)]
            for cfg, s in summaries.items():
                cells = [f"{s[m][0]:.3f} [{s[m][1]:.3f}, {s[m][2]:.3f}]" if m in s else "-" for m in bucketed]
                lines.append(f"| `{cfg}` | " + " | ".join(cells) + " |")
            lines.append("")
    for exp in EXPERIMENTS:
        rows = [r for r in sig_rows if r["experiment"] == exp.name]
        if not rows:
            continue
        lines += [f"## {exp.name}: {exp.question}" + (" (stretch)" if exp.stretch else ""), "",
                  "| set | metric | baseline | variant | baseline mean | variant mean | diff | p |",
                  "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['set']} | {r['metric']} | `{r['baseline']}` | `{r['variant']}` | "
                         f"{r['baseline_mean']:.4f} | {r['variant_mean']:.4f} | {r['diff']:+.4f} | {fmt_p(r['p_value'])} |")
        lines.append("")
        lines += [f"- {reading(r)}" for r in rows]
        lines.append("")
    if lat_rows:
        lines += ["## E6: query latency (ms, k = %d)" % K, "",
                  f"{LATENCY_QUERIES} `{LATENCY_SET}` queries drawn with seed {SEED}, after a warm-up of "
                  f"{WARMUP} other queries; for each query every configuration is timed, in a random "
                  "order, so that all of them run with the same caches; the query-embedding cache is "
                  "emptied before each timed search, so the vector configurations include the cost "
                  "of embedding the query.", "",
                  "| set | configuration | queries | p50 | p95 | mean |", "|---|---|---|---|---|---|"]
        for r in lat_rows:
            lines.append(f"| {r['set']} | `{r['config']}` | {r['queries']} | {r['p50_ms']} | {r['p95_ms']} | {r['mean_ms']} |")
        lines += ["", "Indexing time and index size: `results/indexing.csv` (Daniel).", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# --- main --------------------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dev", action="store_true", help="the 1000 dev queries of fonti, outputs in results/runs/dev/")
    parser.add_argument("--sets", nargs="+", default=TEST_SETS, choices=TEST_SETS)
    parser.add_argument("--configs", nargs="+", help="rerun only these configurations (the others are reused from disk)")
    parser.add_argument("--no-latency", action="store_true",
                        help="skip the latency pass (latency.csv is then written empty): development only")
    parser.add_argument("--resamples", type=int, default=N_RESAMPLES, help=argparse.SUPPRESS)
    args = parser.parse_args()

    from wikisearch.search import search

    runs_root = RESULTS / "runs" / "dev" if args.dev else RESULTS / "runs"
    metrics_dir = runs_root / "metrics" if args.dev else RESULTS / "metrics"
    summary_path = runs_root / "summary.md" if args.dev else RESULTS / "summary.md"
    doc_ids = all_doc_ids()

    summaries_by_set, sig_rows, lat_rows, bucket_sizes = {}, [], [], {}
    for set_name in args.sets:
        loaded = load_set(set_name, args.dev)
        if loaded is None:
            print(f"{set_name}: no qrels.txt yet, skipped (the manual judgments come in G4)")
            continue
        queries, qrels = loaded
        run_dir = runs_root / set_name
        print(f"{set_name}: {len(queries)} queries")
        if set_name == "fonti":
            for _, meta in queries.values():
                bucket_sizes[meta.get("bucket")] = bucket_sizes.get(meta.get("bucket"), 0) + 1

        per_query_by_config = {}
        write_run(run_dir / f"{RANDOM}.txt", random_run(queries, doc_ids), RANDOM)
        per_query_by_config[RANDOM] = score_run(set_name, queries, qrels, read_run(run_dir / f"{RANDOM}.txt"))
        built = [name for name in configs_for(set_name) if index_built(name)]
        for name in configs_for(set_name):
            run_path = run_dir / f"{name}.txt"
            if name not in built:
                print(f"  {name}: index not built on this laptop, skipped")
                continue
            if args.configs is None or name in args.configs:
                print(f"  {name}: searching", flush=True)
                write_run(run_path, run_config(queries, name, search), name)
            elif run_path.exists():
                print(f"  {name}: reused run from {datetime.fromtimestamp(run_path.stat().st_mtime):%d %b %H:%M}")
            else:
                continue
            per_query_by_config[name] = score_run(set_name, queries, qrels, read_run(run_path))

        if set_name == LATENCY_SET and not args.no_latency:
            print(f"  latency: {LATENCY_QUERIES} queries x {len(built)} configurations, "
                  "configurations in random order per query", flush=True)
            from wikisearch.search import embed

            latencies = measure_latency(queries, built, search, before_each=embed.embed_query.cache_clear)
            lat_rows += [latency_row(set_name, name, latencies[name]) for name in built]

        print(f"  {set_name}: confidence intervals and significance tests", flush=True)
        summaries = {name: summarize(set_name, pq, args.resamples) for name, pq in per_query_by_config.items()}
        summaries_by_set[set_name] = summaries
        write_csv(metrics_dir / f"{set_name}.csv", metrics_rows(set_name, summaries))
        write_csv(metrics_dir / f"{set_name}_per_query.csv", per_query_rows(set_name, queries, per_query_by_config))
        sig_rows += significance_rows(set_name, per_query_by_config, args.resamples)

    write_csv(metrics_dir / "significance.csv", sig_rows)
    write_csv(metrics_dir / "latency.csv", lat_rows)
    info = {"dev": args.dev, "date": f"{datetime.now():%d %b %Y %H:%M}", "commit": git_commit(), "machine": machine()}
    write_summary(summary_path, info, summaries_by_set, sig_rows, lat_rows, bucket_sizes)
    print(f"Wrote {metrics_dir.relative_to(config.ROOT)} and {summary_path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
