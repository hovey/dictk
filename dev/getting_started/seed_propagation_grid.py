"""`locate_warp` against `locate_warp_propagated` on a 17x17 grid at
5 px spacing, across the sweep's 49 stretch and shear combinations.

Each current image deforms about the image center, then shifts by
(2.3, 1.6) px. `locate_warp` gets each point's true position, rounded,
as its search center, so its search area always contains the true
position and only the rigid seed can fail it. `locate_warp_propagated`
gets no search centers.
"""

import numpy as np
from scipy.ndimage import affine_transform

from dictk.grid import generate, locate_warp, locate_warp_propagated
from dictk.image import PixelCoordinate, read

STRETCHES = np.round(np.arange(0.0, 0.31, 0.05), 2)
SHEARS = np.round(np.arange(0.0, 0.31, 0.05), 2)
MISS_LIMIT = 1.0
CENTER = np.array([149.5, 149.5])
SHIFT = np.array([2.3, 1.6])

reference_image = read(path="astronaut0.png").astype(np.float64)
points = generate(
    origin=PixelCoordinate(x=110, y=110),
    count_x=17,
    count_y=17,
    spacing_x=5,
    spacing_y=5,
)
reference = np.array([[p.x, p.y] for p in points], dtype=np.float64)
margins = dict(
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
)

names = ["`locate_warp`", "`locate_warp_propagated`"]
miss_counts = np.zeros((2, len(STRETCHES), len(SHEARS)), dtype=int)
largest = np.zeros(2)
for i, stretch in enumerate(STRETCHES):
    for j, shear in enumerate(SHEARS):
        F = np.array([[1.0 + stretch, shear], [0.0, 1.0]])
        # affine_transform maps each output (row, column) back to its
        # input position, so it takes the inverse deformation, in (y, x)
        # order.
        inverse = np.linalg.inv(F)[::-1, ::-1]
        offset = CENTER[::-1] - inverse @ (CENTER[::-1] + SHIFT[::-1])
        current_image = affine_transform(
            reference_image, inverse, offset=offset, order=5
        )
        true = CENTER + (reference - CENTER) @ F.T + SHIFT
        search_centers = [
            PixelCoordinate(x=int(x), y=int(y)) for x, y in np.round(true)
        ]
        for k, (locate, extra) in enumerate(
            [
                (locate_warp, dict(search_centers=search_centers)),
                (locate_warp_propagated, {}),
            ]
        ):
            found = locate(
                reference_image=reference_image,
                current_image=current_image,
                reference_points=points,
                **margins,
                **extra,
            )
            errors = np.linalg.norm(
                np.array([[f.x, f.y] for f in found]) - true, axis=1
            )
            miss_counts[k, i, j] = (errors > MISS_LIMIT).sum()
            largest[k] = max(largest[k], errors.max())

print(f"{names[0]} misses of more than {MISS_LIMIT:g} px, out of {len(points)} points:")
print()
print("| Stretch \\ Shear | " + " | ".join(f"{g:.2f}" for g in SHEARS) + " |")
print("|---|" + "---|" * len(SHEARS))
for stretch, row in zip(STRETCHES, miss_counts[0]):
    print(f"| {stretch:.0%} | " + " | ".join(str(c) for c in row) + " |")
print()

fits = len(points) * len(STRETCHES) * len(SHEARS)
print(f"| Tracker | Misses, of {fits} | Largest error (px) |")
print("|---|---|---|")
for name, counts, error in zip(names, miss_counts, largest):
    print(f"| {name} | {counts.sum()} | {error:.3f} |")
