"""Synthetic speckle pattern generation.

Implements the Rosta algorithm described by Olufsen SN, Andersen ME,
Fagerholt E. "muDIC: An open-source toolkit for digital image
correlation." SoftwareX. 2020 Jan 1;11:100391, Algorithm 1, page 6.
https://doi.org/10.1016/j.softx.2019.100391
https://github.com/PolymerGuy/muDIC
"""

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from scipy.ndimage import gaussian_filter


class ImageSize(NamedTuple):
    """Image size specification as a width and a height.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.
    """

    width: int
    height: int


@dataclass(frozen=True)
class RostaParameters:
    """Configuration parameters for Rosta pattern generation.

    Attributes:
        image_size: Target image dimensions.
        dot_size: Size factor for pattern dots (0.0 to 100.0).
        density: Density of pattern elements (0.0 to 1.0).
        smoothness: Smoothness factor for final blur (0.0 to 100.0).
        random_seed: Seed for reproducible random number generation.
    """

    image_size: ImageSize
    dot_size: float
    density: float
    smoothness: float
    random_seed: int
    name: str = "rosta"

    def __post_init__(self):
        if not 0.0 < self.dot_size < 100.0:
            raise ValueError(
                f"dot_size {self.dot_size} must be in the range (0.0, 100.0)"
            )
        if not 0.0 < self.density < 1.0:
            raise ValueError(f"density {self.density} must be in the range (0.0, 1.0)")
        if not 0.0 < self.smoothness < 100.0:
            raise ValueError(
                f"smoothness {self.smoothness} must be in the range (0.0, 100.0)"
            )


def rosta_pattern(rp: RostaParameters) -> np.ndarray:
    """Generate a Rosta speckle pattern as a 2D array.

    Args:
        rp: Configuration parameters for the pattern.

    Returns:
        A 2D NumPy array of shape (rp.image_size.height, rp.image_size.width),
        normalized grayscale values in the range [0.0, 1.0].
    """
    # Characteristic length: the minimum image dimension
    minimum_side_length = min(rp.image_size.width, rp.image_size.height)

    merge_sigma = rp.dot_size * minimum_side_length / 1000.0
    blur_sigma = rp.smoothness * minimum_side_length / 1000.0

    rng = np.random.default_rng(rp.random_seed)
    # Explicit height x width call: numpy's random shape convention is
    # ambiguous unless the axis order is spelled out.
    noise = rng.standard_normal(size=(rp.image_size.height, rp.image_size.width))

    noise_blurred = gaussian_filter(input=noise, sigma=merge_sigma)

    peak_to_peak = np.ptp(noise_blurred)
    noise_blurred_normalized = (noise_blurred - np.min(noise_blurred)) / peak_to_peak

    sorted_gray_scales = np.sort(noise_blurred_normalized.flatten())
    clip_index = int(rp.density * np.size(sorted_gray_scales))
    clip_value = sorted_gray_scales[clip_index]

    clipped = np.zeros_like(noise_blurred_normalized)
    clipped[noise_blurred_normalized > clip_value] = 1.0

    pattern = gaussian_filter(input=clipped, sigma=blur_sigma) * -1.0 + 1.0

    return pattern


def rosta(
    width: int = 200,
    height: int = 200,
    *,
    dot_size: float = 4.0,
    density: float = 0.32,
    smoothness: float = 2.0,
    random_seed: int = 42,
) -> np.ndarray:
    """Generate a Rosta speckle pattern as a uint8 grayscale image array.

    Same parameters and pixel values as the `dictk rosta` CLI command, minus
    the file write — see the `dictk` package docstring for why the API
    layer stops at the array.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        dot_size: Size factor for pattern dots (0.0 to 100.0).
        density: Density of pattern elements (0.0 to 1.0).
        smoothness: Smoothness factor for final blur (0.0 to 100.0).
        random_seed: Seed for reproducible random number generation.

    Returns:
        A 2D uint8 array of shape (height, width), grayscale in [0, 255].

    Raises:
        ValueError: If dot_size, density, or smoothness is out of range.
    """
    rp = RostaParameters(
        image_size=ImageSize(width=width, height=height),
        dot_size=dot_size,
        density=density,
        smoothness=smoothness,
        random_seed=random_seed,
    )
    pattern = rosta_pattern(rp)
    return (pattern * 255).astype(np.uint8)
