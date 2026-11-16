"""Parse the Wikinews dump into processed documents (step D2, contract: docs/contracts.md section 1).

Input: the Wikimedia Enterprise HTML dump (one JSON page per line, `config.RAW_DUMP`).
Output: `config.DOCS_JSONL` (one document per line), the committed sample `config.SAMPLE_JSONL`
and a coverage report in `results/parse_report.json`.

Run: `uv run python -m wikisearch.ingest.parse`

Where each field comes from:
1. Text (`lead`, `body`): the Parsoid HTML of the article, because the wikitext would need a full
   template expander. Sections about sources and links ("Fonti", "Collegamenti esterni", "Note",
   ...) are dropped, and so is every transclusion of a source template wherever it appears:
   the titles of the sources are the queries of the known-item test set, so they must never be
   searchable by default (leakage).
2. Metadata (date, sources, entities): the wikitext, where the templates are still readable.
3. Categories, image, Wikidata id: the structured fields of the dump.
"""

import argparse
import json
import random
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from selectolax.lexbor import LexborHTMLParser

from wikisearch import config

REPORT_JSON = config.ROOT / "results" / "parse_report.json"
SAMPLE_SIZE = 300
SAMPLE_SEED = 42

MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7,
    "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}
_DATE_RE = re.compile(
    r"(\d{1,2})\s*[º°o]?\s+(" + "|".join(MONTHS) + r")\s+(\d{4})", re.IGNORECASE
)
_DAILY_CATEGORY_RE = re.compile(r"^\d{1,2}\s*[º°]?\s+(" + "|".join(MONTHS) + r")\s+\d{4}$", re.IGNORECASE)

# Maintenance categories: about the page, not about the news. Removed from `categories`.
MAINTENANCE_CATEGORIES = {
    "Pubblicati",
    "Articoli archiviati",
    "Articoli da controllare per l'archiviazione",
    "Articoli da archiviare",
    "Articoli da non elencare",
    "Articoli da sistemare",
    "Articoli in vetrina",
    "Articolo in CC BY-SA",
    "Notizie da prima pagina",
    "Notizie originali",
    "Notizie per Wikivoyage scadute",
    "Categoria da definire",
    "Da cancellare subito",
    "Bozze",
}
_MAINTENANCE_PREFIXES = ("Articoli con box", "Box ", "Pagine ", "Template ", "Da cancellare", "Voci ")

# Sections whose heading matches are not part of the article text.
_DROPPED_SECTIONS_RE = re.compile(
    r"^(fonti|fonte|collegamenti esterni|note|articoli correlati|notizie correlate"
    r"|notizie precedenti|altri progetti|risorse|voci correlate|vedi anche)\b",
    re.IGNORECASE,
)

# Block-level templates whose text is part of the article (interview questions, quotations,
# match reports). Every other block-level template is a box, a banner or a navigation aid.
KEEP_BLOCK_TEMPLATES = {"interv", "quote", "citazione", "incontro di club", "footballbox", "hockeybox",
                        "waterpolobox"}
# Inline templates that are never text: the date line and the publication marker.
DROP_INLINE_TEMPLATES = {"data", "luogodata", "pubblicato", "archiviato"}
SOURCE_TEMPLATES = {"fonte": False, "fonteestera": True}  # name -> foreign
_BLOCK_TAGS = {"div", "table", "ul", "ol", "dl", "figure", "center", "section", "p", "blockquote"}
_TEXT_BLOCKS = {"p", "li", "dd", "dt", "pre", "blockquote"}
_SKIPPED_TAGS = {"figure", "style", "script", "h1", "h2", "h3", "h4", "h5", "h6", "link", "meta"}

