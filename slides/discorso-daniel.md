# Wikinews search - discorso di Daniel

Homework 4, parte di Daniel (dati e indicizzazione): copertina e slide 2-8, circa 5:55 minuti. Lo stesso testo è nelle note del pptx (`slides/wikinews-search.pptx`) e in `slides/daniel.md`.

## 1. Copertina (0:00-0:39)

*chi siamo, cosa abbiamo fatto, la query della copertina*

Buongiorno. Siamo Gioia Buratti, Fabio Massimo Di Marco e Daniel Sadun. Abbiamo costruito un **motore di ricerca sulle notizie di Wikinews in italiano**, e abbiamo **misurato ogni scelta di progetto** con un'ablazione. A destra vedete una delle query della demo, "il pontefice è deceduto": BM25 cerca le parole e trova persone decedute, ma nessun papa; la ricerca semantica mette al primo posto la morte di **Benedetto XVI, che BM25 mette al settantottesimo posto**. Io presento i dati e l'indicizzazione, Fabio le scelte di ricerca e la demo, Gioia la valutazione e i risultati.

## 2. Il corpus (0:39-1:19)

*12.213 documenti, metà delle notizie nel 2005-2008*

Il corpus è il dump di Wikinews in italiano del **20 marzo 2025**: un oggetto JSON per pagina, con l'HTML e il wikitext di ogni articolo. Le righe sono 12.261, ma alcune pagine compaiono più volte, una per revisione: teniamo la più recente e restano **12.213 documenti**. Il 90% è pubblicato, il 96% ha una data, quasi diecimila citano almeno una fonte. Il grafico mostra la cosa più evidente: il corpus è piccolo ma **molto sbilanciato**, più di metà delle notizie datate è del **2005-2008**, gli anni in cui Wikinews in italiano era più attiva.

## 3. Le informazioni sono nei template (1:19-2:10)

*data e lead non sono campi: data dal template, lead dall'HTML*

La prima difficoltà: le informazioni che ci servono **non sono campi del dump**. Il dump ha solo la data dell'ultima modifica, spesso anni dopo la notizia. La data vera è scritta a mano in un **template in italiano**, come questo luogodata, che diventa 2020-05-20. La estraiamo dal wikitext per 11.687 documenti e per 40 dalla categoria del giorno; 486 restano senza data, e un campo dice da dove viene ogni data. Lo stesso per l'abstract: in 11.632 pagine **inizia con la data**, e a volte c'è solo quella, come "martedì 17 giugno 2008". Il lead lo ricostruiamo dall'HTML, con il primo paragrafo vero. Conta perché è quello che leggono gli embeddings: **con la sola data, tutte le notizie dello stesso giorno sembrerebbero uguali**.

## 4. Metadati da ripulire (2:10-2:45)

*categorie e agenzie diventano filtri: via le categorie inutili, una chiave per le grafie*

Categorie e fonti diventano **filtri e faccette** nell'interfaccia, quindi devono essere pulite. Delle quasi seimila categorie, 4.188 sono categorie di data, una per giorno, e 22 sono di manutenzione, come "Pubblicati": le togliamo e ne restano 1.753. Le agenzie sono scritte a mano: **la Repubblica compare in 14 grafie**. Le raggruppiamo con una **chiave normalizzata**, cioè minuscole, senza articolo e senza dominio, più qualche alias, e mostriamo la grafia più frequente. Senza questo passo, filtrando "la Repubblica" **si perderebbe il 28% delle sue fonti**.

## 5. Non tutte le pagine sono notizie (2:45-3:25)

*non pubblicate, serie, tabelle: tutto tenuto e marcato*

Non tutte le pagine sono notizie. **1.181 non sono pubblicate**: speciali, palinsesti, classifiche, bozze. Le teniamo, marcate: uno speciale sulle elezioni può rispondere a una query vera, e **se convenga penalizzarle lo misura un esperimento**, E5, che mostra Fabio. Poi le **serie generate da template**, come i 216 concorsi del SuperEnalotto, con titoli uguali a meno dei numeri: un campo sostituisce le cifre e permette di raggrupparle. Infine il **36% del testo è in tabelle**: le teniamo come testo, una riga per riga, perché 366 pagine sono fatte solo di tabelle e sarebbero rimaste vuote.

## 6. Leakage (3:25-4:21)

