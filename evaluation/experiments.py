"""The comparisons of the ablation study (PLAN.md, "Experiments"), as pairs (baseline, variant).

Every pair is tested with the paired randomization test on the per-query scores of the listed
metrics, on the listed test sets only. Metric names of the form `MRR@10:low` are computed on the
queries of one overlap bucket of `fonti` (`low`, `mid`, `high`).
"""

from dataclasses import dataclass, field

TEST_SETS = ["fonti", "manual"]

# Metrics computed for every configuration of a test set (each mean gets a bootstrap interval).
METRICS = {
    "fonti": ["MRR@10", "R@10", "R@100"],
    "manual": ["P@10", "nDCG@10", "AP", "MRR@10"],
}
BUCKETS = ["low", "mid", "high"]  # `meta["bucket"]` of the `fonti` queries
BUCKET_METRICS = ["MRR@10", "R@100"]  # also computed per bucket on `fonti`

# Only these configurations have their documents judged in the `manual` pool (evaluation/pool.py):
# any other configuration would be scored against judgments it did not contribute to.
MANUAL_CONFIGS = ["bm25-standard", "bm25-italian", "knn", "hybrid-rrf", "hybrid-rrf-published"]

RANDOM = "random"  # baseline computed by the runner, not a configuration of `search()`


@dataclass
class Experiment:
    name: str
    question: str
    pairs: list[tuple[str, str]]
    metrics: dict[str, list[str]] = field(default_factory=dict)  # test set -> metrics tested
    stretch: bool = False


_E3_BUCKETS = [f"{m}:{b}" for m in BUCKET_METRICS for b in BUCKETS]

EXPERIMENTS = [
    Experiment(
        "E1", "Does Italian text analysis help?",
        [("bm25-standard", "bm25-italian")],
        {"fonti": ["MRR@10", "R@100"], "manual": ["nDCG@10"]},
    ),
    Experiment(
        "E2", "Which fields to search, with which weights?",
        [("bm25-italian", "bm25-italian-title"), ("bm25-italian", "bm25-italian-body"),
         ("bm25-italian", "bm25-italian-flat")],
        {"fonti": ["MRR@10", "R@100"]},
    ),
    Experiment(
        "E3", "Lexical, semantic or both?",
        [("bm25-italian", "knn"), ("bm25-italian", "hybrid-rrf"), ("knn", "hybrid-rrf")],
        {"fonti": ["MRR@10", "R@100"] + _E3_BUCKETS, "manual": ["nDCG@10"]},
    ),
    Experiment(
        "E4", "How much does leakage inflate results?",
        [("bm25-italian", "bm25-italian-leak")],
        {"fonti": ["MRR@10"]},
    ),
    Experiment(
        "E5", "Should published pages rank higher?",
        [("hybrid-rrf", "hybrid-rrf-published")],
        {"manual": ["nDCG@10"]},
    ),
    Experiment(
        "E8", "What does vector quantization cost in quality?",
        [("knn", "knn-int8"), ("knn", "knn-bbq")],
        {"fonti": ["MRR@10", "R@100"]},
        stretch=True,
    ),
]