# Agency names: the same newspaper is written in many ways ("la Repubblica", "La Repubblica",
# "Repubblica", "repubblica.it"). `agency_key` reduces them to a key; spellings with the same key
# are one agency, displayed with their most frequent spelling. ALIASES merges keys that the rule
# cannot merge on its own.
AGENCY_ALIASES = {
    "corriere": "corrieredellasera",
    "ilcorrieredellasera": "corrieredellasera",
    "gazzetta": "gazzettadellosport",
    "agenziagiornalisticaitalia": "agi",
    "rainews24": "rainews",
    "tgcom24": "tgcom",
    "bbcnews": "bbc",
    "newyorktimes": "thenewyorktimes",
    "federazioneitalianarugby": "federazionerugbyitalia",
    "legab": "legaserieb",
    "seriebkt": "legaserieb",
    "uefacom": "uefa",
    "legabasketit": "legabasket",
    "repubblicaquotidiano": "repubblica",
}


def agency_key(name: str) -> str:
    key = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().strip()
    key = re.sub(r"\s*\((quotidiano|giornale|agenzia)\)$", "", key)
    key = re.sub(r"^(https?://)?(www\.)?", "", key)
    key = re.sub(r"\.(it|com|net|org|eu|co\.uk)(/.*)?$", "", key)
    key = re.sub(r"^(il|la|lo|l'|i|le|the)\s*", "", key)
    key = re.sub(r"[^a-z0-9]", "", key)
    return AGENCY_ALIASES.get(key, key)


# ---------------------------------------------------------------------------------------------
# Wikitext helpers
# ---------------------------------------------------------------------------------------------


def find_templates(wikitext: str, names: set[str]) -> list[tuple[str, str]]:
    """Return (lowercased name, inner text) of every template `{{name|...}}` in `names`,
    matching nested braces."""
    found = []
    for match in re.finditer(r"\{\{\s*([^|{}\n]+?)\s*(?=[|}])", wikitext):
        name = match.group(1).strip().lower().replace("_", " ")
        if name.startswith("template:"):
            name = name[len("template:"):]
        if name not in names:
            continue
        depth, i = 0, match.start()
        while i < len(wikitext) - 1:
            pair = wikitext[i:i + 2]
            if pair == "{{":
                depth += 1
                i += 2
            elif pair == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    found.append((name, wikitext[match.end():i - 2]))
                    break
            else:
                i += 1
    return found


def template_params(inner: str) -> tuple[list[str], dict[str, str]]:
    """Split the inside of a template (after its name) into positional and named parameters,
    ignoring `|` nested in links or other templates."""
    parts, depth, current = [], 0, []
    i = 0
    while i < len(inner):
        pair = inner[i:i + 2]
        if pair in ("{{", "[["):
            depth += 1
            current.append(pair)
            i += 2
            continue
        if pair in ("}}", "]]"):
            depth -= 1
            current.append(pair)
            i += 2
            continue
        if inner[i] == "|" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(inner[i])
        i += 1
    parts.append("".join(current))
    positional, named = [], {}
    for part in parts[1:] if parts and not parts[0].strip() else parts:
        if "=" in part and re.match(r"^\s*[\w\s]+\s*=", part):
            key, value = part.split("=", 1)
            named[key.strip().lower()] = value.strip()
        else:
            positional.append(part.strip())
    return positional, named


