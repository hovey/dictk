"""Illustrates Fixing `locate`'s dx=31 row: the same phase-correlation
quadrant figure Seeing the Cliff drew for the pre-fix failure, this time
against the real, shipped `dictk.translation.locate`, with
`centered=True` -- the same centered kernel padding `locate` uses
internally now, via `_kernel_pad(..., centered=True)` -- instead of
`phase_correlation`'s own permanent bottom-right-only default.

Unlike Seeing the Cliff's dx=31 figure, the two boxes coincide here: the
surface's own true peak and locate's actual reported position agree,
since the fix is exactly what makes them agree past the old cliff.

Runs live on every book build, not from a committed snapshot.
"""

from dictk.image import PixelCoordinate, read, subimage, translate
from dictk.plot import phase_correlation_quadrant_plot
from dictk.translation import locate

if __name__ == "__main__":
    reference_image = read(path="astronaut0.png")
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin = 30
    search_margin = 150
    dx = 31

    kernel_origin = PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin)
    kernel = subimage(
        image=reference_image,
        origin=kernel_origin,
        width=2 * kernel_margin,
        height=2 * kernel_margin,
    )
    search_origin = PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin)
    current_image = translate(arr=reference_image, dx=dx, dy=0)
    search = subimage(
        image=current_image,
        origin=search_origin,
        width=2 * search_margin,
        height=2 * search_margin,
    )

    found = locate(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=search_margin,
        search_margin_height=search_margin,
    )
    # Same conversion The First Sweep's own table uses: found is
    # point-center convention (kernel_margin already added back in);
    # convert to the surface's own frame-S, search-local convention.
    reported_local = PixelCoordinate(
        x=(found.x - kernel_margin) - search_origin.x,
        y=(found.y - kernel_margin) - search_origin.y,
    )
    path = "recoverable_displacement_range_fixing_locate_quadrant_dx31.png"
    phase_correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        title=f"Phase Correlation, Fixed locate (dx={dx}, succeeds)",
        path=path,
        reported_position=reported_local,
        reported_position_label="locate",
        centered=True,
    )
    print(f"Saved: {path}")
