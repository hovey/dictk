"""Image I/O, grayscale conversion, combination, and inspection utilities."""

import base64
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from matplotlib import pyplot as plt


def checkerboard(
    width: int, height: int, squares_x: int = 8, squares_y: int = 8
) -> np.ndarray:
    """Generate a black-and-white checkerboard test image.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        squares_x: Number of checkerboard squares along the width.
        squares_y: Number of checkerboard squares along the height.

    Returns:
        A 2D uint8 array of shape (height, width) with values 0 or 255.
    """
    rows = (np.arange(height) * squares_y // height) % 2
    cols = (np.arange(width) * squares_x // width) % 2
    pattern = np.logical_xor(rows[:, None], cols[None, :])
    return (pattern * 255).astype(np.uint8)


def is_rgba(arr: np.ndarray) -> bool:
    """Check whether an image array is in RGB or RGBA format.

    Args:
        arr: Input image array.

    Returns:
        True if the array is 3D with 3 or 4 channels, False otherwise.
    """
    return arr.ndim == 3 and arr.shape[2] in (3, 4)


def rgba_to_gray(arr: np.ndarray) -> np.ndarray:
    """Convert an RGB(A) image to grayscale by averaging the RGB channels.

    Args:
        arr: Input image array, either 2D (grayscale) or 3D (color).

    Returns:
        A 2D grayscale image array. If the input is already 2D, it is
        returned unchanged.

    Raises:
        ValueError: If the array is neither 2D nor a 3-or-4-channel 3D array.
    """
    if arr.ndim == 2:
        return arr

    if is_rgba(arr):
        return np.mean(arr[:, :, :3], axis=2).astype(arr.dtype)

    raise ValueError(
        "Input array must be either 2D (grayscale) or 3D with 3 or 4 channels (color)."
    )


def combine_images(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Combine two images by averaging their pixel values.

    Args:
        a: First image, 2D grayscale or 3D color.
        b: Second image, same shape as `a` once converted to grayscale.

    Returns:
        A 2D uint8 array, normalized to the range [0, 255].

    Raises:
        ValueError: If the grayscale-converted images don't share a shape.
    """
    gray_a = rgba_to_gray(a)
    gray_b = rgba_to_gray(b)

    if gray_a.shape != gray_b.shape:
        raise ValueError(
            f"shape mismatch: a.shape={gray_a.shape}, b.shape={gray_b.shape}"
        )

    combined = gray_a.astype(np.float64) + gray_b.astype(np.float64)
    return (combined / combined.max() * 255).astype(np.uint8)


def read_image(path: Path) -> np.ndarray:
    """Read an image file into a NumPy array.

    Args:
        path: Path to the image file.

    Returns:
        The image as a NumPy array.
    """
    return iio.imread(path)


def write_svg(arr: np.ndarray, path: Path) -> None:
    """Write a NumPy array to an SVG file.

    SVG is a vector format with no native pixel-grid concept, so the array
    is PNG-encoded and embedded as a base64 data URI inside a minimal SVG
    wrapper (the standard way to carry raster data in SVG) rather than
    traced into vector shapes.

    Args:
        arr: The image array to save.
        path: The output file path.
    """
    height, width = arr.shape[:2]
    png_bytes = iio.imwrite("<bytes>", arr, extension=".png")
    encoded = base64.b64encode(png_bytes).decode("ascii")

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" '
        f'xlink:href="data:image/png;base64,{encoded}"/>\n'
        "</svg>\n"
    )
    Path(path).write_text(svg, encoding="ascii")


def write_image(arr: np.ndarray, path: Path) -> None:
    """Write a NumPy array to an image file.

    Dispatches on the file extension: `.svg` is handled by `write_svg`
    (embedding a raster PNG in an SVG wrapper); every other extension
    (`.tiff`, `.png`, `.jpg`, ...) is handled by imageio directly.

    Args:
        arr: The image array to save.
        path: The output file path.
    """
    if Path(path).suffix.lower() == ".svg":
        write_svg(arr, path)
        return

    iio.imwrite(path, arr)


def describe_image(arr: np.ndarray) -> str:
    """Format a description of an image array's type, shape, and color format.

    Args:
        arr: The image array to describe.

    Returns:
        A multi-line description string.
    """
    lines = [
        f"Type: {type(arr)}",
        f"Shape: {arr.shape}",
        f"Dtype: {arr.dtype}",
    ]

    match arr.shape:
        case (_height, _width):
            lines.append("The image is grayscale.")
        case (_height, _width, 3):
            lines.append("The image is color (RGB).")
        case (_height, _width, 4):
            lines.append("The image is color (RGBA, includes alpha channel).")
        case _:
            lines.append("The image has an unsupported format.")

    return "\n".join(lines)


def save_histogram(arr: np.ndarray, path: Path, dpi: int = 300) -> None:
    """Save a histogram of pixel intensities [0, 255] for a grayscale image.

    Args:
        arr: The 2D grayscale image array, expected type uint8, range [0, 255].
        path: The output file path for the histogram image.
        dpi: Resolution of the saved figure.
    """
    plt.figure()
    plt.hist(arr.ravel(), bins=256, range=(0, 255), color="black", alpha=0.7)
    plt.title(f"pixel histogram intensity\n{path}", fontsize=8)
    plt.xlabel("pixel intensity (0-255)")
    plt.ylabel("frequency")
    plt.savefig(path, dpi=dpi)
    plt.close()
