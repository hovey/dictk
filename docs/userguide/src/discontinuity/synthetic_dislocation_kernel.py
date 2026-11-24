"""Show the kernel window (green box) straddling the crack in
`reference_image`, centered on the crack's own x = 150.
"""

import dictk
from dictk.image import combine, PixelCoordinate
from dictk.plot import subimage_comparison_plot

WIDTH = HEIGHT = 300
KERNEL_MARGIN = 25

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)

p0 = PixelCoordinate(x=WIDTH // 2, y=HEIGHT // 2)
kernel_origin = PixelCoordinate(x=p0.x - KERNEL_MARGIN, y=p0.y - KERNEL_MARGIN)

subimage_comparison_plot(
    image=reference_image,
    origin=kernel_origin,
    width=2 * KERNEL_MARGIN,
    height=2 * KERNEL_MARGIN,
    point=p0,
    point_color="orange",
    point_label="$P$",
    subimage_label="kernel",
    color="green",
    origin_label="$K$",
    source_origin_label="$O$",
    figsize=(6.4, 4.8),
    path="synthetic_dislocation_kernel.png",
)

print("Saved: synthetic_dislocation_kernel.png")
