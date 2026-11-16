"""Named search configurations: every design choice the experiments compare is one entry here.

Owner: Fabio. The evaluation runs every configuration in CONFIGS; the web UI lists them.
Fields of a configuration:
  analyzer   which index to query (see wikisearch.config.ANALYZER_VARIANTS)
  mode       "bm25", "knn" or "hybrid"
  fields     searched text fields with weights (bm25 and hybrid)
  rrf_k      reciprocal rank fusion constant (hybrid)
  depth      how many hits each retriever returns before fusion (hybrid)
  boost_published  multiplicative boost for published pages (1.0 = none)
"""

CONFIGS: dict[str, dict] = {
    # E1: text analysis
    "bm25-standard": {"analyzer": "standard", "mode": "bm25", "fields": ["title^3", "lead^2", "body"]},
    "bm25-italian": {"analyzer": "italian", "mode": "bm25", "fields": ["title^3", "lead^2", "body"]},
    # E2: fields and weights
    "bm25-italian-title": {"analyzer": "italian", "mode": "bm25", "fields": ["title"]},
    "bm25-italian-body": {"analyzer": "italian", "mode": "bm25", "fields": ["body"]},
    "bm25-italian-flat": {"analyzer": "italian", "mode": "bm25", "fields": ["title", "lead", "body"]},
    # E3: lexical, semantic, hybrid
    "knn": {"analyzer": "italian", "mode": "knn"},
    "hybrid-rrf": {
        "analyzer": "italian",
        "mode": "hybrid",
        "fields": ["title^3", "lead^2", "body"],
        "rrf_k": 60,
        "depth": 100,
    },
    # E4: leakage (sources searchable)
    "bm25-italian-leak": {
        "analyzer": "italian",
        "mode": "bm25",
        "fields": ["title^3", "lead^2", "body", "sources_text"],
    },
    # E5: boost on published pages
    "hybrid-rrf-published": {
        "analyzer": "italian",
        "mode": "hybrid",
        "fields": ["title^3", "lead^2", "body"],
        "rrf_k": 60,
        "depth": 100,
        "boost_published": 1.5,
    },
}

DEFAULT_CONFIG = "hybrid-rrf"
