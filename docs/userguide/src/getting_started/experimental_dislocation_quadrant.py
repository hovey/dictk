"""Plot the correlation surface a window straddling a real experimental
crack produces, ZNCC and FFT side by side. The two source images are
real experimental micrographs, copied in unmodified.
"""

from dictk.image import read, subimage, PixelCoordinate
from dictk.correlation import zncc
from dictk.plot import (
    spatial_correlation_quadrant_plot,
    phase_correlation_quadrant_plot,
)

KERNEL_MARGIN = 25
SEARCH_MARGIN = 65

reference_image = read(path="experimental_dislocation_reference.tiff")
current_image = read(path="experimental_dislocation_current.tiff")

p0 = PixelCoordinate(x=218, y=186)
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
    path="experimental_dislocation_zncc.png",
)
phase_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    title="Phase Correlation (FFT)",
    path="experimental_dislocation_phase.png",
)

print("Saved: experimental_dislocation_zncc.png, experimental_dislocation_phase.png")
