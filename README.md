# wikinews-search

A search engine with a web interface over the Italian Wikinews news archive (about 12,000 pages,
2004-2025), built on Elasticsearch, with an evaluation of the design choices behind it.

Homework 4 of the Data Engineering course (Ingegneria dei Dati, Roma Tre, 2026/27) by
Gioia Buratti, Fabio Massimo Di Marco and Daniel Sadun.

Status: in progress. See `PLAN.md` and `STATE.md`.

## Requirements

1. Docker (Elasticsearch runs in a container with a 1 GB heap).
2. [uv](https://docs.astral.sh/uv/) and Python 3.12 or newer.
3. About 2 GB of free disk for the dump, the index and the embedding model.

## Setup

```bash
git clone https://github.com/dnlsdn/wikinews-search.git
cd wikinews-search
uv sync --extra embed
docker compose up -d
curl localhost:9200
```

Download the dump (73 MB) and extract it into `data/raw/`:

```bash
curl -L -o data/raw/itwikinews.tar.gz https://dumps.wikimedia.org/other/enterprise_html/runs/20250320/itwikinews-NS0-20250320-ENTERPRISE-HTML.json.tar.gz
tar -xzf data/raw/itwikinews.tar.gz -C data/raw
```

## Usage

Sections to be completed as the parts are implemented: parsing and indexing, running the web app,
reproducing the experiments.
