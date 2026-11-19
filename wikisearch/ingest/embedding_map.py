"""Figure for the embeddings slide: what kNN does, drawn on the real vectors.

    uv run python -m wikisearch.ingest.embedding_map
    # -> results/figures/embedding_map.png (static) and embedding_map.gif (animated, 14 s loop)

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
outside the circle (e5 similarities are compressed) and would hide where the top 5 ends.

The animation (the deck shows it on slide 8; the PDF shows the static PNG) tells the same thing in
time. It starts from the complete figure (what PowerPoint shows outside the slide show), holds it,
fades the search out, then a circle grows from the query and the documents light up as it reaches
them, until it holds 5 (the top 5 of `knn`); last, the titles with "disastro" appear, the first
one only 10th, and the figure is complete again (14 s loop). Both files have the size they take on the slide, so
their fonts are in real points. Labels in Italian: the figure goes on the Italian slides.
"""

import json
import textwrap

import matplotlib

matplotlib.use("Agg")  # no window: works the same on macOS, Windows and without a display
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402

from wikisearch import config  # noqa: E402

QUERY = "disastro in una miniera"
FIGURES = config.ROOT / "results" / "figures"
N_TOP, N_WORD, N_RANDOM = 5, 5, 300
SEED = 7
SIZE = (4.75, 3.25)  # inches, as placed on the slide
FPS = 12

# deck colours (slides: dark ink, orange accent, teal for the kNN family, grey, slide background)
DK, OR, TEAL, GR, MUT, BG = "#23373B", "#EB811B", "#4E7C8A", "#A9B4B6", "#6B7B7E", "#FAFAFA"
TEAL_RGB = (0.306, 0.486, 0.541)  # TEAL as RGB
TEAL_FILL = TEAL_RGB + (0.08,)


def short(title: str, width: int = 24) -> str:
    return "\n".join(textwrap.wrap(title, width))


def layout() -> dict:
    """Nearest documents, documents with the word, background, and their positions on the target."""
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
    radius = {i: 1.0 - float(sim[i]) for i in drawn}
    xy = {i: (radius[i] * np.cos(raw[i] + turn), radius[i] * np.sin(raw[i] + turn)) for i in drawn}
    rank = {int(i): r + 1 for r, i in enumerate(order[:200])}
    return {"ids": ids, "docs": docs, "sim": sim, "order": order, "near": near, "word": word,
            "rand": rand, "radius": radius, "xy": xy, "rank": rank, "r5": radius[near[-1]] + 0.0006}


def draw(L: dict, dpi: int) -> tuple:
    """The figure with every element; returns (fig, artists) so the animation can hide them."""
    plt.rcParams["font.family"] = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
    fig, ax = plt.subplots(figsize=SIZE, dpi=dpi)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in (0.90, 0.85, 0.80):
        ax.add_patch(plt.Circle((0, 0), 1 - s, fill=False, color="#D5DCDD", lw=0.7, zorder=0))
        ax.text(0, -(1 - s) - 0.005, f"{s:.2f}".replace(".", ","), ha="center", va="top", fontsize=8,
                color=MUT, zorder=1)
    xy, docs, ids, rank = L["xy"], L["docs"], L["ids"], L["rank"]
    A = {}
    A["circle"] = plt.Circle((0, 0), L["r5"], fc=TEAL_FILL, ec=TEAL, lw=1.2, ls=(0, (3, 2)), zorder=2)
    ax.add_patch(A["circle"])
    A["rand"] = ax.scatter([xy[i][0] for i in L["rand"]], [xy[i][1] for i in L["rand"]], s=4, color=GR,
                           alpha=0.55, lw=0, zorder=1)
    A["word"] = {i: ax.scatter(*xy[i], s=26, color=DK, lw=0, zorder=3) for i in L["word"]}
    A["near"] = {i: ax.scatter(*xy[i], s=26, color=TEAL, lw=0, zorder=3) for i in L["near"]}
    A["star"] = ax.scatter(0, 0, s=110, marker="*", color=OR, lw=0, zorder=4)
    A["qlab"] = ax.text(0, -0.018, "query", ha="center", va="top", fontsize=10, color=OR, fontweight="bold",
                        zorder=5)

    def label(i: int, color: str, tx: float, ty: float, note: str = ""):
        return ax.annotate(f"{rank[i]}°  " + short(docs[ids[i]]["title"]) + note, xy[i], xytext=(tx, ty),
                           fontsize=9.5, color=color, ha="left", va="center",
                           arrowprops={"arrowstyle": "-", "color": color, "lw": 0.6, "shrinkB": 3},
                           bbox={"boxstyle": "square,pad=0.15", "fc": BG, "ec": "none", "alpha": 0.9}, zorder=6)

    # first result and the first title with the word: the two points the slide talks about
    A["l_near"] = label(L["near"][0], TEAL, 0.205, 0.195)
    A["l_word"] = label(L["word"][0], DK, 0.205, 0.02, "\n(contiene «disastro»)")
    ax.set_xlim(-0.235, 0.465)
    ax.set_ylim(-0.245, 0.245)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    return fig, ax, A


