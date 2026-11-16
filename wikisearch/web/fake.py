"""Hard-coded answers for fake mode (WIKISEARCH_FAKE=1): the web API works without Elasticsearch.

Used to build the interface before the index exists, and by tests/test_web.py.
The three hits cover the cases the UI must show: an image, a non-published page, no date.
"""

from wikisearch.schema import Hit

HITS = [
    Hit(
        id="fake-1",
        score=12.5,
        title="Italia: il governo approva la manovra finanziaria",
        url="https://it.wikinews.org/wiki/Fake_1",
        date="2008-03-21",
        snippet="Il Consiglio dei ministri ha approvato ieri la manovra: il <em>governo</em> parla di "
        "un passo necessario per i conti pubblici.",
        categories=["Italia", "Politica e conflitti", "Economia e finanza"],
        agencies=["ANSA", "Corriere della Sera"],
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/120px-Flag_of_Italy.svg.png",
        published=True,
    ),
    Hit(
        id="fake-2",
        score=9.1,
        title="Abruzzo: scossa di terremoto avvertita a L'Aquila",
        url="https://it.wikinews.org/wiki/Fake_2",
        date="2009-04-06",
        snippet="Una forte scossa ha colpito l'Abruzzo nella notte; il <em>governo</em> ha "
        "dichiarato lo stato di emergenza.",
        categories=["Italia", "Abruzzo", "Disastri e incidenti"],
        agencies=["la Repubblica"],
        image_url=None,
        published=True,
    ),
    Hit(
        id="fake-3",
        score=4.7,
        title="Speciale: elezioni politiche",
        url="https://it.wikinews.org/wiki/Fake_3",
        date=None,
        snippet="Pagina speciale con i risultati delle elezioni e la formazione del nuovo "
        "<em>governo</em>.",
        categories=["Italia", "Elezioni"],
        agencies=[],
        image_url=None,
        published=False,
    ),
]

_BODY = (
    "Il Consiglio dei ministri ha approvato ieri la manovra finanziaria per il prossimo anno.\n\n"
    "Secondo il governo il provvedimento è necessario per riportare in equilibrio i conti "
    "pubblici. L'opposizione ha annunciato battaglia in Parlamento."
)


def document(doc_id: str) -> dict | None:
    """A fake processed document with every field of docs/contracts.md section 1."""
    hit = next((h for h in HITS if h.id == doc_id), None)
    if hit is None:
        return None
    lead = _BODY.split("\n\n")[0]
    return {
        "id": hit.id,
        "title": hit.title,
        "url": hit.url,
        "date": hit.date,
        "date_source": "template" if hit.date else "none",
        "lead": lead,
        "body": _BODY,
        "categories": hit.categories,
        "sources": [
            {
                "agency": agency,
                "title": "Approvata la manovra",
                "url": "https://example.org/notizia",
                "date": hit.date,
                "foreign": False,
            }
            for agency in hit.agencies
        ],
        "agencies": hit.agencies,
        "entities": ["Consiglio dei ministri", "Parlamento italiano"],
        "wikidata_id": None,
        "image_url": hit.image_url,
        "published": hit.published,
        "series_key": hit.title,
        "n_chars": len(_BODY),
    }


FACETS = {
    "categories": [
        {"value": "Italia", "count": 3},
        {"value": "Politica e conflitti", "count": 1},
        {"value": "Economia e finanza", "count": 1},
        {"value": "Abruzzo", "count": 1},
        {"value": "Disastri e incidenti", "count": 1},
        {"value": "Elezioni", "count": 1},
    ],
    "agencies": [
        {"value": "ANSA", "count": 1},
        {"value": "Corriere della Sera", "count": 1},
        {"value": "la Repubblica", "count": 1},
    ],
    "years": [
        {"value": "2008", "count": 1},
        {"value": "2009", "count": 1},
    ],
}
