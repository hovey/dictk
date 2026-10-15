"""Q4 baseline: a square Q4 element's nodes, Gauss points, and the weight
of each node in du/dX at the Gauss points with eta = +1/sqrt(3), computed
with dictk.element.
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
NODES = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], dtype=float)

eta = 1 / np.sqrt(3)
derivatives = shape_function_derivatives(xi=-eta, eta=eta)
gradients = shape_function_gradients(
    derivatives=derivatives,
    jacobian=jacobian(derivatives=derivatives, coordinates=NODES * H / 2),
)
weights = gradients[0] * H

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, ax = plt.subplots(figsize=(5.2, 4.6), constrained_layout=True)
ax.plot(*np.vstack([NODES, NODES[:1]]).T, color="black", lw=1.2, zorder=1)
for xi, et in gauss_points():
    top = np.isclose(et, eta)
    ax.plot(
        xi,
        et,
        "x",
        color="royalblue" if top else "gray",
        ms=10 if top else 7,
        mew=2 if top else 1.2,
        zorder=2,
    )
for a, ((x, y), w) in enumerate(zip(NODES, weights, strict=True), start=1):
    color = "royalblue" if w > 0 else "firebrick"
    ax.plot(x, y, "o", color=color, ms=42, zorder=3)
    ax.text(
        x, y, f"{w:+.3f}", ha="center", va="center", color="white", fontsize=9, zorder=4
    )
    ax.text(
        x,
        y + (0.4 if y > 0 else -0.4),
        f"node {a}, $({x:+.0f}, {y:+.0f})$",
        ha="center",
        va="center",
        fontsize=11,
    )
ax.text(
    0,
    eta - 0.2,
    r"Gauss points at $\eta = +1/\sqrt{3}$",
    va="top",
    ha="center",
    fontsize=11,
    color="royalblue",
)
ax.set_xlim(-1.7, 1.7)
ax.set_ylim(-1.7, 1.7)
ax.set_aspect("equal")
ax.set_xticks([-1, 0, 1])
ax.set_yticks([-1, 0, 1])
ax.set_xlabel(r"$\xi$", fontsize=13)
ax.set_ylabel(r"$\eta$", fontsize=13)
ax.set_title(r"weights in $\partial u / \partial X$, units of $1/L$", fontsize=12)
fig.savefig("strain_window_q4_element.png", dpi=300)
