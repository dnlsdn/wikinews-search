# Slide di Gioia: strategia di test, risultati, conclusioni

Scritte il 18 novembre con i numeri della run ufficiale finale (17 novembre 17:27,
`results/summary.md`; figure in `results/figures/`, rigenerabili con
`uv run python -m evaluation.figures`). Circa 6 minuti, nove slide brevi. Tutti i p sono corretti
con Holm; i numeri si riproducono con un solo comando, `uv run python -m evaluation.run`.
I dettagli di E1 e E4 sono nelle slide di Daniel, quelli di E2, E3 e E5 in quelle di Fabio: qui
compaiono solo nella sintesi finale.

## Slide 1: Come valutiamo
Contenuto: due test set complementari, metriche del corso, ogni media con il suo intervallo e ogni
confronto con un test di significatività.

| test set | query | giudizi | domanda a cui risponde | metriche |
|---|---|---|---|---|
| `fonti` | 7.072 | 1 documento giusto, automatico | il motore trova la notizia? | MRR@10, R@10, R@100 |
| `manual` | 30 | 573 documenti graduati 0/1/2: 10 query da due di noi, 20 da un modello (vedi Limiti) | la prima pagina è buona? | P@10, nDCG@10, MAP, MRR@10 |

Figura: nessuna
Note del relatore: Un benchmark ha tre parti: documenti, query, giudizi di rilevanza. I documenti
sono i 12.213 di Daniel; query e giudizi li abbiamo costruiti in due modi. `fonti` è grande e
automatico, con una sola risposta giusta per query: misura la ricerca di un elemento noto, e la
metrica naturale è MRR. `manual` è piccolo, con tre gradi di rilevanza, in parte da noi e in parte
da un modello: misura tutta la prima pagina, con nDCG. Ogni esperimento confronta due
configurazioni che differiscono in una sola cosa: è un'ablazione.

## Slide 2: Il test set `fonti`
Contenuto: la query è il titolo con cui un altro giornale ha dato la stessa notizia; la risposta
giusta è l'articolo che lo cita.

| passo del filtro | titoli rimasti |
|---|---|
| titoli di fonti citate | 17.192 |
| almeno 4 parole | 15.002 |
| fonte non straniera, titolo in italiano | 13.255 |
| titolo non ambiguo (es. "Risultati Serie A") | 12.632 |
| articolo pubblicato | 12.346 |
| una query per articolo | **7.072** |

Figura: nessuna
Note del relatore: Ogni articolo di Wikinews cita le sue fonti con il loro titolo. Quel titolo è
una query realistica, scritta da un altro giornale, e sappiamo già qual è la risposta giusta:
migliaia di query senza lavoro manuale. Il corso sconsiglia termini presi a caso dai documenti:
questi sono titoli veri. Una sola query per articolo, così gli articoli con tante fonti non pesano
di più. Dividiamo le query per parole in comune con il titolo dell'articolo: overlap basso, cioè
parafrasi, 2.643; medio 3.571; alto 858. Due controlli: la regola sulla lingua, verificata a occhio
su 100 titoli, perché i titoli in inglese favorivano il modello multilingue; e il leakage, il
titolo della fonte già nel testo: 7 query su 300, sovrapposizione naturale tra giornali.

## Slide 3: Il test set `manual`
Contenuto: 30 query scritte prima di vedere i risultati, ognuna con il suo bisogno informativo;
giudicato il pool delle prime 10 posizioni di cinque configurazioni.

| | |
|---|---|
| tipi di query | 7 per argomento, 8 per entità, 7 legate a un periodo, 8 vaghe |
| pool | 573 documenti, da 11 a 27 per query; 95 trovati solo da kNN |
| giudizi | 0 = 279, 1 = 76, 2 = 218 |
| accordo su 10 query giudicate due volte | 72,5%, kappa di Cohen 0,543 (0/1/2), 0,674 (rilevante sì/no) |

