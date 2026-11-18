"""Start the public demo inside its container (see deploy/Dockerfile).

    python deploy/start.py --build-index   # at image build: start Elasticsearch, index, stop
    python deploy/start.py                 # at run time: Elasticsearch, warm-up, web app on 7860

Elasticsearch listens on 127.0.0.1 only, so the only open port is the web app's.
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ES_HOME = Path(os.environ.get("ES_HOME", "/home/user/es"))
ES = "http://127.0.0.1:9200"
APP = "http://127.0.0.1:7860"
PY = sys.executable


BUILT = Path.home() / "esdata"  # written while the image is built
RUN = Path.home() / "esdata-run"  # the copy Elasticsearch works on at run time


def run_data_dir() -> Path:
    # The indices built into the image live in a read-only image layer. If Elasticsearch opened
    # them there, the container file system would copy each file to its writable layer on first
    # write, and Elasticsearch stops when its lock file changes under it ("changed by an external
    # force"). So the data is copied once to a directory of the writable layer, without the lock.
    if not RUN.exists():
        tmp = RUN.with_name(RUN.name + ".tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(BUILT, tmp, symlinks=True, ignore=shutil.ignore_patterns("node.lock"))
        tmp.rename(RUN)
    return RUN


def start_es(data: Path) -> subprocess.Popen:
    env = dict(os.environ, ES_JAVA_OPTS="-Xms1g -Xmx1g")
    settings = [
        "discovery.type=single-node",
        "network.host=127.0.0.1",
        "xpack.security.enabled=false",
        "xpack.ml.enabled=false",
        "cluster.name=wikinews",
        "node.name=es01",
        f"path.data={data}",
    ]
    cmd = [str(ES_HOME / "bin" / "elasticsearch"), "-q"] + [f"-E{s}" for s in settings]
    proc = subprocess.Popen(cmd, env=env)
    wait_for(f"{ES}/_cluster/health?wait_for_status=yellow&timeout=5s", "Elasticsearch", proc)
    return proc


def wait_for(url: str, what: str, proc: subprocess.Popen | None = None, timeout: int = 300) -> None:
    start = time.time()
    while time.time() - start < timeout:
        if proc is not None and proc.poll() is not None:
            sys.exit(f"{what} exited with code {proc.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                if resp.status == 200:
                    print(f"{what} ready after {time.time() - start:.0f} s", flush=True)
                    return
        except OSError:
            pass
        time.sleep(2)
    sys.exit(f"{what} not ready after {timeout} s")


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run([PY, *args], check=True)


def build_index() -> None:
    es = start_es(BUILT)
    try:
        run("-m", "wikisearch.ingest.index", "--no-csv")
        run("-m", "wikisearch.ingest.index", "--no-csv", "--analyzers", "italian",
            "--vector-index", "int8_hnsw", "bbq_hnsw")
    finally:
        es.terminate()
        es.wait(timeout=120)


def warm_up() -> None:
    # The first vector query loads the embedding model (about 20 s): do it before the first visitor.
    wait_for(f"{APP}/api/configs", "web app")
    for config in ("bm25-italian", "knn", "hybrid-rrf"):
        try:
            urllib.request.urlopen(f"{APP}/api/search?q=terremoto&config={config}", timeout=120).read()
        except OSError as err:
            print(f"warm-up {config}: {err}", flush=True)
    print("warm-up done", flush=True)


def serve() -> None:
    es = start_es(run_data_dir())
    web = subprocess.Popen([PY, "-m", "uvicorn", "wikisearch.web.app:app", "--host", "0.0.0.0", "--port", "7860"])
    threading.Thread(target=warm_up, daemon=True).start()
    # If either process stops, stop the container, so that Docker restarts it.
    while es.poll() is None and web.poll() is None:
        time.sleep(5)
    for proc in (es, web):
        if proc.poll() is None:
            proc.terminate()
    sys.exit("Elasticsearch or the web app stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build-index", action="store_true")
    args = parser.parse_args()
    build_index() if args.build_index else serve()
