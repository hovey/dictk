"""3x3 least-squares window: the 9 points and the weight of each point in
du/dX and du/dY.
"""

import matplotlib.pyplot as plt
import numpy as np

c, r = np.meshgrid([-1, 0, 1], [-1, 0, 1])
c, r = c.ravel(), r.ravel()

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, axes = plt.subplots(1, 3, figsize=(10, 3.6), constrained_layout=True)
titles = [
    "the 9 points",
    r"weights for $\partial u / \partial X$, units of $1/(6h)$",
    r"weights for $\partial u / \partial Y$, units of $1/(6h)$",
]
for ax, title, weights in zip(
    axes, titles, [None, c.reshape(3, 3), r.reshape(3, 3)], strict=True
):
    for k in range(9):
        if weights is None:
            ax.plot(c[k], r[k], "o", color="darkorange", ms=14)
            ax.annotate(
                f"({c[k]},{r[k]})",
                (c[k], r[k]),
                textcoords="offset points",
                xytext=(0, -22),
                ha="center",
                fontsize=9,
            )
        else:
            w = weights[r[k] + 1, c[k] + 1]
            color = "royalblue" if w > 0 else "firebrick" if w < 0 else "lightgray"
            ax.plot(c[k], r[k], "o", color=color, ms=26)
            ax.text(
                c[k],
                r[k],
                f"{w:+d}" if w else "0",
                ha="center",
                va="center",
                color="white" if w else "black",
                fontsize=11,
            )
    ax.set_xlim(-1.7, 1.7)
    ax.set_ylim(1.7, -1.7)
    ax.set_aspect("equal")
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([-1, 0, 1])
    ax.set_xlabel(r"column $c$")
    ax.set_ylabel(r"row $r$")
    ax.set_title(title, fontsize=11)
axes[0].plot(0, 0, "o", mfc="none", mec="black", ms=22, mew=1.5)
fig.savefig("strain_window_3x3_layout.png", dpi=300)
