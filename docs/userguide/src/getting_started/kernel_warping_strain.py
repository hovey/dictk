"""High Point Density's own strain pipeline, rerun on `grid.locate_warp`
positions: a summary table against `grid.locate_subpixel` and VIC-2D,
the field on VIC-2D's own colorbar, and the distribution against
VIC-2D's own.
"""

import csv

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from dictk.element import gauss_point_coordinates, gauss_point_log_strains
from dictk.grid import elements, generate, locate_subpixel, locate_warp
from dictk.image import PixelCoordinate, read, stretch
from dictk.plot import element_strain_plot

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

FACTOR_X = 1.02
VMIN, VMAX = 17560, 22360

reference_image = read(path="astronaut0.png")
current_image = stretch(arr=reference_image, factor_x=FACTOR_X)
points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)
kwargs = dict(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
)
element_indices = elements(count_x=53, count_y=54)


def strains(found):
    values, coordinates = [], []
    for element in element_indices:
        current_corners = [found[i] for i in element]
        values.extend(
            strain[0, 0]
            for strain in gauss_point_log_strains(
                reference_points=[points[i] for i in element],
                current_points=current_corners,
            )
        )
        coordinates.extend(gauss_point_coordinates(points=current_corners))
    return np.array(values) * 1e6, coordinates


phase, _ = strains(locate_subpixel(**kwargs, upsample_factor=100))
found = locate_warp(**kwargs)
warp, coordinates = strains(found)

with open("../verification/simple_stretch_vic_out.csv") as f:
    rows = [{k.strip(' "'): v for k, v in row.items()} for row in csv.DictReader(f)]
vic = np.array([float(r["exx"]) * 1e6 for r in rows if float(r["sigma"]) != -1])
analytical = np.log(FACTOR_X) * 1e6

print(
    f"| Source | Mean (µε) | Std (µε) | Min (µε) | Max (µε) | Inside [{VMIN}, {VMAX}] |"
)
print("|---|---|---|---|---|---|")
for name, values in [
    ("`locate_subpixel` + Q4", phase),
    ("`locate_warp` + Q4", warp),
    ("VIC-2D", vic),
]:
    inside = np.mean((values >= VMIN) & (values <= VMAX)) * 100
    print(
        f"| {name} | {values.mean():.0f} | {values.std():.0f} | {values.min():.0f} "
        f"| {values.max():.0f} | {inside:.1f}% |"
    )
print(f"| Analytical, $\\ln(1.02)$ | {analytical:.0f} | 0 | | | |")

vic2d_cmap = ListedColormap(
    [
        (0.8314, 0.0000, 1.0000),
        (0.5176, 0.0000, 1.0000),
        (0.1843, 0.0000, 1.0000),
        (0.0000, 0.1333, 1.0000),
        (0.0000, 0.4510, 1.0000),
        (0.0000, 0.7843, 1.0000),
        (0.0000, 1.0000, 0.8980),
        (0.0000, 1.0000, 0.5843),
        (0.0000, 1.0000, 0.2510),
        (0.0667, 1.0000, 0.0000),
        (0.3843, 1.0000, 0.0000),
        (0.7176, 1.0000, 0.0000),
        (1.0000, 0.9686, 0.0000),
        (1.0000, 0.6510, 0.0000),
        (1.0000, 0.3176, 0.0000),
        (1.0000, 0.0000, 0.0000),
    ]
)
element_strain_plot(
    points=found,
    elements=element_indices,
    coordinates=coordinates,
    values=warp,
    label=r"Log Strain, $E_{11}$ (microstrain)",
    image=current_image,
    dot_size=6,
    marker="s",
    show_mesh_lines=False,
    cmap=vic2d_cmap,
    vmin=VMIN,
    vmax=VMAX,
    figsize=(6.9, 6.0),
    path="kernel_warping_strain_vic_colorbar.png",
)

fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
bins = np.linspace(min(warp.min(), vic.min()), max(warp.max(), vic.max()), 61)
ax.hist(
    warp,
    bins=bins,
    density=True,
    color="gray",
    alpha=0.8,
    label="dictk.grid.locate_warp",
)
ax.hist(vic, bins=bins, density=True, histtype="step", color="black", label="VIC-2D")
ax.axvline(analytical, color="red", linestyle="--", linewidth=1.5)
ax.set_xlabel(r"Log strain $E_{11}$ (microstrain)")
ax.set_ylabel("density")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
fig.savefig("kernel_warping_strain_histogram.png", dpi=300)
