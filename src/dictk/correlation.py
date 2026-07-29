"""Spatial-domain cross-correlation criteria between a kernel and a search area."""

import numpy as np


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
