"""Build the `fonti` test set (known-item search).

Each Wikinews article cites external sources, each with its own headline. That headline, written
by another newspaper about the same event, is the query; the article is the only relevant
document (grade 1).

    uv run python -m evaluation.build_fonti                       # full docs.jsonl
    uv run python -m evaluation.build_fonti --input data/sample/docs.sample.jsonl --out <dir>
    uv run python -m evaluation.build_fonti --show-language 50    # eye check of the English rule

Writes `evaluation/testsets/fonti/queries.tsv`, `qrels.txt` and `queries_dev.tsv` (fixed subset
of 1000 queries, seed 42), and prints the funnel, the bucket sizes and the leakage check.
"""

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from wikisearch import config

OUT_DIR = config.ROOT / "evaluation" / "testsets" / "fonti"
SEED = 42
DEV_SIZE = 1000
LEAKAGE_SAMPLE = 300
MIN_WORDS = 4

# Language rule: a title is English when it has one of these words and none of the Italian ones.
# Words that are the same in both languages ("a", "in") are in neither list.
ENGLISH_WORDS = {"the", "of", "for", "and", "with", "to", "is"}
ITALIAN_WORDS = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "del", "dello", "della", "dei",
    "degli", "delle", "da", "dal", "dalla", "dai", "al", "allo", "alla", "ai", "agli", "alle",
    "nel", "nella", "nei", "sul", "sulla", "sui", "che", "per", "con", "non", "e", "è", "ma",
    "più", "sono", "ha", "anche", "tra", "fra",
}

# Stop words for the overlap between query and article title: articles, prepositions,
# conjunctions, the fragments left by elision (l', d', dell', ...) and a few frequent verbs.
STOP_WORDS = ITALIAN_WORDS | {
    "a", "in", "o", "se", "si", "ci", "ne", "su", "l", "d", "c", "s", "dell", "all", "dall",
    "nell", "sull", "un", "quell", "questo", "questa", "come", "dopo", "oltre", "contro", "sarà",
    "era", "essere", "stato", "stata", "hanno", "suo", "sua", "loro", "chi", "cosa", "dove",
}