*le query di fonti sono dentro le pagine: le togliamo, E4 misura quanto conta*

Il problema più insidioso riguarda la valutazione. Il test set fonti, che presenta Gioia, usa come query **i titoli delle fonti citate**: qui "Il Dna lo scagiona, ma ha già scontato 24 anni", un titolo di Euronews; la risposta giusta è l'articolo che lo cita. Ma quel titolo **sta dentro la pagina**, nel template della fonte: se fosse cercabile, il motore troverebbe la query parola per parola e **il test non misurerebbe niente**. Non basta togliere la sezione "Fonti": in 381 pagine le fonti sono altrove. Quindi **togliamo ogni template di fonte, dovunque sia**, e teniamo i titoli in un campo a parte solo per misurare l'effetto, l'esperimento E4: con le fonti cercabili **MRR@10 salirebbe da 0,768 a 0,900**. Un test con leakage avrebbe fatto sembrare il motore molto migliore di quello che è.

## 7. Due indici, due analisi del testo (4:21-5:04)

*standard contro italian: meglio su tutto, anche più veloce*

Indicizziamo con **Elasticsearch**, un nodo e uno shard su un portatile. Costruiamo **due indici con gli stessi campi** e due analizzatori: standard e **italian**, che aggiunge elisione, stop word italiane e uno **stemmer leggero**. "Elezioni" ed "elezione" diventano elezion, "l'Italia" diventa ital; ma lo stemmer leggero non unisce tutto: scagiona e scagionato restano diversi. Con meno termini distinti l'indice è più piccolo del 6%. Il risultato, l'esperimento E1, è a destra: l'analisi italiana migliora MRR@10 e recall su fonti, entrambi significativi, e **nDCG@10 su manual da 0,648 a 0,701**; e la query è anche più veloce. **Non è un compromesso: è meglio su tutto.**

## 8. Embeddings (5:04-5:55)

*un vettore per documento su titolo e lead; kNN capisce le parafrasi; E8: memoria*

Per la ricerca semantica calcoliamo **un vettore per documento** con multilingual-e5-small, 384 dimensioni, su **titolo e lead**, perché il modello tronca i testi lunghi e l'inizio di una notizia ne dice l'essenziale. Bastano due minuti su CPU, e i vettori sono nel repository, così tutti indicizzano gli stessi. A destra un esempio: "disastro in una miniera" trova "Cina: esplosione in miniera, 11 morti", ma **nessun risultato contiene la parola disastro**: il vettore coglie il significato. Sulle parafrasi **kNN batte BM25**, da 0,525 a 0,557 di MRR@10. Infine l'esperimento E8: comprimere i vettori costa quasi niente in qualità, come mostrerà Gioia, e **riduce la memoria da 19 a 5 e a poco più di 1 megabyte**. Con dodicimila documenti non serve; con milioni sì.

## Domande a cui rispondo io

