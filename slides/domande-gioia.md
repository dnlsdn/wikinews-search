# Domande probabili sulla valutazione (Gioia)

Domande che il professore può fare sulla parte di Gioia, con una risposta breve. Tutti i numeri
vengono dalla run ufficiale del 17 novembre 17:27 (`results/summary.md`) e dal log di `STATE.md`.
I p sono corretti con Holm, salvo dove scritto "p grezzo".

## Test set e metriche

1. **Perché due test set e non uno?** Rispondono a domande diverse. `fonti` è grande (7.072
   query) ma ha **una sola risposta giusta** per query: misura se il motore trova la notizia.
   `manual` è piccolo (30 query) ma ha **giudizi graduati** su tutta la prima pagina: misura
   quanto è buona la pagina. Uno dà potenza statistica, l'altro realismo.
2. **I titoli delle fonti non sono una scorciatoia? La risposta è già nel testo.** No, perché le
   fonti sono **tolte dal testo indicizzato** (Daniel toglie ogni template di fonte). Il controllo
   su 300 query: il titolo compare nel testo in **7 casi (2,3%)**, perché l'articolo cita il
   titolo: sovrapposizione naturale tra giornali. E4 mostra cosa succederebbe con le fonti
   cercabili: MRR@10 **da 0,768 a 0,900**.
3. **Perché una query per articolo, e perché tutte e non un campione?** Una per articolo così gli
   articoli con molte fonti non pesano di più. Tutte le 7.072, così non c'è una scelta di
   campione da difendere; le 1.000 di sviluppo servivano solo mentre il sistema cambiava.
4. **Come è definito l'overlap, e perché le soglie 0,2 e 0,5?** Jaccard tra gli insiemi di parole
   della query e del titolo dell'articolo, in minuscolo, senza stop word italiane. Le soglie sono
   **fissate nel piano prima dei risultati**, non scelte guardandoli. Gruppi: basso 2.643, medio
   3.571, alto 858.
5. **Perché avete tolto i titoli non italiani?** A occhio, su 100 query senza parole funzionali
   italiane, **17 erano in altre lingue**, due su tre nel gruppo basso. Favorivano kNN, che è
   multilingue: su 9 di queste query MRR@10 kNN 0,833 contro BM25 0,448. Avrebbero gonfiato E3
   proprio sulle parafrasi. Regola nuova, 1.122 titoli tolti, controllata a occhio: 50 scartati
   su 50 non italiani, 1 tenuto su 50 non italiano.
6. **Perché MRR su `fonti` e nDCG su `manual`?** Con un solo documento giusto contano solo la sua
   posizione e se c'è: MRR@10 = 1 / posizione del primo rilevante nei primi 10, e P@10 sarebbe al
   massimo 0,1. Con tre gradi serve una metrica che usi il grado e la posizione: nDCG@10, guadagno
   2^grado - 1, sconto log2(posizione + 1), normalizzato con l'ordinamento ideale.
7. **Perché anche R@100?** Dice se il documento giusto è almeno **tra i candidati**. È lì che kNN
   perde: R@100 0,942 contro 0,958 di BM25. Un metodo che fonde le liste, come l'ibrida, può
   recuperare solo ciò che è tra i candidati.
8. **Come si calcola MAP?** Per ogni query, la media della precisione alle posizioni dei
   rilevanti, divisa per **tutti** i rilevanti giudicati (quelli non trovati contano 0). MAP è la
   media sulle query.

## Il test set `manual`

9. **Come avete scelto le 30 query?** Scritte **prima di vedere un solo risultato**, quattro tipi
   (argomento, entità, periodo, vaghe), anni e temi misti, ognuna con il suo bisogno informativo.
   Approvate senza modifiche da Daniel e Fabio.
