"""Unit tests of the evaluation metrics, file formats and significance tests.

Every expected value is computed by hand in the comment next to it, so that a bug in the metric
code shows up here and not in the results (docs/course.md, section 2).
"""

import json
import math

import pytest

from evaluation import metrics, significance, trec

# Running example: ranked [a, b, c, d], judged {b: 1, d: 2}. Relevant (grade >= 1): b at rank 2,
# d at rank 4. Two relevant documents in all.
RANKED = ["a", "b", "c", "d"]
RELS = {"b": 1, "d": 2}


# --- precision and recall -------------------------------------------------------------------


def test_precision_at_k():
    assert metrics.precision_at_k(RANKED, RELS, 2) == 0.5  # top 2 = [a, b]: 1 relevant / 2
    assert metrics.precision_at_k(RANKED, RELS, 4) == 0.5  # 2 relevant / 4
    # list shorter than k: still divided by k, 2 relevant / 10
    assert metrics.precision_at_k(RANKED, RELS, 10) == 0.2


def test_recall_at_k():
    assert metrics.recall_at_k(RANKED, RELS, 2) == 0.5  # 1 of the 2 relevant
    assert metrics.recall_at_k(RANKED, RELS, 4) == 1.0  # both
    assert metrics.recall_at_k(RANKED, {"b": 0}, 4) == 0.0  # nothing relevant judged


# --- reciprocal rank ------------------------------------------------------------------------


def test_reciprocal_rank():
    assert metrics.reciprocal_rank(RANKED, RELS) == 0.5  # first relevant (b) at rank 2
    assert metrics.reciprocal_rank(RANKED, RELS, k=1) == 0.0  # rank 2 is beyond k = 1
    assert metrics.reciprocal_rank(["d", "a"], RELS) == 1.0  # first relevant at rank 1


def test_grade_zero_is_not_relevant():
    # a is judged with grade 0, b with grade 1: the first relevant is b at rank 2, RR = 1/2
    assert metrics.reciprocal_rank(["a", "b"], {"a": 0, "b": 1}) == 0.5


# --- average precision ----------------------------------------------------------------------


def test_average_precision():
    # precision at rank 2 = 1/2, at rank 4 = 2/4; mean over the 2 relevant: (1/2 + 2/4) / 2
    assert metrics.average_precision(RANKED, RELS) == pytest.approx(0.5)
    # perfect ranking [b, d]: (1/1 + 2/2) / 2 = 1
    assert metrics.average_precision(["b", "d"], RELS) == 1.0


def test_average_precision_counts_unretrieved_relevant_as_zero():
    # ranked [a, b], relevant {a, z}: a at rank 1 gives 1/1, z never retrieved gives 0;
    # divided by the 2 relevant judged: (1 + 0) / 2 = 0.5
    assert metrics.average_precision(["a", "b"], {"a": 1, "z": 1}) == 0.5


# --- nDCG -----------------------------------------------------------------------------------


def test_ndcg_at_k():
    # gains 2**g - 1: b -> 1, d -> 3. DCG@4 = 1/log2(3) + 3/log2(5) = 0.63093 + 1.29203 = 1.92296
    # ideal order [d, b]: 3/log2(2) + 1/log2(3) = 3 + 0.63093 = 3.63093; nDCG@4 = 0.52961
    assert metrics.ndcg_at_k(RANKED, RELS, 4) == pytest.approx(0.52961, abs=1e-5)
    # DCG@2 = 1/log2(3) = 0.63093; ideal@2 is still [d, b] = 3.63093; nDCG@2 = 0.17377
    assert metrics.ndcg_at_k(RANKED, RELS, 2) == pytest.approx(0.17377, abs=1e-5)
    # the ideal ordering gives 1
    assert metrics.ndcg_at_k(["d", "b"], RELS, 10) == pytest.approx(1.0)


def test_ndcg_ideal_uses_all_judged_grades():
    # ranked [b], judged {a: 2, b: 1}: DCG = 1/log2(2) = 1. The ideal ranking uses the judged
    # grades even if a was never retrieved: 3/1 + 1/log2(3) = 3.63093. nDCG = 1 / 3.63093 = 0.27541
    assert metrics.ndcg_at_k(["b"], {"a": 2, "b": 1}, 10) == pytest.approx(1 / (3 + 1 / math.log2(3)))


def test_ndcg_ideal_cut_at_k():
    # judged {a: 2, b: 2, c: 2}, ranked [a], k = 1: DCG@1 = 3, ideal@1 = 3 (only the top 1 counts)
    assert metrics.ndcg_at_k(["a"], {"a": 2, "b": 2, "c": 2}, 1) == 1.0


# --- edge cases -----------------------------------------------------------------------------


def test_no_relevant_retrieved():
    ranked, rels = ["a", "c"], {"b": 1}
    assert metrics.precision_at_k(ranked, rels, 2) == 0.0
    assert metrics.recall_at_k(ranked, rels, 2) == 0.0
    assert metrics.reciprocal_rank(ranked, rels) == 0.0
    assert metrics.average_precision(ranked, rels) == 0.0
    assert metrics.ndcg_at_k(ranked, rels, 10) == 0.0


def test_relevant_beyond_k():
    # the only relevant document, "r", is at rank 11
    ranked = [f"x{i}" for i in range(10)] + ["r"]
    rels = {"r": 1}
    assert metrics.reciprocal_rank(ranked, rels, k=10) == 0.0
    assert metrics.recall_at_k(ranked, rels, 10) == 0.0
    assert metrics.recall_at_k(ranked, rels, 100) == 1.0
    assert metrics.precision_at_k(ranked, rels, 10) == 0.0
    assert metrics.average_precision(ranked, rels) == pytest.approx(1 / 11)  # precision at rank 11
    assert metrics.ndcg_at_k(ranked, rels, 10) == 0.0


