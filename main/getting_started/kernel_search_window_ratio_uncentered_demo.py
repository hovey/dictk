"""Reproduces `dictk.translation.locate`'s behavior before the fix
documented in Recoverable Displacement Range: kernel content anchored at
the padded array's top-left corner, not centered. A `def`-based helper
like this doesn't fit cleanly into a single-line `cmdrun` invocation (the
convention every other live demo in this book uses), so it lives here
instead -- matching parallelization_bench.py's precedent for logic too
complex for a one-liner. Unlike that script, this one is cheap and runs
live on every book build, not a committed one-time snapshot.
"""

from dictk.correlation import _kernel_pad, _window
from dictk.image import PixelCoordinate, read, subimage, translate
from skimage.registration import phase_cross_correlation


def locate_uncentered(
    reference_image,
    current_image,
    reference_point,
    search_center,
    kernel_margin,
    search_margin,
):
    kernel_origin = PixelCoordinate(
        x=reference_point.x - kernel_margin, y=reference_point.y - kernel_margin
    )
    kernel = subimage(
        image=reference_image,
        origin=kernel_origin,
        width=2 * kernel_margin,
        height=2 * kernel_margin,
    )
    search_origin = PixelCoordinate(
        x=search_center.x - search_margin, y=search_center.y - search_margin
    )
    search = subimage(
        image=current_image,
        origin=search_origin,
        width=2 * search_margin,
        height=2 * search_margin,
    )
    kernel, search = _window(kernel=kernel, search=search, windowing=None)
    kernel_padded, _, _ = _kernel_pad(kernel=kernel, shape=search.shape, centered=False)
    shift, _, _ = phase_cross_correlation(
        reference_image=search, moving_image=kernel_padded, normalization="phase"
    )
    return PixelCoordinate(
        x=search_origin.x + int(shift[1]) + kernel_margin,
        y=search_origin.y + int(shift[0]) + kernel_margin,
    )


if __name__ == "__main__":
    reference_image = read(path="astronaut0.png")
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin = 30
    search_margin = (
        180  # generous, fixed -- shouldn't matter, per the ratio result above
    )

    print("| dx | kernel_margin offset | found | match |")
    print("|---|---|---|---|")
    for dx in [
        kernel_margin - 3,
        kernel_margin - 1,
        kernel_margin,
        kernel_margin + 1,
        kernel_margin + 3,
    ]:
        current_image = translate(arr=reference_image, dx=dx, dy=0)
        expected = PixelCoordinate(x=p0.x + dx, y=p0.y)
        found = locate_uncentered(
            reference_image, current_image, p0, p0, kernel_margin, search_margin
        )
        print(
            f"| {dx} | {dx - kernel_margin:+d} | ({found.x},{found.y}) | {found == expected} |"
        )
