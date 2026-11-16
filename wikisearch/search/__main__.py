"""Quick checks from the command line.

    uv run python -m wikisearch.search "terremoto abruzzo" --config bm25-italian
    uv run python -m wikisearch.search "elezioni" --config bm25-standard -k 5 --published
"""

import argparse
import sys
import time

from wikisearch.schema import Filters
from wikisearch.search import search
from wikisearch.search.configs import CONFIGS, DEFAULT_CONFIG


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m wikisearch.search")
    parser.add_argument("query")
    parser.add_argument("--config", default=DEFAULT_CONFIG, choices=list(CONFIGS))
    parser.add_argument("-k", type=int, default=10)
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--agency", action="append", default=[])
    parser.add_argument("--published", action="store_true", help="published pages only")
    args = parser.parse_args()

    filters = Filters(
        date_from=args.date_from,
        date_to=args.date_to,
        categories=args.category,
        agencies=args.agency,
        published=True if args.published else None,
    )
    # The data is full of accents: do not depend on the Windows console code page.
    sys.stdout.reconfigure(encoding="utf-8")
    start = time.perf_counter()
    hits = search(args.query, args.config, k=args.k, filters=filters)
    ms = (time.perf_counter() - start) * 1000
    print(f"{len(hits)} hits in {ms:.0f} ms ({args.config})")
    for rank, hit in enumerate(hits, 1):
        flag = "" if hit.published else "  [not published]"
        print(f"{rank:3d}  {hit.score:8.3f}  {hit.date or '----------'}  {hit.title}{flag}")


if __name__ == "__main__":
    main()
