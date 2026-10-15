"""1D example layout: three points at x = [-h, 0, h], indexed c = [-1, 0, 1],
with tracked displacements [u_{-1}, u_0, u_1] drawn as arrows.
"""

import matplotlib.pyplot as plt

H = 1.0
DISPLACEMENTS = [0.30, 0.52, 0.58]
LABEL_BOX = {"facecolor": "white", "edgecolor": "none", "pad": 1.0}

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, ax = plt.subplots(figsize=(7, 2.6), constrained_layout=True)
ax.annotate(
    "",
    xy=(2.0, 0),
    xytext=(-1.45, 0),
    arrowprops={"arrowstyle": "->", "color": "black", "lw": 1.2},
)
ax.text(2.05, 0, "$X$", va="center", fontsize=14)

for c, u in zip([-1, 0, 1], DISPLACEMENTS, strict=True):
    x = c * H
    ax.plot([x, x], [0, -1.05], color="lightgray", lw=0.6, zorder=0)
    ax.plot(x, 0, "o", color="darkorange", ms=14, zorder=3)
    ax.plot(x + u, 0, "o", mfc="white", mec="darkorange", mew=1.5, ms=14, zorder=3)
    ax.annotate(
        "",
        xy=(x + u, 0.32),
        xytext=(x, 0.32),
        arrowprops={
            "arrowstyle": "-|>",
            "color": "darkorange",
            "lw": 1.5,
            "shrinkA": 0,
            "shrinkB": 0,
        },
    )
    ax.plot([x, x], [0.12, 0.38], color="darkorange", lw=0.8)
    ax.text(
        x + u / 2, 0.45, f"$u_{{{c}}}$", ha="center", fontsize=14, color="darkorange"
    )
    position = {-1: "$-h$", 0: "$0$", 1: "$h$"}[c]
    ax.text(
        x,
        -0.3,
        f"$X = ${position}",
        ha="center",
        va="top",
        fontsize=12,
        bbox=LABEL_BOX,
        zorder=2,
    )
    ax.text(
        x,
        -0.58,
        f"$c = {c}$",
        ha="center",
        va="top",
        fontsize=12,
        bbox=LABEL_BOX,
        zorder=2,
    )

for start in [-H, 0]:
    ax.annotate(
        "",
        xy=(start + H, -0.95),
        xytext=(start, -0.95),
        arrowprops={
            "arrowstyle": "<->",
            "color": "gray",
            "lw": 1.0,
            "shrinkA": 0,
            "shrinkB": 0,
        },
    )
    ax.text(
        start + H / 2, -1.02, "$h$", ha="center", va="top", fontsize=12, color="gray"
    )

ax.set_xlim(-1.5, 2.2)
ax.set_ylim(-1.3, 0.75)
ax.set_aspect("equal")
ax.axis("off")
fig.savefig("strain_window_1d.png", dpi=300)
