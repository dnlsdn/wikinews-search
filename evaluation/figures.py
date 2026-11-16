"""Figures of the presentation, drawn from the metric files written by `evaluation.run`.

    uv run python -m evaluation.figures          # official: results/metrics/ -> results/figures/
    uv run python -m evaluation.figures --dev    # development: results/runs/dev/metrics/ -> results/runs/dev/figures/

No search is run here: the figures only read `fonti.csv`, `significance.csv` and `latency.csv`, so
they can be redrawn in seconds after every run. Three PNGs:

1. `e3_buckets.png` (E3, the key figure): MRR@10 of BM25 (`bm25-italian`), kNN and the hybrid on all
   the `fonti` queries and per overlap bucket, with the 95% bootstrap intervals. It shows where
   semantic search helps: on the low-overlap (paraphrase) queries.
2. `e1_e2_bm25.png` (E1, E2): MRR@10 of the BM25 variants with their intervals, each annotated with
   the difference from its baseline and the p-value of the paired randomization test.
3. `e6_tradeoff.png` (E6): median query latency against MRR@10, one point per configuration.
   `bm25-italian-leak` is left out: it indexes the sources, so it is a measure of leakage, not a
   configuration one could choose.

A figure whose data is missing (e.g. no latency file) is skipped with a message.
"""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window: works the same on macOS, Windows and without a display
import matplotlib.pyplot as plt  # noqa: E402

from wikisearch import config  # noqa: E402

RESULTS = config.ROOT / "results"
N_RESAMPLES = 10000  # of the randomization test (evaluation.run): p = 0 means p < 1 / 10000

# Colors: the first three slots of a categorical palette checked for color-blind readers, text in
# neutral inks, recessive grid. Light background: the figures go on slides.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = {"bm25-italian": "#2a78d6", "knn": "#eb6834", "hybrid-rrf": "#1baf7a"}
ACCENT = "#2a78d6"

LABELS = {
    "bm25-standard": "BM25, standard analyzer",
    "bm25-italian": "BM25, Italian analyzer",
    "bm25-italian-title": "BM25, title only",
    "bm25-italian-body": "BM25, body only",
    "bm25-italian-flat": "BM25, equal field weights",
    "knn": "kNN",
    "hybrid-rrf": "Hybrid (RRF)",
    "hybrid-rrf-published": "Hybrid, published first",
    "knn-int8": "kNN, int8",
    "knn-bbq": "kNN, BBQ",
}
E3_CONFIGS = ["bm25-italian", "knn", "hybrid-rrf"]
E3_SHORT = {"bm25-italian": "BM25", "knn": "kNN", "hybrid-rrf": "Hybrid (RRF)"}
BUCKET_LABELS = {"low": "low overlap\n(paraphrases)", "mid": "mid overlap", "high": "high overlap"}
E1_E2_ORDER = ["bm25-standard", "bm25-italian", "bm25-italian-title", "bm25-italian-body",
               "bm25-italian-flat"]
NOT_A_CHOICE = {"random", "bm25-italian-leak"}
# E6 labels that would overlap a neighbour: below the point instead of above (points, not data)
LABEL_OFFSETS = {"hybrid-rrf": (6, -11), "knn": (6, -11)}


# --- reading -----------------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def by_config(rows: list[dict]) -> dict[str, dict]:
    return {r["config"]: r for r in rows}


def mean_ci(row: dict, metric: str) -> tuple[float, float, float]:
    return (float(row[metric]), float(row[f"{metric}_ci95_lo"]), float(row[f"{metric}_ci95_hi"]))


def format_p(p: float, n: int = N_RESAMPLES) -> str:
    """p as it goes on a slide: the randomization test cannot go below 1/n, so 0 is `p < 1/n`."""
    if p < 1 / n:
        return f"p < {1 / n:g}"
    if p < 0.001:
        return "p < 0.001"
    return f"p = {p:.3f}" if p < 0.01 else f"p = {p:.2f}"


def find_test(sig: list[dict], metric: str, baseline: str, variant: str) -> dict | None:
    for r in sig:
        if (r["set"], r["metric"], r["baseline"], r["variant"]) == ("fonti", metric, baseline, variant):
            return r
    return None


# --- drawing -----------------------------------------------------------------------------------

def new_figure(width: float, height: float):
    fig, ax = plt.subplots(figsize=(width, height), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_2)
    ax.tick_params(colors=INK_2, labelcolor=INK)
    return fig, ax


def save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    print(f"  {path.relative_to(config.ROOT) if path.is_relative_to(config.ROOT) else path}")


