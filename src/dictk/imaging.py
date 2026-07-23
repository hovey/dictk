"""Image I/O, grayscale conversion, combination, and inspection utilities."""

import base64
import importlib.resources
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import zoom


def checkerboard(
    width: int, height: int, count_x: int = 8, count_y: int = 8
) -> np.ndarray:
    """Generate a black-and-white checkerboard test image.

    Same parameters and pixel values as the `dictk checkerboard` CLI
    command, minus the file write — see the `dictk` package docstring for
    why the API layer stops at the array. count_x and count_y are named for
    the rectangles they divide the image into, not "squares": unequal
    counts (or a width/height ratio that doesn't match count_x/count_y)
    produce rectangular cells, not square ones.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        count_x: Number of rectangles along the width. Must be >= 1.
        count_y: Number of rectangles along the height. Must be >= 1.

    Returns:
        A 2D uint8 array of shape (height, width) with values 0 or 255.

    Raises:
        ValueError: If count_x or count_y is less than 1.
    """
    if count_x < 1:
        raise ValueError(f"count_x {count_x} must be >= 1")
    if count_y < 1:
        raise ValueError(f"count_y {count_y} must be >= 1")

    rows = (np.arange(height) * count_y // height) % 2
    cols = (np.arange(width) * count_x // width) % 2
    pattern = np.logical_xor(rows[:, None], cols[None, :])
    return (pattern * 255).astype(np.uint8)


def astronaut(width: int = 512, height: int = 512) -> np.ndarray:
    """Load a bundled real-world grayscale reference image.

    Same parameters and pixel values as the `dictk astronaut` CLI
    command, minus the file write — see the `dictk` package docstring for
    why the API layer stops at the array.

    The source is a NASA portrait of astronaut Eileen Collins, from the
    NASA Great Images database ("No known copyright restrictions, released
    into the public domain."). It's bundled as a color image and converted
    with `rgba_to_gray`; unlike `rosta` and `checkerboard`, it isn't
    procedurally generated, so `width`/`height` other than the native
    512x512 resize the source image (via `scipy.ndimage.zoom`) rather than
    computing a fresh pattern at that size.

    Args:
        width: Image width in pixels. Must be >= 1.
        height: Image height in pixels. Must be >= 1.

    Returns:
        A 2D uint8 array of shape (height, width).

    Raises:
        ValueError: If width or height is less than 1.
    """
    if width < 1:
        raise ValueError(f"width {width} must be >= 1")
    if height < 1:
        raise ValueError(f"height {height} must be >= 1")

    asset_path = importlib.resources.files("dictk") / "data" / "astronaut.png"
    with importlib.resources.as_file(asset_path) as path:
        color = read_image(path)
    gray = rgba_to_gray(color)

    native_height, native_width = gray.shape
    if (width, height) == (native_width, native_height):
        return gray

    zoom_factors = (height / native_height, width / native_width)
    resized = zoom(gray.astype(np.float64), zoom_factors, order=3)
    return np.clip(resized, 0, 255).astype(np.uint8)


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


def brightness(arr: np.ndarray, factor: float) -> np.ndarray:
    """Adjust image brightness by an additive shift, clipped to [0, 255].

    Brightness *translates* the pixel-intensity histogram: every pixel is
    shifted by the same amount, so dark areas lighten right along with
    bright ones (unlike a multiplicative scale, where a black pixel would
    stay exactly black). factor=1.0 leaves the image unchanged; factor=1.5
    shifts every pixel by +127.5*0.5 = +63.75, factor=2.0 by +127.5.

    Args:
        arr: A 2D grayscale image array.
        factor: Brightness factor. 1.0 is unchanged; > 1.0 brightens
            (shifts toward white); < 1.0 darkens (shifts toward black).

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    max_pixel_value = 255.0
    offset = (factor - 1.0) * (max_pixel_value / 2.0)
    shifted = arr.astype(np.float64) + offset
    return np.clip(shifted, 0, max_pixel_value).astype(np.uint8)


def contrast(arr: np.ndarray, factor: float) -> np.ndarray:
    """Adjust image contrast by scaling around the mean, clipped to [0, 255].

    Contrast *stretches* the pixel-intensity histogram outward from its own
    mean, rather than shifting it: the mean stays roughly the same, while
    values spread further from it. factor=1.0 leaves the image unchanged;
    factor=0.0 collapses every pixel to the mean (a flat gray image);
    factor > 1.0 pushes values further toward 0 and 255.

    Args:
        arr: A 2D grayscale image array.
        factor: Contrast factor. 1.0 is unchanged; > 1.0 increases
            contrast; between 0.0 and 1.0 decreases it.

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    mean = arr.astype(np.float64).mean()
    stretched = (arr.astype(np.float64) - mean) * factor + mean
    return np.clip(stretched, 0, 255).astype(np.uint8)


def stretch(
    arr: np.ndarray, factor_x: float = 1.0, factor_y: float = 1.0
) -> np.ndarray:
    """Apply a uniaxial or biaxial stretch, pivoting on the image origin.

    Mimics a continuum-mechanics stretch deformation gradient
    diag(factor_x, factor_y), anchored at the image's top-left corner
    (x=0, y=0): that corner stays fixed, and content grows (factor > 1.0)
    or shrinks (factor < 1.0) away from it along each axis. Uses backward
    mapping — for each output pixel, the inverse of the stretch locates
    its source coordinate in `arr`, with bilinear interpolation for
    non-integer source coordinates — so the result has no gaps, unlike
    naively moving each source pixel forward. A factor < 1.0 shrinks
    content toward the origin, leaving black (fill value 0) margins along
    the far (bottom/right) edges.

    Args:
        arr: A 2D grayscale image array.
        factor_x: Stretch factor along the x-axis. Must be > 0.
        factor_y: Stretch factor along the y-axis. Must be > 0.

    Returns:
        A 2D uint8 array, same shape as `arr`.

    Raises:
        ValueError: If factor_x or factor_y is <= 0.
    """
    if factor_x <= 0:
        raise ValueError(f"factor_x {factor_x} must be > 0")
    if factor_y <= 0:
        raise ValueError(f"factor_y {factor_y} must be > 0")

    height, width = arr.shape
    xs, ys = np.meshgrid(np.arange(width), np.arange(height))

    # Backward mapping, pivoting on the origin (0, 0): for each output
    # pixel, the inverse of the stretch gives the coordinate to sample
    # from in the original image.
    xs_source = xs / factor_x
    ys_source = ys / factor_y

    interpolator = RegularGridInterpolator(
        points=(np.arange(height), np.arange(width)),
        values=arr.astype(np.float64),
        method="linear",
        bounds_error=False,
        fill_value=0.0,
    )
    points = np.stack((ys_source.ravel(), xs_source.ravel()), axis=1)
    deformed = interpolator(points).reshape(arr.shape)

    return np.clip(deformed, 0, 255).astype(np.uint8)


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
