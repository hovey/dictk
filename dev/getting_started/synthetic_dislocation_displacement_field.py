"""Track a full grid of points across the crack. dx stays trivially
near zero everywhere (checked, not assumed), and dy splits cleanly into
a +4 group and a -4 group -- each examined on its own.
"""

import matplotlib.pyplot as plt
import numpy as np

import dictk
from dictk.grid import generate, locate_subpixel
from dictk.image import PixelCoordinate, combine, crack_dislocation
from dictk.plot import point_displacement_plot


def mean_std_histogram(*, values, bins, color, xlabel, path):
    """Save a histogram with its own mean/std drawn behind the bars: a
    semi-transparent band, colored to match the bars, spanning mean +/-
    one std, with a black dashed line at the mean -- black rather than
    matching the bars so it stays visible regardless of bar color (a
    same-color line on tab:gray bars all but disappears).
    """
    mean, std = values.mean(), values.std()
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.axvspan(mean - std, mean + std, color=color, alpha=0.15, zorder=0)
    ax.hist(values, bins=bins, color=color, zorder=1)
    ax.axvline(mean, color="black", linestyle="--", linewidth=1.5, zorder=2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


WIDTH = HEIGHT = 300
OFFSET = 4.0
KERNEL_MARGIN = 25
SEARCH_MARGIN = 45

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)

points = generate(
    origin=PixelCoordinate(x=SEARCH_MARGIN, y=SEARCH_MARGIN),
    count_x=43,
    count_y=43,
    spacing_x=5,
    spacing_y=5,
)
found = locate_subpixel(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
    upsample_factor=100,
)

dx = np.array([f.x - p.x for f, p in zip(found, points)])
dy = np.array([f.y - p.y for f, p in zip(found, points)])

DX_TOLERANCE = 0.1  # px
assert np.abs(dx).max() < DX_TOLERANCE, (
    f"dx should be trivially ~0 (crack_dislocation only shifts pixels "
    f"vertically), got max |dx| = {np.abs(dx).max():.4f} px"
)

point_displacement_plot(
    points=found,
    values=list(dy),
    label=r"Displacement, $\delta y$ (pixels)",
    image=current_image,
    dot_size=6,
    marker="s",
    cmap="coolwarm",
    path="synthetic_dislocation_displacement_field.png",
)

# --- Focus 1: dx, across all 1849 points ---
print("| quantity | value |")
print("|---|---:|")
print(f"| points in group | {len(dx)} |")
print(f"| mean dx (px) | {dx.mean():.4f} |")
print(f"| max abs dx (px) | {np.abs(dx).max():.4f} |")
print()

mean_std_histogram(
    values=dx,
    bins=40,
    color="tab:gray",
    xlabel=r"Displacement, $\delta x$ (pixels)",
    path="synthetic_dislocation_displacement_field_dx_histogram.png",
)

# --- Focus 2 & 3: dy, split into its own +4 and -4 groups ---
dy_positive = dy[dy > 0]
dy_negative = dy[dy < 0]

print("| quantity | value |")
print("|---|---:|")
print(f"| points in group | {len(dy_positive)} |")
print(f"| mean dy (px) | {dy_positive.mean():.4f} |")
print(f"| std dy (px) | {dy_positive.std():.4f} |")
print(f"| min dy (px) | {dy_positive.min():.4f} |")
print(f"| max dy (px) | {dy_positive.max():.4f} |")
print()

mean_std_histogram(
    values=dy_positive,
    bins=40,
    color="tab:red",
    xlabel=r"Displacement, $\delta y$ (pixels)",
    path="synthetic_dislocation_displacement_field_dy_positive_histogram.png",
)

print("| quantity | value |")
print("|---|---:|")
print(f"| points in group | {len(dy_negative)} |")
print(f"| mean dy (px) | {dy_negative.mean():.4f} |")
print(f"| std dy (px) | {dy_negative.std():.4f} |")
print(f"| min dy (px) | {dy_negative.min():.4f} |")
print(f"| max dy (px) | {dy_negative.max():.4f} |")
print()

mean_std_histogram(
    values=dy_negative,
    bins=40,
    color="tab:blue",
    xlabel=r"Displacement, $\delta y$ (pixels)",
    path="synthetic_dislocation_displacement_field_dy_negative_histogram.png",
)

print(
    "Saved: synthetic_dislocation_displacement_field.png, "
    "synthetic_dislocation_displacement_field_dx_histogram.png, "
    "synthetic_dislocation_displacement_field_dy_positive_histogram.png, "
    "synthetic_dislocation_displacement_field_dy_negative_histogram.png"
)