10. **Cos'è il pooling e che rischio ha?** Si giudicano solo le prime 10 posizioni di cinque
    configurazioni: 573 documenti, da 11 a 27 per query. I documenti non giudicati contano come
    non rilevanti, quindi una configurazione **fuori dal pool** è penalizzata: per questo E2 ed E4
    sono misurati solo su `fonti`. kNN è nel pool: **95 documenti** li ha trovati solo lui.
11. **Cos'è il kappa di Cohen e come si legge 0,543?** È l'accordo tra due giudici **al netto di
    quello dovuto al caso**: (accordo osservato - accordo atteso) / (1 - accordo atteso).
    Accordo grezzo 72,5% su 178 documenti; kappa 0,543 sui tre gradi (moderato, Landis e Koch),
    0,674 su rilevante sì/no (sostanziale). È più alto in binario perché il disaccordo più
    frequente è 1 contro 2 (21 su 49), che in binario non è un disaccordo. Gli altri: 0 contro 1
    in 14 casi, 0 contro 2 in 14. Si concentrano su due query legate a un periodo, M03 (13) e
    M07 (11), dove conta la regola "altro anno, altra elezione".
12. **Venti query le ha giudicate un modello: i numeri valgono?** È il limite principale e lo
    diciamo. Il modello segue le stesse linee guida; il kappa è solo tra persone. Sulle sole 10
    query giudicate da persone la direzione è la stessa per E1 (+0,062), ibrida contro BM25
    (+0,050) ed E5 (-0,079), ma **nessuna differenza è significativa** (p da 0,35 a 0,85): 10
    query non bastano né per confermare né per smentire. Lì kNN è sotto BM25 (-0,031, p 0,74).
13. **Come ha lavorato il terzo giudice?** Alla cieca: ha visto solo la query, il bisogno, le
    linee guida e l'articolo, mai i voti dei due giudici. Sui 49 disaccordi ha dato il voto più
    alto 27 volte, il più basso 16, il voto intermedio 1 in 6 coppie 0-2.

## Statistica

14. **Come funziona il test di randomizzazione appaiato?** Se le due configurazioni fossero
    equivalenti, per ogni query i loro due punteggi sarebbero scambiabili. Li scambiamo a caso
    query per query, 10.000 volte, e contiamo quante volte la differenza delle medie è grande
    almeno come quella osservata (a due code). Non assume la normalità, che i punteggi per query
    non hanno (RR vale 1, 0,5, 0,33, ... oppure 0).
15. **E l'intervallo di confidenza?** Bootstrap: ricampioniamo le query con reinserimento 10.000
    volte, ricalcoliamo la media e prendiamo il 2,5° e il 97,5° percentile.
16. **Perché Holm?** Ogni esperimento fa molti test, e con molti test qualche p < 0,05 esce per
    caso. Holm, come Bonferroni, limita la probabilità di **anche un solo falso positivo** nella
    famiglia, ma è meno conservativo e non richiede test indipendenti. La famiglia è
    **esperimento per test set**: E3 su `fonti` ha 24 test, E3 su `manual` 3. Per questo il p più
    piccolo di E3 su `fonti` è 0,0024 = 24 x 1/10.000. Esempio: ibrida contro BM25 sulle query
    facili, p grezzo 0,03, dopo Holm 0,18.
17. **Significativo vuol dire importante?** No. Con 7.072 query anche differenze minime sono
    significative: BBQ perde R@100 0,003, significativo (p 0,026), ma irrilevante in pratica.
    Guardiamo sempre anche la grandezza della differenza.
18. **A cosa serve la baseline casuale?** È il pavimento e un controllo del codice. Con 12.213
    documenti e un solo rilevante, R@100 a caso deve valere circa 100 / 12.213 = 0,008: misuriamo
    0,007 [0,005, 0,009]. MRR@10 e nDCG@10 fanno 0,000. Se un sistema casuale prendesse punti,
    le metriche avrebbero un errore.

## Risultati