def e3_buckets(metrics: dict[str, dict], sig: list[dict], path: Path) -> bool:
    if any(c not in metrics for c in E3_CONFIGS):
        print("  e3_buckets: a configuration of E3 is missing from the metrics, skipped")
        return False
    groups = [("MRR@10", "all queries")]
    for b in ("low", "mid", "high"):
        test = find_test(sig, f"MRR@10:{b}", "bm25-italian", "hybrid-rrf")
        n = f"\nn = {test['queries']}" if test else ""
        groups.append((f"MRR@10:{b}", BUCKET_LABELS[b] + n))
    fig, ax = new_figure(8, 4.5)
    width = 0.26
    for j, name in enumerate(E3_CONFIGS):
        xs, ys, errs = [], [], [[], []]
        for i, (metric, _) in enumerate(groups):
            mean, lo, hi = mean_ci(metrics[name], metric)
            xs.append(i + (j - 1) * width)
            ys.append(mean)
            errs[0].append(mean - lo)
            errs[1].append(hi - mean)
        ax.bar(xs, ys, width, color=SERIES[name], edgecolor=SURFACE, linewidth=2, label=E3_SHORT[name],
               zorder=2)
        ax.errorbar(xs, ys, yerr=errs, fmt="none", ecolor=INK_2, elinewidth=1, capsize=2.5, zorder=3)
        # values only on the low-overlap group: the point of the figure
        ax.text(xs[1], errs[1][1] + ys[1] + 0.015, f"{ys[1]:.2f}", ha="center", va="bottom",
                fontsize=8, color=INK)
    ax.set_xticks(range(len(groups)), [g[1] for g in groups], fontsize=9)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("MRR@10 (95% bootstrap interval)", color=INK_2, fontsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("E3: lexical, semantic or both? (fonti)", loc="left", color=INK, fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="upper left", ncols=3, bbox_to_anchor=(0, 1.0))
    save(fig, path)
    return True


def e1_e2_bm25(metrics: dict[str, dict], sig: list[dict], path: Path) -> bool:
    names = [n for n in E1_E2_ORDER if n in metrics]
    if len(names) < 2:
        print("  e1_e2_bm25: BM25 variants missing from the metrics, skipped")
        return False
    fig, ax = new_figure(8, 3.6)
    ys = list(range(len(names)))[::-1]  # first configuration on top
    means = [mean_ci(metrics[n], "MRR@10") for n in names]
    ax.barh(ys, [m for m, _, _ in means], height=0.55, color=ACCENT, edgecolor=SURFACE, linewidth=2,
            zorder=2)
    ax.errorbar([m for m, _, _ in means], ys,
                xerr=[[m - lo for m, lo, _ in means], [hi - m for m, _, hi in means]],
                fmt="none", ecolor=INK_2, elinewidth=1, capsize=2.5, zorder=3)
    for y, name, (mean, _, hi) in zip(ys, names, means):
        baseline = "bm25-standard" if name == "bm25-italian" else "bm25-italian"
        test = find_test(sig, "MRR@10", baseline, name)
        if name == "bm25-standard":
            note = "E1 baseline"
        elif test is None:
            note = ""
        else:
            exp = "E1" if name == "bm25-italian" else "E2"
            note = (f"{exp}: {float(test['diff']):+.3f} vs {'standard' if exp == 'E1' else 'Italian'}, "
                    f"{format_p(float(test['p_value']))}")
        ax.text(hi + 0.01, y, f"{mean:.3f}   {note}", va="center", fontsize=8, color=INK)
    ax.set_yticks(ys, [LABELS[n] for n in names], fontsize=9)
    ax.set_xlim(0, 1.25)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel("MRR@10 (95% bootstrap interval)", color=INK_2, fontsize=9)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("E1, E2: text analysis and fields of BM25 (fonti)", loc="left", color=INK, fontsize=11)
    save(fig, path)
    return True


def e6_tradeoff(metrics: dict[str, dict], latency: list[dict], path: Path) -> bool:
    lat = {r["config"]: float(r["p50_ms"]) for r in latency if r["set"] == "fonti"}
    names = [n for n in lat if n in metrics and n not in NOT_A_CHOICE]
    if not names:
        print("  e6_tradeoff: no latency measured, skipped")
        return False
    fig, ax = new_figure(8, 4.5)
    xs = [lat[n] for n in names]
    ys = [float(metrics[n]["MRR@10"]) for n in names]
    ax.scatter(xs, ys, s=40, color=ACCENT, edgecolors=SURFACE, linewidths=1.5, zorder=3)
    for x, y, name in zip(xs, ys, names):
        ax.annotate(LABELS.get(name, name), (x, y), xytext=LABEL_OFFSETS.get(name, (6, 4)),
                    textcoords="offset points", fontsize=8, color=INK)
    ax.set_xlim(0, max(xs) * 1.35)
    ax.set_xlabel("median query latency, ms (lower is better)", color=INK_2, fontsize=9)
    ax.set_ylabel("MRR@10 (higher is better)", color=INK_2, fontsize=9)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("E6: quality against cost (fonti)", loc="left", color=INK, fontsize=11)
    save(fig, path)
    return True


def draw_all(metrics_dir: Path, out_dir: Path) -> list[str]:
    """Draw every figure whose data exists; returns the names of the files written."""
    if not (metrics_dir / "fonti.csv").exists():
        print(f"No {metrics_dir / 'fonti.csv'}: run `uv run python -m evaluation.run` first.")
        return []
    metrics = by_config(read_csv(metrics_dir / "fonti.csv"))
    sig = read_csv(metrics_dir / "significance.csv") if (metrics_dir / "significance.csv").exists() else []
    lat_path = metrics_dir / "latency.csv"
    latency = read_csv(lat_path) if lat_path.exists() and lat_path.stat().st_size else []
    written = []
    for name, draw in [("e3_buckets.png", lambda p: e3_buckets(metrics, sig, p)),
                       ("e1_e2_bm25.png", lambda p: e1_e2_bm25(metrics, sig, p)),
                       ("e6_tradeoff.png", lambda p: e6_tradeoff(metrics, latency, p))]:
        if draw(out_dir / name):
            written.append(name)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dev", action="store_true", help="figures of the dev run, in results/runs/dev/figures/")
    args = parser.parse_args()
    root = RESULTS / "runs" / "dev" if args.dev else RESULTS
    print("Figures:")
    draw_all(root / "metrics", root / "figures")


if __name__ == "__main__":
    main()
