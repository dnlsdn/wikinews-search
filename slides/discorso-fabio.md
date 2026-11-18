# Wikinews search - discorso di Fabio

Homework 4, parte di Fabio (scelte di retrieval e demo): slide 1-5 di `slides/fabio.md`, circa 6
minuti: 2:37 di slide, poi la demo dal vivo (circa 3:20, azioni di Daniel comprese). Il testo delle
slide 1-4 è lo stesso delle note del pptx e di `slides/fabio.md`. La demo segue `docs/demo.md`:
**Fabio parla, Daniel usa l'interfaccia**; tra parentesi quadre le azioni di Daniel, su cui
aspettare. Domande probabili e risposte: `slides/domande-fabio.md`.

## 1. Una ricerca, molte configurazioni (0:00-0:24)

*una sola `search()`, undici configurazioni con un nome, default `hybrid-rrf`*

Il motore non ha una configurazione "giusta" scritta nel codice: ha **undici configurazioni con un
nome**, e **la stessa funzione serve la pagina web e gli esperimenti di Gioia**. Ogni numero che
vedrete corrisponde a qualcosa che si apre nell'interfaccia; la modalità Compare, in figura, mette
due configurazioni a confronto sulla stessa query. Il default è **`hybrid-rrf`**.

## 2. BM25: quali campi, con quali pesi (0:24-1:01)

*i pesi 3-2-1 erano un'intuizione, E2 li smentisce*

BM25 cerca titolo, lead e corpo con una `multi_match` di tipo `best_fields`. Avevamo dato più peso
al titolo per intuizione, ma **i pesi uguali battono i nostri di 0,032**, in modo significativo, e
il guadagno è quasi tutto **sulle parafrasi: 0,646 contro 0,525**. Se la query non riusa le parole
del titolo, spingere il titolo premia i documenti sbagliati che quelle parole le hanno. E3 ed E5
usano ancora 3-2-1: **le configurazioni erano fissate prima dei risultati**, e cambiarle dopo
vorrebbe dire tarare il motore sulle query di test.

## 3. Lessicale, semantica, ibrida (1:01-1:56)

*RRF usa le posizioni; ibrida migliore su fonti, sotto i 60 ms; il limite di E3b*

kNN cerca nel grafo HNSW i vettori più vicini alla query: **batte BM25 sulle parafrasi ma perde
recall sui nomi rari**, come vedrete nella demo. L'ibrida esegue le due ricerche, 100 risultati
ciascuna, e **somma 1/(60 + posizione)** di ogni documento, come nello schema. Usiamo le posizioni
perché **i punteggi BM25 e le similarità coseno sono su scale diverse**: una somma pesata
richiederebbe di tarare un peso. Su fonti **l'ibrida è la migliore**, con il guadagno massimo sulle
parafrasi; su manual è significativa solo contro BM25 (p 0,010), perché con 30 query gli
intervalli sono larghi. Costa latenza, 43 ms contro 15, ma **resta sotto i 60 ms anche al 95°
percentile**. Un limite: **contro BM25 a pesi uguali l'ibrida perde sulle parafrasi**; un'ibrida
sui pesi uguali è il passo successivo.

## 4. Filtri, faccette, pagine non pubblicate (1:56-2:37)

*i filtri non cambiano i punteggi; la spinta alle pubblicate peggiora (E5)*

I filtri sono clausole `filter` di Elasticsearch: **escludono documenti senza toccare il
punteggio**, e valgono anche dentro la ricerca kNN, che così restituisce comunque k risultati. Le
faccette contano per categoria, fonte e anno, sulla query BM25 anche in modalità kNN. Le **1.181
pagine non pubblicate** restano nell'indice, marcate. La spinta alle pubblicate, punteggio per 1,5
dopo la fusione, **fa scendere nDCG@10 su manual da 0,804 a 0,758**: alcune pagine non
pubblicate, come uno speciale, rispondono davvero alla query. Non la misuriamo su fonti, dove il
documento giusto è sempre pubblicato. **Quindi il default non usa la spinta.**

## 5. Demo (2:37-6:00)