19. **Perché l'ibrida batte sia BM25 sia kNN?** Perché i due sbagliano in modi diversi: BM25
    perde le parafrasi, kNN perde recall. RRF somma 1 / (60 + posizione) delle due liste, quindi
    premia i documenti alti in entrambe. MRR@10 0,811 contro 0,768 e 0,781; sulle parafrasi
    0,611 contro 0,525; R@100 0,965, sopra entrambi.
20. **E3b: BM25 a pesi uguali batte l'ibrida sulle parafrasi. Perché non l'avete adottato?**
    Perché quel confronto l'abbiamo deciso **dopo** aver visto i risultati: scegliere il motore
    sulle stesse query con cui lo valutiamo è tarare sul test set. Va letto come indicazione.
    In media l'ibrida resta migliore (+0,011, p 0,003); sulle parafrasi BM25 a pesi uguali fa
    0,646 contro 0,611. Il passo successivo sarebbe un'ibrida su BM25 a pesi uguali, provata su
    query nuove.
21. **Perché E5 è misurato su `manual` e non su `fonti`?** Le query di `fonti` hanno come risposta
    solo articoli pubblicati, per costruzione: lì la spinta alle pubblicate è favorita in
    partenza (0,814 contro 0,811). Su `manual` i giudizi guardano solo la rilevanza, e la spinta
    peggiora: nDCG@10 da 0,804 a 0,758 (p 0,029).
22. **Come avete misurato la latenza in modo equo?** 500 query, 20 di riscaldamento scartate;
    per ogni query tutte le configurazioni in ordine casuale, così hanno le stesse cache; per kNN
    la cache dei vettori della query è svuotata, quindi il calcolo del vettore è incluso.
    MacBook Air M4, 16 GB, Elasticsearch con 1 GB di heap. p50: BM25 14,6 ms, kNN 25,8, ibrida
    43,1; p95 dell'ibrida 53,4.
23. **E8: se la quantizzazione non costa nulla, perché non usarla sempre?** Su 12.213 documenti
    la memoria non è un problema (19,2 MB). Il vantaggio conta su corpus grandi; qui misuriamo
    solo che non perde qualità: MRR@10 -0,0004, p 0,95.

## Attenzione

1. **Slide 4, "E3 fa 27 confronti":** sono 24 su `fonti` più 3 su `manual`, e Holm si applica
   alle due famiglie separatamente. Se te lo chiedono, rispondi così (domanda 16).
2. **I disaccordi del kappa:** non sono "quasi tutti" su 1 contro 2; è il tipo più frequente (21
   su 49).
3. **kNN su `manual`:** sulle 30 query è sopra BM25 (+0,063, non significativo), sulle 10 umane è
   sotto. Non dire che kNN "batte" BM25 su `manual`.

## Numeri da avere in testa

| | |
|---|---|
| `fonti` | 17.192 titoli -> 7.072 query; basso 2.643, medio 3.571, alto 858; leakage 7/300 |
| `manual` | 30 query, 573 documenti, 0/1/2 = 279/76/218; 95 solo da kNN |
| Accordo | 72,5%, kappa 0,543 (tre gradi), 0,674 (binario), 178 documenti, 49 disaccordi |
| E1 | MRR@10 0,743 -> 0,768; nDCG@10 0,648 -> 0,701 (p 0,038) |
| E2 | solo titolo -0,104, solo corpo -0,042, pesi uguali +0,032 |
| E3 | MRR@10 0,768 / 0,781 / 0,811; parafrasi 0,525 / 0,557 / 0,611; R@100 kNN 0,942 |
| E3 manual | nDCG@10 0,701 / 0,764 / 0,804; solo ibrida contro BM25 significativo (p 0,010) |
| E4 | MRR@10 0,768 -> 0,900 con le fonti cercabili |
| E5 | nDCG@10 0,804 -> 0,758 (p 0,029) |
| E6 | p50 14,6 / 25,8 / 43,1 ms; p95 ibrida 53,4 ms |
| E8 | MRR@10 -0,0004 (p 0,95); BBQ R@100 -0,003 (p 0,026) |
