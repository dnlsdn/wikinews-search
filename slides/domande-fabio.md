# Domande probabili sul retrieval e la demo (Fabio)

Domande che il professore può fare sulla parte di Fabio, con una risposta breve. I numeri vengono
dalla run ufficiale del 17 novembre 17:27 (`results/summary.md`), dal codice di
`wikisearch/search/` e dal log di `STATE.md`. I p sono corretti con Holm, salvo dove scritto
"p grezzo". Non fa parte del deck.

## Architettura

1. **Perché una sola funzione `search()` per interfaccia e valutazione?** Così quello che si misura
   è esattamente quello che l'utente vede: nessuna seconda implementazione "per gli esperimenti"
   che potrebbe divergere. Ogni scelta è una **configurazione con un nome** in `configs.py`
   (undici), e il runner di Gioia le prova tutte con la stessa chiamata.
2. **Perché la configurazione di default è `hybrid-rrf`?** È la migliore su `manual` (nDCG@10
   0,804) e, tra le configurazioni senza spinta, su `fonti` (MRR@10 0,811). La variante con la
   spinta fa 0,814 su `fonti`, ma lì vince per costruzione (domanda 24) e su `manual` perde: E5
   l'ha smentita.
3. **Cosa restituisce Elasticsearch, e cosa no?** Solo i campi che servono alla lista dei
   risultati (titolo, data, lead, categorie, fonti, immagine, `published`): mai il corpo né il
   vettore (384 numeri per documento). Così la risposta resta piccola.

## BM25 e i campi (E2)

4. **Come funziona la query BM25?** Una `multi_match` di tipo `best_fields` su titolo, lead e
   corpo: il punteggio è quello del campo che corrisponde meglio, più 0,3 volte gli altri
   (`tie_breaker` 0,3). I pesi della nostra configurazione sono titolo x3, lead x2, corpo x1.
5. **Perché avevate scelto 3-2-1?** Per intuizione: il titolo di una notizia ne dice
   l'essenziale. **L'esperimento l'ha smentita**: i pesi uguali danno MRR@10 0,800 contro 0,768
   (+0,032, p 0,0006).
6. **Perché i pesi uguali vincono?** Il guadagno è sulle parafrasi (gruppo a basso overlap): 0,646
   contro 0,525. Se la query non usa le parole del titolo, gonfiare il titolo premia i documenti
   sbagliati che quelle parole le hanno. Sulle query facili (overlap alto) i nostri pesi sono
   anzi un po' meglio: 0,996 contro 0,982.
7. **Allora perché l'ibrida usa ancora 3-2-1?** Le configurazioni sono state fissate **prima** dei
   risultati. Cambiarle dopo aver visto il test set vorrebbe dire tarare il motore sulle stesse
   query che lo valutano: i numeri non sarebbero più onesti. L'ibrida sui pesi uguali è il passo
   successivo, da misurare su query nuove.
8. **Solo titolo o solo corpo?** Solo titolo perde 0,104 di MRR@10 e 0,071 di R@100: il titolo è
   troppo corto (0,283 sulle parafrasi). Solo corpo perde 0,042, ma tiene la recall (R@100 0,956
   contro 0,958, differenza non significativa).

## Ricerca vettoriale (kNN)

9. **Quale modello e cosa è vettorizzato?** `multilingual-e5-small`, 384 dimensioni. Per i
   documenti (lavoro di Daniel) titolo + lead, con il prefisso "passage: "; e5 tronca a 512 token,
   un motivo per non usare tutto il corpo. La query con "query: ", vettore normalizzato. Lo stesso
   modello per documenti e query, altrimenti i vettori non sarebbero confrontabili.
10. **Come trova i vicini?** Ricerca approssimata sul grafo **HNSW** di Elasticsearch, similarità
    coseno. `num_candidates` = max(100, 10 x k): quanti vicini esaminare prima di tenere i k
    migliori; più alto è più preciso e più lento.
11. **Dove vince e dove perde kNN?** Vince sulle parafrasi: MRR@10 0,557 contro 0,525 (+0,032, p
    0,0024). Perde sulle query facili (0,979 contro 0,996) e in recall: R@100 0,942 contro 0,958.
    Sui nomi rari il modello non ha un vettore preciso: nella demo "Pontecorvo" BM25 lo trova
    primo, kNN no.
