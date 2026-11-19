# Wikinews search - discorso di Gioia

Homework 4, parte di Gioia (strategia di test, risultati, conclusioni): slide 1-9 di
`slides/gioia.md`, subito dopo la demo di Fabio, circa 6 minuti. È scritto per essere detto a
voce: stessi contenuti e stessi numeri delle note del pptx, con i passaggi tra una slide e
l'altra. In grassetto le frasi da non perdere; in corsivo, sotto ogni titolo, il messaggio della
slide in una riga, da ricordare se perdi il filo. Numeri dalla run ufficiale del 17 novembre 17:27
(`results/summary.md`); tutti i p sono corretti con Holm. Domande probabili e risposte:
`slides/domande-gioia.md`.

## 1. Come valutiamo (0:00-0:40)

*due test set che si completano: uno dice se troviamo la notizia, l'altro quanto è buona la pagina*

Grazie Fabio. Nella demo avete visto casi singoli; io vi mostro **come abbiamo misurato cosa
funziona meglio in media**. Servono tre cose: **documenti, query e giudizi di rilevanza**. I
documenti sono i 12.213 di Daniel; query e giudizi li abbiamo costruiti in due modi. **`fonti` è
grande e automatico, con una sola risposta giusta per query**: dice se il motore trova la notizia,
e la metrica è **MRR**. **`manual` è piccolo, ma con tre gradi di rilevanza**: dice quanto è buona
la prima pagina, con **nDCG**. Ogni esperimento cambia una cosa sola: **è un'ablazione**.

## 2. Il test set `fonti` (0:40-1:30)

*il titolo di un altro giornale è la query, l'articolo che lo cita è la risposta: 7.072 query*

Ogni articolo di Wikinews cita le sue fonti con il loro titolo. Quel titolo è **una query
realistica, scritta da un altro giornale sulla stessa notizia**, e la risposta giusta la sappiamo
già: l'articolo che lo cita. Sono **migliaia di query senza lavoro manuale**, e non termini presi
a caso: **titoli veri**. Togliamo i titoli corti, stranieri o ambigui e teniamo **una query per
articolo**, così gli articoli con tante fonti non pesano di più: restano **7.072 query**. Le
dividiamo per parole in comune con il titolo dell'articolo: **overlap basso, cioè parafrasi,
2.643**; medio 3.571; alto 858. Due controlli: la regola sulla lingua, verificata a occhio su 100
titoli, perché l'inglese favoriva il modello multilingue; e il leakage, il titolo già nel testo:
**7 query su 300**.

## 3. Il test set `manual` (1:30-2:15)

*query scritte prima dei risultati, pooling alla cieca, kappa 0,54*

Le 30 query di `manual` le abbiamo scritte **prima di vedere un solo risultato**, ognuna con il
suo **bisogno informativo**: la rilevanza si giudica rispetto al bisogno, non alle parole. Poi
**pooling**: le prime 10 posizioni di cinque configurazioni, unite e mescolate, così **chi giudica
non sa quale sistema ha trovato cosa**. Sono 573 documenti, voto 0, 1 o 2; **95 li ha trovati
solo kNN**, che fuori dal pool sarebbe stato penalizzato. Dieci query le abbiamo giudicate in due: **kappa di Cohen 0,54**, accordo moderato sui
tre gradi, sostanziale, 0,67, su rilevante sì o no. I 49 disaccordi li ha risolti **un terzo
giudice alla cieca**, un modello.

## 4. Quando una differenza è vera (2:15-2:55)

*intervallo bootstrap, test di randomizzazione appaiato, Holm, baseline casuale a zero*

Una media da sola non basta. Per ogni media **ricampioniamo le query 10.000 volte** e riportiamo
**l'intervallo al 95%**. Per ogni confronto, **test di randomizzazione appaiato**: query per query
scambiamo a caso i punteggi delle due configurazioni e contiamo quante volte la differenza è grande
almeno come quella vera. E3 fa 24 confronti solo su `fonti`, e qualche p sotto 0,05 uscirebbe per
caso: per questo **correggiamo con Holm**. Ibrida contro BM25 sulle query facili ha **p 0,03, dopo
la correzione 0,18**: non è significativa. E **la baseline casuale fa zero**, come deve: è il
pavimento.

## 5. Il risultato chiave: dove serve la ricerca semantica (E3) (2:55-3:40)

*sulle query facili tutti vicini a 1; sulle parafrasi l'ibrida +0,086; E3b dichiarato*

