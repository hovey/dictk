"""Standard deviation of a full window's du/dX for independent errors, in
units of sigma / h: the closed form, a Monte Carlo check, and a Q4
element's value.
"""

import matplotlib.pyplot as plt
import numpy as np

HALF_WIDTHS = list(range(1, 10))
TABLE_N = [3, 7, 11, 15, 19]
TRIALS = 4000
Q4 = np.sqrt(4 / 3)

rng = np.random.default_rng(0)
formula, simulated = [], []
for m in HALF_WIDTHS:
    n = 2 * m + 1
    formula.append(np.sqrt(3 / (n * n * m * (m + 1))))
    q = np.tile(np.arange(-m, m + 1), n)
    weights = q / (n * m * (m + 1) * (2 * m + 1) / 3)
    errors = rng.normal(0.0, 1.0, size=(TRIALS, n * n))
    simulated.append((errors @ weights).std())

print(
    "| Window | Formula, units of $\\sigma/h$ | "
    f"Monte Carlo, {TRIALS} draws, units of $\\sigma/h$ | Reduction vs Q4 |"
)
print("|---|---|---|---|")
for m, f, s in zip(HALF_WIDTHS, formula, simulated, strict=True):
    n = 2 * m + 1
    if n not in TABLE_N:
        continue
    half_width = f"($m = {m}$)"
    if n == 15:
        window = (
            f"**{n}x{n}**<br>**<span style='white-space: nowrap'>{half_width}</span>**"
        )
    else:
        window = f"{n}x{n}<br><span style='white-space: nowrap'>{half_width}</span>"
    print(f"| {window} | {f:.4f} | {s:.4f} | ${Q4 / f:.1f}\\times$ |")

n_values = [2 * m + 1 for m in HALF_WIDTHS]
plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.axhline(
    Q4, color="firebrick", linestyle="--", label=r"Q4 element, $1.155\,\sigma/h$"
)
ax.plot(
    n_values,
    formula,
    "-",
    color="black",
    label=r"formula $\frac{1}{n}\sqrt{3/(m(m+1))}$",
)
ax.plot(
    n_values,
    simulated,
    "o",
    color="royalblue",
    label=f"Monte Carlo, {TRIALS} draws per window",
)
ax.set_yscale("log")
ax.set_xticks(n_values)
ax.set_xlabel("window points per side, $n = 2m + 1$")
ax.set_ylabel(r"std of $\partial u / \partial X$ ($\sigma / h$)")
ax.legend(loc="center right")
fig.savefig("strain_window_noise.png", dpi=300)
