"""Tests of the pooling and of the judging tool of the `manual` test set (step G3), without
Elasticsearch: a fake search function and scripted answers."""

from evaluation.judge import first_unjudged, judge_loop, read_judgments
from evaluation.pool import assign, pool
from wikisearch.schema import Hit


def items(n_docs=3):
    return [{"qid": "M01", "query": "q", "doc_id": str(i), "title": f"t{i}", "date": "",
             "lead": "lead", "url": f"https://example.org/{i}"} for i in range(1, n_docs + 1)]


def scripted(answers):
    answers = iter(answers)
    return lambda prompt: next(answers)


def test_assign_parts_and_double_judging():
    qids = [f"M{i:02d}" for i in range(1, 31)]
    a = assign(qids)
    assert a["gioia"] == qids[:10]
    # daniel: his part 11-20 plus queries 1-5 as second judge; fabio: 21-30 plus 6-10
    assert a["daniel"] == qids[:5] + qids[10:20]
    assert a["fabio"] == qids[5:10] + qids[20:30]


def test_pool_merges_deduplicates_and_is_deterministic():
    results = {"A": ["1", "2", "3"], "B": ["3", "4"]}

    def fake_search(text, cfg, k):
        return [Hit(id=d, score=1.0, title="", url="") for d in results[cfg][:k]]

    queries = {"M01": ("q", {})}
    pooled, found_by = pool(queries, fake_search, configs=["A", "B"], depth=10)
    assert sorted(pooled["M01"]) == ["1", "2", "3", "4"]
    assert found_by["M01"]["3"] == ["A", "B"]
    assert pool(queries, fake_search, configs=["A", "B"])[0] == pooled  # same shuffle every time


def test_judge_saves_each_grade_and_resumes(tmp_path):
    out = tmp_path / "judgments" / "gioia.tsv"
    # grade doc 1, an invalid key, open the URL (no grade), grade doc 2, quit
    opened = []
    judge_loop(items(), {}, out, ask=scripted(["2", "x", "o", "0", "q"]), out=lambda s: None,
               open_url=opened.append)
    assert read_judgments(out) == {("M01", "1"): 2, ("M01", "2"): 0}
    assert opened == ["https://example.org/2"]
    # resume: starts at doc 3
    assert first_unjudged(items(), read_judgments(out)) == 2
    judge_loop(items(), {}, out, ask=scripted(["1"]), out=lambda s: None)
    assert read_judgments(out)[("M01", "3")] == 1


def test_judge_back_changes_a_grade_and_last_one_wins(tmp_path):
    out = tmp_path / "gioia.tsv"
    # 1 (doc 1), 2 (doc 2), b (from doc 3 back to doc 2), 0 (doc 2 regraded), 2 (doc 3)
    judge_loop(items(), {}, out, ask=scripted(["1", "2", "b", "0", "2"]), out=lambda s: None)
    assert read_judgments(out) == {("M01", "1"): 1, ("M01", "2"): 0, ("M01", "3"): 2}
    assert len(out.read_text(encoding="utf-8").splitlines()) == 4  # every grade appended


def test_judge_enter_keeps_an_existing_grade(tmp_path):
    out = tmp_path / "gioia.tsv"
    judge_loop(items(2), {}, out, ask=scripted(["1", "b", "", "2"]), out=lambda s: None)
    assert read_judgments(out) == {("M01", "1"): 1, ("M01", "2"): 2}
    assert len(out.read_text(encoding="utf-8").splitlines()) == 2
