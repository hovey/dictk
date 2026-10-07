"""Interior, edge, and corner windows near a grid's top-left corner, with
each window's du/dX standard deviation relative to the interior window
and the centroid where the fit reports its gradient.
"""

import matplotlib.pyplot as plt
import numpy as np

M = 3
GRID = 12
CENTERS = {"interior": (6, 6), "edge": (0, 6), "corner": (0, 0)}


def window(*, center: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    cq, cp = center
    q, p = np.meshgrid(np.arange(cq - M, cq + M + 1), np.arange(cp - M, cp + M + 1))
    keep = (q >= 0) & (p >= 0) & (q < GRID) & (p < GRID)
    return q[keep], p[keep]


def std(*, q: np.ndarray, p: np.ndarray) -> float:
    design = np.column_stack([np.ones(q.size), q, p])
    return np.sqrt(np.linalg.inv(design.T @ design)[1, 1])


interior = std(
    q=window(center=CENTERS["interior"])[0], p=window(center=CENTERS["interior"])[1]
)
plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, axes = plt.subplots(1, 3, figsize=(11, 4), constrained_layout=True)
for ax, (name, center) in zip(axes, CENTERS.items(), strict=True):
    q, p = window(center=center)
    all_q, all_p = np.meshgrid(np.arange(GRID), np.arange(GRID))
    ax.plot(all_q, all_p, ".", color="lightgray", ms=5)
    cq, cp = center
    full_q, full_p = np.meshgrid(
        np.arange(cq - M, cq + M + 1), np.arange(cp - M, cp + M + 1)
    )
    lost = (full_q < 0) | (full_p < 0)
    ax.axvspan(-M - 1, -0.5, color="gainsboro", zorder=0)
    ax.axhspan(-M - 1, -0.5, color="gainsboro", zorder=0)
    ax.plot(
        full_q[lost],
        full_p[lost],
        "o",
        mfc="none",
        mec="darkorange",
        ms=6,
        label="lost: outside the grid",
    )
    ax.plot(q, p, "o", color="darkorange", ms=6, label="kept")
    ax.plot(
        *center, "s", mfc="none", mec="black", ms=12, mew=1.5, label="window center"
    )
    ax.plot(
        q.mean(), p.mean(), "x", color="red", ms=11, mew=2, label="centroid of points"
    )
    factor = std(q=q, p=p) / interior
    ax.set_title(f"{name}: {q.size} points, std x {factor:.2f}", fontsize=11)
    ax.set_xlim(-M - 1, GRID)
    ax.set_ylim(GRID, -M - 1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
axes[2].legend(loc="lower right", fontsize=8, framealpha=1.0)
fig.savefig("strain_window_edges.png", dpi=300)