12. **Perché il modello piccolo?** Gira su un portatile da 8 GB, vettorizza la query in circa 17 ms
    e i 12.213 documenti una volta sola (i vettori sono nel repository, uguali per tutti). Un
    modello più grande non l'abbiamo provato: è un limite.

## Ibrida con RRF (E3)

13. **Come funziona RRF?** Si fanno le due ricerche, 100 risultati ciascuna, con gli stessi filtri.
    Ogni documento prende 1/(60 + posizione) da ogni lista in cui compare; si sommano e si ordina.
    Un documento primo in entrambe vale 2/61 = 0,0328, il massimo. A parità decide l'id, così
    l'ordine è deterministico.
14. **Perché le posizioni e non i punteggi?** I punteggi sono su scale diverse: BM25 non ha un
    massimo e dipende dalla query; i punteggi di e5 sono schiacciati in una banda stretta (0,934 -
    0,948 sui primi 5 di "disastro in una miniera"). Una somma pesata richiederebbe di normalizzare
    e di tarare un peso, cioè un altro parametro da scegliere sui dati di test. RRF ha una sola
    costante.
15. **Perché k = 60?** È il valore dell'articolo originale (Cormack e altri, 2009). Non l'abbiamo
    tarato: tararlo sul test set sarebbe lo stesso errore dei pesi. Un k grande appiattisce le
    differenze tra le prime posizioni; uno piccolo dà quasi tutto al primo di ogni lista.
16. **Cosa dicono i numeri?** Su `fonti` l'ibrida è la migliore: MRR@10 0,811 contro 0,768 (BM25) e
    0,781 (kNN), R@100 0,965, tutte le differenze significative. Il guadagno più grande è sulle
    parafrasi: 0,611, +0,086 su BM25. Su `manual` è significativa solo contro BM25 (+0,103, p
    0,010); contro kNN +0,040, p 0,63: con 30 query gli intervalli sono larghi.
17. **C'è un caso in cui l'ibrida perde?** Sì (E3b, misurato dopo aver visto E2): contro BM25 a pesi
    uguali vince in media (+0,011, p 0,003) ma **perde sulle parafrasi** (-0,036, p 0,0008). Lo
    diciamo sulla slide. Anche contro BM25 3-2-1, sulle query facili l'ibrida è un po' sotto
    (-0,006), ma non significativo dopo Holm (p 0,18, p grezzo 0,03).
18. **Perché l'ibrida recupera la recall che kNN perde?** Fonde due liste di 100: un documento che
    kNN non vede ma BM25 sì entra comunque nella lista fusa. R@100 0,965, sopra entrambe.

## Filtri, faccette, pagine non pubblicate (E5)

19. **Filtri: perché `filter` e non `must`?** Le clausole `filter` escludono documenti senza
    cambiare il punteggio, quindi una classifica filtrata è la stessa classifica, ristretta (ed
    Elasticsearch le mette in cache). Data inclusiva; categorie tutte richieste; fonti una
    qualsiasi.
20. **E nella ricerca kNN?** Il filtro sta **dentro** la ricerca nel grafo, non dopo: una query
    vettoriale filtrata restituisce comunque k risultati, se esistono. Filtrare dopo potrebbe
    lasciare la pagina quasi vuota.
21. **Come sono calcolate le faccette?** Aggregazioni su categorie (15), fonti (10) e data per
    anno, calcolate sulla query BM25 senza i filtri, anche quando la configurazione è kNN. Sono
    lessicali per scelta: kNN dà un vicino a qualsiasi documento, quindi non ha un "insieme dei
    risultati" da contare. Effetto: in modalità kNN i conteggi descrivono i documenti che
    contengono le parole, non la lista mostrata.
22. **Perché tenere le 1.181 pagine non pubblicate (10%)?** Speciali, tabelle, bozze: alcune
    rispondono davvero alla query (lo speciale del terremoto nella demo). Restano nell'indice,
    marcate, con un filtro "solo pubblicate" per chi le vuole escludere.
