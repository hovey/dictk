"""Point translation tracking between a reference and current image."""

import numpy as np
from skimage.registration import phase_cross_correlation

from dictk.correlation import WindowingMethod, _kernel_pad, _window
from dictk.image import PixelCoordinate, subimage


def locate(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_point: PixelCoordinate,
    search_center: PixelCoordinate,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
) -> PixelCoordinate:
    """Given a `reference_point` expressed in the `reference_image`
    frame, find its position expressed in the `current_image` frame.

    `reference_point` is a fixed, already-known point in `reference_image`.
    Where that same physical point ends up in `current_image` is exactly
    what this function finds — it is *not* an input, it's the return
    value. `search_center` is a different thing: just where to center the
    search area in `current_image`, i.e., a guess of roughly where to
    look. It doesn't need to be exact — only close enough that the true
    (unknown) position falls within the search area — and if no better
    guess is available, passing `reference_point` again is a reasonable
    default.

    Concretely: extracts a rectangular kernel (also called a subset,
    filter, or convolution matrix; `2 * kernel_margin_width` wide,
    `2 * kernel_margin_height` tall) from `reference_image` centered at
    `reference_point`, and a rectangular search area (also called a
    search window, scanning zone, or area of interest (AOI);
    `2 * search_margin_width` wide, `2 * search_margin_height` tall)
    from `current_image` centered at `search_center`, then locates the
    kernel within the search area via FFT-based phase cross-correlation
    (`skimage.registration.phase_cross_correlation`). The kernel always
    comes from `reference_image`; the search area always comes from
    `current_image`. Integer-pixel precision only; subpixel refinement is
    out of scope for now.

    The true position can be anywhere within `search_margin_width`/
    `search_margin_height` of `search_center` in every direction and
    still be found correctly -- the recoverable range is symmetric,
    bounded only by the search margins themselves, not by
    `kernel_margin_width`/`kernel_margin_height`. See [Recoverable
    Displacement Range](../getting_started/kernel_search_window_ratio.html)
    for why that's worth stating explicitly: an earlier version of this
    function had a real, silent bug here -- it recovered a displacement
    in the negative direction up to the full search margin, but capped
    at exactly the kernel margin in the positive direction, past which it
    returned a confidently wrong position instead of failing visibly.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        reference_point: The point's fixed, known position, in
            `reference_image`'s pixel reference frame.
        search_center: Where to center the search area, in
            `current_image`'s pixel reference frame — a guess of roughly
            where `reference_point` ended up, not the answer itself.
        kernel_margin_width: Half the kernel's width, in pixels. Must
            be >= 1.
        kernel_margin_height: Half the kernel's height, in pixels. Must
            be >= 1.
        search_margin_width: Half the search area's width, in pixels.
            Must be greater than `kernel_margin_width`.
        search_margin_height: Half the search area's height, in pixels.
            Must be greater than `kernel_margin_height`.
        windowing: If given, both the kernel and search area are passed
            through [`dictk.correlation.window`](./correlation.html#window)
            with this method -- tapering their edges toward zero to
            reduce spectral leakage -- before padding/FFT, the same
            `windowing` parameter
            [`dictk.correlation.phase_correlation`](./correlation.html#phase_correlation)
            exposes for the surface this function doesn't return. Default
            `None` applies no windowing, matching this function's
            original behavior exactly.

    Returns:
        The point's location, in `current_image`'s pixel reference frame.

    Raises:
        ValueError: If `kernel_margin_width` or `kernel_margin_height` is
            less than 1, or either `search_margin_width`/
            `search_margin_height` is not greater than its kernel
            counterpart.
    """
    if kernel_margin_width < 1:
        raise ValueError(f"kernel_margin_width {kernel_margin_width} must be >= 1")
    if kernel_margin_height < 1:
        raise ValueError(f"kernel_margin_height {kernel_margin_height} must be >= 1")
    if search_margin_width <= kernel_margin_width:
        raise ValueError(
            f"search_margin_width {search_margin_width} must be greater than "
            f"kernel_margin_width {kernel_margin_width}"
        )
    if search_margin_height <= kernel_margin_height:
        raise ValueError(
            f"search_margin_height {search_margin_height} must be greater than "
            f"kernel_margin_height {kernel_margin_height}"
        )

    kernel_width = 2 * kernel_margin_width
    kernel_height = 2 * kernel_margin_height
    search_width = 2 * search_margin_width
    search_height = 2 * search_margin_height

    kernel_origin = PixelCoordinate(
        x=reference_point.x - kernel_margin_width,
        y=reference_point.y - kernel_margin_height,
    )
    kernel = subimage(
        image=reference_image,
        origin=kernel_origin,
        width=kernel_width,
        height=kernel_height,
    )

    search_origin = PixelCoordinate(
        x=search_center.x - search_margin_width,
        y=search_center.y - search_margin_height,
    )
    search = subimage(
        image=current_image,
        origin=search_origin,
        width=search_width,
        height=search_height,
    )

    # phase_cross_correlation requires both images the same shape; only
    # the kernel needs padding, since the search area is always larger.
    # _window optionally tapers both first -- the same shared step
    # `phase_correlation` uses -- then _kernel_pad grows kernel up to
    # search's own shape.
    #
    # centered=True matters: phase_cross_correlation's FFT-based shift is
    # only correct up to half the padded array's own size in each
    # direction (it's circular/periodic) -- past that it wraps around to
    # a confidently wrong answer instead of failing visibly. With the
    # default centered=False (kernel's content anchored at the padded
    # array's top-left corner), that safe range is asymmetric: unbounded
    # in the negative direction, but capped at exactly kernel_margin_width/
    # kernel_margin_height in the positive direction, no matter how large
    # search_margin is set. Centering kernel's content in the padded array
    # instead makes the safe range symmetric in both directions -- see
    # [Recoverable Displacement
    # Range](../getting_started/kernel_search_window_ratio.html) for the
    # derivation and how this was found.
    kernel, search = _window(kernel=kernel, search=search, windowing=windowing)
    kernel_padded, pad_before_height, pad_before_width = _kernel_pad(
        kernel=kernel, shape=search.shape, centered=True
    )

    # search=reference_image, kernel_padded=moving_image, not the other
    # way around: skimage docs define `shift` as "the shift required to
    # register moving_image with reference_image", and what we actually
    # want is where the kernel's content sits within the (larger) search
    # area, so search must be reference_image and kernel_padded must be
    # moving_image. Swapping them negates the result and returns the
    # wrong location -- verified empirically, not just by this reasoning.
    #
    # normalization="phase" (skimage's own default) is used here
    # deliberately -- we do NOT follow hdic's registration.py, which uses
    # normalization=None. hdic's None came from its own pipeline running
    # a separate ZNCC-style preprocess() step before calling
    # phase_cross_correlation, specifically to avoid double-normalizing
    # on top of that. locate() has no such preprocessing step, so that
    # reasoning doesn't carry over here -- and empirically, sweeping
    # kernel/search margin ratios against a known displacement,
    # normalization="phase" matched or outperformed normalization=None,
    # not the other way around.
    #
    # What normalization actually does: the core computation is a
    # cross-power spectrum, image_product = FFT(reference) *
    # conj(FFT(moving)). normalization="phase" divides this by its own
    # magnitude at every frequency, discarding contrast/energy
    # information and keeping only phase -- the classic Kuglin-Hines
    # phase correlation, giving a sharp peak and robustness to
    # illumination differences between the two images.
    # normalization=None skips that division (plain unnormalized
    # cross-correlation), which skimage's own docs describe as less
    # robust to noise but sometimes preferable in high-noise scenarios.
    # Which is better is genuinely content-dependent, not a settled
    # default-is-always-better situation.
    shift, _error, _phasediff = phase_cross_correlation(
        reference_image=search, moving_image=kernel_padded, normalization="phase"
    )

    return PixelCoordinate(
        x=search_origin.x + int(shift[1]) + kernel_margin_width + pad_before_width,
        y=search_origin.y + int(shift[0]) + kernel_margin_height + pad_before_height,
    )
