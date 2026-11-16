"""Data report for the slides (step D6): `results/data_report.md`.

Run: `uv run python -m wikisearch.ingest.report` (about 15 s, 0.8 GB of RAM; needs the dump in
`data/raw/`).

Every number and every example is computed from the dump with the parser's own functions, so the
report always describes the documents that are actually indexed: rerun it whenever the parser
changes. The examples are fixed page ids, chosen by hand because they are short and readable;
the script stops if one of them disappears.
"""

import argparse
import csv
import re
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

from wikisearch import config
from wikisearch.ingest import parse as P

REPORT_MD = config.ROOT / "results" / "data_report.md"
INDEXING_CSV = config.ROOT / "results" / "indexing.csv"

# Hand-picked examples (page ids).
EX_DATE_TEMPLATE = "48882"  # {{luogodata|mercoledì|luogo=Bruxelles|data=20 maggio 2020}}
EX_DATE_CATEGORY = "31887"  # TV schedule dated only by its daily category
EX_ABSTRACT = "20962"  # SuperEnalotto draw whose abstract is only the date
EX_CATEGORIES = "49244"  # maintenance and daily categories mixed with topical ones
EX_LEAK = "31695"  # source title that paraphrases the article title
EX_INLINE_SOURCE = "35705"  # source template with no "Fonti" heading at all

_HEADING_RE = re.compile(r"^(=+)\s*(.+?)\s*\1\s*$", re.MULTILINE)
_SOURCE_TEMPLATE_RE = re.compile(r"\{\{\s*(?:fonte|fonteestera)\s*[|}]", re.IGNORECASE)
_SOURCE_HEADING_RE = re.compile(r"^font[ei]\b", re.IGNORECASE)  # "Fonti", "Fonte", "Fonti giornalistiche"


def n(value: int | float) -> str:
    """Number with a thousands separator, as the report is in English."""
    return f"{value:,}" if isinstance(value, int) else f"{value:,.1f}"


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "-"


def sources_outside(wikitext: str) -> tuple[bool, bool]:
    """Whether at least one source template is (1) outside every "Fonti"-like section, (2) outside
    every section that the parser drops by its heading. A template is inside a section when that
    heading, or one of its parent headings, comes before it."""
    headings = [(m.start(), len(m.group(1)), P.wikitext_plain(m.group(2)).strip())
                for m in _HEADING_RE.finditer(wikitext)]
    outside_fonti = outside_dropped = False
    for match in _SOURCE_TEMPLATE_RE.finditer(wikitext):
        stack: list[tuple[int, str]] = []  # (level, heading) of the sections that contain the template
        for pos, level, text in headings:
            if pos > match.start():
                break
            stack = [(lv, t) for lv, t in stack if lv < level] + [(level, text)]
        outside_fonti |= not any(_SOURCE_HEADING_RE.match(t) for _, t in stack)
        outside_dropped |= not any(P._DROPPED_SECTIONS_RE.match(t) for _, t in stack)
    return outside_fonti, outside_dropped


# Function words left out when showing which words a query and a text share.
_STOP_WORDS = {"il", "lo", "la", "i", "gli", "le", "un", "una", "di", "a", "da", "in", "con", "su",
               "per", "e", "ma", "ha", "ho", "è", "che", "non", "si", "del", "della", "al", "alla"}


def words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def non_published_kind(doc: dict) -> str:
    if doc["title"].lower().startswith("speciale"):
        return "special pages (\"Speciale ...\" hubs and their subpages)"
    if doc["title"].startswith("Prima serata televisiva"):
        return "daily TV schedules"
    if doc["_tables"]:
        return "pages with tables (results, standings, calendars)"
    return "other (sport round reports in prose, news never reviewed, drafts)"


