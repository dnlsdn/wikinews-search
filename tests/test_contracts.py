from wikisearch import config
from wikisearch.search.configs import CONFIGS, DEFAULT_CONFIG


def test_configs_are_well_formed():
    assert DEFAULT_CONFIG in CONFIGS
    for name, cfg in CONFIGS.items():
        assert cfg["analyzer"] in config.ANALYZER_VARIANTS, name
        assert cfg["mode"] in {"bm25", "knn", "hybrid"}, name
        if cfg["mode"] in {"bm25", "hybrid"}:
            assert cfg["fields"], name
