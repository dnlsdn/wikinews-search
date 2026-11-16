"""Tests of the `fonti` test set builder on hand-made documents."""

import pytest

from evaluation.build_fonti import bucket, build, dev_subset, normalise, not_italian, overlap, vowel_share


def doc(id, title, sources, published=True):
    return {"id": id, "title": title, "published": published, "lead": "", "body": "",
            "sources": [{"title": t, "foreign": f} for t, f in sources]}


def test_normalise_lowercases_and_removes_punctuation():
    assert normalise("Papa: Navarro, colpito da febbre forte!") == "papa navarro colpito da febbre forte"
    assert normalise("L'Italia vince") == "l italia vince"


def test_language_rule():
    assert not_italian("Moldova: Direct assignment for Rotterdam")  # "for", no Italian word
    assert not not_italian("Festival of Venezia: il programma")  # "of" but also "il"
    assert not not_italian("Romano Prodi vince le elezioni")  # no English word
    # two English markers, none of the first list (missed by the first version of the rule)
    assert not_italian("Whitney Houston, Pop Superstar, Dies at 48")  # dies, at
    assert not_italian("Bomb kills 11 on military bus in Iran")  # bomb, kills, on
    assert not_italian("Янукович просить військових не стріляти")  # non-Latin script
    assert not_italian("Άνδρες το 91% των συντακτών")
    # Italian headlines with names or a single English word are kept
    assert not not_italian("New York, finito sciopero trasporti")
    assert not not_italian("Why not: Saladino, ho solo offerto lavoro")
    assert not not_italian("McDonald's preannuncia calo utili")
    assert not not_italian("Alitalia: CdA nomina presidente Aristide Police")
    assert not not_italian("Coming out a Sanremo")  # one marker only


def test_language_rule_with_the_corpus_vocabulary():
    vocab = {"fiorentina", "rossi", "aggredisce", "morta", "netflix", "malaysia", "partita"}
    # few known words AND few words ending in a vowel: another language
    assert not_italian("Netflix tests cheaper mobile-only plan in Malaysia", vocab)
    assert not_italian("Baerbock reagiert zurückhaltend auf ukrainischen Beitrittsantrag", vocab)
    # unknown foreign names, but the Italian words end in a vowel: kept
    assert not not_italian("Fiorentina: Delio Rossi aggredisce Ljaic", vocab)
    assert not not_italian("Morta l'olimpionica Colette Besson", vocab)
    # without the vocabulary the fourth case is off
    assert not not_italian("Netflix tests cheaper mobile-only plan in Malaysia")


def test_vowel_share_counts_lowercase_words_when_there_are_two():
    # lowercase words "batte", "terzo": the capitalised names do not count
    assert vowel_share("Hamilton batte Button, Webber terzo") == 1.0
    # Title Case: every word counts; steve, apple end in a vowel, jobs, resigns do not
    assert vowel_share("Steve Jobs Resigns Apple") == 0.5
    assert vowel_share("Ok") is None


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
    assert funnel["after: in Italian"] == 5
    assert funnel["after: not ambiguous"] == 3
    assert funnel["after: article published"] == 2
    assert funnel["final: one query per document"] == 1


def test_dev_subset_is_fixed_and_in_order():
    queries = [{"qid": f"F{i:04d}"} for i in range(1, 3001)]
    a, b = dev_subset(queries), dev_subset(queries)
    assert len(a) == 1000 and a == b
    assert [q["qid"] for q in a] == sorted(q["qid"] for q in a)
