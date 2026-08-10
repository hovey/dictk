"""Spatial- and Fourier-domain cross-correlation criteria between a kernel and a search area."""

from enum import Enum

import numpy as np


class WindowingMethod(Enum):
    """Tapering window `window()` can apply before an FFT.

    - HANN: tapers all the way to exactly 0 at both ends.
    - HAMMING: stops short, around 0.08, trading a little residual
      discontinuity for a narrower main lobe in the transformed signal.
    """

    HANN = "hann"
    HAMMING = "hamming"


def window(
    *, arr: np.ndarray, method: WindowingMethod = WindowingMethod.HANN
) -> np.ndarray:
    r"""Taper `arr`'s edges toward zero with a 2D Hann or Hamming window.

    An FFT implicitly treats an array as one period of an
    infinitely-repeating signal. If the content doesn't tile seamlessly --
    the general case, since nothing arranges `arr`'s edges to match up --
    that discontinuity leaks energy across many frequencies rather than the
    few the underlying content actually has, an effect called **spectral
    leakage**. In a correlation surface, leakage broadens and can shift the
    peak.

    This counters that by tapering `arr`'s edges toward zero before it's
    transformed, so the (still discontinuous, but now near-zero) seam
    contributes far less energy. The 2D window is the outer product of a 1D
    window with itself along each axis:

    $$w_{\rm Hann}(n) = 0.5 \left(1 - \cos\left(\frac{2\pi n}{N - 1}\right)\right)$$

    $$w_{\rm Hamming}(n) = 0.54 - 0.46 \cos\left(\frac{2\pi n}{N - 1}\right)$$

    for $n = 0, \ldots, N-1$ across a window of length $N$.

    See Harris FJ. "[On the use of windows for harmonic analysis with
    the discrete Fourier
    transform](https://www.cs.cmu.edu/afs/cs/user/bhiksha/WWW/courses/dsp/spring2013/WWW/schedule/readings/windows_comparison2_harris.pdf)."
    *Proceedings of the IEEE* 1978;66(1):51-83. A U.S. government work,
    not protected by U.S. copyright.

    Args:
        arr: A 2D array to window.
        method: Which window to apply. Default `WindowingMethod.HANN`.

    Returns:
        A 2D float64 array the same shape as `arr`, with `arr` multiplied
        elementwise by the 2D window.

    Raises:
        ValueError: If `arr` is not 2D.
    """
    if arr.ndim != 2:
        raise ValueError(f"arr must be 2D, got shape {arr.shape}")

    match method:
        case WindowingMethod.HANN:
            win_func = np.hanning
        case WindowingMethod.HAMMING:
            win_func = np.hamming
        case _:
            raise ValueError(f"Unsupported windowing method: {method}")

    rows, cols = arr.shape
    window_2d = np.outer(win_func(rows), win_func(cols))
    return arr.astype(np.float64) * window_2d