def measure(path: Path) -> dict:
    counts: Counter = Counter()
    records, lines, duplicates = P.read_latest(path, counts)
    docs, raw = [], {}
    for record in records:
        doc = P.parse_page(record)
        wikitext = record.get("article_body", {}).get("wikitext", "") or ""
        raw[doc["id"]] = {
            "categories": [c["name"].removeprefix("Categoria:") for c in record.get("categories", []) or []],
            "abstract": record.get("abstract") or "",
            "agencies": [s["agency"] for s in doc["sources"] if s["agency"]],
            "head": wikitext.lstrip()[:200],
            "date_template": next((name for name, _ in P.find_templates(wikitext, {"data", "luogodata"})), None)
            if doc["date_source"] == "template" else None,
            "outside": sources_outside(wikitext) if doc["sources"] else (False, False),
            "source_wikitext": next((m.group(0) for m in re.finditer(r"\{\{\s*fonte\b.*?\}\}", wikitext,
                                                                       re.IGNORECASE | re.DOTALL)), ""),
        }
        docs.append(doc)
    P.normalize_agencies(docs)
    docs.sort(key=lambda d: int(d["id"]))
    by_id = {d["id"]: d for d in docs}
    for example in (EX_DATE_TEMPLATE, EX_DATE_CATEGORY, EX_ABSTRACT, EX_CATEGORIES, EX_LEAK, EX_INLINE_SOURCE):
        if example not in by_id:
            raise SystemExit(f"example page {example} is no longer in the corpus: pick another one")
    return {"lines": lines, "duplicates": duplicates, "counts": counts, "docs": docs, "raw": raw,
            "by_id": by_id}


