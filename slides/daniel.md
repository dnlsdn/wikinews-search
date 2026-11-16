# Slide di Daniel: i dati e l'indicizzazione

Bozza del 16 novembre. Numeri da `results/data_report.md` (rigenerabile con
`uv run python -m wikisearch.ingest.report`) e da `results/indexing.csv`. Circa 6 minuti, sette
slide; la numerazione definitiva si fa quando si monta il deck.

## Slide 1: Il corpus
Contenuto: Wikinews in italiano, dump del 20 marzo 2025.

| | |
|---|---|
| righe nel dump | 12.261 |
| documenti dopo i duplicati | 12.213 |
| pubblicati | 11.032 (90%) |
| con data | 11.727 (96%) |
| con almeno una fonte | 9.891 |
| notizie 2005-2008 | 55% delle datate |

Figura: nessuna
Note del relatore: Il dump è un file JSON per pagina, con l'HTML e il wikitext di ogni articolo.
Alcune pagine compaiono più volte, una per revisione (fino a 13 volte): teniamo la più recente.
Il corpus è piccolo ma molto sbilanciato: più di metà delle notizie datate è del 2005-2008, e le
lunghezze vanno da poche righe a oltre 80.000 caratteri.

## Slide 2: Le informazioni sono nei template
Contenuto: la data non è un campo, l'abstract non è un sommario.

| problema | quanto | scelta |
|---|---|---|
| data scritta a mano in `{{data}}` / `{{luogodata}}` | 11.687 date dal template, 40 dalla categoria del giorno, 486 senza | data estratta dal wikitext, campo `date_source` |
| abstract del dump che inizia con la data | 11.632 abstract | lead ricostruito dall'HTML |

Figura: nessuna
Note del relatore: Il dump ha solo la data dell'ultima modifica, spesso anni dopo. La data della
notizia è dentro un template in italiano, per esempio `{{luogodata|mercoledì|luogo=Bruxelles|data=20
maggio 2020}}`, che diventa 2020-05-20. Il testo lo prendiamo dall'HTML, i metadati dal wikitext,
dove i template sono leggibili. Il lead conta perché è quello che leggono gli embeddings: un
abstract fatto solo di data, come "martedì 17 giugno 2008", renderebbe simili tutte le notizie
dello stesso giorno.

## Slide 3: Metadati da ripulire
Contenuto: categorie e agenzie diventano filtri, quindi devono essere pulite.

| | nel dump | indicizzate |
|---|---|---|
| categorie | 5.963 | 1.753 |
| nomi di agenzia | 2.965 grafie | 2.304 |

Figura: nessuna
Note del relatore: Fra le categorie ci sono 4.188 categorie di data, una per giorno, e 22 di
manutenzione come "Pubblicati" o "Articoli da controllare per l'archiviazione": le togliamo,
perché nel filtro sarebbero solo rumore. Le agenzie sono scritte a mano: la Repubblica compare in
14 grafie ("la Repubblica", "La Repubblica", "repubblica.it", ...). Le raggruppiamo con una chiave
normalizzata (minuscole, senza articolo, senza dominio) più qualche alias, e mostriamo la grafia
più frequente. Senza questo passo, filtrando "la Repubblica" si perderebbe il 28% delle sue fonti.

## Slide 4: Non tutte le pagine sono notizie
Contenuto: pagine non pubblicate, serie quasi identiche, tabelle; le teniamo tutte, marcate.

| | documenti | scelta |
|---|---|---|
| non pubblicate (speciali, palinsesti, tabelle, bozze) | 1.181 | tenute con `published: false` |
| serie generate da template (5+ pagine) | 2.742 (22%) | tenute, con `series_key` |
| pagine con tabelle | 3.661 (36% del testo) | tabelle come testo, una riga per riga |

Figura: nessuna
Note del relatore: Una classifica o uno speciale sulle elezioni possono rispondere a una query
vera, e la valutazione deve vedere tutte le pagine; se convenga penalizzare le non pubblicate lo
misura un esperimento (E5). Le serie, come i 216 concorsi del SuperEnalotto, hanno titoli uguali a
meno dei numeri: `series_key` sostituisce le cifre con `#` e permette di raggrupparle. Le tabelle
non si possono buttare: 366 pagine sono fatte solo di tabelle e sarebbero rimaste vuote.

