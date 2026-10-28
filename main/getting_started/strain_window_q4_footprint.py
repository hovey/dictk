"""Q4 baseline: which tracked points a 15x15 window, an equal-spacing Q4
element, and an equal-footprint Q4 element use, on the same grid.
"""

import matplotlib.pyplot as plt
import numpy as np

M = 7
N = 2 * M + 1
Q4_STD = np.sqrt(4 / 3)
WINDOW_STD = np.sqrt(3 / (M * (M + 1))) / N

c, r = np.meshgrid(np.arange(-M, M + 1), np.arange(-M, M + 1))
c, r = c.ravel(), r.ravel()

panels = [
    (f"{N}x{N} window", np.ones(c.size, dtype=bool), None, WINDOW_STD),
    (
        "Q4, equal spacing",
        (np.isin(c, [0, 1])) & (np.isin(r, [0, 1])),
        (0, 1),
        Q4_STD,
    ),
    (
        "Q4, equal footprint",
        (np.abs(c) == M) & (np.abs(r) == M),
        (-M, M),
        Q4_STD / (2 * M),
    ),
]

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, axes = plt.subplots(1, 3, figsize=(10, 3.9), constrained_layout=True)
for ax, (title, used, corners, std) in zip(axes, panels, strict=True):
    ax.plot(c[~used], r[~used], "o", color="lightgray", ms=3)
    ax.plot(c[used], r[used], "o", color="darkorange", ms=5 if used.sum() > 4 else 8)
    if corners is None:
        lo, hi = -M, M
        ax.plot([lo, hi, hi, lo, lo], [lo, lo, hi, hi, lo], color="royalblue", lw=1.5)
    else:
        lo, hi = corners
        ax.plot([lo, hi, hi, lo, lo], [lo, lo, hi, hi, lo], color="firebrick", lw=1.5)
    ax.set_title(
        f"{title}\n{used.sum()} points, std {std:.4f} $\\sigma/h$", fontsize=11
    )
    ax.set_xlim(-M - 1, M + 1)
    ax.set_ylim(M + 1, -M - 1)
    ax.set_aspect("equal")
    ax.set_xticks([-M, 0, M])
    ax.set_yticks([-M, 0, M])
    ax.set_xlabel("column $c$")
axes[0].set_ylabel("row $r$")
fig.savefig("strain_window_q4_footprint.png", dpi=300)
