"""1D example fit: the least-squares line through the three displacements
of strain_window_1d.py, with its intercept, slope, and residuals.
"""

import matplotlib.pyplot as plt
import numpy as np

DISPLACEMENTS = [0.30, 0.52, 0.58]

c = np.array([-1, 0, 1])
u = np.array(DISPLACEMENTS)
intercept = u.mean()
slope = (c * u).sum() / (c**2).sum()
fitted = intercept + slope * c

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, ax = plt.subplots(figsize=(6, 3.8), constrained_layout=True)
x_line = np.array([-1.35, 1.35])
ax.plot(x_line, intercept + slope * x_line, color="black", lw=1.5, zorder=1)
for ck, uk, fk in zip(c, u, fitted, strict=True):
    ax.plot([ck, ck], [uk, fk], color="firebrick", ls="--", lw=1.2, zorder=2)
ax.plot(c, u, "o", color="darkorange", ms=11, zorder=3)
for ck, uk, fk in zip(c, u, fitted, strict=True):
    above = uk > fk
    ax.annotate(
        f"$u_{{{ck}}}$",
        (ck, uk),
        textcoords="offset points",
        xytext=(18, 4 if above else -20),
        ha="center",
        fontsize=14,
        color="darkorange",
    )
ax.plot(0, intercept, "s", mfc="white", mec="royalblue", mew=1.5, ms=9, zorder=4)
ax.annotate(
    r"$\hat{u}_0$",
    (0, intercept),
    textcoords="offset points",
    xytext=(16, -16),
    fontsize=14,
    color="royalblue",
)

run_start, run_end = -0.8, -0.25
y_start = intercept + slope * run_start
y_end = intercept + slope * run_end
ax.plot([run_start, run_end], [y_start, y_start], color="royalblue", lw=1.2)
ax.plot([run_end, run_end], [y_start, y_end], color="royalblue", lw=1.2)
ax.text(
    (run_start + run_end) / 2,
    y_start - 0.012,
    r"$\Delta x$",
    ha="center",
    va="top",
    fontsize=12,
    color="royalblue",
)
ax.text(
    run_end + 0.05,
    (y_start + y_end) / 2,
    r"$\dfrac{\partial u}{\partial X}\, \Delta x$",
    va="center",
    fontsize=13,
    color="royalblue",
)

ax.set_xlim(-1.45, 1.6)
ax.set_ylim(0.22, 0.7)
ax.set_xticks([-1, 0, 1], ["$-h$", "$0$", "$h$"], fontsize=12)
ax.set_yticks([])
ax.set_xlabel("$x$", fontsize=13)
ax.set_ylabel("$u$", fontsize=13)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("strain_window_1d_fit.png", dpi=300)