## Slide 5: Leakage
Contenuto: le query del test set sono scritte dentro le pagine; le togliamo dal testo cercato.

| | |
|---|---|
| query | "Il Dna lo scagiona, ma ha già scontato 24 anni" (titolo della fonte) |
| articolo | "Texas: scagionato da una violenza sessuale dopo 25 anni di carcere" |
| pagine con fonti fuori dalla sezione "Fonti" | 381 |

Figura: nessuna
Note del relatore: Il test set `fonti` usa come query i titoli delle fonti citate, cioè titoli di
altri giornali sulla stessa notizia; l'articolo giusto è uno solo. Quei titoli però stanno dentro
la pagina, nel template `{{fonte}}`: se fossero cercabili il test non misurerebbe niente. Non basta
togliere la sezione "Fonti": in 381 pagine le fonti sono altrove, e in 19 resterebbero anche
togliendo tutte le sezioni di link. Quindi togliamo ogni template di fonte, dovunque sia. I titoli
restano in un campo separato, `sources_text`, usato solo per misurare quanto il leakage gonfierebbe
i risultati (E4).

## Slide 6: Due indici, due analisi del testo
Contenuto: stessi campi, analyzer `standard` contro `italian` (esperimento E1).

| indice | secondi (media di 3) | MB |
|---|---|---|
| `wikinews-standard` | 4,2 | 38,2 |
| `wikinews-italian` | 3,8 | 35,7 |
| `wikinews-standard` con vettori | 14,9 | 57,4 |
| `wikinews-italian` con vettori | 13,8 | 54,9 |

Figura: nessuna
Note del relatore: `italian` aggiunge elisione, stop word italiane e uno stemmer leggero:
"l'Italia" diventa `ital`, "elezioni" ed "elezione" diventano entrambi `elezion`. L'indice viene il 6% più piccolo,
perché ci sono meno termini distinti. Lo stemmer leggero però non unisce tutto: "scagiona" e
"scagionato" restano diversi. Gli accenti: lo stemmer li toglie già nelle parole lunghe ("perché"
e "perche" diventano `perc`), non in quelle corte ("città" e "citta" restano diverse) né nei nomi
come "Erdoğan". Una variante con `asciifolding` non è stata costruita: nei due test set le query
hanno gli accenti, quindi non avrebbe misurato nulla. Titolo, lead e corpo sono campi di testo; categorie, agenzie e serie
sono `keyword`, per filtri e faccette. Mapping rigido: un campo non previsto è un errore. Un nodo,
uno shard, 1 GB di heap su un portatile con 8 GB. Ogni costruzione è ripetuta tre volte perché la
prima è più lenta.

## Slide 7: Embeddings
Contenuto: un vettore per documento, calcolato una volta e condiviso da tutti.

| | |
|---|---|
| modello | multilingual-e5-small, 384 dimensioni |
| testo | "passage: " + titolo + lead |
| tempo | 121 s per 12.213 documenti, su CPU |
| struttura | HNSW non quantizzato: +19 MB, costruzione 3,6 volte più lenta |

Figura: nessuna
Note del relatore: I vettori sono nel repository, così tutti indicizzano gli stessi e i portatili
da 8 GB non devono ricalcolarli. Vettorizziamo titolo e lead perché il modello tronca i testi
lunghi (512 token) e l'inizio di una notizia ne dice l'essenziale. La query "disastro in una
miniera" trova "Cina: esplosione in miniera, 11 morti" e notizie simili, nessuna delle quali
contiene la parola "disastro": il vettore coglie il significato, non le parole. I punteggi di
similarità sono tutti vicini (0,91-0,96), quindi conta solo l'ordine; per questo la ricerca ibrida
fonde le classifiche con RRF e non i punteggi. Abbiamo fissato HNSW senza quantizzazione perché
Elasticsearch 9.5, a 384 dimensioni, sceglierebbe da solo `bbq_hnsw`, la quantizzazione binaria:
quanto costi in qualità è l'esperimento E8.
