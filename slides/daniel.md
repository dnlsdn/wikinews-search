# Slide di Daniel: i dati e l'indicizzazione

Bozza del 16 novembre, risultati aggiunti il 17 (run ufficiale finale delle 17:27). Numeri da `results/data_report.md` (rigenerabile
con `uv run python -m wikisearch.ingest.report`), da `results/indexing.csv` e, per gli esperimenti,
dalla run ufficiale di Gioia (`results/summary.md`). Circa 6 minuti, sette
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
misura un esperimento (E5): non conviene, la spinta alle pubblicate fa scendere nDCG@10 su `manual`
da 0,804 a 0,758 (p 0,029), perché porta su pagine pubblicate ma meno pertinenti. Tenerle e trattarle come le altre funziona
meglio che penalizzarle. Le serie, come i 216 concorsi del SuperEnalotto, hanno titoli uguali a
meno dei numeri: `series_key` sostituisce le cifre con `#` e permette di raggrupparle. Le tabelle
non si possono buttare: 366 pagine sono fatte solo di tabelle e sarebbero rimaste vuote.

## Slide 5: Leakage
Contenuto: le query del test set sono scritte dentro le pagine; le togliamo dal testo cercato.

| | |
|---|---|
| query | "Il Dna lo scagiona, ma ha già scontato 24 anni" (titolo della fonte) |
| articolo | "Texas: scagionato da una violenza sessuale dopo 25 anni di carcere" |
| pagine con fonti fuori dalla sezione "Fonti" | 381 |
| se le fonti fossero cercabili (E4, 7.072 query) | MRR@10 da 0,768 a 0,900 (+0,132, p Holm 0,0001) |

Figura: nessuna
Note del relatore: Il test set `fonti` usa come query i titoli delle fonti citate, cioè titoli di
altri giornali sulla stessa notizia; l'articolo giusto è uno solo. Quei titoli però stanno dentro
la pagina, nel template `{{fonte}}`: se fossero cercabili il test non misurerebbe niente. Non basta
togliere la sezione "Fonti": in 381 pagine le fonti sono altrove, e in 19 resterebbero anche
togliendo tutte le sezioni di link. Quindi togliamo ogni template di fonte, dovunque sia. I titoli
restano in un campo separato, `sources_text`, usato solo per misurare quanto il leakage gonfierebbe
i risultati (E4). L'abbiamo misurato: con le fonti cercabili MRR@10 sale da 0,77 a 0,90, il 17% in
più, e sulle query più difficili (poche parole in comune col titolo) da 0,53 a 0,81. Un test set
con leakage avrebbe fatto sembrare il motore molto migliore di quello che è.

## Slide 6: Due indici, due analisi del testo
Contenuto: stessi campi, analyzer `standard` contro `italian` (esperimento E1).

| indice | secondi (media di 3) | MB |
|---|---|---|
| `wikinews-standard` | 4,2 | 38,2 |
| `wikinews-italian` | 3,8 | 35,7 |
| `wikinews-standard` con vettori | 14,9 | 57,4 |
| `wikinews-italian` con vettori | 13,8 | 54,9 |

E1 su `fonti` (7.072 query): MRR@10 da 0,743 a 0,768 (+0,025), R@100 da 0,945 a 0,958 (+0,013),
entrambi p Holm 0,0002; latenza p50 da 19,2 a 14,6 ms.
E1 su `manual` (30 query, giudizi 0/1/2): nDCG@10 da 0,648 a 0,701 (+0,052, p 0,038).

Figura: nessuna
Note del relatore: `italian` aggiunge elisione, stop word italiane e uno stemmer leggero:
"l'Italia" diventa `ital`, "elezioni" ed "elezione" diventano entrambi `elezion`. L'indice viene il 6% più piccolo,
perché ci sono meno termini distinti. Lo stemmer leggero però non unisce tutto: "scagiona" e
"scagionato" restano diversi. Gli accenti: lo stemmer li toglie già nelle parole lunghe ("perché"
e "perche" diventano `perc`), non in quelle corte ("città" e "citta" restano diverse) né nei nomi
come "Erdoğan". Il risultato di E1: l'analisi italiana migliora sia la precisione in cima
(MRR@10 +0,025) sia il recall (R@100 +0,013), entrambi significativi dopo la correzione di Holm,
e costa meno, perché l'indice è più piccolo e la query più veloce (14,6 contro 19,2 ms). Non è
un compromesso: è meglio su tutto. Lo conferma il secondo test set, `manual`, con giudizi
graduati: nDCG@10 da 0,648 a 0,701, significativo (p 0,038) ma con intervalli larghi, perché le
query sono solo 30. Il guadagno è più grande sulle query con poche parole in comune
col titolo (MRR@10 da 0,475 a 0,525), dove conta riconoscere forme diverse della stessa parola.
Una variante con `asciifolding` non è stata costruita: nei due test set le query
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
| `knn` contro BM25, query con poche parole in comune | MRR@10 da 0,525 a 0,557 (+0,032, p Holm 0,002) |
| quantizzazione (E8): `int8_hnsw`, `bbq_hnsw` contro HNSW | MRR@10 -0,0004 (non significativo); `bbq` R@100 -0,003 (p Holm 0,03); latenza uguale, 25-26 ms |

Figura: nessuna
Note del relatore: I vettori sono nel repository, così tutti indicizzano gli stessi e i portatili
da 8 GB non devono ricalcolarli. Vettorizziamo titolo e lead perché il modello tronca i testi
lunghi (512 token) e l'inizio di una notizia ne dice l'essenziale. La query "disastro in una
miniera" trova "Cina: esplosione in miniera, 11 morti" e notizie simili, nessuna delle quali
contiene la parola "disastro": il vettore coglie il significato, non le parole. I numeri lo
confermano dove ce lo aspettavamo: sulle parafrasi `knn` batte BM25 (+0,032 MRR@10), ma da solo
perde recall (R@100 0,942 contro 0,958) e costa quasi il doppio (25,8 contro 14,6 ms, quasi tutto per
vettorizzare la query); per questo nel motore i due si combinano, come mostra Fabio. I punteggi di
similarità sono tutti vicini (0,91-0,96), quindi conta solo l'ordine; per questo la ricerca ibrida
fonde le classifiche con RRF e non i punteggi. Abbiamo fissato HNSW senza quantizzazione perché
Elasticsearch 9.5, a 384 dimensioni, sceglierebbe da solo `bbq_hnsw`, la quantizzazione binaria:
quanto costi in qualità è l'esperimento E8. Risultato: quasi niente. `int8` e `bbq` perdono 0,0004
di MRR@10, non significativo; `bbq` perde un po' di recall (R@100 -0,003, significativo dopo
Holm); la latenza non cambia. Il guadagno è nella memoria: la parte che la ricerca tiene in RAM
passa da 19,2 MB (HNSW) a 5,3 MB (`int8`) e 1,2 MB (`bbq`), perché il grafo si percorre sui
vettori compressi e i float32 servono solo a riordinare i candidati finali. Con 12.213 documenti
tutto sta comunque in memoria: la quantizzazione conterebbe con milioni di vettori, e qui mostra
solo che costerebbe poco in qualità. Su disco gli indici quantizzati sono anzi più grandi, perché
Elasticsearch tiene anche i vettori originali.
