"""Tests of the parser (step D2) on three real pages of the dump (tests/fixtures/pages.json):

1. 9630 "Strage di Marzabotto: 10 ergastoli e 7 assoluzioni": {{data}}, two {{fonte}} under "Fonti";
2. 15832 "The Verve: fissati 4 concerti aggiuntivi a dicembre": one {{fonteestera}} (foreign source);
3. 35705 "Ligue 1 2012-2013: il PSG pareggia in Corsica ...": a {{fonte}} with no section heading
   at all, so it can only be removed as a template, not as a section.
"""

import json
from pathlib import Path

import pytest

from wikisearch.ingest.parse import (
    agency_key,
    extract_date,
    normalize_agencies,
    parse_date,
    parse_page,
    read_latest,
    template_params,
)

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "pages.json").read_text(encoding="utf-8"))
PAGES = {str(r["identifier"]): r for r in FIXTURES}


@pytest.fixture(scope="module")
def docs():
    parsed = [parse_page(r) for r in FIXTURES]
    normalize_agencies(parsed)
    return {d["id"]: d for d in parsed}


def test_date_from_the_data_template(docs):
    assert docs["9630"]["date"] == "2007-01-13"
    assert docs["9630"]["date_source"] == "template"
    assert docs["15832"]["date"] == "2007-10-03"


def test_date_line_is_not_in_lead_or_body(docs):
    for doc in docs.values():
        assert not doc["lead"].startswith(("13 gennaio 2007", "3 ottobre 2007", "20 agosto 2012"))
    assert docs["9630"]["lead"].startswith("Il tribunale militare di La Spezia, presieduto")


def test_sources_and_foreign_flag(docs):
    marzabotto = docs["9630"]["sources"]
    assert len(marzabotto) == 2
    assert all(not s["foreign"] for s in marzabotto)
    assert marzabotto[0]["title"].startswith("Strage Marzabotto, 10 ergastoli")
    assert set(docs["9630"]["agencies"]) == {"AdnKronos", "Agi"}
    verve = docs["15832"]["sources"]
    assert [s["foreign"] for s in verve] == [True]
    assert verve[0]["title"] == "The Verve announce new tour dates"
    assert verve[0]["agency"] == "New Musical Express"


@pytest.mark.parametrize("page_id", sorted(PAGES))
def test_sources_never_in_body(docs, page_id):
    doc = docs[page_id]
    assert doc["sources"], "every fixture has at least one source"
    body = doc["body"].lower()
    for source in doc["sources"]:
        if len(source["title"].split()) >= 3:
            assert source["title"].lower() not in body, source["title"]
        if source["url"]:
            assert source["url"].lower() not in body
    assert "fonti" not in body.split()


def test_categories_are_clean(docs):
    for doc in docs.values():
        assert "Pubblicati" not in doc["categories"]
        assert not any(c.startswith("Categoria:") for c in doc["categories"])
        assert "Articoli archiviati" not in doc["categories"]
        assert "13 gennaio 2007" not in doc["categories"]
    assert "Emilia-Romagna" in docs["9630"]["categories"]


def test_other_fields(docs):
    doc = docs["9630"]
    assert doc["published"] is True
    assert doc["wikidata_id"] == "Q17960466"
    assert "Eccidio di Monte Sole" in doc["entities"]
    assert doc["n_chars"] == len(doc["body"])
    assert docs["35705"]["series_key"].startswith("Ligue # #-#:")


def test_parse_date_variants():
    assert parse_date("1 agosto 2006") == "2006-08-01"
    assert parse_date("1º Agosto 2006") == "2006-08-01"
    assert parse_date("21 marzo 2008|venerdì") == "2008-03-21"
    assert parse_date("agosto 2006") is None
    assert parse_date("") is None


def test_date_falls_back_to_the_daily_category():
    assert extract_date("no template here", ["Politica", "21 marzo 2008"]) == ("2008-03-21", "category")
    assert extract_date("", ["Politica"]) == (None, "none")


def test_template_params_ignore_nested_pipes():
    positional, named = template_params(
        "|autore=|url=http://x.it|titolo=Il [[w:Senato|Senato]] approva|agenzia={{w|ANSA}}|data=1 agosto 2006")
    assert positional == []
    assert named["titolo"] == "Il [[w:Senato|Senato]] approva"
    assert named["agenzia"] == "{{w|ANSA}}"


def test_agency_spellings_are_merged():
    assert agency_key("la Repubblica") == agency_key("La Repubblica") == agency_key("repubblica.it")
    assert agency_key("Repubblica") == agency_key("La Repubblica (quotidiano)")
    assert agency_key("ANSA") == agency_key("Ansa") == agency_key("ansa.it")
    assert agency_key("Gazzetta dello Sport") == agency_key("La Gazzetta dello Sport") == agency_key("gazzetta.it")
    assert agency_key("Corriere della Sera") == agency_key("Corriere.it")
    assert agency_key("ANSA") != agency_key("AGI")


def test_normalized_agency_is_the_most_frequent_spelling():
    docs = [{"sources": [{"agency": a}]} for a in ["ANSA", "ANSA", "Ansa", "ansa.it"]]
    normalize_agencies(docs)
    assert [d["agencies"] for d in docs] == [["ANSA"]] * 4


def test_duplicates_keep_the_latest_version(tmp_path):
    dump = tmp_path / "dump.ndjson"
    lines = [{"identifier": 1, "date_modified": "2008-01-01T00:00:00Z", "name": "old"},
             {"identifier": 2, "date_modified": "2008-01-01T00:00:00Z", "name": "other"},
             {"identifier": 1, "date_modified": "2010-01-01T00:00:00Z", "name": "new"}]
    dump.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    records, read, removed = read_latest(dump)
    assert (read, removed) == (3, 1)
    assert sorted(r["name"] for r in records) == ["new", "other"]
