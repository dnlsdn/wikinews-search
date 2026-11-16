"""Tests of the `fonti` test set builder (step G2) on hand-made documents."""

import pytest

from evaluation.build_fonti import bucket, build, dev_subset, is_english, normalise, overlap


def doc(id, title, sources, published=True):
    return {"id": id, "title": title, "published": published, "lead": "", "body": "",
            "sources": [{"title": t, "foreign": f} for t, f in sources]}


def test_normalise_lowercases_and_removes_punctuation():
    assert normalise("Papa: Navarro, colpito da febbre forte!") == "papa navarro colpito da febbre forte"
    assert normalise("L'Italia vince") == "l italia vince"


def test_english_rule():
    assert is_english("Moldova: Direct assignment for Rotterdam")  # "for", no Italian word
    assert not is_english("Festival of Venezia: il programma")  # "of" but also "il"
    assert not is_english("Romano Prodi vince le elezioni")  # no English word


def test_overlap_and_bucket():
    # query words without stop words {terremoto, abruzzo, morti}, title {terremoto, abruzzo}:
    # Jaccard = 2 / 3
    assert overlap("Terremoto in Abruzzo morti", "Terremoto in Abruzzo") == pytest.approx(2 / 3)
    assert overlap("il la di", "del della") == 0.0  # only stop words on both sides
    assert bucket(0.19) == "low" and bucket(0.2) == "mid" and bucket(0.5) == "mid" and bucket(0.51) == "high"


def test_filters_and_one_query_per_document():
    docs = [
        # d1: first source too short, second foreign, third valid, fourth valid but not first
        doc("1", "Terremoto in Abruzzo", [("Scossa forte", False),
                                          ("Forte scossa di terremoto in Abruzzo", True),
                                          ("Forte scossa di terremoto in Abruzzo stanotte", False),
                                          ("Danni e paura in tutta la regione", False)]),
        # d2 and d3 share the same normalised title: ambiguous for both, even if d3 is not published
        doc("2", "Serie A", [("Risultati Serie A giornata 1", False)]),
        doc("3", "Tabella", [("Risultati, Serie A giornata 1!", False)], published=False),
        # d4: English title
        doc("4", "Moldavia", [("Moldova: Direct assignment for Rotterdam", False)]),
        # d5: valid title but the article is not published
        doc("5", "Bozza", [("Una bozza di articolo mai pubblicata", False)], published=False),
    ]
    result = build(docs)
    queries = result["queries"]
    assert [(q["qid"], q["doc_id"], q["text"]) for q in queries] == [
        ("F0001", "1", "Forte scossa di terremoto in Abruzzo stanotte")
    ]
    assert queries[0]["meta"]["bucket"] == "mid"  # {forte, scossa, terremoto, abruzzo, stanotte} vs 2 words: 2/5
    funnel = result["funnel"]
    assert funnel["candidates"] == 8
    assert funnel["after: at least 4 words"] == 7
    assert funnel["after: not foreign"] == 6
    assert funnel["after: not English"] == 5
    assert funnel["after: not ambiguous"] == 3
    assert funnel["after: article published"] == 2
    assert funnel["final: one query per document"] == 1


def test_dev_subset_is_fixed_and_in_order():
    queries = [{"qid": f"F{i:04d}"} for i in range(1, 3001)]
    a, b = dev_subset(queries), dev_subset(queries)
    assert len(a) == 1000 and a == b
    assert [q["qid"] for q in a] == sorted(q["qid"] for q in a)
