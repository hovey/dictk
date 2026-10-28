"""Where `locate_warp`'s rigid whole-pixel seed breaks: a sweep of
stretch and shear, each cell tracked at the same 30 random points, each
under its own random fractional shift.

Random points, not one, because a single point's image content can make
some deformations look easier than smaller ones. Each deformation
pivots on its tracked point, so that point's own displacement is just
the shift. The shift never exceeds 10 px, inside
the 12 px a 25 px search margin leaves around a 13 px kernel margin.
The search area therefore always contains the true position, and any
failure comes from the rigid kernel's mismatch alone.
"""

import numpy as np
from scipy.ndimage import affine_transform

from dictk import translation, warp
from dictk.image import PixelCoordinate, read

MARGIN = 13
SEARCH_MARGIN = 25
SAMPLE_COUNT = 30
STRETCHES = np.round(np.arange(0.0, 0.31, 0.05), 2)
SHEARS = np.round(np.arange(0.0, 0.31, 0.05), 2)
# A correct whole-pixel match lies within sqrt(0.5^2 + 0.5^2) = 0.71 px
# of the truth. More than 1 px means at least one whole pixel off.
SEED_LIMIT = 1.0
MISS_LIMIT = 1.0

reference_image = read(path="astronaut0.png")
rng = np.random.default_rng(0)
# Points at least 40 px from every edge of the 300x300 image, so the
# 25 px search area plus an 8 px shift stays inside it.
pivots = rng.integers(40, 261, size=(SAMPLE_COUNT, 2)).astype(np.float64)
# The same shift range as Kernel Warping, rounded to 0.01 px so each
# shift prints exactly as used.
shifts = np.round(rng.uniform([4, 2], [8, 6], size=(SAMPLE_COUNT, 2)), 2)


def deformed(F, pivot, shift):
    # affine_transform maps each output (row, column) back to its input
    # position, so it takes the inverse deformation, in (y, x) order.
    inverse = np.linalg.inv(F)[::-1, ::-1]
    offset = pivot[::-1] - inverse @ (pivot[::-1] + shift[::-1])
    return affine_transform(
        reference_image.astype(np.float64), inverse, offset=offset, order=5
    )


seed_errors = np.zeros((len(STRETCHES), len(SHEARS), SAMPLE_COUNT))
warp_errors = np.zeros_like(seed_errors)
for i, stretch in enumerate(STRETCHES):
    for j, shear in enumerate(SHEARS):
        F = np.array([[1.0 + stretch, shear], [0.0, 1.0]])
        for k, (pivot, shift) in enumerate(zip(pivots, shifts)):
            point = PixelCoordinate(x=int(pivot[0]), y=int(pivot[1]))
            current_image = deformed(F, pivot, shift)
            true_position = pivot + shift
            for errors, locate in [
                (seed_errors, translation.locate),
                (warp_errors, warp.locate),
            ]:
                found = locate(
                    reference_image=reference_image,
                    current_image=current_image,
                    reference_point=point,
                    search_center=point,
                    kernel_margin_width=MARGIN,
                    kernel_margin_height=MARGIN,
                    search_margin_width=SEARCH_MARGIN,
                    search_margin_height=SEARCH_MARGIN,
                )
                errors[i, j, k] = np.hypot(
                    found.x - true_position[0], found.y - true_position[1]
                )

seed_counts = (seed_errors > SEED_LIMIT).sum(axis=2)
miss_counts = (warp_errors > MISS_LIMIT).sum(axis=2)


def table(counts, title):
    print(f"{title}, out of {SAMPLE_COUNT} points:")
    print()
    print("| Stretch \\ Shear | " + " | ".join(f"{g:.2f}" for g in SHEARS) + " |")
    print("|---|" + "---|" * len(SHEARS))
    for stretch, row in zip(STRETCHES, counts):
        print(f"| {stretch:.0%} | " + " | ".join(str(c) for c in row) + " |")
    print()


table(seed_counts, f"Seeds more than {SEED_LIMIT:g} px off")
table(miss_counts, f"`locate_warp` misses of more than {MISS_LIMIT:g} px")
converged = warp_errors[warp_errors <= MISS_LIMIT]
missed = warp_errors[warp_errors > MISS_LIMIT]
print(
    f"Across all {warp_errors.size} fits, the largest error at or under "
    f"{MISS_LIMIT:g} px is {converged.max():.3f} px, and the smallest error "
    f"over it is {missed.min():.2f} px."
)
seed_failed = seed_errors > SEED_LIMIT
warp_missed = warp_errors > MISS_LIMIT
print()
print(
    f"Across the sweep, the seed fails {seed_failed.sum()} times and "
    f"`locate_warp` misses {warp_missed.sum()} times. IC-GN rescues "
    f"{(seed_failed & ~warp_missed).sum()} failed seeds. "
    f"{(warp_missed & ~seed_failed).sum()} misses start from a correct seed."
)
