"""Tests of the merge of the `manual` judgments: Cohen's kappa computed by hand, disagreements,
qrels file."""

import sys

import pytest

from evaluation import merge_judgments as mj
from evaluation.judge import ASSIGNMENT_COLUMNS
from evaluation.trec import read_qrels


def test_kappa_binary_by_hand():
    # a = [1, 1, 0, 0], b = [1, 0, 0, 0]: p_o = 3/4; a says 1 half the time, b a quarter:
    # p_e = 0.5 * 0.25 + 0.5 * 0.75 = 0.5; kappa = (0.75 - 0.5) / (1 - 0.5) = 0.5
    assert mj.cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0], [0, 1]) == pytest.approx(0.5)


def test_kappa_three_grades_by_hand():
    # a = [2, 1, 0, 0], b = [2, 0, 0, 1]: p_o = 2/4; both judges give 2, 1, 0 with frequency
    # 0.25, 0.25, 0.5: p_e = 0.0625 + 0.0625 + 0.25 = 0.375; kappa = (0.5 - 0.375) / 0.625 = 0.2
    assert mj.cohen_kappa([2, 1, 0, 0], [2, 0, 0, 1], [0, 1, 2]) == pytest.approx(0.2)


def test_kappa_edge_cases():
    assert mj.cohen_kappa([1, 0, 2], [1, 0, 2], [0, 1, 2]) == pytest.approx(1.0)
    assert mj.cohen_kappa([0, 0], [0, 0], [0, 1, 2]) == 1.0  # one grade only: p_e = 1
    # agreement only by chance: a always 1, b half 1 half 0 -> p_o = 0.5 = p_e -> kappa 0
    assert mj.cohen_kappa([1, 1, 1, 1], [1, 1, 0, 0], [0, 1]) == pytest.approx(0.0)


def test_merge_lower_grade_unless_resolved():
    grades = {
        "gioia": {("M01", "a"): 2, ("M01", "b"): 1, ("M01", "c"): 0},
        "daniel": {("M01", "a"): 2, ("M01", "b"): 0, ("M01", "c"): 2, ("M11", "d"): 1},
    }
    qrels, double, dis, unresolved = mj.merge(grades, resolved={("M01", "c"): 1})
    assert qrels == {"M01": {"a": 2, "b": 0, "c": 1}, "M11": {"d": 1}}
    assert double[("M01", "b")] == [("gioia", 1), ("daniel", 0)]  # first judge first
    assert dis == [("M01", "b"), ("M01", "c")] and unresolved == [("M01", "b")]
    agree = mj.agreement(double)
    assert agree["all"][0] == 3 and agree["all"][1] == pytest.approx(1 / 3)
    assert "gioia-daniel" in agree


def test_main_writes_qrels_and_disagreements(tmp_path, monkeypatch, capsys):
    (tmp_path / "judging").mkdir()
    (tmp_path / "judgments").mkdir()
    rows = {"gioia": [("M01", "a"), ("M01", "b")], "daniel": [("M01", "a"), ("M01", "b"), ("M11", "c")]}
    for judge, pairs in rows.items():
        lines = ["\t".join(ASSIGNMENT_COLUMNS)] + [f"{q}\tquery\t{d}\ttitle {d}\t\tlead\turl" for q, d in pairs]
        (tmp_path / "judging" / f"{judge}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp_path / "judgments" / "gioia.tsv").write_text("M01\ta\t2\tt\nM01\tb\t1\tt\n", encoding="utf-8")
    # daniel has not judged M11 c yet
    (tmp_path / "judgments" / "daniel.tsv").write_text("M01\ta\t2\tt\nM01\tb\t0\tt\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["merge_judgments", "--dir", str(tmp_path)])
    mj.main()
    out = capsys.readouterr().out
    assert "1 STILL TO JUDGE" in out and "still open 1" in out
    assert read_qrels(tmp_path / "qrels.txt") == {"M01": {"a": 2, "b": 0}}
    dis = (tmp_path / "judgments" / "disagreements.tsv").read_text(encoding="utf-8").splitlines()
    assert dis[1].startswith("M01\tb\ttitle b\tgioia\t1\tdaniel\t0")
