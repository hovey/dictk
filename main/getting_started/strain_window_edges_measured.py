"""Edge and corner degradation of a 15x15 strain window on Kernel Warping's
tracked positions: a table by distance to the grid boundary, a map of the
E11 error, and the column-mean error against a window fit of the
column-mean displacement error.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from dictk.grid import generate, locate_warp
from dictk.image import PixelCoordinate, read, stretch
from dictk.strain_window import log_strains, std_factors

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

FACTOR_X = 1.02
COUNT_X, COUNT_Y = 53, 54
SPACING = 5
MARGIN = 7
PERIOD = 51.0

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
error = (
    log_strains(
        reference_points=points,
        current_points=found,
        count_x=COUNT_X,
        count_y=COUNT_Y,
        margin=MARGIN,
    )[:, 0, 0]
    - np.log(FACTOR_X)
) * 1e6
factors = std_factors(count_x=COUNT_X, count_y=COUNT_Y, margin=MARGIN)[:, 0]

i, j = (a.ravel() for a in np.meshgrid(np.arange(COUNT_X), np.arange(COUNT_Y)))
d_x = np.minimum(np.minimum(i, COUNT_X - 1 - i), MARGIN)
d_y = np.minimum(np.minimum(j, COUNT_Y - 1 - j), MARGIN)


def rms(values):
    return np.sqrt(np.mean(values**2))


def wave_passed(*, kept_left):
    """Largest fitted slope of a 51 px sine wave over all phases, as a
    fraction of the wave's slope amplitude, for a window that keeps
    `kept_left` columns left of its center and all MARGIN to its right."""
    x = np.arange(-kept_left, MARGIN + 1) * SPACING
    k = 2 * np.pi / PERIOD
    phases = np.linspace(0, 2 * np.pi, 721)
    return max(abs(np.polyfit(x, np.sin(k * x + p), 1)[0]) / k for p in phases)


interior = (d_x == MARGIN) & (d_y == MARGIN)
interior_rms = rms(error[interior])
print(
    "| Window | $d_X$ | $d_Y$ | Points | RMS error (µε) | Measured / interior "
    "| Independent prediction | 51 px wave slope passed |"
)
print("|---|---:|---:|---:|---:|---:|---:|---:|")
rows = [("interior", MARGIN, MARGIN)]
rows += [("$X$ edge" if a == 0 else "near $X$ edge", a, MARGIN) for a in range(MARGIN)]
rows += [("$Y$ edge", MARGIN, 0), ("corner", 0, 0)]
for name, a, b in rows:
    group = (d_x == a) & (d_y == b)
    print(
        f"| {name} | {a} | {b} | {group.sum()} | {rms(error[group]):.0f} "
        f"| {rms(error[group]) / interior_rms:.2f} | {factors[group].mean():.2f} "
        f"| {wave_passed(kept_left=a) * 100:.1f}% |"
    )

reference = np.array([[p.x, p.y] for p in points], dtype=float)
current = np.array([[p.x, p.y] for p in found], dtype=float)
design = np.column_stack([reference[:, 0], np.ones(len(reference))])
residual = current[:, 0] - design @ np.linalg.lstsq(design, current[:, 0])[0]
full_rows = slice(MARGIN, COUNT_Y - MARGIN)
column_residual = residual.reshape(COUNT_Y, COUNT_X)[full_rows].mean(axis=0)
column_error = error.reshape(COUNT_Y, COUNT_X)[full_rows].mean(axis=0)
x_columns = reference[:COUNT_X, 0]
predicted = np.array(
    [
        np.polyfit(
            x_columns[max(c - MARGIN, 0) : c + MARGIN + 1] - x_columns[c],
            column_residual[max(c - MARGIN, 0) : c + MARGIN + 1],
            1,
        )[0]
        * 1e6
        for c in range(COUNT_X)
    ]
)
print()
print(
    f"The column-mean displacement error has an RMS of "
    f"{column_residual.std():.4f} px. A window fit of it predicts the "
    f"column-mean $E_{{11}}$ error with correlation "
    f"{np.corrcoef(column_error, predicted)[0, 1]:.4f}."
)

fig, (ax_map, ax_column) = plt.subplots(
    1, 2, figsize=(10, 4.2), constrained_layout=True, width_ratios=[1, 1.25]
)
limit = np.abs(error).max()
scatter = ax_map.scatter(
    reference[:, 0],
    reference[:, 1],
    c=error,
    cmap="RdBu_r",
    vmin=-limit,
    vmax=limit,
    s=9,
    marker="s",
)
low = reference[MARGIN * COUNT_X + MARGIN]
high = reference[(COUNT_Y - 1 - MARGIN) * COUNT_X + COUNT_X - 1 - MARGIN]
ax_map.add_patch(
    Rectangle(
        low - SPACING / 2,
        *(high - low + SPACING),
        fill=False,
        edgecolor="black",
        linestyle="--",
        linewidth=1.2,
    )
)
ax_map.set_aspect("equal")
ax_map.invert_yaxis()
ax_map.set_xlabel("$X$ (px)")
ax_map.set_ylabel("$Y$ (px)")
ax_map.set_title(r"(a) $E_{11} - \ln 1.02$")
fig.colorbar(scatter, ax=ax_map, label="microstrain", shrink=0.9)

columns = np.arange(COUNT_X)
for edge in (MARGIN - 0.5, COUNT_X - MARGIN - 0.5):
    ax_column.axvline(edge, color="gray", linestyle="--", linewidth=1)
ax_column.axhline(0, color="black", linewidth=0.6)
ax_column.plot(
    columns,
    predicted,
    "-",
    color="black",
    label="window fit of displacement error",
)
ax_column.plot(columns, column_error, "o", color="royalblue", ms=5, label="measured")
ax_column.set_xlabel("grid column")
ax_column.set_ylabel(r"mean $E_{11} - \ln 1.02$ (microstrain)")
ax_column.set_title("(b) column means over rows with a full $Y$ window")
ax_column.set_ylim(top=330)
ax_column.legend(loc="upper center", ncol=1, frameon=False)
fig.savefig("strain_window_edges_measured.png", dpi=300)
