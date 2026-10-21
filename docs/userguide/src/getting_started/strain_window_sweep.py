"""Window-size sweep on Kernel Warping's tracked positions: the E11
spread for n = 3 to 19 against an independent-error prediction and a
prediction from the measured displacement error.
"""

import matplotlib.pyplot as plt
import numpy as np

from dictk.grid import generate, locate_warp
from dictk.image import PixelCoordinate, read, stretch
from dictk.strain_window import log_strains

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

FACTOR_X = 1.02
COUNT_X, COUNT_Y = 53, 54
SPACING = 5
MARGINS = range(1, 10)
PERIOD = 51.0
Q4_STD = 1161.0

reference_image = read(path="astronaut0.png")
current_image = stretch(arr=reference_image, factor_x=FACTOR_X)
points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=COUNT_X,
    count_y=COUNT_Y,
    spacing_x=SPACING,
    spacing_y=SPACING,
)
found = locate_warp(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
)

reference = np.array([[p.x, p.y] for p in points], dtype=float)
current = np.array([[p.x, p.y] for p in found], dtype=float)
design = np.column_stack([reference[:, 0], np.ones(len(reference))])
residual = (current[:, 0] - design @ np.linalg.lstsq(design, current[:, 0])[0]).reshape(
    COUNT_Y, COUNT_X
)
column_residual = residual.mean(axis=0)
row_sigma = (residual - column_residual).std()
x_columns = reference[:COUNT_X, 0]


def slope(*, x, y):
    return np.polyfit(x, y, 1)[0]


rows = []
for m in MARGINS:
    n = 2 * m + 1
    error = (
        log_strains(
            reference_points=points,
            current_points=found,
            count_x=COUNT_X,
            count_y=COUNT_Y,
            margin=m,
        )[:, 0, 0]
        - np.log(FACTOR_X)
    ).reshape(COUNT_Y, COUNT_X) * 1e6
    interior = error[m : COUNT_Y - m, m : COUNT_X - m]
    shape = np.sqrt(3 / (m * (m + 1))) / n
    wave = np.array(
        [
            slope(
                x=x_columns[c - m : c + m + 1] - x_columns[c],
                y=column_residual[c - m : c + m + 1],
            )
            for c in range(m, COUNT_X - m)
        ]
    )
    offsets = np.arange(-m, m + 1) * SPACING
    k = 2 * np.pi / PERIOD
    rows.append(
        dict(
            n=n,
            m=m,
            points=interior.size,
            share=interior.size / error.size,
            interior=interior.std(),
            all=error.std(),
            independent=Q4_STD * shape / np.sqrt(4 / 3),
            measured_error=np.hypot(
                wave.std() * 1e6, row_sigma / SPACING * shape * 1e6
            ),
            response=slope(x=offsets, y=np.sin(k * offsets)) / k,
        )
    )

print(
    "| Window | Interior points | Interior std (µε) | All-points std (µε) "
    "| Independent prediction (µε) | Measured-error prediction (µε) "
    "| $T$ at 51 px |"
)
print("|---|---:|---:|---:|---:|---:|---:|")
for r in rows:
    window = f"{r['n']}x{r['n']}<br><span style='white-space: nowrap'>($m = {r['m']}$)</span>"
    if r["n"] == 15:
        window = (
            f"**{r['n']}x{r['n']}**<br>"
            f"**<span style='white-space: nowrap'>($m = {r['m']}$)</span>**"
        )
    print(
        f"| {window} | {r['points']} ({r['share'] * 100:.1f}%) | {r['interior']:.0f} "
        f"| {r['all']:.0f} | {r['independent']:.1f} | {r['measured_error']:.0f} "
        f"| {r['response']:+.3f} |"
    )
print()
print(
    f"The row-to-row displacement error has a standard deviation of {row_sigma:.4f} px."
)

n_values = [r["n"] for r in rows]
fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.plot(
    n_values,
    [r["independent"] for r in rows],
    "--",
    color="gray",
    label="independent-error prediction",
)
ax.plot(
    n_values,
    [r["measured_error"] for r in rows],
    "-",
    color="black",
    label="measured-error prediction",
)
ax.plot(
    n_values,
    [r["all"] for r in rows],
    "s",
    color="firebrick",
    mfc="white",
    label="measured, all points",
)
ax.plot(
    n_values,
    [r["interior"] for r in rows],
    "o",
    color="royalblue",
    label="measured, interior points",
)
best = next(r for r in rows if r["n"] == 15)
ax.annotate(
    f"{best['interior']:.0f}",
    xy=(15, best["interior"]),
    xytext=(15, best["interior"] / 2.2),
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "royalblue"},
    color="royalblue",
)
ax.set_yscale("log")
ax.set_xticks(n_values)
ax.set_xlabel("window points per side, $n = 2m + 1$")
ax.set_ylabel(r"std of $E_{11}$ (microstrain)")
ax.legend(loc="lower left")
fig.savefig("strain_window_sweep.png", dpi=300)
