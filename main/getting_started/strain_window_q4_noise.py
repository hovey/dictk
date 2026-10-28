"""Q4 baseline: standard deviation of du/dX against window size n for the
window, an equal-spacing Q4 element, and an equal-footprint Q4 element.
The Q4 values come from dictk.element and are checked against 1.155 / L.
"""

import matplotlib.pyplot as plt
import numpy as np

from dictk.element import (
    gauss_points,
    jacobian,
    shape_function_derivatives,
    shape_function_gradients,
)

H = 1.0
M_VALUES = np.arange(1, 10)
N_VALUES = 2 * M_VALUES + 1


def q4_std(*, side):
    """Largest standard deviation of du/dX over the 4 Gauss points of a
    square Q4 element of the given side, in units of sigma."""
    nodes = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * side / 2
    stds = []
    for xi, eta in gauss_points():
        derivatives = shape_function_derivatives(xi=xi, eta=eta)
        gradients = shape_function_gradients(
            derivatives=derivatives,
            jacobian=jacobian(derivatives=derivatives, coordinates=nodes),
        )
        stds.append(np.sqrt((gradients[0] ** 2).sum()))
    return max(stds)


window = np.sqrt(3 / (M_VALUES * (M_VALUES + 1))) / N_VALUES
spacing = np.full(M_VALUES.size, q4_std(side=H))
footprint = np.array([q4_std(side=2 * m * H) for m in M_VALUES])
gap = max(
    abs(spacing[0] - np.sqrt(4 / 3)),
    np.abs(footprint - np.sqrt(4 / 3) / (2 * M_VALUES)).max(),
)

print(
    "| $n$ | window | Q4, equal spacing | Q4, equal footprint "
    "| equal-spacing ratio | equal-footprint ratio |"
)
print("|---|---|---|---|---|---|")
for n, w, s, f in zip(N_VALUES, window, spacing, footprint, strict=True):
    if n in (3, 7, 15, 19):
        print(f"| {n} | {w:.4f} | {s:.4f} | {f:.4f} | {s / w:.1f} | {f / w:.2f} |")
print()
print(
    f"All values are in units of $\\sigma / h$. The Q4 columns come from "
    f"`dictk.element` and match $1.155 / L$ within {gap:.0e}."
)

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.plot(N_VALUES, spacing, "--", color="firebrick", label="Q4, equal spacing, side $h$")
ax.plot(
    N_VALUES,
    footprint,
    "-",
    color="firebrick",
    marker="s",
    mfc="white",
    label="Q4, equal footprint, side $(n - 1)h$",
)
ax.plot(N_VALUES, window, "-", color="royalblue", marker="o", label="window")
for n, w, s, f in zip(N_VALUES, window, spacing, footprint, strict=True):
    if n == 15:
        for value in (s, f, w):
            ax.text(
                n - 0.2,
                value / 1.12,
                f"{value:.4f}",
                ha="right",
                va="top",
                fontsize=10,
                color="black",
            )
        for y_top, y_bottom, text, dx in [
            (s, f, f"${s / f:.0f}\\times$\nfootprint", 0.35),
            (f, w, f"${f / w:.2f}\\times$\nleast-squares fit", 0.35),
        ]:
            ax.annotate(
                "",
                xy=(n, y_bottom),
                xytext=(n, y_top),
                arrowprops={"arrowstyle": "<->", "color": "gray", "lw": 1},
            )
            ax.text(
                n + dx,
                np.sqrt(y_top * y_bottom),
                text,
                va="center",
                fontsize=10,
                color="dimgray",
            )
ax.set_yscale("log")
ax.set_xticks(N_VALUES)
ax.set_xlabel("window points per side, $n = 2m + 1$")
ax.set_ylabel(r"std of $\partial u / \partial X$ ($\sigma / h$)")
ax.legend(loc="lower left")
fig.savefig("strain_window_q4_noise.png", dpi=300)
