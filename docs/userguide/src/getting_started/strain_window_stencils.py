"""The du/dX weights of a full (2m + 1) x (2m + 1) window for m = 1, 2, 3,
from the closed form q / (h n S_m), checked against a direct least-squares
solve.
"""

import matplotlib.pyplot as plt
import numpy as np

H = 5.0
HALF_WIDTHS = [1, 2, 3]

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, axes = plt.subplots(1, 3, figsize=(11, 4.2), constrained_layout=True)
print(
    "| $m$ | $n$ | $S_m$ | $n S_m$ | weight of column $q$ | largest gap to direct solve |"
)
print("|---|---|---|---|---|---|")
for ax, m in zip(axes, HALF_WIDTHS, strict=True):
    n = 2 * m + 1
    s_m = m * (m + 1) * (2 * m + 1) // 3
    q, p = np.meshgrid(np.arange(-m, m + 1), np.arange(-m, m + 1))
    closed_form = q / (H * n * s_m)
    design = np.column_stack([np.ones(n * n), H * q.ravel(), H * p.ravel()])
    direct = (np.linalg.inv(design.T @ design) @ design.T)[1].reshape(n, n)
    gap = np.abs(closed_form - direct).max()
    print(f"| {m} | {n} | {s_m} | {n * s_m} | $q / ({n * s_m}h)$ | {gap:.1e} |")

    ax.imshow(
        q,
        cmap="RdBu",
        vmin=-m - 0.5,
        vmax=m + 0.5,
        extent=(-m - 0.5, m + 0.5, m + 0.5, -m - 0.5),
    )
    for qq, pp in zip(q.ravel(), p.ravel(), strict=True):
        ax.text(
            qq,
            pp,
            f"{qq:+d}" if qq else "0",
            ha="center",
            va="center",
            fontsize=11 if m < 3 else 9,
            color="white" if abs(qq) == m else "black",
        )
    ax.plot(0, 0, "s", mfc="none", mec="black", ms=26 if m < 3 else 18, mew=1.5)
    ax.set_xticks(range(-m, m + 1))
    ax.set_yticks(range(-m, m + 1))
    ax.set_xlabel("column $q$")
    ax.set_ylabel("row $p$")
    ax.set_title(rf"$m = {m}$, $n = {n}$: weight $= q\,/\,({n * s_m}h)$", fontsize=11)
fig.savefig("strain_window_stencils.png", dpi=300)