**Questa è la figura che riassume il progetto.** A destra, quando la query riusa le parole del
titolo, **BM25 è già quasi perfetto**: non c'è niente da guadagnare. A sinistra, sulle parafrasi,
**BM25 scende a 0,525**, ed è lì che serve la semantica: **kNN guadagna 0,032, l'ibrida 0,086**,
tutto significativo. kNN da solo però **perde recall**, 0,942 contro 0,958: sono i nomi rari della
demo. **L'ibrida prende il meglio dei due ed è la migliore anche in media, 0,811.** Una cosa la
dichiariamo: un confronto aggiunto dopo i risultati, E3b, mostra che **BM25 con pesi uguali batte
l'ibrida sulle parafrasi**, 0,646 contro 0,611. Essendo deciso dopo, **è un'indicazione**, non
un'ipotesi testata.

## 6. La prima pagina, sul test set `manual` (3:40-4:10)

*stesso ordine di `fonti`; con 30 query solo le differenze grandi sono significative*

Sulla prima pagina **l'ordine è lo stesso**. L'analizzatore italiano batte lo standard, **+0,052,
p 0,04**; **l'ibrida è la migliore, 0,804, e batte BM25 di 0,103, p 0,010**. kNN è sopra BM25, ma
**non in modo significativo**: con 30 query gli intervalli sono larghi. La spinta alle pubblicate
**peggiora, -0,046, p 0,03**, quindi non è nel default. Sulle 10 query giudicate da persone la
direzione è la stessa, ma sono troppo poche per la significatività.

## 7. Quanto costa la qualità (E6, E8) (4:10-4:50)

*ibrida tre volte BM25 ma sotto i 60 ms; quantizzare i vettori non costa qualità*

La latenza la misuriamo su **500 query, dopo un riscaldamento**, con le configurazioni **in ordine
casuale per ogni query**, così hanno le stesse cache; per kNN è incluso il calcolo del vettore.
BM25 risponde in 15 millisecondi, kNN in 26, **l'ibrida, che fa due ricerche, in 43: tre volte
BM25, ma sotto i 60 ms anche al 95° percentile**. E8: comprimere i vettori a 8 bit o a 1 bit **non
cambia MRR@10 in modo misurabile, p 0,95**. La latenza resta uguale perché il corpus è piccolo:
**il vantaggio è la memoria**, che ha mostrato Daniel.

## 8. Limiti (4:50-5:20)

*20 query di `manual` giudicate da un modello: kappa e risultati anche sulle 10 umane*

I limiti **cambiano come leggere i numeri**. Il più importante: **per stare nei tempi, 20 query
di `manual` su 30 le ha giudicate un modello linguistico**, con le stesse linee guida. Per questo
**il kappa lo misuriamo sulle dieci query giudicate da persone, e su quelle riportiamo anche i
risultati**. Poi, i documenti non giudicati contano come non rilevanti: E2 ed E4, fuori dal pool,
li misuriamo **solo su `fonti`**.

## 9. Conclusioni (5:20-6:00)

*tre scelte confermate, due smentite; il passo successivo; ogni numero con un comando*

Per chiudere. Le misure hanno **confermato tre scelte**: l'analizzatore italiano, la ricerca
ibrida e la rimozione delle fonti, senza la quale il leakage avrebbe gonfiato MRR da 0,768 a
0,900. E **ne hanno smentite due**: i pesi dei campi e la spinta alle pubblicate. **Senza la
valutazione avremmo tenuto due scelte sbagliate.** Il passo successivo sarebbe un'ibrida su BM25 a
pesi uguali, provata su query nuove, **per non tarare il motore sulle query con cui lo valutiamo**.
E **ogni numero che avete visto si riproduce con un solo comando**. Grazie.

## Se sei in ritardo

Taglia in quest'ordine:

1. Slide 2: i due controlli (lingua e leakage); restano nelle domande 2 e 5.
2. Slide 3: il terzo giudice; resta la domanda 13.
3. Slide 7: come si misura la latenza; tieni solo "15, 26, 43 millisecondi, sotto i 60".

Non tagliare mai la slide 5 (E3) né la frase sulle due scelte smentite.

## Cosa non dire

1. **"E3 fa 27 confronti"** (come scrive la slide 4): sono 24 su `fonti` e 3 su `manual`, e Holm
   si applica alle due famiglie separatamente (domanda 16). Il discorso dice "24 solo su `fonti`".
2. **"kNN batte BM25 su `manual`"**: sulle 30 query è sopra di 0,063 ma non significativo, sulle
   10 umane è sotto.
3. **"I disaccordi sono quasi tutti 1 contro 2"**: è il tipo più frequente, 21 su 49.