def mean_indexing() -> list[tuple[str, bool, int, float, float]]:
    """(index, embeddings, builds, mean seconds, size MB) from the last three full-corpus builds."""
    if not INDEXING_CSV.exists():
        return []
    rows = defaultdict(list)
    with open(INDEXING_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["input"].endswith("docs.jsonl"):
                rows[(row["index"], row["embeddings"] == "True")].append(row)
    out = []
    for (index, embeddings), group in sorted(rows.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        last = group[-3:]
        out.append((index, embeddings, len(last), statistics.mean(float(r["seconds"]) for r in last),
                    int(last[-1]["size_bytes"]) / 1e6))
    return out


def render(m: dict) -> str:
    docs, raw, by_id = m["docs"], m["raw"], m["by_id"]
    total = len(docs)
    published = sum(d["published"] for d in docs)
    out: list[str] = []
    w = out.append

    w("# Data report")
    w("")
    w("Generated by `uv run python -m wikisearch.ingest.report` from the Italian Wikinews dump of "
      "20 March 2025 (Wikimedia Enterprise HTML, `itwikinews-NS0-20250320`). Every number below is "
      "recomputed from the dump with the parser of `wikisearch/ingest/parse.py`: the report "
      "describes exactly the documents that are indexed. Base of Daniel's slides (the data and its "
      "challenges, the indexing choices).")
    w("")

    # -- 1. Overview ---------------------------------------------------------------------------
    years = Counter(d["date"][:4] for d in docs if d["date"])
    dated = sum(years.values())
    golden = sum(c for y, c in years.items() if "2005" <= y <= "2008")
    lengths = sorted(d["n_chars"] for d in docs)

    def q(p: float) -> int:
        return lengths[int(p * (len(lengths) - 1))]

    w("## 1. The corpus at a glance")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| lines in the dump | {n(m['lines'])} |")
    w(f"| documents after removing duplicates | {n(total)} |")
    w(f"| published (`Categoria:Pubblicati`) | {n(published)} ({pct(published, total)}) |")
    w(f"| with a news date | {n(dated)} ({pct(dated, total)}) |")
    w(f"| with at least one source | {n(sum(bool(d['sources']) for d in docs))} |")
    w(f"| sources in all | {n(sum(len(d['sources']) for d in docs))} |")
    w(f"| with at least one topical category | {n(sum(bool(d['categories']) for d in docs))} |")
    w(f"| with Wikipedia entities (`[[w:...]]` links) | {n(sum(bool(d['entities']) for d in docs))} |")
    w(f"| with an image | {n(sum(bool(d['image_url']) for d in docs))} |")
    w(f"| body length in characters: median (p10, p90) | {n(q(0.5))} ({n(q(0.1))}, {n(q(0.9))}) |")
    w("")
    first, last = min(years), max(years)
    w(f"News from {first} to {last}, very unevenly: {n(golden)} dated documents "
      f"({pct(golden, dated)}) are from 2005-2008, the years when Italian Wikinews was most active. "
      "Per year: " + ", ".join(f"{y} {n(c)}" for y, c in sorted(years.items())) + ".")
    w("")
    w(f"Lengths are very uneven too: {n(sum(x < 300 for x in lengths))} documents have under 300 "
      f"characters, {n(sum(x > 10000 for x in lengths))} over 10,000; the longest is "
      f"\"{max(docs, key=lambda d: d['n_chars'])['title']}\" ({n(lengths[-1])} characters).")
    w("")

    # -- 2. Challenges -------------------------------------------------------------------------
    w("## 2. The challenges, with numbers and one real example each")
    w("")
    w("Each item: what makes the data hard, how much of the corpus it touches, a real page, what "
      "we did, and why.")
    w("")

    # 2.1 duplicates
    repeated = {k: c for k, c in m["counts"].items() if c > 1}
    worst_id, worst = max(repeated.items(), key=lambda kv: kv[1])
    w("### 2.1 The same page appears more than once")
    w("")
    w(f"{n(len(repeated))} page ids appear on more than one line ({n(m['duplicates'])} extra lines): "
      f"{n(sum(c == 2 for c in repeated.values()))} twice, the others up to {worst} times. Example: "
      f"\"{by_id[str(worst_id)]['title']}\" (id {worst_id}) is on {worst} lines, one per revision. "
      "**We keep the version with the latest `date_modified`**: the dump is a snapshot, and older "
      "revisions would be near-identical documents competing in the ranking.")
    w("")

    # 2.2 date
    template_head = Counter()
    for d in docs:
        if raw[d["id"]]["date_template"]:
            template_head[raw[d["id"]]["date_template"]] += 1
    sources = Counter(d["date_source"] for d in docs)
    ex = by_id[EX_DATE_TEMPLATE]
    exc = by_id[EX_DATE_CATEGORY]
    daily = [c for c in raw[EX_DATE_CATEGORY]["categories"] if P._DAILY_CATEGORY_RE.match(c)]
    undated = [d for d in docs if d["date_source"] == "none"]
    w("### 2.2 The news date is not a field")
    w("")
    w("The dump has `date_modified` (the last edit, often years later) but no publication date. "
      "The date is written by hand in a template at the top of the wikitext, in Italian, "
      f"in two templates: `{{{{data}}}}` ({n(template_head['data'])} pages) and `{{{{luogodata}}}}` "
      f"({n(template_head['luogodata'])}, with the place). Example, \"{ex['title']}\":")
    w("")
    w(f"    {raw[EX_DATE_TEMPLATE]['head'].splitlines()[0]}")
    w("")
    w(f"becomes `date: {ex['date']}`. Without a template we fall back to the daily category "
      f"(\"{exc['title']}\", category `{daily[0]}` -> `{exc['date']}`).")
    w("")
    w(f"Result: {n(sources['template'])} dates from the template, {n(sources['category'])} from the "
      f"category, {n(sources['none'])} documents without a date "
      f"({n(sum(d['published'] for d in undated))} of them published). `date_source` records where "
      "each date comes from. **Why it matters:** the date filter and the time-bound queries of the "
      "`manual` set (\"elezioni 2008\") depend on it.")
    w("")

    # 2.3 abstract
    short = [d for d in docs if len(raw[d["id"]]["abstract"]) < 40]
    starts_with_date = sum(
        1 for d in docs if d["date"] and P.parse_date(raw[d["id"]]["abstract"][:60]) == d["date"])
    exa = by_id[EX_ABSTRACT]
    w("### 2.3 The dump's abstract is not a usable lead")
    w("")
    w(f"The dump has an `abstract` field, but {n(starts_with_date)} abstracts start with the date "
      f"line and {n(len(short))} are under 40 characters. Example, \"{exa['title']}\": the abstract "
      f"is only \"{raw[EX_ABSTRACT]['abstract'].replace(chr(160), ' ')}\". **We build `lead` from the HTML** (first real "
      f"paragraph after the date): \"{exa['lead']}\". The lead is what the embeddings see (title + "
      "lead), so a date in its place would make every vector of the same day look alike.")
    w("")

    # 2.4 categories
    raw_cats = Counter(c for d in docs for c in raw[d["id"]]["categories"])
    clean_cats = Counter(c for d in docs for c in d["categories"])
    daily_cats = {c for c in raw_cats if P._DAILY_CATEGORY_RE.match(c)}
    maint = {c for c in raw_cats if c in P.MAINTENANCE_CATEGORIES or c.startswith(P._MAINTENANCE_PREFIXES)}
    exk = by_id[EX_CATEGORIES]
    w("### 2.4 Categories mix topics, places, dates and maintenance")
    w("")
    w(f"{n(len(raw_cats))} distinct categories in the dump, {n(sum(raw_cats.values()))} assignments. "
      f"{n(len(daily_cats))} of them are daily date categories (one per day, "
      f"{n(sum(raw_cats[c] for c in daily_cats))} assignments) and {n(len(maint))} are maintenance "
      f"categories ({n(sum(raw_cats[c] for c in maint))} assignments: "
      + ", ".join(f"`{c}` {n(raw_cats[c])}" for c in sorted(maint, key=lambda c: -raw_cats[c])[:3])
      + "). Example, \"" + exk["title"] + "\":")
    w("")
    w("    dump:    " + ", ".join(raw[EX_CATEGORIES]["categories"]))
    w("    indexed: " + ", ".join(exk["categories"]))
    w("")
    w(f"After cleaning: {n(len(clean_cats))} categories, {n(sum(clean_cats.values()))} assignments. "
      "Top: " + ", ".join(f"{c} {n(k)}" for c, k in clean_cats.most_common(6)) + ". "
      f"{n(sum(k == 1 for k in clean_cats.values()))} categories are used by a single page. "
      "**Why:** categories are a facet in the interface; maintenance labels and dates (already in "
      "`date`) would fill the facet with noise.")
    w("")

    # 2.5 agencies
    spellings: dict[str, Counter] = defaultdict(Counter)
    raw_names: set[str] = set()
    keyless: Counter = Counter()  # names with no ASCII letter or digit (Cyrillic, "-"): kept as written
    for d in docs:
        for a in raw[d["id"]]["agencies"]:
            raw_names.add(a)
            if P.agency_key(a):
                spellings[P.agency_key(a)][a] += 1
            else:
                keyless[a] += 1
    groups = sorted(spellings.values(), key=lambda c: -sum(c.values()))
    agencies = Counter(a for d in docs for a in d["agencies"])
    top_name, top_count = groups[0].most_common(1)[0]
    top_total = sum(groups[0].values())
    top_missed = top_total - top_count
    w("### 2.5 The same newspaper is written in many ways")
    w("")
    w(f"Sources name their agency by hand: {n(len(raw_names))} different spellings. The top "
      "groups:")
    w("")
    w("| agency (name kept) | sources | spellings in the dump |")
    w("|---|---|---|")
    for group in groups[:5]:
        w(f"| {group.most_common(1)[0][0]} | {n(sum(group.values()))} | "
          + ", ".join(f"`{s}` {n(c)}" for s, c in group.most_common(6))
          + (f", +{len(group) - 6} more" if len(group) > 6 else "") + " |")
    w("")
    w(f"**We normalise with a key** (lowercase, no accents, no leading article, no `.it`/`.com`, "
      f"no punctuation) plus {len(P.AGENCY_ALIASES)} explicit aliases (`Corriere.it` -> Corriere "
      "della Sera, `AGI` = Agenzia Giornalistica Italia, ...), and display the most frequent "
      f"spelling of each group: {n(len(raw_names))} -> {n(len(agencies))} agencies, "
      f"{n(sum(len(c) > 1 for c in spellings.values()))} of which merged more than one spelling. "
      "Most used afterwards (documents): "
      + ", ".join(f"{a} {n(c)}" for a, c in agencies.most_common(6)) + ". **Why:** the agency is a "
      f"filter in the interface; without this, filtering on `{top_name}` would miss "
      f"{pct(top_missed, top_total)} of its sources.")
    w("")

    # 2.6 near duplicates
    series = Counter(d["series_key"] for d in docs)
    in_big = sum(c for c in series.values() if c >= 5)
    lottery = next(k for k, _ in series.most_common() if "SuperEnalotto" in k)
    lottery_titles = [d["title"] for d in docs if d["series_key"] == lottery][:3]
    w("### 2.6 Template-generated near-duplicates")
    w("")
    w(f"Many pages are filled from the same template: same title up to the numbers, almost the same "
      f"text. {n(sum(1 for c in series.values() if c >= 5))} title patterns (digits replaced by `#`) "
      f"have 5 or more pages, {n(in_big)} documents in all ({pct(in_big, total)} of the corpus). "
      "The largest:")
    w("")
    w("| pattern (`series_key`) | pages |")
    w("|---|---|")
    for key, count in series.most_common(5):
        w(f"| {key} | {n(count)} |")
    w("")
    w("Example: " + "; ".join(f"\"{t}\"" for t in lottery_titles) + ". **We keep them** (they are "
      "real news) and store `series_key`, so the interface can collapse a series into one result "
      "(stretch experiment E7). They also make some queries hard: \"risultati SuperEnalotto\" has "
      f"{n(series[lottery])} almost equally good answers.")
    w("")

    # 2.7 non-published
    nonpub = [d for d in docs if not d["published"]]
    kinds = Counter(non_published_kind(d) for d in nonpub)
    w("### 2.7 Not every page is a news article")
    w("")
    w(f"{n(len(nonpub))} documents ({pct(len(nonpub), total)}) are not in `Categoria:Pubblicati`:")
    w("")
    for kind, count in kinds.most_common():
        w(f"1. {kind}: {n(count)}")
    w("")
    w(f"Only {n(sum(bool(d['date']) for d in nonpub))} of them have a date; median length "
      f"{n(int(statistics.median(d['n_chars'] for d in nonpub)))} characters. **We keep them, "
      "flagged with `published: false`** (decided 16 Nov): some answer real queries (a standings "
      "table, an election special), and the evaluation needs every page. Whether to rank them "
      "lower is experiment E5 (boost on `published`).")
    w("")

    # 2.8 tables
    with_tables = [d for d in docs if d["_tables"]]
    table_chars = sum(d["_table_chars"] for d in docs)
    text_chars = sum(d["_text_chars"] for d in docs)
    only_tables = [d for d in with_tables if d["_table_chars"] == d["_text_chars"]]
    w(f"### 2.8 {pct(table_chars, text_chars)} of the text is in tables")
    w("")
    w(f"{n(len(with_tables))} documents ({n(sum(d['published'] for d in with_tables))} published) "
      f"contain tables: match reports, standings, lottery draws, TV schedules. Tables hold "
      f"{pct(table_chars, text_chars)} of all the text of the corpus, and {n(len(only_tables))} "
      f"documents ({n(sum(d['published'] for d in only_tables))} published) are nothing but tables. "
      "**We keep tables as text, one line per row** (decided 16 Nov; the brief first said "
      "paragraphs and lists only): dropping them would leave those pages empty and unfindable.")
    w("")

    # 2.9 leakage
    exl = by_id[EX_LEAK]
    query = exl["sources"][0]["title"]
    shared = words(query) & words(exl["title"])
    outside = [d for d in docs if raw[d["id"]]["outside"][0]]
    outside_all = [d for d in docs if raw[d["id"]]["outside"][1]]
    exi = by_id[EX_INLINE_SOURCE]
    natural = P.leakage_count(docs)
    w("### 2.9 Leakage: the test queries are written inside the pages")
    w("")
    w("Our known-item test set (`fonti`) uses the titles of the sources as queries: headlines "
      "written by other newspapers about the same event. Those titles are inside each page, in the "
      f"`{{{{fonte}}}}` templates. Example, \"{exl['title']}\":")
    w("")
    for line in raw[EX_LEAK]["source_wikitext"].splitlines():
        w(f"    {line}")
    w("")
    w(f"Query: \"{query}\". It shares "
      + (f"only {', '.join(f'`{x}`' for x in sorted(shared))} with the title" if shared else "no word with the title")
      + ", and the `italian` analyzer does not help: its light stemmer gives `scagion` for "
      "\"scagiona\" and `scagionat` for \"scagionato\". Searching the title alone cannot find the "
      "article; the body can, through "
      + ", ".join(f"`{x}`" for x in sorted(words(query) & words(exl["body"]) - _STOP_WORDS))
      + ". This is why we search title, lead and body together, and why queries that share no "
      "word at all are left to the embeddings (experiment E3). If the source title were "
      "searchable, the page would contain the query word for word and the test would measure "
      "nothing.")
    w("")
    w(f"**We remove every source template from `body`**, not only the \"Fonti\" section: in "
      f"{n(len(outside))} pages at least one source is not in a \"Fonti\" section (mostly under "
      "\"Collegamenti esterni\"), and even dropping every section the parser drops by heading "
      f"(\"Fonti\", \"Collegamenti esterni\", \"Note\", ...) would leave sources in "
      f"{n(len(outside_all))} pages: with no heading at all, like \"{exi['title']}\", in the text "
      "before the \"Fonti\" heading, or under headings such as \"Riferimenti\" and "
      "\"Aggiornamenti\". Check: the body still contains a source title "
      f"(4+ words) verbatim in {n(natural)} documents; read by hand, they are natural (the name of "
      "an exhibition or a play quoted in both), not source text left behind. The titles are kept "
      "in a separate `sources_text` field, searched only by `bm25-italian-leak`, to measure how much "
      "leakage would inflate the results (experiment E4).")
    w("")

    # -- 3. Indices ----------------------------------------------------------------------------
    indexing = mean_indexing()
    if indexing:
        w("## 3. The indices")
        w("")
        w("Two indices with the same fields and two text analyses (experiment E1): `standard` "
          "(tokenise, lowercase) and the built-in `italian` (elision, Italian stop words, light "
          "stemmer: `elezioni` = `elezione`, `l'Italia` = `Italia`). 1 shard, 0 replicas, "
          "Elasticsearch 9.5.0 with a 1 GB heap on an 8 GB laptop. Means of the last three builds "
          "(`results/indexing.csv`):")
        w("")
        w("| index | vectors | builds | seconds (mean) | size (MB) |")
        w("|---|---|---|---|---|")
        for index, embeddings, builds, seconds, size in indexing:
            w(f"| `{index}` | {'yes' if embeddings else 'no'} | {builds} | {seconds:.1f} | {size:.1f} |")
        w("")
        stats = {(i, e): (s, mb) for i, e, _, s, mb in indexing}
        std, ita = stats.get(("wikinews-standard", False)), stats.get(("wikinews-italian", False))
        plain, vec = ita, stats.get(("wikinews-italian", True))
        vector_mb = total * 384 * 4 / 1e6
        if std and ita:
            w(f"1. Without vectors, `italian` is {100 * (1 - ita[1] / std[1]):.0f}% smaller than `standard`: stop words "
              "are gone and stems merge word forms, so fewer distinct terms and postings.")
        if vec and plain:
            w(f"2. Vectors (e5-small, 384 dimensions, one per document from title + lead) make the "
              f"build {vec[0] / plain[0]:.1f}x slower (the HNSW graph) and add {vec[1] - plain[1]:.1f} MB, "
              f"about the size of the raw float32 vectors ({n(total)} x 384 x 4 bytes = "
              f"{vector_mb:.1f} MB): `index_options: hnsw` keeps them unquantized. Quantization "
              "(`int8_hnsw`, `bbq_hnsw`) is the stretch experiment E8.")
        w("3. The first build is slower (JVM warm-up): that is why every build is repeated three "
          "times.")
        w("")

    # -- 4. Limits -----------------------------------------------------------------------------
    entities = Counter(e for d in docs for e in d["entities"])
    noisy = [e for e in ("Central European Time", "Central European Summer Time", "Calcio di rigore")
             if e in entities]
    w("## 4. Known limits")
    w("")
    w(f"1. {n(sources['none'])} documents have no date (mostly specials and non-published pages): "
      "a date filter hides them.")
    w("2. The agency key removes a leading article even without a space (needed for `ilpost.it`, "
      "`LaStampa`): it merges two pairs it should not (`VG` with `IVG`, `post.com` with Il Post), "
      "one or two sources each.")
    w(f"3. The agency key keeps only ASCII letters and digits: {n(len(keyless))} names in Cyrillic "
      f"or made of punctuation (`-`), {n(sum(keyless.values()))} sources, are not normalised and "
      "stay as written.")
    w("4. Entities are the Wikipedia links of the text and include noise from templates of match "
      "reports: " + ", ".join(f"`{e}` ({n(entities[e])} pages)" for e in noisy) + ".")
    w("5. Some `{{fonte}}` titles are in English although the template is not `{{fonteestera}}` "
      "(e.g. Euronews in English); Gioia's brief drops them from the `fonti` test set with a rule on "
      "English function words (G2, not built yet).")
    w("6. Printed sources (`{{fontecarta}}`) are not parsed: they are not in the contract.")
    w("")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, default=config.RAW_DUMP)
    parser.add_argument("--output", type=Path, default=REPORT_MD)
    args = parser.parse_args()
    start = time.perf_counter()
    text = render(measure(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {args.output} in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
