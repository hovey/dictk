"""Can one bad region spread? Covers a 40x40 px patch of the current
image with unrelated speckle, under a 15% stretch with a 0.15 shear,
and tracks the 17x17 grid with `locate_warp_propagated` with its ZNSSD
gate off (`znssd_limit=4`, the largest ZNSSD) and on (the default 0.3).
"""

import numpy as np
from scipy.ndimage import affine_transform

from dictk.grid import generate, locate_warp_propagated
from dictk.image import PixelCoordinate, read
from dictk.rosta import rosta

CENTER = np.array([149.5, 149.5])
SHIFT = np.array([2.3, 1.6])
F = np.array([[1.15, 0.15], [0.0, 1.0]])
PATCH = 40
KERNEL_MARGIN = 13
GATE = 0.3

reference_image = read(path="astronaut0.png").astype(np.float64)
points = generate(
    origin=PixelCoordinate(x=110, y=110),
    count_x=17,
    count_y=17,
    spacing_x=5,
    spacing_y=5,
)
reference = np.array([[p.x, p.y] for p in points], dtype=np.float64)
inverse = np.linalg.inv(F)[::-1, ::-1]
offset = CENTER[::-1] - inverse @ (CENTER[::-1] + SHIFT[::-1])
deformed = affine_transform(reference_image, inverse, offset=offset, order=5)
true = CENTER + (reference - CENTER) @ F.T + SHIFT
speckle = rosta(width=PATCH, height=PATCH, density=0.5, random_seed=7)
speckle = speckle.astype(np.float64) * 255.0 / speckle.max()

print(
    "| Patch corner | Gate | Points outside | Bad outside | Bad inside "
    "| Never fitted | Bad but passing the gate | Right but failing the gate |"
)
print("|---|---|---|---|---|---|---|---|")
for corner in [(160, 160), (130, 130)]:
    x0, y0 = corner
    current_image = deformed.copy()
    current_image[y0 : y0 + PATCH, x0 : x0 + PATCH] = speckle
    # A point is inside when its current-image kernel overlaps the patch.
    reach = PATCH / 2 + KERNEL_MARGIN + 0.5
    middle = np.array([x0, y0]) + (PATCH - 1) / 2
    inside = np.all(np.abs(true - middle) < reach, axis=1)
    for gate, limit in [("off", 4.0), ("on", GATE)]:
        found, znssds = locate_warp_propagated(
            reference_image=reference_image,
            current_image=current_image,
            reference_points=points,
            kernel_margin_width=KERNEL_MARGIN,
            kernel_margin_height=KERNEL_MARGIN,
            search_margin_width=25,
            search_margin_height=25,
            znssd_limit=limit,
        )
        errors = np.linalg.norm(np.array([[f.x, f.y] for f in found]) - true, axis=1)
        # A never-fitted point has a nan position, so it counts as bad.
        bad = ~(errors <= 1.0)
        print(
            f"| ({x0}, {y0}) | {gate} | {(~inside).sum()} | {bad[~inside].sum()} "
            f"| {bad[inside].sum()} of {inside.sum()} | {np.isinf(znssds).sum()} "
            f"| {(bad & (znssds <= GATE)).sum()} "
            f"| {(~bad & (znssds > GATE)).sum()} |"
        )
