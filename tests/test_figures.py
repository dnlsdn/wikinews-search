"""Tests of the figures: drawn from tiny metric files, no Elasticsearch, no display."""

import csv

from evaluation import figures

CONFIGS = ["random", "bm25-standard", "bm25-italian", "bm25-italian-title", "bm25-italian-body",
           "bm25-italian-flat", "knn", "hybrid-rrf", "bm25-italian-leak"]
METRICS = ["MRR@10", "MRR@10:low", "MRR@10:mid", "MRR@10:high"]


def write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def fake_manual(folder):
    names = ["random", "bm25-standard", "bm25-italian", "knn", "hybrid-rrf", "hybrid-rrf-published"]
    write(folder / "manual.csv", [{"config": n, "queries": 30, "nDCG@10": i / 10,
                                   "nDCG@10_ci95_lo": i / 10 - 0.05, "nDCG@10_ci95_hi": i / 10 + 0.05}
                                  for i, n in enumerate(names)])


def fake_metrics(folder, latency=True):
    rows = []
    for i, name in enumerate(CONFIGS):
        row = {"config": name, "queries": 4}
        for m in METRICS:
            v = i / 10
            row.update({m: v, f"{m}_ci95_lo": v - 0.05, f"{m}_ci95_hi": v + 0.05})
        rows.append(row)
    write(folder / "fonti.csv", rows)
    write(folder / "significance.csv", [
        {"experiment": "E1", "set": "fonti", "metric": "MRR@10", "baseline": "bm25-standard",
         "variant": "bm25-italian", "queries": 4, "baseline_mean": 0.1, "variant_mean": 0.2,
         "diff": 0.1, "p_value": 0.0},
        {"experiment": "E3", "set": "fonti", "metric": "MRR@10:low", "baseline": "bm25-italian",
         "variant": "hybrid-rrf", "queries": 2, "baseline_mean": 0.2, "variant_mean": 0.7,
         "diff": 0.5, "p_value": 0.03},
    ])
    if latency:
        write(folder / "latency.csv", [{"set": "fonti", "config": n, "queries": 4, "p50_ms": 10 + i,
                                        "p95_ms": 20 + i, "mean_ms": 12 + i}
                                       for i, n in enumerate(CONFIGS)])
    else:
        (folder / "latency.csv").write_text("", encoding="utf-8")  # as `run --no-latency` writes it


def test_every_figure_is_drawn(tmp_path):
    fake_metrics(tmp_path)
    fake_manual(tmp_path)
    written = figures.draw_all(tmp_path, tmp_path / "figures")
    assert written == ["e3_buckets.png", "e1_e2_bm25.png", "e6_tradeoff.png", "manual_ndcg.png"]
    for name in written:
        assert (tmp_path / "figures" / name).read_bytes()[:4] == b"\x89PNG"


def test_missing_data_skips_only_that_figure(tmp_path):
    fake_metrics(tmp_path, latency=False)
    assert figures.draw_all(tmp_path, tmp_path / "figures") == ["e3_buckets.png", "e1_e2_bm25.png"]
    assert figures.draw_all(tmp_path / "nothing", tmp_path / "figures") == []


def test_p_values_as_on_the_slides():
    # the randomization test with 10,000 permutations cannot give less than 1/10,000
    assert figures.format_p(0.0) == "p < 0.0001"
    assert figures.format_p(0.0009) == "p < 0.001"
    assert figures.format_p(0.0041) == "p = 0.004"
    assert figures.format_p(0.1972) == "p = 0.20"


def test_holm_p_is_preferred():
    assert figures.holm({"p_value": "0.0", "p_holm": "0.0024"}) == "p Holm = 0.002"
    assert figures.holm({"p_value": "0.0379"}) == "p Holm = 0.04"
