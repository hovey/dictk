"""Illustrates The First Sweep's cliff directly: a phase-correlation
quadrant figure for dx=30 (succeeds) and dx=31 (fails), the same
scenario as recoverable_displacement_range_first_sweep.py.

The correlation surface itself is always correct -- dictk.correlation.
phase_correlation() never wraps, confirmed separately. The bug lives in
locate_uncentered's downstream, skimage-based signed-shift conversion,
not in the surface. So each figure marks two positions on the Fixed
Image panel: the surface's own true peak (yellow dashed, unchanged from
phase_correlation_quadrant_plot's normal behavior), and where
locate_uncentered actually reports the point (magenta,
reported_position) -- for dx=30 the two coincide; for dx=31 the magenta
box lands entirely outside the visible search frame, off by exactly the
padded array's own width, matching Root Cause's description.

Runs live on every book build, not from a committed snapshot.
"""

from dictk.image import PixelCoordinate, read, subimage, translate
from dictk.plot import phase_correlation_quadrant_plot
from recoverable_displacement_range_uncentered_demo import locate_uncentered

if __name__ == "__main__":
    reference_image = read(path="astronaut0.png")
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin = 30
    search_margin = 150  # exactly half of astronaut0's 300px canvas --
    # search reads the whole image, no extraction-margin black of its
    # own, so the only black left is dx's own left-side gap

    kernel_origin = PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin)
    kernel = subimage(
        image=reference_image,
        origin=kernel_origin,
        width=2 * kernel_margin,
        height=2 * kernel_margin,
    )
    search_origin = PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin)

    for dx, label in [(30, "succeeds"), (31, "fails")]:
        current_image = translate(arr=reference_image, dx=dx, dy=0)
        search = subimage(
            image=current_image,
            origin=search_origin,
            width=2 * search_margin,
            height=2 * search_margin,
        )
        found = locate_uncentered(
            reference_image, current_image, p0, p0, kernel_margin, search_margin
        )
        # found is point-center convention (kernel_margin already added
        # back in); convert to the surface's own top-left-corner-of-
        # kernel-box, search-local convention to compare directly against
        # the surface's own peak.
        reported_local = PixelCoordinate(
            x=(found.x - kernel_margin) - search_origin.x,
            y=(found.y - kernel_margin) - search_origin.y,
        )
        path = f"recoverable_displacement_range_first_sweep_quadrant_dx{dx}.png"
        phase_correlation_quadrant_plot(
            kernel=kernel,
            search=search,
            title=f"Phase Correlation, Pre-Fix locate (dx={dx}, {label})",
            path=path,
            reported_position=reported_local,
            reported_position_label="locate_uncentered",
        )
        print(f"Saved: {path}\n")
