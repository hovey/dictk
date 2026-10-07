"""Worked 3x3 least-squares window: layout and weights, one noisy fit, and
a Monte Carlo of the fitted du/dX against a Q4 element.
"""

import matplotlib.pyplot as plt
import numpy as np

H = 5.0
SIGMA = 0.01
TRUE_UC, TRUE_DUDX, TRUE_DUDY = 0.3, 0.02, 0.01
TRIALS = 10000

q, p = np.meshgrid([-1, 0, 1], [-1, 0, 1])
q, p = q.ravel(), p.ravel()
s_x, s_y = H * q, H * p
design = np.column_stack([np.ones(9), s_x, s_y])
estimator = np.linalg.inv(design.T @ design) @ design.T
true_u = TRUE_UC + TRUE_DUDX * s_x + TRUE_DUDY * s_y

rng = np.random.default_rng(0)
errors = rng.normal(0.0, SIGMA, size=(TRIALS, 9))
fits = (true_u + errors) @ estimator.T
dudx = fits[:, 1]
std_window = dudx.std()
std_formula = SIGMA / (H * np.sqrt(6))
std_q4 = np.sqrt(4 / 3) * SIGMA / H

median_error = np.median(np.abs(dudx - TRUE_DUDX))
pick = int(np.argmin(np.abs(np.abs(dudx - TRUE_DUDX) - median_error)))
noisy_u = true_u + errors[pick]
uc_fit, dudx_fit, dudy_fit = fits[pick]

print(
    "| $q$ | $p$ | $qh$ (px) | $ph$ (px) | true $u$ (px) "
    "| error (px) | tracked $u$ (px) |"
)
print("|---|---|---|---|---|---|---|")
for k in range(9):
    print(
        f"| {q[k]} | {p[k]} | {s_x[k]:.0f} | {s_y[k]:.0f} | {true_u[k]:.4f} "
        f"| {errors[pick, k]:+.4f} | {noisy_u[k]:.4f} |"
    )
row_differences = [(noisy_u[3 * i + 2] - noisy_u[3 * i]) / (2 * H) for i in range(3)]
print()
print(
    f"The fit returns $u_c$ = {uc_fit:.4f} px, "
    f"$\\partial u / \\partial X$ = {dudx_fit:.5f}, and "
    f"$\\partial u / \\partial Y$ = {dudy_fit:.5f}. "
    f"The true values are {TRUE_UC} px, {TRUE_DUDX}, and {TRUE_DUDY}. "
    f"The $\\partial u / \\partial X$ error is "
    f"{(dudx_fit - TRUE_DUDX) * 1e6:+.0f} microstrain. "
    f"The three row differences $(u_{{1,p}} - u_{{-1,p}}) / 2h$ are "
    f"{', '.join(f'{d:.5f}' for d in row_differences)}. "
    f"Their mean is {np.mean(row_differences):.5f}, the fitted "
    f"$\\partial u / \\partial X$."
)
print()
print(
    f"Over {TRIALS} draws, $\\partial u / \\partial X$ has a standard "
    f"deviation of {std_window * 1e6:.0f} microstrain. "
    f"The formula $\\sigma / (h\\sqrt{{6}})$ gives {std_formula * 1e6:.0f}. "
    f"A Q4 element gives {std_q4 * 1e6:.0f}."
)

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, axes = plt.subplots(1, 3, figsize=(10, 3.6), constrained_layout=True)
titles = [
    "the 9 points",
    r"weights for $\partial u / \partial X$, units of $1/(6h)$",
    r"weights for $\partial u / \partial Y$, units of $1/(6h)$",
]
for ax, title, weights in zip(
    axes, titles, [None, q.reshape(3, 3), p.reshape(3, 3)], strict=True
):
    for k in range(9):
        if weights is None:
            ax.plot(q[k], p[k], "o", color="darkorange", ms=14)
            ax.annotate(
                f"({q[k]},{p[k]})",
                (q[k], p[k]),
                textcoords="offset points",
                xytext=(0, -22),
                ha="center",
                fontsize=9,
            )
        else:
            w = weights[p[k] + 1, q[k] + 1]
            color = "royalblue" if w > 0 else "firebrick" if w < 0 else "lightgray"
            ax.plot(q[k], p[k], "o", color=color, ms=26)
            ax.text(
                q[k],
                p[k],
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
    ax.set_xlabel(r"column $q$")
    ax.set_ylabel(r"row $p$")
    ax.set_title(title, fontsize=11)
axes[0].plot(0, 0, "o", mfc="none", mec="black", ms=22, mew=1.5)
fig.savefig("strain_window_3x3_layout.png", dpi=300)

fig, (ax_fit, ax_hist) = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
line = np.array([-H, H])
ax_fit.plot(
    line,
    uc_fit + dudx_fit * line,
    "-",
    color="black",
    label=rf"fit, $\partial u / \partial X$ = {dudx_fit:.5f}",
)
ax_fit.plot(
    line,
    TRUE_UC + TRUE_DUDX * line,
    "--",
    color="red",
    label=rf"true, $\partial u / \partial X$ = {TRUE_DUDX}",
)
colors = {-1: "royalblue", 0: "darkorange", 1: "seagreen"}
for row in [-1, 0, 1]:
    mask = p == row
    ax_fit.plot(
        s_x[mask],
        noisy_u[mask] - dudy_fit * s_y[mask],
        "o",
        color=colors[row],
        label=f"row $p$ = {row}",
    )
ax_fit.set_xlabel(r"$x = qh$ (px)")
ax_fit.set_ylabel(r"$u$ minus fitted $(\partial u / \partial Y)\, ph$ (px)")
ax_fit.set_title("one draw: nine tracked $u$, row offset removed", fontsize=11)
ax_fit.legend(loc="upper left", fontsize=8)

ax_hist.hist(dudx * 1e6, bins=60, color="gray", alpha=0.8)
ax_hist.axvline(TRUE_DUDX * 1e6, color="red", linestyle="--", label="true")
ax_hist.axvspan(
    (TRUE_DUDX - std_window) * 1e6,
    (TRUE_DUDX + std_window) * 1e6,
    color="royalblue",
    alpha=0.15,
    label=f"3x3 window, $\\pm${std_window * 1e6:.0f} µε",
)
ax_hist.axvspan(
    (TRUE_DUDX - std_q4) * 1e6,
    (TRUE_DUDX + std_q4) * 1e6,
    color="firebrick",
    alpha=0.08,
    label=f"Q4 element, $\\pm${std_q4 * 1e6:.0f} µε",
)
ax_hist.set_xlabel(r"fitted $\partial u / \partial X$ (µε)")
ax_hist.set_ylabel("frequency")
ax_hist.set_title(f"{TRIALS} draws, $\\sigma$ = {SIGMA} px", fontsize=11)
ax_hist.legend(loc="upper right", fontsize=8)
fig.savefig("strain_window_3x3_fit.png", dpi=300)
