"""Statistical robustness (docs/course.md, section 2): paired randomization test between two
configurations, bootstrap confidence interval for the mean of one configuration.

Both work on per-query scores (one number per query, e.g. the reciprocal rank). The random
draws are done in chunks so that about 7,000 queries x 10,000 draws fit in the 8 GB laptops.
"""

import numpy as np

_CHUNK = 500  # draws per chunk: 7,000 queries x 500 draws x 8 bytes = 28 MB


def paired_randomization_test(
    scores_a: list[float], scores_b: list[float], n: int = 10000, seed: int = 42
) -> float:
    """Two-sided p-value for H0: configurations A and B are interchangeable.

    Under H0 the labels A and B of each query can be swapped, which flips the sign of that
    query's difference. We draw `n` random swaps and count how often the absolute mean
    difference is at least the observed one. p = count / n, so its resolution is 1 / n: report
    p = 0 as p < 1 / n.
    """
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or a.size == 0:
        raise ValueError("need two non-empty lists of per-query scores over the same queries")
    diff = a - b
    observed = abs(diff.mean())
    rng = np.random.default_rng(seed)
    count = 0
    done = 0
    while done < n:
        m = min(_CHUNK, n - done)
        signs = rng.choice((-1.0, 1.0), size=(m, diff.size))
        means = np.abs((signs * diff).mean(axis=1))
        count += int(np.sum(means >= observed - 1e-12))  # tolerance for float rounding
        done += m
    return count / n


def bootstrap_ci(
    scores: list[float], n: int = 10000, seed: int = 42, alpha: float = 0.05
) -> tuple[float, float]:
    """Percentile bootstrap interval for the mean: resample the queries with replacement `n`
    times, take the alpha/2 and 1 - alpha/2 quantiles of the resampled means."""
    x = np.asarray(scores, dtype=float)
    if x.ndim != 1 or x.size == 0:
        raise ValueError("need a non-empty list of per-query scores")
    rng = np.random.default_rng(seed)
    means = np.empty(n)
    done = 0
    while done < n:
        m = min(_CHUNK, n - done)
        idx = rng.integers(0, x.size, size=(m, x.size))
        means[done : done + m] = x[idx].mean(axis=1)
        done += m
    low, high = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(low), float(high)
