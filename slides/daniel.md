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

Figura: nessuna
Note del relatore: Il corpus è il dump di Wikinews in italiano del 20 marzo 2025: un oggetto JSON per pagina, con l'HTML e il wikitext di ogni articolo. Le righe sono 12.261, ma alcune pagine compaiono più volte, una per revisione: teniamo la più recente e restano 12.213 documenti. Il 90% è pubblicato, il 96% ha una data, quasi diecimila citano almeno una fonte. Il grafico mostra la cosa più evidente: il corpus è piccolo ma molto sbilanciato, più di metà delle notizie datate è del 2005-2008, gli anni in cui Wikinews in italiano era più attiva.

## Slide 2: Le informazioni sono nei template
Contenuto: la data non è un campo, l'abstract non è un sommario.

| problema | quanto | scelta |
|---|---|---|
| data scritta a mano in `{{data}}` / `{{luogodata}}` | 11.687 date dal template, 40 dalla categoria del giorno, 486 senza | data estratta dal wikitext, campo `date_source` |
| abstract del dump che inizia con la data | 11.632 abstract | lead ricostruito dall'HTML |

Figura: nessuna
Note del relatore: La prima difficoltà: le informazioni che ci servono non sono campi del dump. Il dump ha solo la data dell'ultima modifica, spesso anni dopo la notizia. La data vera è scritta a mano in un template in italiano, come questo luogodata, che diventa 2020-05-20. La estraiamo dal wikitext per 11.687 documenti e per 40 dalla categoria del giorno; 486 restano senza data, e un campo dice da dove viene ogni data. Lo stesso per l'abstract: in 11.632 pagine inizia con la data, e a volte c'è solo quella, come "19 dicembre 2005". Il lead lo ricostruiamo dall'HTML, dal primo paragrafo vero: "Evo Morales vince le presidenziali in Bolivia". Conta perché è quello che leggono gli embeddings: con la sola data, tutte le notizie dello stesso giorno sembrerebbero uguali.

## Slide 3: Metadati da ripulire
Contenuto: categorie e agenzie diventano filtri, quindi devono essere pulite.

| | nel dump | indicizzate |
|---|---|---|
| categorie | 5.963 | 1.753 |
| nomi di agenzia | 2.965 grafie | 2.304 |

Figura: nessuna
Note del relatore: Categorie e fonti diventano filtri e faccette nell'interfaccia, quindi devono essere pulite. Delle quasi seimila categorie, 4.188 sono categorie di data, una per giorno, e 22 sono di manutenzione, come "Pubblicati": le togliamo e ne restano 1.753. Le agenzie sono scritte a mano: la Repubblica compare in 14 grafie. Le raggruppiamo con una chiave normalizzata, cioè minuscole, senza articolo e senza dominio, più qualche alias, e mostriamo la grafia più frequente. Senza questo passo, filtrando "la Repubblica" si perderebbe il 28% delle sue fonti.

## Slide 4: Non tutte le pagine sono notizie
Contenuto: pagine non pubblicate, serie quasi identiche, tabelle; le teniamo tutte, marcate.

| | documenti | scelta |
|---|---|---|
| speciali, palinsesti, classifiche, bozze | 1.181 (pagine) | tenute con `published: false` |
| 5 o più pagine dallo stesso template | 2.742 (pagine, il 22%) | tenute, con `series_key` |
| le tabelle sono il 36% di tutto il testo | 3.661 (pagine) | tabelle come testo, una riga per riga |

Figura: nessuna
Note del relatore: Non tutte le pagine sono notizie. 1.181 non sono pubblicate: speciali, palinsesti, classifiche, bozze. Le teniamo, marcate: uno speciale sulle elezioni può rispondere a una query vera, e se convenga penalizzarle lo misura un esperimento, E5, che mostra Fabio. Poi le serie generate da template, come i 216 concorsi del SuperEnalotto, con titoli uguali a meno dei numeri: un campo sostituisce le cifre e permette di raggrupparle. Infine il 36% del testo è in tabelle: le teniamo come testo, una riga per riga, perché 366 pagine sono fatte solo di tabelle e sarebbero rimaste vuote.

