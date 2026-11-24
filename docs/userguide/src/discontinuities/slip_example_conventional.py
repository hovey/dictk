"""Track a full grid from t0 to t1 with conventional DIC, `locate_warp`,
at three kernel sizes: 15, 31, and 45 px. Gates each fit by its ZNSSD
and checks the accepted points of the two smaller kernels against the
45 px kernel's accepted field. Prints the host that ran the tracking, a
table of fits per kernel, and the agreement check. Saves a map with one
row per kernel: ZNSSD, then u and v at accepted points only.
"""

import os
import platform
import subprocess
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

from dictk.grid import generate, locate_warp
from dictk.image import PixelCoordinate, read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

SPACING = 10
# slip_example_motion.py measures at most 8 px of motion from t0 to t1.
# A 40 px search margin covers it and exceeds the largest kernel
# margin, 22 px.
SEARCH_MARGIN = 40
KERNEL_MARGINS = [7, 15, 22]
# Seed Propagation's ZNSSD gate.
GATE = 0.3
# An accepted point disagrees with the 45 px field past this distance.
AGREEMENT = 1.0

reference_image = read(path="slip_example_t0.tiff")
current_image = read(path="slip_example_t1.tiff")
height, width = reference_image.shape

origin = SEARCH_MARGIN + SPACING
count_x = (width - 2 * origin) // SPACING + 1
count_y = (height - 2 * origin) // SPACING + 1
points = generate(
    origin=PixelCoordinate(x=origin, y=origin),
    count_x=count_x,
    count_y=count_y,
    spacing_x=SPACING,
    spacing_y=SPACING,
)
x = np.array([p.x for p in points], dtype=np.float64)
y = np.array([p.y for p in points], dtype=np.float64)


def cpu_model():
    """The CPU's marketing name, or its vendor if the OS reports no
    model name."""
    if sys.platform == "darwin":
        command = ["sysctl", "-n", "machdep.cpu.brand_string"]
        return subprocess.run(command, capture_output=True, text=True).stdout.strip()
    info = dict(
        line.split(":", 1)
        for line in subprocess.run(
            ["lscpu"], capture_output=True, text=True
        ).stdout.splitlines()
        if ":" in line
    )
    model = info.get("Model name", "").strip()
    if model and model != "-":
        return model
    return f"{info.get('Vendor ID', 'unknown').strip()}, model not reported"


memory = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
print("| Host | |")
print("|---|---|")
print(f"| Operating system | {platform.system()} {platform.release()} |")
print(f"| Architecture | {platform.machine()} |")
print(f"| CPU | {cpu_model()} |")
print(f"| Logical CPU cores | {os.cpu_count()} |")
print(f"| Memory | {memory:.1f} GiB |")
print(f"| Python | {platform.python_version()} |")
print(f"| NumPy | {np.__version__} |")
print(f"| Worker threads per kernel | {os.cpu_count()} |")
print()

results = {}
print(
    "| Kernel width | `kernel_margin_width` | Points tracked | Failed fits "
    "| ZNSSD above 0.3 | Accepted | Median ZNSSD | Wall time |"
)
print("|---|---|---|---|---|---|---|---|")
for kernel_margin in KERNEL_MARGINS:
    start = time.perf_counter()
    found, znssds = locate_warp(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=SEARCH_MARGIN,
        search_margin_height=SEARCH_MARGIN,
        max_workers=os.cpu_count(),
    )
    seconds = time.perf_counter() - start
    found = np.array([(f.x, f.y) for f in found])
    failed = np.isinf(znssds)
    accepted = znssds <= GATE
    results[kernel_margin] = (found, znssds, accepted)
    print(
        f"| {2 * kernel_margin + 1} px | {kernel_margin} | {len(points)} "
        f"| {failed.sum()} | {(~failed & ~accepted).sum()} | {accepted.sum()} "
        f"| {np.median(znssds[~failed]):.3f} | {seconds:.0f} s |"
    )

# The 45 px kernel's accepted field is the comparison, not ground truth.
reference_found, _, reference_accepted = results[KERNEL_MARGINS[-1]]
print()
print(
    "| Kernel width | Accepted, more than 1 px from the 45 px field "
    "| Rejected, within 1 px of the 45 px field | Median distance, accepted |"
)
print("|---|---|---|---|")
for kernel_margin in KERNEL_MARGINS[:-1]:
    found, znssds, accepted = results[kernel_margin]
    both = reference_accepted & np.isfinite(znssds)
    distance = np.hypot(*(found - reference_found).T)
    kept = both & accepted
    dropped = both & ~accepted
    print(
        f"| {2 * kernel_margin + 1} px | {(distance[kept] > AGREEMENT).sum()} "
        f"of {kept.sum()} | {(distance[dropped] <= AGREEMENT).sum()} of "
        f"{dropped.sum()} | {np.median(distance[kept]):.3f} px |"
    )


def grid(values):
    """`values`, one per point, as a `count_y` by `count_x` image."""
    return values.reshape(count_y, count_x)


# One color range per displacement column, shared by all three kernels,
# from the 45 px kernel's accepted field.
reference_displacements = [
    reference_found[reference_accepted, column] - xy[reference_accepted]
    for column, xy in ((0, x), (1, y))
]
limits = [(values.min(), values.max()) for values in reference_displacements]
extent = [
    origin - SPACING / 2,
    origin + (count_x - 0.5) * SPACING,
    origin + (count_y - 0.5) * SPACING,
    origin - SPACING / 2,
]
znssd_colormap = plt.get_cmap("viridis").copy()
znssd_colormap.set_bad("tab:red")
displacement_colormap = plt.get_cmap("coolwarm").copy()
displacement_colormap.set_bad("black")

fig, axes = plt.subplots(
    len(KERNEL_MARGINS), 3, figsize=(15.0, 13.0), constrained_layout=True
)
for row, kernel_margin in zip(axes, KERNEL_MARGINS):
    found, znssds, accepted = results[kernel_margin]
    kernel = f"{2 * kernel_margin + 1} px kernel"
    shown = row[0].imshow(
        grid(np.where(np.isinf(znssds), np.nan, np.minimum(znssds, 1.0))),
        extent=extent,
        cmap=znssd_colormap,
        vmin=0.0,
        vmax=1.0,
        interpolation="nearest",
    )
    fig.colorbar(shown, ax=row[0], label="ZNSSD (clipped at 1)")
    row[0].set_title(f"ZNSSD, {kernel} (red: failed)")
    for column, (axis, name, xy) in enumerate(zip(row[1:], ("u", "v"), (x, y))):
        values = np.where(accepted, found[:, column] - xy, np.nan)
        shown = axis.imshow(
            grid(values),
            extent=extent,
            cmap=displacement_colormap,
            vmin=limits[column][0],
            vmax=limits[column][1],
            interpolation="nearest",
        )
        fig.colorbar(shown, ax=axis, label=f"{name} (pixels)")
        axis.set_title(f"{name}, {kernel}, ZNSSD ≤ {GATE}")
    for axis in row:
        axis.set_xlabel("x (pixels)")
        axis.set_ylabel("y (pixels)")
        axis.set_xlim(0, width)
        axis.set_ylim(height, 0)
fig.savefig("slip_example_conventional.png", dpi=300)
