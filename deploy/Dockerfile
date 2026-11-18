# Public demo of wikinews-search: one container with Elasticsearch and the web app.
# One container: Elasticsearch on 127.0.0.1 (not reachable from outside) and the web app on 7860.
# Everything is built from public sources: the code from GitHub, the Wikinews dump from Wikimedia,
# the embedding model from Hugging Face. The indices are built once, while the image is built.
FROM python:3.12-slim

ARG REPO=https://github.com/dnlsdn/wikinews-search.git
ARG REF=main
ARG ES_VERSION=9.5.0
ARG DUMP=https://dumps.wikimedia.org/other/enterprise_html/runs/20250320/itwikinews-NS0-20250320-ENTERPRISE-HTML.json.tar.gz

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.11.28

# A non-root user: Elasticsearch refuses to run as root.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    HF_HOME=/home/user/cache \
    ES_HOME=/home/user/es \
    ES_URL=http://127.0.0.1:9200
WORKDIR /home/user

# Elasticsearch, the same version as docker-compose.yml (bundled JDK).
RUN curl -fsSL "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ES_VERSION}-linux-$(uname -m).tar.gz" \
    | tar -xz -C /home/user \
    && mv /home/user/elasticsearch-${ES_VERSION} /home/user/es

RUN git clone --branch "${REF}" "${REPO}" app
WORKDIR /home/user/app

# The locked dependencies, with the CPU build of torch instead of the CUDA one (no GPU here).
RUN uv venv --python 3.12 .venv \
    && TORCH=$(uv export --frozen --no-dev --no-hashes --no-emit-project | grep '^torch==' | cut -d' ' -f1) \
    && uv pip install --python .venv "${TORCH}" --index-url https://download.pytorch.org/whl/cpu \
    && uv export --frozen --no-dev --no-hashes --no-emit-project --no-emit-package torch \
       | grep -v -E '^(nvidia|triton|cuda)' > /tmp/requirements.txt \
    && uv pip install --python .venv -r /tmp/requirements.txt \
    && uv pip install --python .venv --no-deps -e .

# Data: the public dump -> data/processed/docs.jsonl (the dump itself is removed afterwards).
RUN mkdir -p data/raw \
    && curl -fsSL -A "wikinews-search/1.0 (course project; https://github.com/dnlsdn/wikinews-search)" "${DUMP}" \
    | tar -xz -C data/raw \
    && .venv/bin/python -m wikisearch.ingest.parse --no-sample \
    && rm -rf data/raw

# The embedding model, downloaded now so that the first vector query does not wait for it.
RUN .venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-small')"

# The indices, built with the committed vectors (data/shared/), as in the README.
RUN .venv/bin/python deploy/start.py --build-index

EXPOSE 7860
CMD [".venv/bin/python", "deploy/start.py"]
