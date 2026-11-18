# Public demo of wikinews-search: one container with Elasticsearch and the web app.
# Build from the root of the repository (the code is copied, not cloned):
#   docker build -f deploy/Dockerfile -t wikinews-demo .
# Elasticsearch listens on 127.0.0.1 inside the container; the web app answers on 7860.
# The Wikinews dump comes from Wikimedia and the embedding model from Hugging Face; the indices
# are built once, while the image is built.
FROM python:3.12-slim

ARG ES_VERSION=9.5.0
ARG DUMP=https://dumps.wikimedia.org/other/enterprise_html/runs/20250320/itwikinews-NS0-20250320-ENTERPRISE-HTML.json.tar.gz

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.11.28

# A non-root user: Elasticsearch refuses to run as root.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    HF_HOME=/home/user/cache \
    ES_HOME=/home/user/es \
    ES_URL=http://127.0.0.1:9200 \
    PYTHONPATH=/home/user/app
WORKDIR /home/user

# Elasticsearch, the same version as docker-compose.yml (bundled JDK).
RUN curl -fsSL "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ES_VERSION}-linux-$(uname -m).tar.gz" \
    | tar -xz -C /home/user \
    && mv /home/user/elasticsearch-${ES_VERSION} /home/user/es

# Dependencies first (cached while only the code changes): the locked versions, with the CPU
# build of torch instead of the CUDA one (no GPU here).
WORKDIR /home/user/app
COPY --chown=user pyproject.toml uv.lock ./
RUN uv venv --python 3.12 .venv \
    && TORCH=$(uv export --frozen --no-dev --no-hashes --no-emit-project | grep '^torch==' | cut -d' ' -f1) \
    && uv pip install --python .venv "${TORCH}" --index-url https://download.pytorch.org/whl/cpu \
    && uv export --frozen --no-dev --no-hashes --no-emit-project --no-emit-package torch \
       | grep -v -E '^(nvidia|triton|cuda)' > /tmp/requirements.txt \
    && uv pip install --python .venv -r /tmp/requirements.txt

# The embedding model, downloaded now so that the first vector query does not wait for it.
RUN .venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-small')"

# Data: the public dump -> data/processed/docs.jsonl (the dump itself is removed afterwards).
COPY --chown=user wikisearch ./wikisearch
COPY --chown=user data/shared ./data/shared
RUN mkdir -p data/raw \
    && curl -fsSL -A "wikinews-search/1.0 (course project)" "${DUMP}" | tar -xz -C data/raw \
    && .venv/bin/python -m wikisearch.ingest.parse --no-sample \
    && rm -rf data/raw

# The indices, built with the committed vectors (data/shared/), as in the README.
COPY --chown=user deploy ./deploy
RUN .venv/bin/python deploy/start.py --build-index

EXPOSE 7860
CMD [".venv/bin/python", "deploy/start.py"]
