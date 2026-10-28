"""Every whole-pixel seed on Kernel Warping's 2862 points, under its 2%
stretch: how far each seed lands from the true position, and how far
`locate_warp` lands after IC-GN refines it.
"""

import numpy as np

from dictk import translation
from dictk.grid import generate, locate_warp
from dictk.image import PixelCoordinate, read, stretch

FACTOR_X = 1.02
SEED_LIMIT = 1.0

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
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
)
seeds = [
    translation.locate(reference_point=point, search_center=point, **kwargs)
    for point in points
]
found = locate_warp(reference_points=points, **kwargs)

# `image.stretch` pivots on the image origin, so each true x is the
# reference x times the stretch factor, and y is unchanged.
true_positions = np.array([[point.x * FACTOR_X, point.y] for point in points])
seed_errors = np.linalg.norm(
    np.array([[seed.x, seed.y] for seed in seeds]) - true_positions, axis=1
)
warp_errors = np.linalg.norm(
    np.array([[f.x, f.y] for f in found]) - true_positions, axis=1
)

print(
    f"| Points | Seeds more than {SEED_LIMIT:g} px off | Largest seed error (px) "
    "| Largest `locate_warp` error (px) |"
)
print("|---|---|---|---|")
print(
    f"| {len(points)} | {(seed_errors > SEED_LIMIT).sum()} "
    f"| {seed_errors.max():.2f} | {warp_errors.max():.3f} |"
)