Figura: nessuna
Note del relatore: Le 30 query le abbiamo scritte prima di vedere un solo risultato, ognuna con il
suo bisogno informativo: come dice il corso, la rilevanza si giudica rispetto al bisogno, non alle
parole della query. Giudicare tutto il corpus è impossibile, quindi pooling: le prime 10 posizioni
di cinque configurazioni, unite e mescolate, così chi giudica non sa quale sistema ha trovato cosa.
95 documenti li ha trovati solo kNN: senza kNN nel pool sarebbe stato penalizzato. Su dieci query
giudicate da due persone il kappa è 0,54: accordo moderato sui tre gradi, sostanziale su rilevante
sì o no. I 49 disaccordi li ha risolti un terzo giudice alla cieca (un modello).

## Slide 4: Quando una differenza è vera
Contenuto: intervallo di confidenza bootstrap al 95% per ogni media, test di randomizzazione
appaiato per ogni confronto, correzione di Holm, baseline casuale.

| controllo | perché |
|---|---|
| baseline casuale: MRR@10 0,000, nDCG@10 0,000 | il codice delle metriche non regala punti |
| metriche testate su esempi calcolati a mano | un bug nelle metriche falsa tutto |
| test di randomizzazione appaiato, 10.000 permutazioni | la differenza non è dovuta al caso |
| correzione di Holm per esperimento | E3 fa 27 confronti: qualche p < 0,05 uscirebbe per caso |
| tutte le query, semi fissi, un comando | nessuna scelta di campione da difendere, numeri riproducibili |

Figura: nessuna
Note del relatore: Una media da sola non basta: per ogni media ricampioniamo le query 10.000 volte
e riportiamo l'intervallo al 95%. Per ogni confronto, test di randomizzazione appaiato: per ogni
query scambiamo a caso i punteggi delle due configurazioni e contiamo quante volte la differenza è
grande almeno come quella osservata. Con molti confronti per esperimento correggiamo i p con Holm.
Un esempio: ibrida contro BM25 sulle query facili ha p 0,03, dopo la correzione 0,18, quindi non la
chiamiamo significativa. La baseline casuale fa zero, come deve: è il pavimento.

## Slide 5: Il risultato chiave: dove serve la ricerca semantica (E3)
Contenuto: sulle query facili tutti sono vicini a 1; sulle parafrasi l'ibrida guadagna 0,086 su
BM25.

| MRR@10 su `fonti` | tutte | overlap basso | overlap medio | overlap alto |
|---|---|---|---|---|
| BM25 italiano | 0,768 | 0,525 | 0,893 | 0,996 |
| kNN | 0,781 | 0,557 | 0,899 | 0,979 |
| ibrida RRF | **0,811** | **0,611** | **0,915** | 0,990 |

Figura: results/figures/e3_buckets.png
Note del relatore: Questa è la figura che riassume il progetto. Quando la query riusa le parole del
titolo, BM25 è già quasi perfetto. Quando è una parafrasi, overlap basso, BM25 scende a 0,525: lì
kNN aiuta (+0,032) e l'ibrida ancora di più (+0,086), tutto significativo dopo Holm. kNN da solo
però perde recall: R@100 0,942 contro 0,958. L'ibrida prende il meglio dei due ed è la migliore in
media, 0,811. Un confronto deciso dopo aver visto i risultati, E3b: BM25 con pesi uguali sui campi
batte l'ibrida sulle parafrasi (0,646 contro 0,611); lo dichiariamo.

## Slide 6: La prima pagina, sul test set `manual`
Contenuto: l'ibrida ha la nDCG@10 più alta; con 30 query solo le differenze grandi sono
significative.

| nDCG@10 (30 query) | media [intervallo 95%] |
|---|---|
| BM25 standard | 0,648 [0,546, 0,746] |
| BM25 italiano | 0,701 [0,599, 0,797] |
| kNN | 0,764 [0,677, 0,841] |
| ibrida RRF | **0,804** [0,737, 0,866] |
| ibrida + spinta pubblicate | 0,758 [0,673, 0,837] |

Figura: results/figures/manual_ndcg.png
Note del relatore: Su `manual` l'ordine è lo stesso di `fonti`: analizzatore italiano meglio dello
standard (+0,052, p 0,04), ibrida meglio di BM25 (+0,103, p 0,010). kNN sopra BM25 di 0,063, ma non
significativo: con 30 query gli intervalli sono larghi. La spinta alle pagine pubblicate peggiora
(-0,046, p 0,03), quindi non è nel default. Sulle sole 10 query giudicate da persone la direzione è
la stessa, ma 10 query sono troppo poche per la significatività.