_WORD = re.compile(r"\w+")
_SPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Single-line text for a TSV cell: tabs and newlines become spaces."""
    return _SPACE.sub(" ", text or "").strip()


def words(text: str) -> list[str]:
    """Lowercased words; punctuation and apostrophes split words ("l'Italia" -> l, italia)."""
    return _WORD.findall((text or "").lower())


def normalise(text: str) -> str:
    """Lowercase, punctuation removed: the key used to find repeated titles and verbatim matches."""
    return " ".join(words(text))


def is_english(title: str) -> bool:
    ws = set(words(title))
    return bool(ws & ENGLISH_WORDS) and not (ws & ITALIAN_WORDS)


def overlap(query: str, doc_title: str) -> float:
    """Jaccard similarity of the word sets without stop words (0 when both are empty)."""
    q = set(words(query)) - STOP_WORDS
    t = set(words(doc_title)) - STOP_WORDS
    if not q and not t:
        return 0.0
    return len(q & t) / len(q | t)


def bucket(value: float) -> str:
    if value < 0.2:
        return "low"
    if value <= 0.5:
        return "mid"
    return "high"


def read_docs(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build(docs: list[dict]) -> dict:
    """Apply the filters in the order of the brief and keep the first valid source per document.

    Returns the queries (one per document, in corpus order), the funnel and the dropped/kept
    titles of the language rule (for the eye check)."""
    # A normalised title is ambiguous when it is the source title of more than one document. All
    # documents count, published or not: a non-published page is in the index too, so it would be
    # a second plausible answer to the query.
    title_docs: dict[str, set[str]] = defaultdict(set)
    for doc in docs:
        for src in doc["sources"]:
            key = normalise(src.get("title") or "")
            if key:
                title_docs[key].add(doc["id"])

    funnel = Counter()
    dropped_english: list[str] = []
    kept_language: list[str] = []
    queries: list[dict] = []
    for doc in docs:
        chosen = None
        for src in doc["sources"]:
            title = clean_text(src.get("title") or "")
            funnel["candidates"] += 1
            if len(words(title)) < MIN_WORDS:
                continue
            funnel["after: at least 4 words"] += 1
            if src.get("foreign"):
                continue
            funnel["after: not foreign"] += 1
            if is_english(title):
                dropped_english.append(title)
                continue
            kept_language.append(title)
            funnel["after: not English"] += 1
            if len(title_docs[normalise(title)]) > 1:
                continue
            funnel["after: not ambiguous"] += 1
            if not doc["published"]:
                continue
            funnel["after: article published"] += 1
            if chosen is None:
                chosen = title
        if chosen is not None:
            ov = overlap(chosen, doc["title"])
            queries.append(
                {
                    "text": chosen,
                    "doc_id": doc["id"],
                    "meta": {"doc_title": doc["title"], "overlap": round(ov, 4), "bucket": bucket(ov)},
                }
            )
    funnel["final: one query per document"] = len(queries)
    for i, q in enumerate(queries, start=1):
        q["qid"] = f"F{i:04d}"
    return {"queries": queries, "funnel": funnel, "dropped_english": dropped_english,
            "kept_language": kept_language}


def leakage_check(queries: list[dict], docs: list[dict], n: int = LEAKAGE_SAMPLE) -> list[dict]:
    """Queries (of a random sample of n) that appear verbatim, normalised, in title + lead + body."""
    by_id = {doc["id"]: doc for doc in docs}
    sample = random.Random(SEED).sample(queries, min(n, len(queries)))
    found = []
    for q in sample:
        doc = by_id[q["doc_id"]]
        text = f" {normalise(doc['title'] + ' ' + doc['lead'] + ' ' + doc['body'])} "
        if f" {normalise(q['text'])} " in text:
            found.append(q)
    return found


def write_queries(path: Path, queries: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for q in queries:
            f.write(f"{q['qid']}\t{q['text']}\t{json.dumps(q['meta'], ensure_ascii=False)}\n")


def write_qrels(path: Path, queries: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for q in queries:
            f.write(f"{q['qid']} 0 {q['doc_id']} 1\n")


def dev_subset(queries: list[dict], size: int = DEV_SIZE) -> list[dict]:
    """Fixed random subset (seed 42), in qid order."""
    if len(queries) <= size:
        return list(queries)
    picked = set(q["qid"] for q in random.Random(SEED).sample(queries, size))
    return [q for q in queries if q["qid"] in picked]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=config.DOCS_JSONL)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--show-language", type=int, default=0, metavar="N",
                        help="print N random titles dropped and N kept by the English rule")
    args = parser.parse_args()

    docs = read_docs(args.input)
    result = build(docs)
    queries = result["queries"]

    args.out.mkdir(parents=True, exist_ok=True)
    write_queries(args.out / "queries.tsv", queries)
    write_qrels(args.out / "qrels.txt", queries)
    dev = dev_subset(queries)
    write_queries(args.out / "queries_dev.tsv", dev)

    print(f"{len(docs)} documents from {args.input}")
    print("Funnel (source titles):")
    for step, count in result["funnel"].items():
        print(f"  {step:32s} {count:6d}")
    buckets = Counter(q["meta"]["bucket"] for q in queries)
    dev_buckets = Counter(q["meta"]["bucket"] for q in dev)
    print("Buckets (overlap with the article title):")
    for b in ("low", "mid", "high"):
        print(f"  {b:5s} {buckets[b]:6d}   dev {dev_buckets[b]:5d}")
    same = sum(normalise(q["text"]) == normalise(q["meta"]["doc_title"]) for q in queries)
    print(f"Queries identical to the article title (normalised): {same}")
    leaked = leakage_check(queries, docs)
    n = min(LEAKAGE_SAMPLE, len(queries))
    share = len(leaked) / n if n else 0.0
    print(f"Leakage check: {len(leaked)}/{n} sampled queries ({share:.1%}) appear verbatim in "
          "title + lead + body")
    for q in leaked[:10]:
        print(f"  {q['qid']} doc {q['doc_id']}: {q['text']}")
    print(f"Wrote {len(queries)} queries ({len(dev)} in queries_dev.tsv) to {args.out}")

    if args.show_language:
        rng = random.Random(SEED)
        for label, titles in (("DROPPED as English", result["dropped_english"]),
                              ("KEPT", result["kept_language"])):
            pick = rng.sample(titles, min(args.show_language, len(titles)))
            print(f"\n{label} ({len(titles)} in all), {len(pick)} at random:")
            for t in pick:
                print(f"  {t}")


if __name__ == "__main__":
    main()
