"""Figure for the embeddings slide: what kNN does, drawn on the real vectors.

    uv run python -m wikisearch.ingest.embedding_map    # -> results/figures/embedding_map.png

The query "disastro in una miniera" is embedded with the search-side prefix ("query: ") and
compared with the shared document vectors (`data/shared/embeddings.npy`), exactly as the `knn`
configuration does, but with an exact scan instead of the HNSW graph.

The 384 dimensions cannot be drawn, so the figure is a target centred on the query:

1. the distance from the centre is the real cosine distance (1 - cosine similarity) between the
   query and the document, so who is near and who is far is exact;
2. the direction is only a layout: the angle of each document in a 2D PCA of the drawn vectors,
   so that documents similar to each other end up on the same side.

Drawn: the 5 nearest documents (the top 5 of `knn`, all mine accidents, inside the dashed circle),
the 5 nearest published documents with "disastro" in the title (they contain the word, not the
meaning), and 300 random documents as background. Ranks 6 to 9 are not drawn: they sit just
outside the circle (e5 similarities are compressed) and would hide where the top 5 ends. Labels in Italian: the
figure goes on the Italian slides.
"""

import json
import textwrap

import matplotlib

matplotlib.use("Agg")  # no window: works the same on macOS, Windows and without a display
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from wikisearch import config  # noqa: E402

QUERY = "disastro in una miniera"
OUT = config.ROOT / "results" / "figures" / "embedding_map.png"
N_TOP, N_WORD, N_RANDOM = 5, 5, 300
SEED = 7

# deck colours (slides: dark ink, orange accent, teal for the kNN family, grey)
DK, OR, TEAL, GR, MUT = "#23373B", "#EB811B", "#4E7C8A", "#A9B4B6", "#6B7B7E"


def short(title: str, width: int = 30) -> str:
    return "\n".join(textwrap.wrap(title, width))


def main() -> None:
    from sentence_transformers import SentenceTransformer

    vectors = np.load(config.EMBEDDINGS_NPY)
    ids = json.loads(config.EMBEDDINGS_IDS.read_text(encoding="utf-8"))
    docs = {}
    with open(config.DOCS_JSONL, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            docs[d["id"]] = d

    model = SentenceTransformer(config.EMBEDDING_MODEL, device="cpu")
    q = model.encode([config.QUERY_PREFIX + QUERY], normalize_embeddings=True)[0]
    sim = vectors @ q
    order = np.argsort(-sim)

    near = [int(i) for i in order[:N_TOP]]
    word = [int(i) for i in order if "disastro" in docs[ids[i]]["title"].lower()
            and docs[ids[i]]["published"]][:N_WORD]
    rng = np.random.default_rng(SEED)
    taken = set(near) | set(word)
    rand = [int(i) for i in rng.choice(len(ids), N_RANDOM + 50, replace=False) if int(i) not in taken][:N_RANDOM]

    drawn = near + word + rand
    X = vectors[drawn] - vectors[drawn].mean(axis=0)
    _, _, vt = np.linalg.svd(X, full_matrices=False)
    pc = X @ vt[:2].T
    raw = {i: float(np.arctan2(pc[k, 1], pc[k, 0])) for k, i in enumerate(drawn)}
    # rotate the layout so that the nearest documents sit up and to the right, next to the labels
    turn = np.deg2rad(40) - float(np.angle(np.mean([np.exp(1j * raw[i]) for i in near])))
    angle = {i: raw[i] + turn for i in drawn}
    radius = {i: 1.0 - float(sim[i]) for i in drawn}

    def xy(i: int) -> tuple[float, float]:
        return radius[i] * np.cos(angle[i]), radius[i] * np.sin(angle[i])

    plt.rcParams["font.family"] = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
    fig, ax = plt.subplots(figsize=(4.75, 3.25), dpi=300)  # its size on the slide: fonts in real points
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    for s in (0.90, 0.85, 0.80):
        ax.add_patch(plt.Circle((0, 0), 1 - s, fill=False, color="#D5DCDD", lw=0.7, zorder=0))
        ax.text(0, -(1 - s) - 0.005, f"{s:.2f}".replace(".", ","), ha="center", va="top", fontsize=8,
                color=MUT, zorder=1)
    r5 = radius[near[-1]] + 0.0006
    ax.add_patch(plt.Circle((0, 0), r5, fill=False, color=TEAL, lw=1.0, ls=(0, (3, 2)), zorder=2))

    for i in rand:
        ax.scatter(*xy(i), s=4, color=GR, alpha=0.55, lw=0, zorder=1)
    for i in word:
        ax.scatter(*xy(i), s=26, color=DK, lw=0, zorder=3)
    for i in near:
        ax.scatter(*xy(i), s=26, color=TEAL, lw=0, zorder=3)
    ax.scatter(0, 0, s=110, marker="*", color=OR, lw=0, zorder=4)
    ax.annotate("query", (0, 0), xytext=(0, -11), textcoords="offset points",
                ha="center", fontsize=10, color=OR, fontweight="bold", zorder=5)

    rank = {int(i): r + 1 for r, i in enumerate(order[:200])}

    def label(i: int, color: str, tx: float, ty: float, note: str = "") -> None:
        text = f"{rank[i]}°  " + short(docs[ids[i]]["title"], 24) + note
        ax.annotate(text, xy(i), xytext=(tx, ty), fontsize=9.5, color=color, ha="left", va="center",
                    arrowprops={"arrowstyle": "-", "color": color, "lw": 0.6, "shrinkB": 3},
                    bbox={"boxstyle": "square,pad=0.15", "fc": "#FAFAFA", "ec": "none", "alpha": 0.9},
                    zorder=5)

    # first result and the first title with the word: the two points the slide talks about
    label(near[0], TEAL, 0.205, 0.195)
    label(word[0], DK, 0.205, 0.02, "\n(contiene «disastro»)")

    ax.set_xlim(-0.235, 0.465)
    ax.set_ylim(-0.245, 0.245)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, transparent=True)

    for name, group in (("nearest", [int(i) for i in order[:8]]), ("disastro in the title", word)):
        print(name)
        for i in group:
            print(f"  {int(np.where(order == i)[0][0]) + 1:>4}  {sim[i]:.3f}  {docs[ids[i]]['title']}")
    print(f"random documents: median similarity {np.median(sim[rand]):.3f}; wrote {OUT}")


if __name__ == "__main__":
    main()