def show(artist, alpha: float) -> None:
    artist.set_alpha(alpha)
    if hasattr(artist, "arrow_patch"):  # a label: its leader line and its box too
        artist.arrow_patch.set_alpha(alpha)
        artist.get_bbox_patch().set_alpha(0.9 * alpha)


def animate(L: dict, out) -> None:
    fig, ax, A = draw(L, dpi=160)
    qtext = ax.text(-0.225, 0.232, f"«{QUERY}»", ha="left", va="top", fontsize=9.5, color=OR)
    cap = ax.text(0.205, -0.17, "", fontsize=9, color=MUT, va="center", ha="left")
    # The first frame is the complete figure (what PowerPoint shows outside the slide show, and the
    # thumbnails): it holds, the search fades out, then it is redrawn; the last frame is complete
    # again, so the loop has no jump. Background and query stay on the whole time.
    t_hold, t_grow0, t_grow1, t_top, t_word, t_end = 2.5, 3.5, 7.0, 7.5, 9.5, 14.0

    def ramp(t: float, start: float, length: float = 0.5) -> float:
        return min(1.0, max(0.0, (t - start) / length))

    def frame(n: int) -> list:
        t = n / FPS
        if t < t_hold + 0.5:  # complete figure, then fading out
            fade = 1.0 - ramp(t, t_hold)
            A["circle"].set_visible(True)
            A["circle"].set_radius(L["r5"])
            A["circle"].set_linestyle((0, (3, 2)))
            # set_alpha would overwrite the transparency of the fill: fade fill and edge separately
            A["circle"].set_facecolor(TEAL_FILL[:3] + (TEAL_FILL[3] * fade,))
            A["circle"].set_edgecolor(TEAL_RGB + (fade,))
            for s in list(A["near"].values()) + list(A["word"].values()):
                s.set_alpha(fade)
            show(A["l_near"], fade)
            show(A["l_word"], fade)
            cap.set_text("il vettore guarda il significato,\nnon le parole")
            cap.set_alpha(fade)
            return []
        A["circle"].set_facecolor(TEAL_FILL)
        A["circle"].set_edgecolor(TEAL_RGB + (1.0,))
        cap.set_alpha(1.0)
        g = min(1.0, max(0.0, (t - t_grow0) / (t_grow1 - t_grow0)))
        r = max(0.0001, g * g * (3 - 2 * g) * L["r5"])  # smoothstep
        A["circle"].set_visible(t >= t_grow0)
        A["circle"].set_radius(r)
        A["circle"].set_linestyle((0, (3, 2)) if t >= t_grow1 else "-")
        for i, s in A["near"].items():
            s.set_alpha(1.0 if t >= t_grow0 and L["radius"][i] <= r + 1e-9 else 0.0)
        show(A["l_near"], ramp(t, t_top))
        w = ramp(t, t_word)
        for s in A["word"].values():
            s.set_alpha(w)
        show(A["l_word"], w)
        if t < t_grow0:
            cap.set_text("")
        elif t < t_top:
            cap.set_text("kNN: si allarga il cerchio\nfinché contiene 5 notizie")
        elif t < t_word:
            cap.set_text("i 5 più vicini = i risultati,\nnessuno con «disastro» nel titolo")
        else:
            cap.set_text("il vettore guarda il significato,\nnon le parole")
        return []

    FuncAnimation(fig, frame, frames=int(t_end * FPS), blit=False).save(
        out, writer=PillowWriter(fps=FPS), savefig_kwargs={"facecolor": BG})
    plt.close(fig)


def main() -> None:
    L = layout()
    FIGURES.mkdir(parents=True, exist_ok=True)
    png, gif = FIGURES / "embedding_map.png", FIGURES / "embedding_map.gif"
    fig, _, _ = draw(L, dpi=300)
    fig.savefig(png, facecolor=BG)
    plt.close(fig)
    animate(L, gif)

    docs, ids, sim, order = L["docs"], L["ids"], L["sim"], L["order"]
    for name, group in (("nearest", [int(i) for i in order[:8]]), ("disastro in the title", L["word"])):
        print(name)
        for i in group:
            print(f"  {L['rank'][i]:>4}  {sim[i]:.3f}  {docs[ids[i]]['title']}")
    print(f"random documents: median similarity {np.median(sim[L['rand']]):.3f}; wrote {png} and {gif}")


if __name__ == "__main__":
    main()
