"""Core numerical primitives for digital image correlation."""

import numpy as np


def zero_normalized_cross_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Compute the zero-normalized cross-correlation (ZNCC) between two arrays.

    ZNCC is a similarity metric commonly used as the matching criterion in
    digital image correlation (DIC) template matching: it compares two
    equal-shaped patches (e.g. image subsets) while being invariant to
    linear changes in brightness and contrast. A return value of ``1.0``
    indicates a perfect match, ``-1.0`` a perfect inverse match, and ``0.0``
    no correlation.

    Args:
        a: First array (e.g. a reference image subset).
        b: Second array, same shape as ``a`` (e.g. a deformed image subset).

    Returns:
        The ZNCC score in the range ``[-1.0, 1.0]``.

    Raises:
        ValueError: If ``a`` and ``b`` do not have the same shape.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)

    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: a.shape={a.shape}, b.shape={b.shape}")

    a_centered = a - a.mean()
    b_centered = b - b.mean()

    denominator = np.sqrt(np.sum(a_centered**2) * np.sum(b_centered**2))
    if denominator == 0:
        return 0.0

    return float(np.sum(a_centered * b_centered) / denominator)
