# Wikinews search - discorso di Gioia

Homework 4, parte di Gioia (strategia di test, risultati, conclusioni): slide 1-9 di
`slides/gioia.md`, circa 5:44 minuti a 2,4 parole al secondo. Il testo è lo stesso delle note del
pptx (`slides/wikinews-search.pptx`) e di `slides/gioia.md`: qui sono solo evidenziati i passaggi
chiave. Numeri dalla run ufficiale del 17 novembre 17:27 (`results/summary.md`); tutti i p sono
corretti con Holm. Domande probabili, risposte e numeri da avere in testa:
`slides/domande-gioia.md`.

## 1. Come valutiamo (0:00-0:37)

*tre parti di un benchmark; due test set complementari; ogni esperimento è un'ablazione*

Un benchmark ha tre parti: **documenti, query, giudizi di rilevanza**. I documenti sono i 12.213 di
Daniel; query e giudizi li abbiamo costruiti in due modi. **`fonti` è grande e automatico, con una
sola risposta giusta per query**: misura la ricerca di un elemento noto, e la metrica naturale è
**MRR**. **`manual` è piccolo, con tre gradi di rilevanza**, in parte da noi e in parte da un
modello: misura tutta la prima pagina, con **nDCG**. Ogni esperimento confronta due configurazioni
che differiscono in una sola cosa: **è un'ablazione**.

## 2. Il test set `fonti` (0:37-1:28)

*il titolo di un altro giornale è la query, l'articolo che lo cita è la risposta; 7.072 query*

Ogni articolo di Wikinews cita le sue fonti con il loro titolo. Quel titolo è **una query
realistica, scritta da un altro giornale**, e sappiamo già qual è la risposta giusta: **migliaia di
query senza lavoro manuale**. Il corso sconsiglia termini presi a caso dai documenti: **questi sono
titoli veri**. **Una sola query per articolo**, così gli articoli con tante fonti non pesano di
più. Dividiamo le query per parole in comune con il titolo dell'articolo: **overlap basso, cioè
parafrasi, 2.643**; medio 3.571; alto 858. Due controlli: **la regola sulla lingua**, verificata a
occhio su 100 titoli, perché i titoli in inglese favorivano il modello multilingue; e **il
leakage**, il titolo della fonte già nel testo: **7 query su 300**, sovrapposizione naturale tra
giornali.

## 3. Il test set `manual` (1:28-2:15)

*query scritte prima dei risultati, pooling alla cieca, kappa 0,54*

Le 30 query le abbiamo scritte **prima di vedere un solo risultato**, ognuna con il suo **bisogno
informativo**: come dice il corso, la rilevanza si giudica rispetto al bisogno, non alle parole
della query. Giudicare tutto il corpus è impossibile, quindi **pooling**: le prime 10 posizioni di
cinque configurazioni, unite e mescolate, così **chi giudica non sa quale sistema ha trovato
cosa**. **95 documenti li ha trovati solo kNN**: senza kNN nel pool sarebbe stato penalizzato. Su
dieci query giudicate da due persone **il kappa è 0,54**: accordo moderato sui tre gradi,
sostanziale su rilevante sì o no. I 49 disaccordi li ha risolti **un terzo giudice alla cieca** (un
modello).

## 4. Quando una differenza è vera (2:15-2:52)

*intervallo bootstrap, test di randomizzazione appaiato, Holm, baseline casuale a zero*

Una media da sola non basta: per ogni media **ricampioniamo le query 10.000 volte** e riportiamo
**l'intervallo al 95%**. Per ogni confronto, **test di randomizzazione appaiato**: per ogni query
scambiamo a caso i punteggi delle due configurazioni e contiamo quante volte la differenza è grande
almeno come quella osservata. Con molti confronti per esperimento **correggiamo i p con Holm**. Un
esempio: ibrida contro BM25 sulle query facili ha **p 0,03, dopo la correzione 0,18**, quindi non la
chiamiamo significativa. **La baseline casuale fa zero**, come deve: è il pavimento.

