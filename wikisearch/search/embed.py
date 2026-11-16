"""Query embeddings for the knn and hybrid configurations (owner: Fabio).

The model is loaded lazily, the first time a query is embedded: the bm25 configurations (and the
web app used only with them) never import sentence-transformers or torch.
"""

from functools import lru_cache

from wikisearch.config import EMBEDDING_MODEL, QUERY_PREFIX


@lru_cache(maxsize=1)
def model():
    """The same model that embedded the documents (data/shared/embeddings.npy), loaded once."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=2048)
def embed_query(text: str) -> tuple[float, ...]:
    """Unit-length vector of "query: " + text, as e5 expects (documents use "passage: ").

    Cached by text: knn, hybrid-rrf and hybrid-rrf-published embed the same query, and the web
    app asks again for every page and for compare mode.
    """
    vector = model().encode(QUERY_PREFIX + text, normalize_embeddings=True)
    return tuple(float(x) for x in vector)
