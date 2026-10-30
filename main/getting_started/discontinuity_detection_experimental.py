"""Track a full grid across the real crack image pair with
`locate_warp_propagated`, at two kernel sizes, and map each point's
ZNSSD. Fits a line to the band of rejected points, checks each accepted
point against its neighbors on the same side, and measures the
displacement across a fainter streak parallel to the crack. Prints two
tables and saves the 27 px kernel's maps.
"""

import matplotlib.pyplot as plt
import numpy as np

from dictk.grid import generate, locate_warp_propagated
from dictk.image import PixelCoordinate, read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

SPACING = 5
GATE = 0.3
NEIGHBOR_REACH = 10
# The largest rigid motion is 37 px. A 50 px search margin covers it
# with room to spare; 65 px matches Experimental Dislocation's.
MARGINS = [(13, 50), (25, 65)]
# A 100 px stretch along the crack, near the middle of the streak.
ALONG_RANGE = (250, 350)
STREAK_BANDS = [(-240, -200), (-200, -185), (-185, -155), (-155, -140), (-140, -100)]

reference_image = read(path="experimental_dislocation_reference.tiff")
current_image = read(path="experimental_dislocation_current.tiff")
size = reference_image.shape[0]

rows = {}
for kernel_margin, search_margin in MARGINS:
    origin = search_margin + SPACING
    count = (size - 2 * origin) // SPACING + 1
    points = generate(
        origin=PixelCoordinate(x=origin, y=origin),
        count_x=count,
        count_y=count,
        spacing_x=SPACING,
        spacing_y=SPACING,
    )
    found, znssds = locate_warp_propagated(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=search_margin,
        search_margin_height=search_margin,
    )
    x = np.array([p.x for p in points], dtype=np.float64)
    y = np.array([p.y for p in points], dtype=np.float64)
    u = np.array([f.x for f in found]) - x
    v = np.array([f.y for f in found]) - y
    accepted = znssds <= GATE
    fitted = np.isfinite(znssds)

    # Each row's band center is the mean x of its rejected points, after
    # dropping any more than 40 px from the row's median.
    centers, widths = [], []
    for row in np.unique(y):
        xs = x[(y == row) & ~accepted]
        if len(xs) >= 2:
            xs = xs[np.abs(xs - np.median(xs)) < 40]
            centers.append((row, xs.mean()))
            widths.append(xs.max() - xs.min() + SPACING)
    band_y, band_x = np.array(centers).T
    slope, intercept = np.polyfit(band_y, band_x, 1)
    scatter = np.std(band_x - (slope * band_y + intercept))
    cosine = np.cos(np.arctan(slope))
    across = (x - (slope * y + intercept)) * cosine
    along = (y + slope * (x - intercept)) * cosine
    near = np.abs(across) <= 2 * kernel_margin + 10

    side = np.sign(across)
    deviations = []
    for i in np.flatnonzero(accepted):
        neighbors = (
            accepted
            & (side == side[i])
            & (np.abs(x - x[i]) <= NEIGHBOR_REACH)
            & (np.abs(y - y[i]) <= NEIGHBOR_REACH)
        )
        neighbors[i] = False
        if neighbors.sum() >= 3:
            deviations.append(
                max(
                    abs(u[i] - np.median(u[neighbors])),
                    abs(v[i] - np.median(v[neighbors])),
                )
            )
    deviations = np.array(deviations)
    lower, upper = accepted & (side < 0), accepted & (side > 0)

    rows[kernel_margin] = [
        f"{2 * kernel_margin + 1} px",
        f"{search_margin} px",
        f"{len(points)}",
        f"{accepted.sum()} / {(fitted & ~accepted).sum()} / {(~fitted).sum()}",
        f"{np.median(znssds[fitted]):.3f}",
        f"{(~accepted & near).sum()} / {(~accepted & ~near).sum()}",
        f"x = {slope:.3f} y + {intercept:.1f}",
        f"{np.degrees(np.arctan(slope)):.1f}°",
        f"{scatter:.2f} px",
        f"{np.median(widths):.0f} px",
        f"{(deviations > 1.0).sum()} of {accepted.sum()} ({deviations.max():.2f} px)",
        f"{np.median(u[lower]):.2f} / {np.median(v[lower]):.2f} px",
        f"{np.median(u[upper]):.2f} / {np.median(v[upper]):.2f} px",
    ]
    if kernel_margin == 13:
        map_case = (x, y, znssds, u, v, slope, intercept)
        streak = []
        for low, high in STREAK_BANDS:
            band = (
                accepted
                & (across >= low)
                & (across < high)
                & (along > ALONG_RANGE[0])
                & (along < ALONG_RANGE[1])
            )
            streak.append(
                f"| {low} to {high} px | {band.sum()} | {np.median(znssds[band]):.3f} "
                f"| {np.median(u[band]):.2f} px | {np.median(v[band]):.2f} px |"
            )

