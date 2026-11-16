"""Types shared by the search function, the web API and the evaluation harness (docs/contracts.md)."""

from dataclasses import dataclass, field


@dataclass
class Filters:
    date_from: str | None = None  # YYYY-MM-DD, inclusive
    date_to: str | None = None  # YYYY-MM-DD, inclusive
    categories: list[str] = field(default_factory=list)  # all must match
    agencies: list[str] = field(default_factory=list)  # any may match
    published: bool | None = None  # None = both


@dataclass
class Hit:
    id: str
    score: float
    title: str
    url: str
    date: str | None = None
    snippet: str | None = None  # may contain <em> highlight tags
    categories: list[str] = field(default_factory=list)
    agencies: list[str] = field(default_factory=list)
    image_url: str | None = None
    published: bool = True
