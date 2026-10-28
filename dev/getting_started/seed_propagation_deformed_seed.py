"""How many misses remain when IC-GN starts from the right stretch and
shear? Reruns the sweep's 1470 fits, seeding each from the true
deformation with its translation rounded to whole pixels, as coarse as
the rigid seed's.
"""

import numpy as np
from scipy.ndimage import affine_transform

from dictk import warp
from dictk.image import PixelCoordinate, read

MARGIN = 13
SAMPLE_COUNT = 30
STRETCHES = np.round(np.arange(0.0, 0.31, 0.05), 2)
SHEARS = np.round(np.arange(0.0, 0.31, 0.05), 2)
MISS_LIMIT = 1.0

reference_image = read(path="astronaut0.png")
reference_gradients = warp._gradients(reference_image)
rng = np.random.default_rng(0)
pivots = rng.integers(40, 261, size=(SAMPLE_COUNT, 2)).astype(np.float64)
shifts = np.round(rng.uniform([4, 2], [8, 6], size=(SAMPLE_COUNT, 2)), 2)

errors = []
for stretch in STRETCHES:
    for shear in SHEARS:
        F = np.array([[1.0 + stretch, shear], [0.0, 1.0]])
        inverse = np.linalg.inv(F)[::-1, ::-1]
        for pivot, shift in zip(pivots, shifts):
            point = PixelCoordinate(x=int(pivot[0]), y=int(pivot[1]))
            offset = pivot[::-1] - inverse @ (pivot[::-1] + shift[::-1])
            current_image = affine_transform(
                reference_image.astype(np.float64), inverse, offset=offset, order=5
            )
            initial_warp = np.eye(3)
            initial_warp[:2, :2] = F
            initial_warp[:2, 2] = np.round(shift)
            fitted, _, _ = warp._refine(
                reference_image=reference_image,
                reference_gradients=reference_gradients,
                current_coefficients=warp._spline_coefficients(current_image),
                reference_point=point,
                initial_warp=initial_warp,
                kernel_margin_width=MARGIN,
                kernel_margin_height=MARGIN,
                max_iterations=50,
                tolerance=1e-6,
            )
            errors.append(np.hypot(*(fitted[:2, 2] - shift)))

errors = np.array(errors)
print(
    f"Across all {errors.size} fits, {(errors > MISS_LIMIT).sum()} land more than "
    f"{MISS_LIMIT:g} px from the true position. The largest error is "
    f"{errors.max():.3f} px."
)
