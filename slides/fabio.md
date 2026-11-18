# Slide di Fabio: le scelte di retrieval e la demo

Scritte il 17 novembre con i numeri della run ufficiale finale di Gioia (17:27, `results/summary.md`;
figure in `results/figures/`). Circa 6 minuti: 2,5 per le quattro slide, 3,5 per la demo
(`docs/demo.md`). Tutti i p sono corretti con Holm; "fonti" sono 7.072 query con un solo documento
giusto, "manual" sono 30 query con giudizi 0/1/2.

## Slide 1: Una ricerca, molte configurazioni
Contenuto: una sola funzione `search(query, configurazione)`, usata dall'interfaccia e dalla
valutazione; ogni scelta di progetto è una configurazione con un nome, cioè una manopola
dell'ablazione.

| configurazione | cosa cambia | esperimento |
|---|---|---|
| `bm25-standard`, `bm25-italian` | analisi del testo | E1 |
| `-title`, `-body`, `-flat` | campi e pesi di BM25 | E2 |
| `knn`, `hybrid-rrf` | lessicale, semantica, ibrida | E3 |
| `bm25-italian-leak` | fonti cercabili | E4 |
| `hybrid-rrf-published` | spinta alle pagine pubblicate | E5 |
| `knn-int8`, `knn-bbq` | quantizzazione dei vettori | E8 |

Figura: results/demo/3-exact-name-bm25-vs-knn.png
Note del relatore: Il motore non ha una configurazione "giusta" scritta nel codice: ha undici
configurazioni con un nome, e la stessa funzione serve la pagina web e gli esperimenti di Gioia.
Ogni numero che vedrete corrisponde a qualcosa che si apre nell'interfaccia; la modalità
Compare, in figura, mette due configurazioni a confronto sulla stessa query. Il default è
`hybrid-rrf`.

## Slide 2: BM25, quali campi e con quali pesi (E2)
Contenuto: titolo, lead e corpo con pesi 3, 2, 1 era la nostra scelta iniziale; l'esperimento
l'ha smentita.

| BM25 (analyzer italiano) | MRR@10 su fonti | MRR@10 sulle parafrasi |
|---|---|---|
| solo titolo | 0,663 (-0,104) | 0,283 |
| solo corpo | 0,726 (-0,042) | 0,621 |
| titolo^3 + lead^2 + corpo (la nostra) | 0,768 | 0,525 |
| pesi uguali | **0,800** (+0,032, p 0,0006) | **0,646** |

Figura: results/figures/e1_e2_bm25.png
Note del relatore: BM25 cerca titolo, lead e corpo con una `multi_match` di tipo `best_fields`.
Avevamo dato più peso al titolo per intuizione, ma i pesi uguali battono i nostri di 0,032, in
modo significativo, e il guadagno è quasi tutto sulle parafrasi: 0,646 contro 0,525. Se la query
non riusa le parole del titolo, spingere il titolo premia i documenti sbagliati che quelle
parole le hanno. E3 ed E5 usano ancora 3-2-1: le configurazioni erano fissate prima dei
risultati, e cambiarle dopo vorrebbe dire tarare il motore sulle query di test.

## Slide 3: Lessicale, semantica, ibrida (E3)
Contenuto: BM25 trova le parole, kNN il significato; l'ibrida fonde le due classifiche con
reciprocal rank fusion (RRF).

| | BM25 | kNN | ibrida RRF |
|---|---|---|---|
| MRR@10, fonti | 0,768 | 0,781 | **0,811** |
| MRR@10, parafrasi (2.643 query) | 0,525 | 0,557 | **0,611** |
| R@100, fonti | 0,958 | 0,942 | 0,965 |
| nDCG@10, manual | 0,701 | 0,764 | **0,804** |
| latenza p50 | 14,6 ms | 25,8 ms | 43,1 ms |

Figura: schema di RRF (disegnato nel deck)
Note del relatore: kNN cerca nel grafo HNSW i vettori più vicini alla query: batte BM25 sulle
parafrasi ma perde recall sui nomi rari, come vedrete nella demo. L'ibrida esegue le due
ricerche, 100 risultati ciascuna, e somma 1/(60 + posizione) di ogni documento, come nello
schema. Usiamo le posizioni perché i punteggi BM25 e le similarità coseno sono su scale diverse:
una somma pesata richiederebbe di tarare un peso. Su fonti l'ibrida è la migliore, con il
guadagno massimo sulle parafrasi; su manual è significativa solo contro BM25 (p 0,010), perché
con 30 query gli intervalli sono larghi. Costa latenza, 43 ms contro 15, ma resta sotto i 60 ms
anche al 95° percentile. Un limite: contro BM25 a pesi uguali l'ibrida perde sulle parafrasi;
un'ibrida sui pesi uguali è il passo successivo.

## Slide 4: Filtri, faccette, pagine non pubblicate (E5)
Contenuto: i filtri restringono senza cambiare i punteggi; le faccette contano per categoria,
fonte e anno; la spinta alle pagine pubblicate peggiora i risultati.

| E5 su manual | nDCG@10 |
|---|---|
| ibrida | **0,804** |
| ibrida, punteggio delle pubblicate x 1,5 | 0,758 (-0,046, p 0,029) |

Figura: results/demo/2-filters-date-agency.png
Note del relatore: I filtri sono clausole `filter` di Elasticsearch: escludono documenti senza
toccare il punteggio, e valgono anche dentro la ricerca kNN, che così restituisce comunque k
risultati. Le faccette contano per categoria, fonte e anno, sulla query BM25 anche in modalità
kNN. Le 1.181 pagine non pubblicate restano nell'indice, marcate. La spinta alle pubblicate,
punteggio per 1,5 dopo la fusione, fa scendere nDCG@10 su manual da 0,804 a 0,758: alcune pagine
non pubblicate, come uno speciale, rispondono davvero alla query. Non la misuriamo su fonti,
dove il documento giusto è sempre pubblicato. Quindi il default non usa la spinta.

## Slide 5: Demo
Contenuto: cinque query dal vivo sul portatile di Daniel: una ricerca con pagina non pubblicata,
filtri per data e fonte, un nome proprio (vince BM25), una parafrasi (vince kNN, poi l'ibrida),
le serie quasi identiche del SuperEnalotto.
Figura: nessuna (dal vivo; screenshot di riserva in `results/demo/`)
Note del relatore: Io parlo, Daniel usa l'interfaccia. Passi, azioni e frasi in `docs/demo.md`.
Il punto da far vedere: i numeri delle slide precedenti corrispondono a casi concreti. BM25 trova
"Pontecorvo" e kNN no; kNN trova "il pontefice è deceduto" (Benedetto XVI primo) dove BM25 lo
mette al 78° posto; l'ibrida sta in mezzo. E per la pagina speciale del terremoto: la spinta la
toglie dalla cima, ma E5 dice che in media non conviene.