## 5. Il risultato chiave: dove serve la ricerca semantica (E3) (2:52-3:30)

*sulle query facili tutti vicini a 1; sulle parafrasi l'ibrida +0,086; E3b dichiarato*

**Questa è la figura che riassume il progetto.** Quando la query riusa le parole del titolo, **BM25
è già quasi perfetto**. Quando è una parafrasi, overlap basso, **BM25 scende a 0,525**: lì **kNN
aiuta (+0,032) e l'ibrida ancora di più (+0,086)**, tutto significativo dopo Holm. kNN da solo però
**perde recall**: R@100 0,942 contro 0,958. **L'ibrida prende il meglio dei due ed è la migliore in
media, 0,811.** Un confronto deciso dopo aver visto i risultati, E3b: **BM25 con pesi uguali sui
campi batte l'ibrida sulle parafrasi** (0,646 contro 0,611); **lo dichiariamo**.

## 6. La prima pagina, sul test set `manual` (3:30-4:00)

*stesso ordine di `fonti`; con 30 query solo le differenze grandi sono significative*

Su `manual` **l'ordine è lo stesso di `fonti`**: analizzatore italiano meglio dello standard
(**+0,052, p 0,04**), **ibrida meglio di BM25 (+0,103, p 0,010)**. kNN sopra BM25 di 0,063, ma
**non significativo: con 30 query gli intervalli sono larghi**. La spinta alle pagine pubblicate
**peggiora (-0,046, p 0,03)**, quindi non è nel default. Sulle sole 10 query giudicate da persone
**la direzione è la stessa**, ma 10 query sono troppo poche per la significatività.

## 7. Quanto costa la qualità (E6, E8) (4:00-4:40)

*come si misura la latenza; ibrida tre volte BM25 ma sotto i 60 ms; quantizzare non costa qualità*

Latenza su **500 query, dopo un riscaldamento**, con le configurazioni **in ordine casuale per ogni
query**, così hanno le stesse cache; per kNN è incluso il calcolo del vettore della query.
**L'ibrida fa due ricerche e costa circa tre volte BM25, ma resta sotto i 60 ms al 95°
percentile.** E8: **comprimere i vettori a 8 bit o a 1 bit non cambia MRR@10 in modo misurabile (p
0,95)**; BBQ perde un poco di recall (R@100 -0,003). La latenza non cambia perché il corpus è
piccolo: **il vantaggio è la memoria**, che ha mostrato Daniel.

## 8. Limiti (4:40-5:10)

*20 query di `manual` giudicate da un modello; kappa e risultati anche sulle 10 umane*

Questi limiti **cambiano come leggere i numeri**. Il più importante per `manual`: per stare nei
tempi, **le query da M11 a M30 le ha giudicate un modello linguistico** con le stesse linee guida,
e un modello ha fatto da terzo giudice. **L'accordo lo misuriamo sulle dieci query giudicate da
persone, e su quelle riportiamo anche i risultati.** E2 ed E4 sono misurati **solo su `fonti`**,
perché i loro documenti non sono nel pool.

## 9. Conclusioni (5:10-5:44)

*tre scelte confermate, due smentite; il passo successivo; ogni numero con un comando*

Le misure hanno **confermato tre scelte**, l'analizzatore italiano, la ricerca ibrida e la
rimozione delle fonti, e **ne hanno smentite due**, i pesi dei campi e la spinta alle pagine
pubblicate. Anche questo è un risultato: **senza la valutazione avremmo tenuto due scelte
sbagliate**. Il passo successivo sarebbe **un'ibrida costruita su BM25 a pesi uguali**, che non
abbiamo provato **per non tarare il motore sulle stesse query con cui lo valutiamo**. **Ogni numero
di queste slide si riproduce con un comando.**
