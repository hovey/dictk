"""Track a full grid from t0 to t1 with conventional DIC, `locate_warp`,
at three kernel sizes: 15, 31, and 45 px. Maps u and v for each kernel,
one row per kernel. A point whose fit fails comes back as `nan` and
shows black. Prints the host that ran the tracking, then how many
points each kernel tracked and lost and how long each kernel took, and
saves the map.
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

fields = {}
print(
    "| Kernel width | `kernel_margin_width` | Points tracked | Points lost "
    "| Wall time |"
)
print("|---|---|---|---|---|")
for kernel_margin in KERNEL_MARGINS:
    start = time.perf_counter()
    found, _znssds = locate_warp(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=SEARCH_MARGIN,
        search_margin_height=SEARCH_MARGIN,
        max_workers=os.cpu_count(),
    )
    found = np.array([(f.x, f.y) for f in found])
    seconds = time.perf_counter() - start
    u = (found[:, 0] - x).reshape(count_y, count_x)
    v = (found[:, 1] - y).reshape(count_y, count_x)
    fields[kernel_margin] = (u, v)
    lost = int(np.isnan(u).sum())
    print(
        f"| {2 * kernel_margin + 1} px | {kernel_margin} | {len(points)} | {lost} "
        f"| {seconds:.0f} s |"
    )


# One color range per column, shared by all three kernels. The 1st and
# 99th percentiles of the 45 px kernel's field keep a few wild fits
# from the smaller kernels from washing out the scale.
limits = [
    np.nanpercentile(fields[KERNEL_MARGINS[-1]][column], [1, 99]) for column in (0, 1)
]
extent = [
    origin - SPACING / 2,
    origin + (count_x - 0.5) * SPACING,
    origin + (count_y - 0.5) * SPACING,
    origin - SPACING / 2,
]
colormap = plt.get_cmap("coolwarm").copy()
colormap.set_bad("black")

fig, axes = plt.subplots(
    len(KERNEL_MARGINS), 2, figsize=(10.5, 13.0), constrained_layout=True
)
for row, kernel_margin in zip(axes, KERNEL_MARGINS):
    for column, (axis, name) in enumerate(zip(row, ("u", "v"))):
        shown = axis.imshow(
            fields[kernel_margin][column],
            extent=extent,
            cmap=colormap,
            vmin=limits[column][0],
            vmax=limits[column][1],
            interpolation="nearest",
        )
        fig.colorbar(shown, ax=axis, label=f"{name} (pixels)")
        axis.set_title(f"{name}, {2 * kernel_margin + 1} px kernel")
        axis.set_xlabel("x (pixels)")
        axis.set_ylabel("y (pixels)")
        axis.set_xlim(0, width)
        axis.set_ylim(height, 0)
fig.savefig("slip_example_conventional.png", dpi=300)