## Slide 7: Quanto costa la qualità (E6, E8)
Contenuto: più qualità costa latenza, ma tutto resta sotto i 60 ms; quantizzare i vettori non
costa qualità.

| configurazione | MRR@10 | latenza p50 | p95 |
|---|---|---|---|
| BM25 italiano | 0,768 | 14,6 ms | 21,7 ms |
| kNN | 0,781 | 25,8 ms | 34,5 ms |
| kNN int8 / BBQ | 0,780 / 0,780 | 25,4 / 26,0 ms | 34,1 / 34,5 ms |
| ibrida RRF | 0,811 | 43,1 ms | 53,4 ms |

Figura: results/figures/e6_tradeoff.png
Note del relatore: Latenza su 500 query, dopo un riscaldamento, con le configurazioni in ordine
casuale per ogni query, così hanno le stesse cache; per kNN è incluso il calcolo del vettore della
query. L'ibrida fa due ricerche e costa circa tre volte BM25, ma resta sotto i 60 ms al 95°
percentile. E8: comprimere i vettori a 8 bit o a 1 bit non cambia MRR@10 in modo misurabile (p
0,95); BBQ perde un poco di recall (R@100 -0,003). La latenza non cambia perché il corpus è
piccolo: il vantaggio è la memoria, che ha mostrato Daniel.

## Slide 8: Limiti
Contenuto: li dichiariamo perché cambiano come leggere i numeri.

| limite | effetto |
|---|---|
| `fonti` ha un solo documento giusto per query | misura la ricerca della notizia, non la qualità della pagina |
| `manual` ha 30 query | intervalli larghi, solo le differenze grandi sono significative |
| 10 query di `manual` giudicate da noi, autori del sistema | possibile distorsione; mitigata dal pool mescolato |
| 20 query su 30 giudicate da un modello, disaccordi risolti da un modello | il kappa è tra umani, ma la maggior parte dei voti no |
| documenti non giudicati contano come non rilevanti | sottostima per configurazioni fuori dal pool |
| E3b scelto dopo aver visto i risultati | va letto come indicazione, non come ipotesi testata |

Figura: nessuna
Note del relatore: Questi limiti cambiano come leggere i numeri. Il più importante per `manual`:
per stare nei tempi, le query da M11 a M30 le ha giudicate un modello linguistico con le stesse
linee guida, e un modello ha fatto da terzo giudice. L'accordo lo misuriamo sulle dieci query
giudicate da persone, e su quelle riportiamo anche i risultati. E2 ed E4 sono misurati solo su
`fonti`, perché i loro documenti non sono nel pool.

## Slide 9: Conclusioni
Contenuto: una riga per esperimento; le scelte confermate e quelle smentite dai numeri.

| esperimento | risultato | scelta |
|---|---|---|
| E1 analizzatore italiano | +0,025 MRR@10, +0,052 nDCG@10, e più veloce | confermata |
| E2 campi e pesi | pesi uguali +0,032 sui nostri pesi 3-2-1 | smentita, dichiarata |
| E3 lessicale, semantica, ibrida | ibrida migliore, +0,086 sulle parafrasi | confermata, è il default |
| E4 leakage | fonti cercabili gonfierebbero MRR@10 da 0,768 a 0,900 | togliere le fonti era necessario |
| E5 spinta alle pubblicate | -0,046 nDCG@10 | smentita, non usata |
| E6 costi | ibrida 43 ms contro 15 di BM25 | costo accettabile |
| E8 quantizzazione | nessuna perdita misurabile di MRR@10 | int8 o BBQ si possono usare |

Figura: nessuna
Note del relatore: Le misure hanno confermato tre scelte, l'analizzatore italiano, la ricerca
ibrida e la rimozione delle fonti, e ne hanno smentite due, i pesi dei campi e la spinta alle
pagine pubblicate. Anche questo è un risultato: senza la valutazione avremmo tenuto due scelte
sbagliate. Il passo successivo sarebbe un'ibrida costruita su BM25 a pesi uguali, che non abbiamo
provato per non tarare il motore sulle stesse query con cui lo valutiamo. Ogni numero di queste
slide si riproduce con un comando.
