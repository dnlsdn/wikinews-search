---
title: Wikinews search
colorFrom: gray
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
short_description: Lexical, semantic and hybrid search over the Italian Wikinews
---

# Wikinews search

Public demo of [wikinews-search](https://github.com/dnlsdn/wikinews-search): a search engine over
the 12,213 news articles of the Italian Wikinews (dump of 20 March 2025), with BM25, vector (kNN on
multilingual-e5-small) and hybrid (reciprocal rank fusion) retrieval, filters, facets and a
side-by-side comparison of two configurations. Homework 4 of Ingegneria dei Dati, Roma Tre, by
Gioia Buratti, Fabio Massimo Di Marco and Daniel Sadun.

How it runs: the `Dockerfile` of this Space clones the code from GitHub, downloads the public dump
from Wikimedia, parses it and builds the Elasticsearch indices while the image is built; at start
Elasticsearch listens only inside the container and the web app answers on port 7860. On the free
tier the Space sleeps after a period without visits and takes a few minutes to wake up.

Texts from [Wikinotizie](https://it.wikinews.org), under CC BY 4.0 (articles before 25 September
2005: CC BY 2.5); every article links to its original page.
