"""Monte Carlo check of the 3x3 least-squares window's du/dX noise against
the formula and a Q4 element.
"""

import matplotlib.pyplot as plt
import numpy as np

H = 5.0
SIGMA = 0.01
TRUE_U0, TRUE_DUDX, TRUE_DUDY = 0.3, 0.02, 0.01
TRIALS = 10000

c, r = np.meshgrid([-1, 0, 1], [-1, 0, 1])
x, y = H * c.ravel(), H * r.ravel()
design = np.column_stack([np.ones(9), x, y])
estimator = np.linalg.inv(design.T @ design) @ design.T
true_u = TRUE_U0 + TRUE_DUDX * x + TRUE_DUDY * y

rng = np.random.default_rng(0)
errors = rng.normal(0.0, SIGMA, size=(TRIALS, 9))
dudx = ((true_u + errors) @ estimator.T)[:, 1]
std_window = dudx.std()
std_formula = SIGMA / (H * np.sqrt(6))
std_q4 = np.sqrt(4 / 3) * SIGMA / H

print(
    f"The formula gives {std_formula * 1e6:.0f} microstrain. "
    f"The {TRIALS:,} Monte Carlo draws give {std_window * 1e6:.0f} microstrain. "
    f"A Q4 element gives {std_q4 * 1e6:.0f} microstrain, "
    f"{std_q4 / std_window:.1f} times more. "
    "[Q4 Noise](#q4-noise) derives that value."
)

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, ax = plt.subplots(figsize=(5.6, 3.8), constrained_layout=True)
ax.hist(dudx * 1e6, bins=60, color="gray", alpha=0.8)
ax.axvline(TRUE_DUDX * 1e6, color="red", linestyle="--", label="true")
ax.axvspan(
    (TRUE_DUDX - std_window) * 1e6,
    (TRUE_DUDX + std_window) * 1e6,
    color="royalblue",
    alpha=0.15,
    label=f"3x3 window, $\\pm${std_window * 1e6:.0f} µε",
)
ax.axvspan(
    (TRUE_DUDX - std_q4) * 1e6,
    (TRUE_DUDX + std_q4) * 1e6,
    color="firebrick",
    alpha=0.08,
    label=f"Q4 element, $\\pm${std_q4 * 1e6:.0f} µε",
)
ax.set_xlabel(r"fitted $\partial u / \partial X$ (µε)")
ax.set_ylabel("frequency")
ax.set_title(f"{TRIALS} Monte Carlo draws, $\\sigma$ = {SIGMA} px", fontsize=11)
ax.legend(loc="upper right", fontsize=8)
fig.savefig("strain_window_3x3_noise.png", dpi=300)