*cinque query: ogni numero delle slide diventa un caso concreto*

Ora la demo. **Io spiego, Daniel usa l'interfaccia.** Cinque query, e per ognuna un numero delle
slide diventa un caso concreto.

**Query 1, una ricerca qualsiasi e una pagina non pubblicata.**
[Daniel: `terremoto in Abruzzo`, configurazione `hybrid-rrf`, Invio]
Questa è la configurazione di default, l'ibrida. Ogni risultato ha titolo, data, uno snippet con
le parole evidenziate, categorie e fonti; a sinistra le faccette. Il primo risultato è lo
**Speciale Terremoto in Abruzzo, marcato come non pubblicato**: è una pagina indice, non una
notizia.
[Daniel: menu su `hybrid-rrf-published`]
Con la spinta alle pubblicate lo speciale scende e in cima arriva una notizia. Qui sembra meglio,
ma **E5 dice che in media non conviene**: per questo il default non ha la spinta.

**Query 2, filtri per data e per fonte.**
[Daniel: `terremoto`, `bm25-italian`, Invio; date dal 6 al 30 aprile 2009]
Con le date restano gli articoli sul terremoto dell'Abruzzo del 2009.
[Daniel: spunta `ANSA`]
Con la fonte ANSA ne restano tre. I filtri **restringono senza cambiare i punteggi**, e passano
anche dentro la ricerca vettoriale. I numeri accanto alle caselle sono le faccette, calcolate sulla
query senza filtri.
[Daniel: "Clear filters"]

**Query 3, un nome proprio: vince BM25.**
[Daniel: `Pontecorvo`, `bm25-italian`, spunta Compare con `knn` a destra]
A sinistra BM25, a destra kNN. **BM25 trova subito "Si è spento Gillo Pontecorvo"**: il nome è una
parola sola e corrisponde esattamente. kNN restituisce pagine di servizio e "crolla un ponteggio":
il modello spezza il nome in pezzi e lo avvicina a parole che si somigliano, ponte, ponteggio.
**Sui nomi che non conosce il vettore è debole**: è la recall più bassa di kNN in E3.

**Query 4, una parafrasi: vince kNN.**
[Daniel: `il pontefice è deceduto`, Invio]
BM25 trova persone decedute, ma nessun papa. **kNN mette primo "Il papa emerito Benedetto XVI è
morto"**: l'articolo non dice mai "pontefice" e dice "deceduto" una volta sola, e **BM25 lo mette
al settantottesimo posto**. I vettori colgono il significato: pontefice è papa, deceduto è morto.
[Daniel: secondo menu `hybrid-rrf`, poi primo menu `knn`]
L'ibrida fonde le due classifiche con RRF: Giovanni Paolo II al quarto posto, Benedetto XVI al
sesto. È un compromesso: **non è mai la peggiore, ma non sempre la migliore**; quale convenga in
media lo dice la valutazione, e su fonti vince l'ibrida.

**Query 5, i quasi duplicati.**
[Daniel: togli Compare, `bm25-italian`, `concorso superenalotto`, Invio]
Nove dei primi dieci sono estrazioni del SuperEnalotto che cambiano solo per numero e data. **2.742
pagine, il 22% del corpus, sono generate da template**, estrazioni e giornate di campionato, e
affollano la pagina dei risultati. Le abbiamo marcate con una chiave di serie; raggrupparle nei
risultati era l'esperimento opzionale E7, che **non abbiamo fatto: resta un limite**.

## Se chiedono "i vettori vincono sempre?"

[Daniel: `rincaro del greggio`, `bm25-italian`, Compare con `knn`]
BM25 trova gli articoli sul prezzo del petrolio dal quarto posto; kNN parte con pagine che non
c'entrano e ha il primo articolo sul petrolio solo al quinto. Una parola rara, "greggio", **un
modello piccolo e multilingue non la capisce bene**.

## Se la demo non parte

Gli screenshot di ogni passo sono in `results/demo/`, nell'ordine delle query (`1a`, `1b`, `2`,
`3`, `4a`, `4b`, `5`); il discorso resta lo stesso.
