"""Track a full grid across the synthetic crack with
`locate_warp_propagated`, and map each point's ZNSSD. Two cases: a 4 px
offset with a grid column on the crack, and a 4.3 px offset with the
grid shifted 2 px so no column lines up with it. Prints one table and
saves the off-grid case's ZNSSD and v maps.
"""

import matplotlib.pyplot as plt
import numpy as np

import dictk
from dictk.grid import generate, locate_warp, locate_warp_propagated
from dictk.image import PixelCoordinate, combine, crack_dislocation

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

WIDTH = HEIGHT = 300
KERNEL_MARGIN = 13
SEARCH_MARGIN = 25
GATE = 0.3
CRACK_X = 149.5
CASES = [("on-grid", 4.0, 45), ("off-grid", 4.3, 47)]

reference_image = combine(
    a=dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5),
    b=dictk.astronaut(width=WIDTH, height=HEIGHT),
)
margins = dict(
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)

rows = {}
for name, offset, origin_x in CASES:
    current_image = crack_dislocation(arr=reference_image, offset=offset)
    points = generate(
        origin=PixelCoordinate(x=origin_x, y=45),
        count_x=43,
        count_y=43,
        spacing_x=5,
        spacing_y=5,
    )
    x = np.array([p.x for p in points], dtype=np.float64)
    y = np.array([p.y for p in points], dtype=np.float64)
    true_y = y + np.where(x < CRACK_X, offset, -offset)
    found, znssds = locate_warp_propagated(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        **margins,
    )
    rigid_seeded = locate_warp(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        **margins,
    )
    errors = np.hypot([f.x for f in found] - x, [f.y for f in found] - true_y)
    rigid_errors = np.hypot(
        [f.x for f in rigid_seeded] - x, [f.y for f in rigid_seeded] - true_y
    )
    # A kernel spans x - 13 to x + 13, so it straddles the crack when it
    # holds pixels from both columns 149 and 150.
    straddling = np.abs(x - CRACK_X) < KERNEL_MARGIN + 1
    accepted = znssds <= GATE
    columns = np.unique(x)
    medians = [np.median(znssds[x == column]) for column in columns]
    peak_column = columns[np.argmax(medians)]
    rows[name] = [
        f"{offset} px",
        f"{(~straddling).sum()}",
        f"{znssds[~straddling].max():.3f}",
        f"{errors[~straddling].max():.3f} px",
        f"{straddling.sum()}",
        f"{(straddling & ~accepted).sum()}",
        f"{np.isinf(znssds).sum()}",
        f"{(straddling & accepted).sum()}",
        f"{errors[straddling & accepted].max():.3f} px",
        f"{(accepted & ~(errors <= 1.0)).sum()}",
        f"{(rigid_errors > 1.0).sum()}",
        f"{peak_column:.0f} ({abs(peak_column - CRACK_X):.1f} px)",
    ]
    if name == "off-grid":
        map_case = (x, y, znssds, np.array([f.y for f in found]) - y, offset)

labels = [
    "Crack offset",
    "Points away from the crack",
    "... largest ZNSSD",
    "... largest error",
    "Points straddling the crack",
    "... rejected by the gate",
    "... of those, never fitted",
    "... accepted",
    "... largest error when accepted",
    "Accepted points more than 1 px off",
    "`locate_warp` points more than 1 px off",
    "Column with the highest median ZNSSD",
]
print("| | " + " | ".join(name for name, _, _ in CASES) + " |")
print("|---|" + "---|" * len(CASES))
for i, label in enumerate(labels):
    print(f"| {label} | " + " | ".join(rows[name][i] for name, _, _ in CASES) + " |")

x, y, znssds, v, offset = map_case
accepted = znssds <= GATE
fitted = np.isfinite(znssds)
fig, (left, right) = plt.subplots(1, 2, figsize=(10.0, 4.4), constrained_layout=True)
for axis in (left, right):
    axis.imshow(reference_image, cmap="gray", vmin=0, vmax=255)
    axis.axvline(CRACK_X, color="white", linestyle="--", linewidth=0.8)
    axis.set_xlabel("x (pixels)")
    axis.set_ylabel("y (pixels)")
shown = left.scatter(
    x[fitted],
    y[fitted],
    c=np.minimum(znssds[fitted], 1.0),
    s=20,
    marker="s",
    linewidths=0,
    cmap="viridis",
    vmin=0.0,
    vmax=1.0,
)
left.scatter(x[~fitted], y[~fitted], s=20, marker="s", linewidths=0, color="tab:red")
fig.colorbar(shown, ax=left, label="ZNSSD (clipped at 1)")
left.set_title("ZNSSD (red: never fitted)")
shown = right.scatter(
    x[accepted],
    y[accepted],
    c=v[accepted],
    s=20,
    marker="s",
    linewidths=0,
    cmap="coolwarm",
    vmin=-offset,
    vmax=offset,
)
fig.colorbar(shown, ax=right, label="v (pixels)")
right.set_title(f"v, accepted points only (ZNSSD ≤ {GATE})")
fig.savefig("discontinuity_detection_synthetic.png", dpi=300)