## Slide 5: Leakage
Contenuto: le query del test set sono scritte dentro le pagine; le togliamo dal testo cercato.

| | |
|---|---|
| query | "Il Dna lo scagiona, ma ha già scontato 24 anni" (titolo della fonte) |
| articolo | "Texas: scagionato da una violenza sessuale dopo 25 anni di carcere" |
| pagine con fonti fuori dalla sezione "Fonti" | 381 |
| se le fonti fossero cercabili (E4, 7.072 query) | MRR@10 da 0,768 a 0,900 (+0,132, p Holm 0,0001) |

Figura: nessuna
Note del relatore: Il problema più insidioso riguarda la valutazione. Il test set fonti, che presenta Gioia, usa come query i titoli delle fonti citate: qui "Il Dna lo scagiona, ma ha già scontato 24 anni", un titolo di Euronews; la risposta giusta è l'articolo che lo cita. Ma quel titolo sta dentro la pagina, nel template della fonte: se fosse cercabile, il motore troverebbe la query parola per parola e il test non misurerebbe niente. Non basta togliere la sezione "Fonti": in 381 pagine le fonti sono altrove. Quindi togliamo ogni template di fonte, dovunque sia, e teniamo i titoli in un campo a parte solo per misurare l'effetto, l'esperimento E4: con le fonti cercabili MRR@10 salirebbe da 0,768 a 0,900. Un test con leakage avrebbe fatto sembrare il motore molto migliore di quello che è.

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
Note del relatore: Indicizziamo con Elasticsearch, un nodo e uno shard su un portatile. Costruiamo due indici con gli stessi campi e due analizzatori: standard e italian, che aggiunge elisione, stop word italiane e uno stemmer leggero. "Elezioni" ed "elezione" diventano elezion, "l'Italia" diventa ital; ma lo stemmer leggero non unisce tutto: scagiona e scagionato restano diversi. Con meno termini distinti l'indice è più piccolo del 6%. Il risultato, l'esperimento E1, è a destra: l'analisi italiana migliora MRR@10 e recall su fonti, entrambi significativi, e nDCG@10 su manual da 0,648 a 0,701; e la query è anche più veloce. Non è un compromesso: è meglio su tutto.

## Slide 7: Embeddings
Contenuto: un vettore per documento, calcolato una volta e condiviso da tutti.

| | |
|---|---|
| modello | multilingual-e5-small, 384 dimensioni |
| testo | "passage: " + titolo + lead |
| tempo | 121 s per 12.213 documenti, su CPU |
| parafrasi, 2.643 query | MRR@10: kNN 0,557, BM25 0,525 (p Holm 0,002) |
| quantizzazione (E8): memoria della ricerca | HNSW 19,2 MB, `int8_hnsw` 5,3 MB, `bbq_hnsw` 1,2 MB; qualità e latenza nelle slide di Gioia |

Figura: results/figures/embedding_map.png (vettori veri della query "disastro in una miniera", `uv run python -m wikisearch.ingest.embedding_map`)
Note del relatore: Per la ricerca semantica calcoliamo un vettore per documento con multilingual-e5-small, 384 dimensioni, su titolo e lead, perché il modello tronca i testi lunghi e l'inizio di una notizia ne dice l'essenziale. Il disegno mostra cosa fa kNN, sui vettori veri: al centro la query "disastro in una miniera", e la distanza dal centro è la distanza vera tra i vettori. Il cerchio si allarga finché contiene cinque notizie: sono i primi cinque risultati, tutti incidenti in miniera, nessuno con la parola disastro nel titolo. "Disastro aereo in Perù" la contiene, ma è solo decimo: il vettore coglie il significato, non le parole. Sulle parafrasi kNN batte BM25, da 0,525 a 0,557 di MRR@10. Infine l'esperimento E8: comprimere i vettori costa quasi niente in qualità e riduce la memoria da 19 a 5 e a poco più di 1 megabyte. Con dodicimila documenti non serve; con milioni sì.