1. **Perché tenere le pagine non pubblicate?** Perché alcune rispondono a query vere (uno speciale, una classifica) e la valutazione deve vedere tutto il corpus. Le marchiamo con **published: false** e la penalizzazione la decide un esperimento: **E5**, spinta x1,5 alle pubblicate, fa scendere nDCG@10 su manual **da 0,804 a 0,758 (p 0,029)**. Quindi niente spinta.
2. **Quale versione tieni quando una pagina compare due volte?** La **più recente**: stesse pagine con lo stesso identificativo, una per revisione (fino a 13 volte). Da 12.261 righe a **12.213 documenti**.
3. **Perché BM25 e non tf-idf?** BM25 è il **ranking di default di Lucene ed Elasticsearch** ed è un tf-idf migliorato: la frequenza del termine **satura** (parametro k1, la decima occorrenza conta meno della prima) e il punteggio è **normalizzato sulla lunghezza** del campo (parametro b). Abbiamo tenuto i valori di default.
4. **Cosa fa esattamente l'analizzatore italian?** Toglie l'**elisione** (l'Italia -> Italia), mette in minuscolo, toglie le **stop word italiane** e applica uno **stemmer leggero** (light italian): elezioni ed elezione -> elezion. Leggero vuol dire che taglia poco: scagiona e scagionato restano diversi.
5. **Perché non avete provato asciifolding, cioè togliere gli accenti?** Perché le query dei due test set **hanno gli accenti** scritti bene: una variante senza accenti non avrebbe misurato nulla. Lo stemmer li toglie già nelle parole lunghe (perché e perche -> perc), non in quelle corte (città e citta restano diverse).
6. **Perché categorie e agenzie sono keyword?** Perché servono per **filtri esatti e faccette** (aggregazioni): un campo keyword non viene analizzato, quindi "la Repubblica" resta un valore solo e si può contare. Il testo (titolo, lead, corpo) invece è text, analizzato.
7. **Perché il mapping è rigido?** Con **dynamic: strict** un campo non previsto è un errore invece di diventare un campo nuovo in silenzio: così il contratto tra le nostre tre parti non si rompe senza che ce ne accorgiamo.
8. **Perché un solo shard?** 12.213 documenti e 1 GB di heap su un portatile da 8 GB: più shard non servono. E con uno shard le statistiche per l'idf sono calcolate su **tutto il corpus**, non shard per shard.
9. **Come funziona il leakage e perché non basta togliere la sezione Fonti?** Le query di fonti sono i titoli delle fonti, che stanno nella pagina dentro il template {{fonte}}. In **381 pagine** almeno una fonte è fuori dalla sezione Fonti (per esempio sotto Collegamenti esterni), e anche togliendo tutte le sezioni di link resterebbero in 19. Quindi togliamo **ogni template di fonte dal corpo**. E4 misura il danno evitato: **MRR@10 da 0,768 a 0,900**, sulle parafrasi da 0,53 a 0,81.
10. **Perché il prefisso passage: e perché titolo più lead?** I modelli **e5** sono addestrati con i prefissi **"passage: "** per i documenti e **"query: "** per le query: senza, la qualità cala. Titolo e lead perché il modello tronca a **512 token** e l'inizio di una notizia ne contiene l'essenziale.
11. **Cos'è HNSW?** Un **grafo di prossimità a più livelli** per la ricerca approssimata dei vicini: si parte dal livello alto, con pochi nodi e collegamenti lunghi, e si scende verso quelli più fitti avvicinandosi alla query. Approssimato: non garantisce i k vicini esatti, ma è molto più veloce della ricerca esaustiva.
12. **Cosa misura E8 e perché su disco gli indici quantizzati sono più grandi?** Quanto costa in qualità comprimere i vettori: **int8** (8 bit per dimensione) e **BBQ** (1 bit). MRR@10 perde 0,0004, non significativo; BBQ perde un po' di recall (R@100 -0,003). La memoria della ricerca scende da **19,2 a 5,3 e 1,2 MB**. Su disco sono più grandi perché Elasticsearch tiene anche i **vettori originali**, che usa per riordinare i candidati finali.
13. **I punteggi coseno sono tutti vicini: è un problema?** Vanno da 0,91 a 0,96, quindi **conta solo l'ordine**, non il valore: per questo la ricerca ibrida fonde le **classifiche** con RRF e non i punteggi (lo spiega Fabio).

## Numeri da avere in testa

| | |
|---|---|
| Corpus | dump 20/3/2025; 12.261 righe -> 12.213 documenti; 11.032 pubblicati (90%); 11.727 con data (96%); 9.891 con fonte; 55% delle datate nel 2005-2008 |
| Date | 11.687 dal template, 40 dalla categoria, 486 senza |
| Metadati | categorie 5.963 -> 1.753 (via 4.188 di data e 22 di manutenzione); agenzie 2.965 grafie -> 2.304; la Repubblica 14 grafie, -28% senza chiave |
| Pagine | 1.181 non pubblicate; 2.742 in serie (22%); 3.661 con tabelle (36% del testo); 366 solo tabelle |
| Leakage (E4) | 381 pagine con fonti fuori sezione; MRR@10 0,768 -> 0,900 (+0,132, p Holm 0,0001) |
| E1 | MRR@10 0,743 -> 0,768; R@100 0,945 -> 0,958 (p Holm 0,0002); nDCG@10 manual 0,648 -> 0,701 (p 0,038); p50 19,2 -> 14,6 ms; indice -6% |
| Embeddings | multilingual-e5-small, 384 dim, 121 s su CPU; parafrasi MRR@10 0,525 -> 0,557 (p Holm 0,002); kNN R@100 0,942 contro 0,958; p50 25,8 ms |
| E8 | memoria 19,2 / 5,3 / 1,2 MB; MRR@10 -0,0004 (n.s.); BBQ R@100 -0,003 |