23. **E5: perché la spinta peggiora?** Punteggio per 1,5 alle pubblicate dopo la fusione: nDCG@10
    su `manual` da 0,804 a 0,758 (-0,046, p 0,029). La nostra lettura: porta su pagine pubblicate
    meno pertinenti, mentre alcune pagine non pubblicate (uno speciale, una classifica) rispondono
    davvero alla query, come nella demo. È un'interpretazione, non l'abbiamo contata query per
    query. Per questo il default non la usa.
24. **Perché E5 non è misurato su `fonti`?** Lì il documento giusto è sempre un articolo
    pubblicato: la spinta vincerebbe per costruzione. Infatti su `fonti` sale appena (0,814 contro
    0,811), e non lo usiamo come prova.

## Costi (E6)

25. **Quanto costa l'ibrida?** p50 43,1 ms contro 14,6 di BM25 e 25,8 di kNN; p95 53,4 ms. Fa le due
    ricerche una dopo l'altra, e infatti 43 è circa 15 + 26. Misurato sul Mac di Gioia
    (Apple M4, 16 GB), 500 query, k = 100, compreso il calcolo del vettore della query.
26. **Perché "solo titolo" è così veloce (3,9 ms)?** Un solo campo, e corto: poche notizie hanno le
    parole della query nel titolo, quindi le liste di occorrenze da scorrere sono brevi. È anche
    la configurazione peggiore: la velocità non basta.
27. **Il primo avvio è lento?** Sì: caricare il modello richiede da 19 s (Mac di Daniel) a 78 s
    (portatile di Fabio subito dopo l'avvio di Docker). Per questo prima della demo si lancia una
    query kNN di riscaldamento. Le configurazioni BM25 non caricano mai il modello.

## Interfaccia e demo

28. **A cosa serve la modalità Compare?** Mostra due configurazioni affiancate sulla stessa query:
    rende visibili gli esperimenti. Esempio: "il pontefice è deceduto", BM25 mette "Il papa emerito
    Benedetto XVI è morto" al 78° posto (l'articolo dice "papa", non "pontefice"), kNN primo,
    l'ibrida al 6° (con "Giovanni Paolo II è morto" al 4°): sta in mezzo.
29. **Il nuovo stile cambia qualcosa nei risultati?** No: cambiano solo colori e impaginazione
    (BM25 scuro, kNN verde acqua, ibrida arancione, come nelle slide). Stessa `search()`, stesse
    configurazioni, stessi numeri.

## Attenzione

1. **Non dire che i nostri pesi erano giusti.** E2 li smentisce: pesi uguali +0,032. La difesa è
   il metodo (configurazioni fissate prima, non ritarate sul test set), non la scelta.
2. **Non dire che l'ibrida batte sempre tutto.** Contro BM25 a pesi uguali perde sulle parafrasi
   (-0,036); su `manual` contro kNN la differenza non è significativa (p 0,63).
3. **Latenze:** quelle ufficiali sono del Mac di Gioia (43,1 ms p50 per l'ibrida). Le misure sul
   portatile di Fabio del 16 novembre (circa 140 ms) erano un controllo, non i numeri ufficiali.
4. **kNN su `manual`:** +0,063 su BM25 ma non significativo (p 0,63). Non dire che "batte" BM25
   lì.

## Numeri da avere in testa

| | |
|---|---|
| E2 | 3-2-1 0,768; solo titolo 0,663; solo corpo 0,726; pesi uguali 0,800 (p 0,0006); parafrasi 0,525 contro 0,646 |
| E3 fonti | MRR@10 BM25 / kNN / ibrida 0,768 / 0,781 / 0,811; parafrasi 0,525 / 0,557 / 0,611; R@100 0,958 / 0,942 / 0,965 |
| E3 manual | nDCG@10 0,701 / 0,764 / 0,804; ibrida contro BM25 +0,103 (p 0,010) |
| E3b | ibrida contro pesi uguali: +0,011 in media, -0,036 sulle parafrasi |
| E5 | nDCG@10 0,804 -> 0,758 (p 0,029); 1.181 pagine non pubblicate |
| E6 | p50 14,6 / 25,8 / 43,1 ms; p95 ibrida 53,4 ms |
| RRF | 1/(60 + posizione), 100 per lista, massimo 2/61 = 0,0328 |
| kNN | e5-small, 384 dimensioni, HNSW, num_candidates max(100, 10k) |