labels = [
    "Kernel width",
    "Search margin",
    "Points tracked",
    "Accepted / rejected / never fitted",
    "Median ZNSSD of fitted points",
    "Rejected near the band / farther away",
    "Line fitted to the band",
    "Band angle from vertical",
    "RMS scatter of band centers about the line",
    "Median band width",
    "Accepted points more than 1 px from same-side neighbors (largest)",
    "Lower-left side, median u / v",
    "Upper-right side, median u / v",
]
print("| | " + " | ".join(f"`kernel_margin={k}`" for k, _ in MARGINS) + " |")
print("|---|" + "---|" * len(MARGINS))
for i, label in enumerate(labels):
    print(f"| {label} | " + " | ".join(rows[k][i] for k, _ in MARGINS) + " |")
print()
print("| Distance from the crack line | Points | Median ZNSSD | Median u | Median v |")
print("|---|---|---|---|---|")
print("\n".join(streak))

x, y, znssds, u, v, slope, intercept = map_case
accepted = znssds <= GATE
fitted = np.isfinite(znssds)
line_y = np.array([y.min(), y.max()])
fig, axes = plt.subplots(2, 2, figsize=(10.5, 9.0), constrained_layout=True)
(current_axis, znssd_axis), (u_axis, v_axis) = axes
current_axis.imshow(current_image, cmap="gray", vmin=0, vmax=255)
current_axis.set_title("Current image")
for axis in (znssd_axis, u_axis, v_axis):
    axis.imshow(reference_image, cmap="gray", vmin=0, vmax=255)
shown = znssd_axis.scatter(
    x[fitted],
    y[fitted],
    c=np.minimum(znssds[fitted], 1.0),
    s=8,
    marker="s",
    linewidths=0,
    cmap="viridis",
    vmin=0.0,
    vmax=1.0,
)
znssd_axis.scatter(
    x[~fitted], y[~fitted], s=8, marker="s", linewidths=0, color="tab:red"
)
znssd_axis.plot(
    slope * line_y + intercept, line_y, color="white", linestyle="--", linewidth=0.8
)
fig.colorbar(shown, ax=znssd_axis, label="ZNSSD (clipped at 1)")
znssd_axis.set_title("ZNSSD (red: never fitted)")
for axis, values, name in ((u_axis, u, "u"), (v_axis, v, "v")):
    shown = axis.scatter(
        x[accepted],
        y[accepted],
        c=values[accepted],
        s=8,
        marker="s",
        linewidths=0,
        cmap="coolwarm",
    )
    fig.colorbar(shown, ax=axis, label=f"{name} (pixels)")
    axis.set_title(f"{name}, accepted points only (ZNSSD ≤ {GATE})")
for axis in axes.flat:
    axis.set_xlabel("x (pixels)")
    axis.set_ylabel("y (pixels)")
    axis.set_xlim(0, size)
    axis.set_ylim(size, 0)
fig.savefig("discontinuity_detection_experimental.png", dpi=300)