def _prepare(
    *, kernel: np.ndarray, search: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Validate `kernel`/`search` and cast both to float64.

    Args:
        kernel: The fixed template subimage.
        search: The larger subimage to slide `kernel` across.

    Returns:
        `(kernel, search)`, both cast to float64.

    Raises:
        ValueError: If either array is not 2D, or `search` is smaller than
            `kernel` in either dimension.
    """
    if kernel.ndim != 2:
        raise ValueError(f"kernel must be 2D, got shape {kernel.shape}")
    if search.ndim != 2:
        raise ValueError(f"search must be 2D, got shape {search.shape}")
    if search.shape[0] < kernel.shape[0] or search.shape[1] < kernel.shape[1]:
        raise ValueError(
            f"search shape {search.shape} must be >= kernel shape {kernel.shape} "
            "in both dimensions"
        )
    return kernel.astype(np.float64), search.astype(np.float64)


def _safe_divide(*, numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Elementwise `numerator / denominator`, substituting 0 wherever `denominator` is 0.

    Args:
        numerator: Values to divide.
        denominator: Values to divide by; must be broadcastable against
            `numerator` and non-negative (as with a square root of an
            energy term).

    Returns:
        `numerator / denominator`, with 0 wherever `denominator` is 0
        (avoiding a division-by-zero warning, not just its result).
    """
    safe_denominator = np.where(denominator == 0, 1.0, denominator)
    return np.where(denominator == 0, 0.0, numerator / safe_denominator)


def _windows(*, search: np.ndarray, kernel_shape: tuple[int, int]) -> np.ndarray:
    """Return every `kernel_shape`-sized window of `search`, as one strided view.

    Args:
        search: The 2D array to slide a window across.
        kernel_shape: The `(height, width)` of each window.

    Returns:
        A 4D array of shape `(out_height, out_width, *kernel_shape)`, where
        `out_height = search.shape[0] - kernel_shape[0] + 1` and likewise for
        `out_width`. Entry `[dy, dx]` is the `kernel_shape`-sized window of
        `search` with its own top-left corner at offset `(dx, dy)`.
    """
    return np.lib.stride_tricks.sliding_window_view(search, kernel_shape)


def cc(*, kernel: np.ndarray, search: np.ndarray) -> np.ndarray:
    r"""Cross-correlation (CC) surface of `kernel` slid over `search`.

    At every valid position, computes $C_{\rm CC} = \sum f_i g_i$, where
    $f$ is `kernel` and $g$ is the same-sized window of `search` at that
    position. Robust to neither brightness nor contrast differences between
    `kernel` and `search` — a uniform offset or scaling of either changes
    every value.

    See Pan B, Xie H, Wang Z. "Equivalence of digital image correlation
    criteria for pattern matching." Applied Optics 2010;49(28):5501-9.

    Args:
        kernel: The fixed template subimage (`f`).
        search: The larger subimage to slide `kernel` across (`g`'s source).

    Returns:
        A 2D float64 array of shape
        `(search.shape[0] - kernel.shape[0] + 1, search.shape[1] - kernel.shape[1] + 1)`.
        Entry `[dy, dx]` is $C_{\rm CC}$ with `kernel`'s top-left corner at
        offset `(dx, dy)` in `search`'s local frame.

    Raises:
        ValueError: If either array is not 2D, or `search` is smaller than
            `kernel` in either dimension.
    """
    kernel, search = _prepare(kernel=kernel, search=search)
    windows = _windows(search=search, kernel_shape=kernel.shape)
    return (windows * kernel).sum(axis=(-2, -1))


def ncc(*, kernel: np.ndarray, search: np.ndarray) -> np.ndarray:
    r"""Normalized cross-correlation (NCC) surface of `kernel` slid over `search`.

    At every valid position, computes
    $C_{\rm NCC} = \sum f_i g_i \,/\, \sqrt{\sum f_i^2 \sum g_i^2}$, where
    $f$ is `kernel` and $g$ is the same-sized window of `search` at that
    position. Robust to a uniform contrast (multiplicative) difference
    between `kernel` and `search`, since scaling either side by a positive
    constant cancels between the numerator and denominator. Not robust to
    brightness (additive) differences. A window with zero energy (e.g. a
    flat, constant-valued region) contributes a value of 0 rather than
    raising a division-by-zero error.

    See Pan B, Xie H, Wang Z. "Equivalence of digital image correlation
    criteria for pattern matching." Applied Optics 2010;49(28):5501-9.

    Args:
        kernel: The fixed template subimage (`f`).
        search: The larger subimage to slide `kernel` across (`g`'s source).

    Returns:
        A 2D float64 array of shape
        `(search.shape[0] - kernel.shape[0] + 1, search.shape[1] - kernel.shape[1] + 1)`.
        Entry `[dy, dx]` is $C_{\rm NCC}$ with `kernel`'s top-left corner at
        offset `(dx, dy)` in `search`'s local frame.

    Raises:
        ValueError: If either array is not 2D, or `search` is smaller than
            `kernel` in either dimension.
    """
    kernel, search = _prepare(kernel=kernel, search=search)
    windows = _windows(search=search, kernel_shape=kernel.shape)
    numerator = (windows * kernel).sum(axis=(-2, -1))
    kernel_energy = np.sum(kernel**2)
    window_energy = (windows**2).sum(axis=(-2, -1))
    denominator = np.sqrt(kernel_energy * window_energy)
    return _safe_divide(numerator=numerator, denominator=denominator)


def zcc(*, kernel: np.ndarray, search: np.ndarray) -> np.ndarray:
    r"""Zero-mean cross-correlation (ZCC) surface of `kernel` slid over `search`.

    At every valid position, computes
    $C_{\rm ZCC} = \sum (f_i - \bar{f})(g_i - \bar{g})$, where $f$ is
    `kernel`, $g$ is the same-sized window of `search` at that position,
    $\bar{f}$ is `kernel`'s own mean (fixed across all positions, since the
    kernel never moves), and $\bar{g}$ is that window's own local mean
    (recomputed at every position, not a global `search` statistic). Robust
    to a uniform brightness (additive) difference between `kernel` and
    `search`, since subtracting each side's own local mean cancels any
    constant added to that side. Not robust to contrast (multiplicative)
    differences.

    See Pan B, Xie H, Wang Z. "Equivalence of digital image correlation
    criteria for pattern matching." Applied Optics 2010;49(28):5501-9.

    Args:
        kernel: The fixed template subimage (`f`).
        search: The larger subimage to slide `kernel` across (`g`'s source).

    Returns:
        A 2D float64 array of shape
        `(search.shape[0] - kernel.shape[0] + 1, search.shape[1] - kernel.shape[1] + 1)`.
        Entry `[dy, dx]` is $C_{\rm ZCC}$ with `kernel`'s top-left corner at
        offset `(dx, dy)` in `search`'s local frame.

    Raises:
        ValueError: If either array is not 2D, or `search` is smaller than
            `kernel` in either dimension.
    """
    kernel, search = _prepare(kernel=kernel, search=search)
    windows = _windows(search=search, kernel_shape=kernel.shape)
    kernel_centered = kernel - kernel.mean()
    windows_centered = windows - windows.mean(axis=(-2, -1), keepdims=True)
    return (windows_centered * kernel_centered).sum(axis=(-2, -1))


def zncc(*, kernel: np.ndarray, search: np.ndarray) -> np.ndarray:
    r"""Zero-mean normalized cross-correlation (ZNCC) surface of `kernel` slid over `search`.

    At every valid position, computes
    $C_{\rm ZNCC} = \sum \bar{f}_i \bar{g}_i \,/\, \sqrt{\sum \bar{f}_i^2 \sum \bar{g}_i^2}$,
    where $\bar{f}_i = f_i - \bar{f}$ and $\bar{g}_i = g_i - \bar{g}$ ($f$ =
    `kernel`, $g$ = the same-sized window of `search` at that position,
    $\bar{f}$/$\bar{g}$ their respective means -- $\bar{f}$ fixed, $\bar{g}$
    recomputed locally per position, as in `zcc`). Robust to both brightness
    (additive) and contrast (multiplicative) differences between `kernel`
    and `search`, combining `zcc`'s brightness invariance with `ncc`'s
    contrast invariance. A window with zero variance (e.g. a flat,
    constant-valued region) contributes a value of 0 rather than raising a
    division-by-zero error.

    See Pan B, Xie H, Wang Z. "Equivalence of digital image correlation
    criteria for pattern matching." Applied Optics 2010;49(28):5501-9.

    Args:
        kernel: The fixed template subimage (`f`).
        search: The larger subimage to slide `kernel` across (`g`'s source).

    Returns:
        A 2D float64 array of shape
        `(search.shape[0] - kernel.shape[0] + 1, search.shape[1] - kernel.shape[1] + 1)`.
        Entry `[dy, dx]` is $C_{\rm ZNCC}$ with `kernel`'s top-left corner at
        offset `(dx, dy)` in `search`'s local frame.

    Raises:
        ValueError: If either array is not 2D, or `search` is smaller than
            `kernel` in either dimension.
    """
    kernel, search = _prepare(kernel=kernel, search=search)
    windows = _windows(search=search, kernel_shape=kernel.shape)
    kernel_centered = kernel - kernel.mean()
    windows_centered = windows - windows.mean(axis=(-2, -1), keepdims=True)
    numerator = (windows_centered * kernel_centered).sum(axis=(-2, -1))
    kernel_energy = np.sum(kernel_centered**2)
    window_energy = (windows_centered**2).sum(axis=(-2, -1))
    denominator = np.sqrt(kernel_energy * window_energy)
    return _safe_divide(numerator=numerator, denominator=denominator)


def _window_and_pad(
    *,
    kernel: np.ndarray,
    search: np.ndarray,
    windowing: WindowingMethod | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Optionally window, then zero-pad `kernel` up to `search`'s own shape.

    Shared by `phase_correlation` and
    [`dictk.translation.locate`](../translation.html#locate) -- the two
    functions that zero-pad `kernel` before comparing it against `search`
    via an FFT-based technique -- so the "window, then pad" step (and its
    ordering) lives in exactly one place.

    Args:
        kernel: The fixed template subimage, before padding.
        search: The larger subimage `kernel` is compared against.
        windowing: If given, both `kernel` and `search` are passed through
            `window()` with this method before padding. `None` leaves
            both untouched -- including their dtype, so a caller that
            never windows sees no incidental cast either.

    Returns:
        `(kernel_padded, search)` -- `kernel_padded` the same shape as
        `search`, `search` itself unchanged except by windowing.
    """
    if windowing is not None:
        kernel = window(arr=kernel, method=windowing)
        search = window(arr=search, method=windowing)
    pad_height = search.shape[0] - kernel.shape[0]
    pad_width = search.shape[1] - kernel.shape[1]
    kernel_padded = np.pad(kernel, ((0, pad_height), (0, pad_width)))
    return kernel_padded, search


def phase_correlation(
    *,
    kernel: np.ndarray,
    search: np.ndarray,
    windowing: WindowingMethod | None = None,
) -> np.ndarray:
    r"""Phase correlation surface of `kernel` against `search`, via FFT.

    Unlike `cc`/`ncc`/`zcc`/`zncc`, which slide `kernel` over `search` one
    valid window at a time, this computes the same kind of answer all at
    once in the Fourier domain: `kernel` is zero-padded (bottom and right)
    up to `search`'s own shape, then

    $$
    C_{\rm phase} = \mathcal{F}^{-1}\!\left(\frac{\mathcal{F}(g)\,
    \overline{\mathcal{F}(f)}}{\left|\mathcal{F}(g)\,\overline{\mathcal{F}(f)}\right|}\right)
    $$

    where $f$ is the zero-padded `kernel`, $g$ is `search`, and
    $\mathcal{F}$ is the 2D discrete Fourier transform. Dividing by the
    cross-power spectrum's own magnitude at every frequency -- rather than
    summing raw products like `cc` does -- is the classic Kuglin-Hines
    *phase correlation* technique, and is robust to both brightness
    (additive) and contrast (multiplicative) differences between `kernel`
    and `search`, the same pair of invariances `zncc` has, though by a
    completely different mechanism: a brightness shift only touches the
    zero-frequency (DC) term, leaving every other frequency -- and thus the
    peak's position -- untouched, while dividing by magnitude at every
    frequency cancels any overall contrast scaling directly. This is *not*
    a Fourier-domain equivalent of `zncc`'s formula -- `zncc` recomputes a
    local mean/variance at every candidate window as it slides; this
    normalizes once, globally, per frequency, over the whole padded
    extent -- it just lands in the same "robust to both" category.

    This is exactly what [`dictk.translation.locate`](../translation.html#locate)
    computes internally via `skimage.registration.phase_cross_correlation`
    (`normalization="phase"`), reproduced here to expose the full surface
    for visualization -- `phase_cross_correlation` itself only returns the
    final shift, not the array it was computed from. The two aren't
    directly comparable value-for-value, though: `locate` additionally
    unwraps indices past the array's midpoint into negative shifts (since
    this surface is circular/periodic), which this function does not --
    its raw `argmax` is always in `[0, search.shape)`, matching the same
    offset-within-`search` convention `cc`/`ncc`/`zcc`/`zncc` use. For the
    small, comfortably-within-bounds displacements this book's examples
    use, the two agree without any unwrapping needed.

    See Kuglin CD, Hines DC. "The phase correlation image alignment
    method." Proceedings of IEEE International Conference on Cybernetics
    and Society, 1975:163-165.

    Args:
        kernel: The fixed template subimage (`f`, before padding).
        search: The larger subimage `kernel` is compared against (`g`).
        windowing: If given, both `kernel` and `search` are passed through
            `window()` with this method -- tapering their edges toward
            zero to reduce spectral leakage -- before padding/FFT. `kernel`
            is windowed first, then zero-padded, so the padding stays
            outside the tapered region. Default `None` applies no
            windowing, matching this function's original behavior exactly.

    Returns:
        A 2D float64 array the same shape as `search` (unlike
        `cc`/`ncc`/`zcc`/`zncc`'s smaller "valid" shape, since nothing
        here excludes any candidate offset). Entry `[dy, dx]` is
        $C_{\rm phase}$ with `kernel`'s top-left corner at offset
        `(dx, dy)` in `search`'s local frame.

    Raises:
        ValueError: If either array is not 2D, or `search` is smaller than
            `kernel` in either dimension.
    """
    kernel, search = _prepare(kernel=kernel, search=search)
    kernel_padded, search = _window_and_pad(
        kernel=kernel, search=search, windowing=windowing
    )

    search_freq = np.fft.fft2(search)
    kernel_freq = np.fft.fft2(kernel_padded)
    image_product = search_freq * kernel_freq.conj()
    eps = np.finfo(image_product.real.dtype).eps
    image_product /= np.maximum(np.abs(image_product), 100 * eps)
    return np.fft.ifft2(image_product).real
