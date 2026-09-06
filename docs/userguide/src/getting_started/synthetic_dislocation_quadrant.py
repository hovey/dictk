"""Build a synthetic crack-dislocation image pair and plot the correlation
surface a window straddling the crack produces, ZNCC and FFT side by side.

Harvested from hdic's docs/userguide/src/formulation/examples/08a (Ex. 8a:
Synthetic Dislocation), replacing cameraman with dictk's own astronaut.
"""

import dictk
from dictk.image import combine, crack_dislocation, subimage, write, PixelCoordinate
from dictk.correlation import zncc, phase_correlation
from dictk.plot import spatial_correlation_quadrant_plot, phase_correlation_quadrant_plot

WIDTH = HEIGHT = 300
OFFSET = 4.0
KERNEL_MARGIN = 25
SEARCH_MARGIN = 45

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)

write(arr=reference_image, path="synthetic_dislocation_reference.png")
write(arr=current_image, path="synthetic_dislocation_current.png")

p0 = PixelCoordinate(x=WIDTH // 2, y=HEIGHT // 2)
kernel = subimage(
    image=reference_image,
    origin=PixelCoordinate(x=p0.x - KERNEL_MARGIN, y=p0.y - KERNEL_MARGIN),
    width=2 * KERNEL_MARGIN,
    height=2 * KERNEL_MARGIN,
)
search = subimage(
    image=current_image,
    origin=PixelCoordinate(x=p0.x - SEARCH_MARGIN, y=p0.y - SEARCH_MARGIN),
    width=2 * SEARCH_MARGIN,
    height=2 * SEARCH_MARGIN,
)

spatial_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    correlation_surface=zncc(kernel=kernel, search=search),
    title="Zero-mean Normalized Cross-Correlation (ZNCC)",
    path="synthetic_dislocation_zncc.png",
)
phase_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    title="Phase Correlation (FFT)",
    path="synthetic_dislocation_phase.png",
)

print(
    "Saved: synthetic_dislocation_reference.png, "
    "synthetic_dislocation_current.png, "
    "synthetic_dislocation_zncc.png, "
    "synthetic_dislocation_phase.png"
)