def test_empty_run():
    for name in ["P@10", "R@100", "MRR@10", "AP", "nDCG@10"]:
        assert metrics.score(name, [], RELS) == 0.0


def test_repeated_document_counts_once():
    # ranked [b, b], relevant {b, c}: b counts only at rank 1, so P@2 = 1/2 (not 2/2), R@2 = 1/2
    assert metrics.precision_at_k(["b", "b"], {"b": 1, "c": 1}, 2) == 0.5
    assert metrics.recall_at_k(["b", "b"], {"b": 1, "c": 1}, 2) == 0.5


def test_unknown_metric_name():
    with pytest.raises(ValueError):
        metrics.score("F1", RANKED, RELS)


# --- evaluate -------------------------------------------------------------------------------


def test_evaluate():
    qrels = {
        "q1": RELS,  # in the run: RR = 1/2
        "q2": {"x": 0},  # no relevant judged: skipped
        "q3": {"y": 1},  # missing from the run: scores 0
    }
    run = {"q1": RANKED, "q4": ["y"]}  # q4 is not judged: ignored
    per_query, mean = metrics.evaluate(qrels, run, ["MRR@10", "P@2"])
    assert set(per_query) == {"q1", "q3"}
    assert per_query["q1"] == {"MRR@10": 0.5, "P@2": 0.5}
    assert per_query["q3"] == {"MRR@10": 0.0, "P@2": 0.0}
    assert mean == {"MRR@10": 0.25, "P@2": 0.25}  # (0.5 + 0) / 2


# --- TREC files -----------------------------------------------------------------------------


def test_trec_round_trip(tmp_path):
    queries = tmp_path / "queries.tsv"
    queries.write_text(
        'F0001\tTerremoto in Abruzzo, città distrutta\t{"bucket": "low", "overlap": 0.1}\n',
        encoding="utf-8",
    )
    assert trec.read_queries(queries) == {
        "F0001": ("Terremoto in Abruzzo, città distrutta", {"bucket": "low", "overlap": 0.1})
    }

    qrels = tmp_path / "qrels.txt"
    qrels.write_text("q1 0 10 2\nq1 0 11 0\nq2 0 12 1\n", encoding="utf-8")
    assert trec.read_qrels(qrels) == {"q1": {"10": 2, "11": 0}, "q2": {"12": 1}}

    run = tmp_path / "runs" / "bm25.txt"
    trec.write_run(run, {"q1": [("10", 7.5), ("11", 3.25)], "q2": [("12", 1.0)]}, "bm25")
    assert run.read_text(encoding="utf-8").splitlines()[0] == "q1 Q0 10 1 7.500000 bm25"
    assert trec.read_run(run) == {"q1": ["10", "11"], "q2": ["12"]}


def test_read_run_sorts_by_rank(tmp_path):
    run = tmp_path / "run.txt"
    run.write_text("q1 Q0 b 2 1.0 t\nq1 Q0 a 1 2.0 t\nq1 Q0 c 10 0.1 t\n", encoding="utf-8")
    assert trec.read_run(run) == {"q1": ["a", "b", "c"]}  # 10 after 2: ranks are numbers


def test_queries_meta_is_json(tmp_path):
    path = tmp_path / "q.tsv"
    path.write_text("q1\ttesto\tnot json\n", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        trec.read_queries(path)


# --- significance ---------------------------------------------------------------------------


def test_randomization_identical_lists():
    scores = [0.1, 0.5, 1.0, 0.0, 0.33]
    # observed difference 0; every random swap also gives 0 >= 0, so p = 1
    assert significance.paired_randomization_test(scores, scores) == 1.0


def test_randomization_clearly_better():
    # A beats B by 1 on all 30 queries: only the 2 all-same-sign swaps out of 2**30 reach the
    # observed difference, so p is about 0
    assert significance.paired_randomization_test([1.0] * 30, [0.0] * 30) < 0.05


def test_randomization_two_queries_by_hand():
    # differences [1, 1]: the 4 sign patterns give |mean| = 1, 0, 0, 1, so the exact p = 2/4 = 0.5
    p = significance.paired_randomization_test([1.0, 1.0], [0.0, 0.0], n=10000)
    assert abs(p - 0.5) < 0.03


def test_randomization_is_symmetric_and_reproducible():
    a = [0.2, 0.9, 0.4, 0.7, 0.1, 0.8, 0.5, 0.6]
    b = [0.1, 0.7, 0.5, 0.3, 0.1, 0.6, 0.2, 0.6]
    p = significance.paired_randomization_test(a, b)
    assert p == significance.paired_randomization_test(a, b)  # same seed, same p
    assert p == significance.paired_randomization_test(b, a)  # two-sided


def test_randomization_rejects_unpaired_lists():
    with pytest.raises(ValueError):
        significance.paired_randomization_test([1.0, 0.0], [1.0])


def test_bootstrap_constant_scores():
    # every resample of [0.3, 0.3, ...] has mean 0.3
    assert significance.bootstrap_ci([0.3] * 50) == pytest.approx((0.3, 0.3))


def test_bootstrap_contains_the_mean():
    scores = [0.0, 1.0] * 50  # mean 0.5; standard error 0.05, so the interval is about 0.4-0.6
    low, high = significance.bootstrap_ci(scores)
    assert low < 0.5 < high
    assert 0.38 < low < 0.45 and 0.55 < high < 0.62
    assert (low, high) == significance.bootstrap_ci(scores)  # reproducible with the seed
