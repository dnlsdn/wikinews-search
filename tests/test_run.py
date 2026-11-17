"""Tests of the experiment runner without Elasticsearch: a fake search function and a tiny
`fonti`-like test set."""

from evaluation import run
from evaluation.experiments import EXPERIMENTS, MANUAL_CONFIGS
from evaluation.trec import read_run, write_run
from wikisearch.schema import Hit
from wikisearch.search.configs import CONFIGS

QUERIES = {
    "F1": ("query one", {"bucket": "low"}),
    "F2": ("query two", {"bucket": "mid"}),
    "F3": ("query three", {"bucket": "high"}),
    "F4": ("query four", {"bucket": "low"}),
}
QRELS = {"F1": {"d1": 1}, "F2": {"d2": 1}, "F3": {"d3": 1}, "F4": {"d4": 1}}


def fake_search(calls=None):
    # "good" puts the right document first, "bad" never finds it
    def search(text, config, k=10):
        if calls is not None:
            calls.append(text)
        qid = next(q for q, (t, _) in QUERIES.items() if t == text)
        right = "d" + qid[1:]
        docs = [right, "x1", "x2"] if config == "good" else ["x1", "x2", "x3"]
        return [Hit(id=d, score=1.0 / (i + 1), title="", url="") for i, d in enumerate(docs[:k])]
    return search


def test_every_configuration_is_known_and_manual_uses_the_pooled_ones():
    for exp in EXPERIMENTS:
        for base, variant in exp.pairs:
            assert base in CONFIGS and variant in CONFIGS, (exp.name, base, variant)
    assert run.configs_for("manual") == MANUAL_CONFIGS
    assert run.configs_for("fonti") == list(CONFIGS)


def test_random_run_is_deterministic_per_query_and_has_no_repeats():
    ids = [f"d{i}" for i in range(500)]
    a = run.random_run(QUERIES, ids, k=100)
    assert a == run.random_run(QUERIES, ids, k=100)
    assert all(len({d for d, _ in hits}) == 100 for hits in a.values())
    # same ranking for a query whatever the other queries (dev subset vs full run)
    assert run.random_run({"F2": QUERIES["F2"]}, ids, k=100)["F2"] == a["F2"]


def test_run_config_searches_every_query_once():
    calls = []
    results = run.run_config(QUERIES, "good", fake_search(calls), k=10)
    assert len(calls) == len(QUERIES)
    assert results["F1"][0][0] == "d1"


def test_latency_warm_up_on_other_queries_and_random_order():
    calls = []

    def search(text, config, k=10):
        calls.append((text, config))
        return []

    lat = run.measure_latency(QUERIES, ["good", "bad", "other"], search, n=3, warmup=1)
    assert all(len(v) == 3 and all(t >= 0 for t in v) for v in lat.values())
    warm_text = calls[0][0]
    assert calls[:3] == [(warm_text, c) for c in ["good", "bad", "other"]]  # warm-up, discarded
    timed = calls[3:]
    assert len(timed) == 9 and warm_text not in {t for t, _ in timed}  # timed on other queries
    orders = [tuple(c for _, c in timed[i:i + 3]) for i in range(0, 9, 3)]
    assert all(sorted(o) == ["bad", "good", "other"] for o in orders)  # every configuration once
    calls.clear()
    cleared = []
    run.measure_latency(QUERIES, ["good", "bad", "other"], search, n=3, warmup=1,
                        before_each=lambda: cleared.append(1))
    assert [c for _, c in calls[3:]] == [c for o in orders for c in o]  # same order every time (seed)
    assert len(cleared) == 9  # before every timed search, not before the warm-up


def test_scores_buckets_and_random_floor(tmp_path):
    good = run.run_config(QUERIES, "good", fake_search(), k=10)
    write_run(tmp_path / "good.txt", good, "good")
    pq = run.score_run("fonti", QUERIES, QRELS, read_run(tmp_path / "good.txt"))
    assert pq["F1"]["MRR@10"] == 1.0 and pq["F1"]["MRR@10:low"] == 1.0
    assert "MRR@10:low" not in pq["F2"] and pq["F2"]["R@100:mid"] == 1.0

    ids = [f"n{i}" for i in range(10000)] + ["d1", "d2", "d3", "d4"]
    rnd = {q: [d for d, _ in hits] for q, hits in run.random_run(QUERIES, ids, k=100).items()}
    pq_random = run.score_run("fonti", QUERIES, QRELS, rnd)
    assert sum(s["MRR@10"] for s in pq_random.values()) / len(QUERIES) < 0.1

    summary = run.summarize("fonti", pq, n_resamples=200)
    assert summary["MRR@10"][0] == 1.0 and summary["MRR@10:low"][3] == 2
    rows = run.metrics_rows("fonti", {"good": summary})
    assert rows[0]["MRR@10"] == 1.0 and "MRR@10:low_ci95_lo" in rows[0]


def test_dev_queries_score_only_their_subset():
    subset = {"F1": QUERIES["F1"]}
    pq = run.score_run("fonti", subset, QRELS, {"F1": ["d1"]})
    assert list(pq) == ["F1"]


def test_significance_rows_and_summary(tmp_path):
    good = {q: {"MRR@10": 1.0, "R@100": 1.0, "R@10": 1.0} for q in QUERIES}
    bad = {q: {"MRR@10": 0.0, "R@100": 0.0, "R@10": 0.0} for q in QUERIES}
    rows = run.significance_rows("fonti", {"bm25-standard": bad, "bm25-italian": good}, n_resamples=200)
    e1 = [r for r in rows if r["experiment"] == "E1"]
    assert {r["metric"] for r in e1} == {"MRR@10", "R@100"}
    assert all(r["diff"] == 1.0 and r["queries"] == 4 for r in e1)
    # two tests in the E1 family: Holm doubles the smaller p
    assert all(r["p_holm"] >= r["p_value"] for r in e1)

    # pairs whose configurations were not run are left out
    assert all(r["experiment"] == "E1" for r in rows)

    summaries = {"fonti": {"bm25-standard": run.summarize("fonti", bad, 200),
                           "bm25-italian": run.summarize("fonti", good, 200)}}
    lat = [run.latency_row("fonti", "bm25-italian", [1.0, 2.0, 3.0])]
    info = {"dev": True, "date": "today", "commit": "abc", "machine": "test"}
    run.write_summary(tmp_path / "summary.md", info, summaries, rows, lat, {"low": 2, "mid": 1, "high": 1})
    text = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "## E1" in text and "`bm25-italian` vs `bm25-standard`" in text and "| 2.0 |" in text


def test_load_set_skips_a_set_without_judgments(tmp_path):
    (tmp_path / "manual").mkdir()
    (tmp_path / "manual" / "queries.tsv").write_text('M01\tq\t{"type": "topical"}\n', encoding="utf-8")
    assert run.load_set("manual", root=tmp_path) is None
    (tmp_path / "manual" / "qrels.txt").write_text("M01 0 d1 2\n", encoding="utf-8")
    queries, qrels = run.load_set("manual", root=tmp_path)
    assert qrels == {"M01": {"d1": 2}} and "M01" in queries
