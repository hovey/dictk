"""What a seed is: `translation.locate`'s whole-pixel match, the rigid
starting warp IC-GN refines. Two of the sweep's 30 points under a 15%
stretch and a 0.15 shear, one with a correct seed (top row) and one
with a defeated seed (bottom row).

Each row picks the point whose seed error sits nearest the median seed
error of its group, so neither example is hand-picked.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from scipy.ndimage import affine_transform

from dictk import translation, warp
from dictk.image import PixelCoordinate, read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

MARGIN = 13
SEARCH_MARGIN = 25
EDGE = 40
SAMPLE_COUNT = 30
SEED_LIMIT = 1.0
F = np.array([[1.15, 0.15], [0.0, 1.0]])
ZOOM = 30

reference_image = read(path="astronaut0.png")
rng = np.random.default_rng(0)
pivots = rng.integers(EDGE, 261, size=(SAMPLE_COUNT, 2)).astype(np.float64)
shifts = np.round(rng.uniform([4, 2], [8, 6], size=(SAMPLE_COUNT, 2)), 2)
inverse = np.linalg.inv(F)[::-1, ::-1]


def deformed(pivot, shift):
    offset = pivot[::-1] - inverse @ (pivot[::-1] + shift[::-1])
    return affine_transform(
        reference_image.astype(np.float64), inverse, offset=offset, order=5
    )


def tracked(pivot, shift):
    point = PixelCoordinate(x=int(pivot[0]), y=int(pivot[1]))
    current_image = deformed(pivot, shift)
    kwargs = dict(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=point,
        search_center=point,
        kernel_margin_width=MARGIN,
        kernel_margin_height=MARGIN,
        search_margin_width=SEARCH_MARGIN,
        search_margin_height=SEARCH_MARGIN,
    )
    seed = translation.locate(**kwargs)
    return current_image, seed, warp.fit(**kwargs)


seed_errors = np.array(
    [
        np.hypot(seed.x - pivot[0] - shift[0], seed.y - pivot[1] - shift[1])
        for pivot, shift in zip(pivots, shifts)
        for _, seed, _ in [tracked(pivot, shift)]
    ]
)
rows = []
for failed in (False, True):
    group = np.flatnonzero((seed_errors > SEED_LIMIT) == failed)
    rows.append(
        group[np.argmin(np.abs(seed_errors[group] - np.median(seed_errors[group])))]
    )

square = np.array(
    [[-MARGIN, -MARGIN], [MARGIN, -MARGIN], [MARGIN, MARGIN], [-MARGIN, MARGIN]],
    dtype=np.float64,
)
fig, axes = plt.subplots(2, 3, figsize=(13, 8.6), constrained_layout=True)
for (kernel_ax, surface_ax, current_ax), index, label in zip(
    axes, rows, ["correct seed", "defeated seed"]
):
    pivot, shift = pivots[index], shifts[index]
    x, y = int(pivot[0]), int(pivot[1])
    current_image, seed, fitted = tracked(pivot, shift)
    true_position = pivot + shift
    seed_offset = np.array([seed.x, seed.y]) - pivot

    kernel_ax.imshow(reference_image, cmap="gray", vmin=0, vmax=255)
    kernel_ax.add_patch(
        Polygon(
            pivot + square,
            fill=False,
            edgecolor="white",
            linestyle="--",
            linewidth=1.5,
        )
    )
    kernel_ax.plot(x, y, marker="o", color="red", markersize=7, mec="black")
    kernel_ax.set_xlim(x - ZOOM, x + ZOOM)
    kernel_ax.set_ylim(y + ZOOM, y - ZOOM)
    kernel_ax.set_title(f"{label}: reference kernel at ({x}, {y})")

    # locate's own phase correlation, step for step as its
    # skimage.registration.phase_cross_correlation call computes it: the
    # kernel centered in a zero-padded copy the search area's size, the
    # cross-power spectrum normalized to unit magnitude, and the peak of
    # the inverse transform's magnitude. After fftshift, the surface's
    # index minus SEARCH_MARGIN is the displacement from the point.
    kernel = reference_image[y - MARGIN : y + MARGIN, x - MARGIN : x + MARGIN]
    search = current_image[
        y - SEARCH_MARGIN : y + SEARCH_MARGIN, x - SEARCH_MARGIN : x + SEARCH_MARGIN
    ]
    pad = SEARCH_MARGIN - MARGIN
    kernel_padded = np.pad(kernel.astype(np.float64), pad)
    product = np.fft.fft2(search) * np.fft.fft2(kernel_padded).conj()
    product /= np.maximum(np.abs(product), 100 * np.finfo(np.float64).eps)
    surface = np.fft.fftshift(np.abs(np.fft.ifft2(product)))
    peak_row, peak_column = np.unravel_index(np.argmax(surface), surface.shape)
    assert (peak_column - SEARCH_MARGIN, peak_row - SEARCH_MARGIN) == tuple(seed_offset)
    extent = [-SEARCH_MARGIN - 0.5, SEARCH_MARGIN - 0.5] * 2
    surface_ax.imshow(surface, cmap="viridis", extent=extent[:2] + extent[2:][::-1])
    surface_ax.plot(
        *seed_offset, marker="s", markersize=9, mfc="none", mec="orange", mew=2
    )
    surface_ax.plot(*shift, marker="+", color="red", markersize=14, mew=2)
    surface_ax.set_xlabel("$u$ (pixels)")
    surface_ax.set_ylabel("$v$ (pixels)")
    surface_ax.set_title(
        f"phase correlation: seed $(u_0, v_0) = ({seed_offset[0]:.0f}, "
        f"{seed_offset[1]:.0f})$"
    )

    current_ax.imshow(current_image, cmap="gray", vmin=0, vmax=255)
    current_ax.add_patch(
        Polygon(
            pivot + seed_offset + square,
            fill=False,
            edgecolor="orange",
            linestyle="--",
            linewidth=2,
            label="seed: rigid square",
        )
    )
    current_ax.add_patch(
        Polygon(
            pivot + fitted[:2, 2] + square @ fitted[:2, :2].T,
            fill=False,
            edgecolor="orange",
            linewidth=2,
            label="IC-GN's final warp",
        )
    )
    current_ax.plot(*true_position, marker="+", color="red", markersize=14, mew=2)
    error = np.hypot(*(fitted[:2, 2] - shift))
    current_ax.set_xlim(x - ZOOM, x + ZOOM)
    current_ax.set_ylim(y + ZOOM, y - ZOOM)
    current_ax.set_title(f"current image: IC-GN misses by {error:.3f} px")
    current_ax.legend(loc="lower left", fontsize=9, framealpha=0.85)

for ax in axes[:, [0, 2]].ravel():
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")

fig.savefig("seed_propagation_seed.png", dpi=300)