def wikitext_plain(value: str) -> str:
    """Plain text of a short wikitext value (a source title, an agency)."""
    value = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", value)  # [[target|label]] -> label
    value = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", value)  # [url label] -> label
    value = re.sub(r"\{\{[^{}]*\}\}", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", value).strip()


def parse_date(text: str) -> str | None:
    match = _DATE_RE.search(text or "")
    if not match:
        return None
    day, month, year = int(match.group(1)), MONTHS[match.group(2).lower()], int(match.group(3))
    if not (1 <= day <= 31 and 1990 <= year <= 2030):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def extract_date(wikitext: str, raw_categories: list[str]) -> tuple[str | None, str]:
    for name, inner in find_templates(wikitext, {"data", "luogodata"}):
        positional, named = template_params(inner)
        for value in [*positional, *named.values()]:
            date = parse_date(wikitext_plain(value))
            if date:
                return date, "template"
    for category in raw_categories:
        if _DAILY_CATEGORY_RE.match(category):
            date = parse_date(category)
            if date:
                return date, "category"
    return None, "none"


def extract_sources(wikitext: str) -> list[dict]:
    sources = []
    for name, inner in find_templates(wikitext, set(SOURCE_TEMPLATES)):
        _, named = template_params(inner)
        agency = wikitext_plain(named.get("agenzia", "")) or None
        sources.append({
            "agency": agency,
            "title": wikitext_plain(named.get("titolo", "")),
            "url": named.get("url", "").strip() or None,
            "date": parse_date(wikitext_plain(named.get("data", ""))),
            "foreign": SOURCE_TEMPLATES[name],
        })
    return sources


def extract_entities(wikitext: str) -> list[str]:
    entities = []
    for target in re.findall(r"\[\[\s*:?\s*w\s*:\s*([^|\]#]+)", wikitext, re.IGNORECASE):
        target = re.sub(r"\s+", " ", target.replace("_", " ")).strip()
        if target:
            target = target[0].upper() + target[1:]
            if target not in entities:
                entities.append(target)
    return entities


# ---------------------------------------------------------------------------------------------
# HTML -> text
# ---------------------------------------------------------------------------------------------


def _template_names(node) -> list[str]:
    try:
        data = json.loads(node.attributes.get("data-mw") or "{}")
    except json.JSONDecodeError:
        return []
    names = []
    for part in data.get("parts", []):
        if isinstance(part, dict) and "template" in part:
            name = part["template"].get("target", {}).get("wt", "")
            name = name.strip().lower().replace("_", " ")
            if name.startswith("template:"):
                name = name[len("template:"):]
            names.append(name.strip())
    return names


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
    # the separator added between inline nodes leaves "La Spezia , presieduto": remove it
    text = re.sub(r" ([,.;:!?)\]»])", r"\1", text)
    return re.sub(r"([(\[«]) ", r"\1", text)


def _drop_template(names: list[str], tag: str) -> bool:
    if any(n in SOURCE_TEMPLATES or n in DROP_INLINE_TEMPLATES or n.startswith("fonte") for n in names):
        return True
    return tag in _BLOCK_TAGS and not any(n in KEEP_BLOCK_TEMPLATES for n in names)


def html_blocks(html: str) -> tuple[list[str], int]:
    """Text blocks of the article in reading order, and the number of tables kept."""
    tree = LexborHTMLParser(html)
    body = tree.body
    if body is None:
        return [], 0
    dropped_abouts = set()
    for node in body.css('[typeof~="mw:Transclusion"]'):
        if _drop_template(_template_names(node), node.tag):
            about = node.attributes.get("about")
            if about:
                dropped_abouts.add(about)
            else:
                node.decompose()
    to_remove = [n for n in body.css("[about]") if n.attributes.get("about") in dropped_abouts]
    for section in body.css("section"):
        heading = section.css_first("h2, h3")
        if heading is not None and heading.parent == section and _DROPPED_SECTIONS_RE.match(_clean(heading.text())):
            to_remove.append(section)
    to_remove += body.css("sup.reference, .mw-ref, .mw-references-wrap, .noprint, .navbox")
    for node in to_remove:
        try:
            node.decompose()
        except Exception:  # already removed with an ancestor
            pass

    blocks, tables = [], 0

    def walk(node):
        nonlocal tables
        for child in node.iter(include_text=False):
            tag = child.tag
            if tag in _SKIPPED_TAGS:
                continue
            if tag in _TEXT_BLOCKS:
                text = _clean(child.text(separator=" "))
                if text:
                    blocks.append(text)
            elif tag == "table":
                rows = []
                for row in child.css("tr"):
                    cells = [_clean(c.text(separator=" ")) for c in row.css("th, td")]
                    line = " ".join(c for c in cells if c)
                    if line:
                        rows.append(line)
                if rows:
                    tables += 1
                    blocks.append("\n".join(rows))
            else:
                walk(child)

    walk(body)
    return blocks, tables


# ---------------------------------------------------------------------------------------------
# One page
# ---------------------------------------------------------------------------------------------


def parse_page(record: dict) -> dict:
    wikitext = record.get("article_body", {}).get("wikitext", "") or ""
    html = record.get("article_body", {}).get("html", "") or ""
    raw_categories = [c["name"].removeprefix("Categoria:") for c in record.get("categories", []) or []]

    date, date_source = extract_date(wikitext, raw_categories)
    blocks, tables = html_blocks(html)
    lead = next((b for b in blocks if "\n" not in b and len(b) >= 20), blocks[0] if blocks else "")
    body = "\n\n".join(blocks)

    categories = []
    for name in raw_categories:
        if name in MAINTENANCE_CATEGORIES or name.startswith(_MAINTENANCE_PREFIXES):
            continue
        if _DAILY_CATEGORY_RE.match(name) or name in categories:
            continue
        categories.append(name)

    title = record.get("name", "")
    image = record.get("image") or {}
    entity = record.get("main_entity") or {}
    return {
        "id": str(record["identifier"]),
        "title": title,
        "url": record.get("url", ""),
        "date": date,
        "date_source": date_source,
        "lead": lead,
        "body": body,
        "categories": categories,
        "sources": extract_sources(wikitext),
        "agencies": [],  # filled after the whole corpus is read (normalize_agencies)
        "entities": extract_entities(wikitext),
        "wikidata_id": entity.get("identifier"),
        "image_url": image.get("content_url"),
        "published": "Pubblicati" in raw_categories,
        "series_key": re.sub(r"\d+", "#", title),
        "n_chars": len(body),
        "_tables": tables,  # internal, removed before writing
    }


def normalize_agencies(docs: list[dict]) -> int:
    """Give every source the most frequent spelling of its agency; fill `agencies`.
    Returns the number of distinct agencies after normalization."""
    spellings: dict[str, Counter] = defaultdict(Counter)
    for doc in docs:
        for source in doc["sources"]:
            if source["agency"]:
                spellings[agency_key(source["agency"])][source["agency"]] += 1
    canonical = {key: counter.most_common(1)[0][0] for key, counter in spellings.items() if key}
    for doc in docs:
        agencies = []
        for source in doc["sources"]:
            if source["agency"]:
                source["agency"] = canonical.get(agency_key(source["agency"])) or source["agency"]
                if source["agency"] not in agencies:
                    agencies.append(source["agency"])
        doc["agencies"] = agencies
    return len(canonical)


# ---------------------------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------------------------


def read_latest(path: Path) -> tuple[list[dict], int, int]:
    """Read the dump line by line and keep, for each identifier, the most recent version.
    Returns (records, lines read, duplicates removed)."""
    latest: dict[int, dict] = {}
    lines = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            lines += 1
            record = json.loads(line)
            key = record["identifier"]
            old = latest.get(key)
            if old is None or (record.get("date_modified") or "") > (old.get("date_modified") or ""):
                latest[key] = record
    return list(latest.values()), lines, lines - len(latest)


_LOTTERY_RE = re.compile(r"superenalotto|\blotto\b|10elotto|win for life|vincicasa|eurojackpot|million day",
                         re.IGNORECASE)


def stratum(doc: dict) -> str:
    if doc["title"].lower().startswith("speciale"):
        return "special"
    if _LOTTERY_RE.search(doc["title"]):
        return "lottery"
    if not doc["published"]:
        return "non-published"
    if doc["_tables"]:
        return "sport-table"
    year = doc["date"][:4] if doc["date"] else "undated"
    return f"news-{year}"


SAMPLE_QUOTAS = {"special": 15, "lottery": 25, "non-published": 40, "sport-table": 40}


def build_sample(docs: list[dict], size: int = SAMPLE_SIZE, seed: int = SAMPLE_SEED) -> list[dict]:
    """A fixed, stratified sample: the special kinds of page get a quota each, news fill the rest
    proportionally to the number of news per year (at least one per year)."""
    rng = random.Random(seed)
    groups: dict[str, list[dict]] = defaultdict(list)
    for doc in sorted(docs, key=lambda d: int(d["id"])):
        groups[stratum(doc)].append(doc)
    chosen = []
    for name, quota in SAMPLE_QUOTAS.items():
        chosen += rng.sample(groups[name], min(quota, len(groups[name])))
    news = sorted(g for g in groups if g.startswith("news-"))
    remaining = size - len(chosen)
    total_news = sum(len(groups[g]) for g in news)
    for g in news:
        quota = max(1, round(remaining * len(groups[g]) / total_news))
        chosen += rng.sample(groups[g], min(quota, len(groups[g])))
    rng.shuffle(chosen)
    return sorted(chosen[:size], key=lambda d: int(d["id"]))


def leakage_count(docs: list[dict]) -> int:
    """Documents whose body contains, verbatim, the title of one of their sources (4+ words)."""
    count = 0
    for doc in docs:
        body = doc["body"].lower()
        if any(len(s["title"].split()) >= 4 and s["title"].lower() in body for s in doc["sources"]):
            count += 1
    return count


def write_jsonl(docs: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for doc in docs:
            f.write(json.dumps({k: v for k, v in doc.items() if not k.startswith("_")},
                               ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, default=config.RAW_DUMP)
    parser.add_argument("--output", type=Path, default=config.DOCS_JSONL)
    parser.add_argument("--sample", type=Path, default=config.SAMPLE_JSONL)
    parser.add_argument("--no-sample", action="store_true", help="do not rewrite the committed sample")
    args = parser.parse_args()

    start = time.perf_counter()
    records, lines, duplicates = read_latest(args.input)
    docs = sorted((parse_page(r) for r in records), key=lambda d: int(d["id"]))
    raw_agencies = len({s["agency"] for d in docs for s in d["sources"] if s["agency"]})
    distinct_agencies = normalize_agencies(docs)
    write_jsonl(docs, args.output)
    seconds = time.perf_counter() - start

    sample = build_sample(docs)
    if not args.no_sample:
        write_jsonl(sample, args.sample)

    report = {
        "pages_read": lines,
        "duplicates_removed": duplicates,
        "documents": len(docs),
        "published": sum(d["published"] for d in docs),
        "non_published": sum(not d["published"] for d in docs),
        "date_source": dict(Counter(d["date_source"] for d in docs)),
        "with_sources": sum(bool(d["sources"]) for d in docs),
        "sources": sum(len(d["sources"]) for d in docs),
        "foreign_sources": sum(s["foreign"] for d in docs for s in d["sources"]),
        "sources_without_title": sum(not s["title"] for d in docs for s in d["sources"]),
        "distinct_agencies_raw": raw_agencies,
        "distinct_agencies": distinct_agencies,
        "with_category": sum(bool(d["categories"]) for d in docs),
        "with_entities": sum(bool(d["entities"]) for d in docs),
        "with_image": sum(bool(d["image_url"]) for d in docs),
        "with_tables": sum(bool(d["_tables"]) for d in docs),
        "empty_body": sum(not d["body"] for d in docs),
        "empty_lead": sum(not d["lead"] for d in docs),
        "median_body_chars": sorted(d["n_chars"] for d in docs)[len(docs) // 2],
        "body_contains_a_source_title": leakage_count(docs),
        "years": dict(sorted(Counter(d["date"][:4] for d in docs if d["date"]).items())),
        "sample_strata": dict(sorted(Counter(stratum(d) if not stratum(d).startswith("news-") else "news"
                                             for d in sample).items())),
        "seconds": round(seconds, 1),
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"wrote {args.output} ({len(docs)} documents)" + ("" if args.no_sample else f" and {args.sample} ({len(sample)})"))


if __name__ == "__main__":
    main()
