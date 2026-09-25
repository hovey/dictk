"""The same 2% stretch, generated two ways: `dictk.image.stretch`'s own
bilinear interpolation, and a quintic spline. Tracks both with
`grid.locate_subpixel` and `grid.locate_warp`, then reports each
combination's x error and E11 spread.
"""

import numpy as np
from scipy.ndimage import map_coordinates

from dictk.element import gauss_point_log_strains
from dictk.grid import elements, generate, locate_subpixel, locate_warp
from dictk.image import PixelCoordinate, read, stretch

FACTOR_X = 1.02

reference_image = read(path="astronaut0.png")
height, width = reference_image.shape
ys, xs = np.mgrid[0:height, 0:width].astype(np.float64)
generators = {
    "bilinear (`image.stretch`)": stretch(arr=reference_image, factor_x=FACTOR_X),
    "quintic spline": map_coordinates(
        reference_image.astype(np.float64), [ys, xs / FACTOR_X], order=5
    ),
}
points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)
element_indices = elements(count_x=53, count_y=54)
true_x = np.array([p.x * FACTOR_X for p in points])

print("| Current image | Tracker | Std $x$ error (px) | Std $E_{11}$ (µε) |")
print("|---|---|---|---|")
for generator, current_image in generators.items():
    for name, locate, extra in [
        ("`locate_subpixel`", locate_subpixel, dict(upsample_factor=100)),
        ("`locate_warp`", locate_warp, {}),
    ]:
        found = locate(
            reference_image=reference_image,
            current_image=current_image,
            reference_points=points,
            kernel_margin_width=13,
            kernel_margin_height=13,
            search_margin_width=25,
            search_margin_height=25,
            **extra,
        )
        error_x = np.array([f.x for f in found]) - true_x
        strains = np.array(
            [
                strain[0, 0]
                for element in element_indices
                for strain in gauss_point_log_strains(
                    reference_points=[points[i] for i in element],
                    current_points=[found[i] for i in element],
                )
            ]
        )
        print(
            f"| {generator} | {name} | {error_x.std():.4f} "
            f"| {strains.std() * 1e6:.0f} |"
        )
