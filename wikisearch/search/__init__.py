"""Search (owner: Fabio). The one function used by both the web app and the evaluation."""

from wikisearch.schema import Filters, Hit


def search(query: str, config: str, k: int = 10, filters: Filters | None = None) -> list[Hit]:
    """Return at most k hits for the query, best first, using the named configuration.

    See docs/contracts.md, section 3. Must not apply default filters.
    """
    raise NotImplementedError("step F1")
