"""The human-judged subset of `manual` keeps only M01-M10 and every configuration's scores."""

from evaluation import manual_human


def test_only_the_human_queries_are_kept(tmp_path):
    path = tmp_path / "manual_per_query.csv"
    rows = ["config,qid,P@10,nDCG@10,AP,MRR@10"]
    for config in ("bm25-italian", "knn"):
        for qid in ("M01", "M10", "M11", "M30"):
            rows.append(f"{config},{qid},0.5,0.6,0.7,1.0")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    out = manual_human.read_per_query(path, manual_human.HUMAN_QUERIES)
    assert sorted(out) == ["bm25-italian", "knn"]
    assert sorted(out["knn"]) == ["M01", "M10"]
    assert out["knn"]["M01"] == {"P@10": 0.5, "nDCG@10": 0.6, "AP": 0.7, "MRR@10": 1.0}
