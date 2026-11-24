"""
The goal of DIC is to find the best match between a small part of an image (the subset) and a region to search (the area of interest) in subsequent loading steps. Shifts in the subset position across multiple loading steps can be used to determine the amount of strain in the sample as a function of physical displacement. Subsets are typically made easier to identify by adding a speckle pattern, which creates a unique set of surface features that can be found across multiple loading steps.

VIC2D, a common DIC package uses the following naming convention, which we will adopt here:

aoi: The area of interest, or region to search within the entire set of images. We will be dynamically and automatically determining the aoi as a "scanning zone" or "search window" centered about the location of the subset.

subset: The small portion of an image we wish to identify across multiple load steps

For our large viewing fields, the subset will typically be a square region on the order of 20-40 pixels on edge, and the area of interest (aoi) will be a square region on the order of 80-120 pixels on edge.

Test herein uses 35x35 pixel subsets in window of 120x120 pixels
            7,396 xcorr per subset
    x  24,822,820 subsets in 6k SEM image
    =
  183,589,576,720 xcorr in an image set of 6,144 x 4,096 pixels

Direct convolution should have complexity O(n*k^2), with:
    n = num pixels in input
    k^2 = num pixels in kernel (subset)
FFT convolution should have complexity O(n log n)
should be ~300 times faster for kernel of 35^2 and window of 120^2

    # tensor(batch_size, n_channels, height, width)
    # image shape:  (1,1,120,120)
    # kernel shape: (1,1,20,20)
    # output conv:  (1,1,101,101)

    # # conv2d will apply all kernels to all inputs if shapes are thus:
    # image shape:  (10,1,120,120)
    # kernel shape: (10,1,20,20)
    # output conv:  (10,10,101,101)

    # # reorganize input images to "trick" conv2d:
    # image shape:  (1,10,120,120)
    # kernel shape: (10,1,20,20)
    # output conv:  (1,10,101,101)

    # as long as you keep track of correct axis dimensions, you can verify the shifts
"""

# from enum import StrEnum
from pathlib import Path
import platform
import time
from typing import Final, Tuple

import numpy as np
from numpy.typing import NDArray
from PIL import Image

import hdic.types.experiment as exp
from hdic.types.experiment import Result
from hdic.types.image import PixelCoordinate, ScanWindow, Subset
from hdic.types.methods import CrossCorrelationMethod, SumSquaredDifferencesMethod

if platform.system() != "Darwin":
    import torch
    import torch.nn.functional as F
else:
    raise RuntimeError("This module requires PyTorch, which does not run on macOS.")


# experimental images
# tile_height, tile_width = 1604, 1400  # pixel count, actual MultiSEM image dimension


# Refactored:
# This class is now in hdic.types.image
# class PixelCoordinate(NamedTuple):
#     """Pixel Coordinate in relation to the origin defined as the top-left corner of the parent image"""
#
#     x: int
#     y: int


# Refactored:
# This class is now in hdic.types.image
# class ScanWindow(NamedTuple):
#     """search window within a reference image as defined by distance (in pixels) from the top-left corner of a subset in a moving image."""
#
#     left: int
#     right: int
#     top: int
#     bottom: int


# Refactored:
# This class is now in hdic.types.methods
# class CrossCorrelationMethod(StrEnum):
#     """Cross-correlation method.
#     A good overlap of images will maximize this value.
#
#     See Pan, Xie, et. al, Applied Optics, 2010 for discussion of methods."""
#
#     ZNCC: str = "ZNCC"  # https://en.wikipedia.org/wiki/Cross-correlation#Zero-normalized_cross-correlation_(ZNCC)
#     ZCC: str = "ZCC"
#     NCC: str = "NCC"
#     CC: str = "CC"


# class SumSquaredDifferencesMethod(StrEnum):
#     """Sum of Squared Differences method.
#     A good overlap of images will minimize this value
#
#     See Pan, Xie, et. al, Applied Optics, 2010 for discussion of methods.
#     """
#
#     SSD: str = "SSD"
#     ZSSD: str = "ZSSD"
#     NSSD: str = "NSSD"
#     ZNSSD: str = "ZNSSD"
#     PSSD_a: str = "PSSD_a"
#     PSSD_b: str = "PSSD_b"
#     PSSD_ab: str = "PSSD_ab"


# Refactored:
# This class is now in hdic.types.image
# class Subset(NamedTuple):
#     width: int
#     height: int
#     origin: PixelCoordinate


# Refactored:
# This class is now in hdic.types.experiment
# class Result(NamedTuple):
#     num_correlations: int
#     output: str
#     error_fraction: float  # 0 to 1
#     calc_time: float  # seconds
#     validation_time: float


def preprocess(
    data: np.array,
    method: CrossCorrelationMethod | SumSquaredDifferencesMethod,
) -> NDArray:
    """Preparatory processing of raw image data depending on correlation method"""

    match method:
        case CrossCorrelationMethod.CC:
            return data
        case CrossCorrelationMethod.ZCC:
            return data - np.mean(data)
        case CrossCorrelationMethod.NCC:
            return data / np.std(data)
        case CrossCorrelationMethod.ZNCC:
            return (data - np.mean(data)) / np.std(data)


def image_aoi(
    image_path: Path,
    window: ScanWindow,
    preprocess_method: CrossCorrelationMethod | SumSquaredDifferencesMethod,
    center: PixelCoordinate,
) -> NDArray:
    """Extract an Area of Interest (AOI) from an image or tile"""
    image = Image.open(image_path)
    filtered = preprocess(
        data=np.array(image),
        method=preprocess_method,
    )
    aoi = filtered[
        center.y - window.top : center.y + window.bottom,
        center.x - window.left : center.x + window.right,
    ]

    if (
        aoi.shape[0] != window.top + window.bottom
        or aoi.shape[1] != window.left + window.right
    ):
        raise ValueError("Area of Interest not created correctly.")

    return aoi


def test_case_subsets(
    num_correlations: int,
    center: Subset,
    data: NDArray,
    x_shifts: NDArray,
    y_shifts: NDArray,
) -> NDArray:
    """TODO: documentation."""
    # take subsets from shifted center of moving tile
    # here we treat each subset as a separate kernel with channel_length=1
    subsets = np.empty(shape=(num_correlations, 1, center.height, center.width))
    for i in range(num_correlations):
        start_idx_y = center.origin.y + y_shifts[i]
        start_idx_x = center.origin.x + x_shifts[i]

        subset = data[
            start_idx_y : start_idx_y + center.height,
            start_idx_x : start_idx_x + center.width,
        ]
        subsets[i, :, :, :] = np.expand_dims(subset, axis=0)
    return subsets


def test_case_data(
    tile_path: Path,
    window: ScanWindow,
    preprocess_method: CrossCorrelationMethod | SumSquaredDifferencesMethod,
    aoi_center: PixelCoordinate,
    num_correlations: int,
    subset: Subset,
) -> list[NDArray, NDArray, NDArray, NDArray]:
    """TODO: Documentation."""
    aoi = image_aoi(
        image_path=tile_path,
        window=window,
        preprocess_method=preprocess_method,
        center=aoi_center,
    )
    moving_image = aoi  # duplicate for test case
    y_shifts = np.random.randint(
        -window.top,
        window.bottom - subset.height + 1,
        size=num_correlations,
    )
    x_shifts = np.random.randint(
        -window.left,
        window.right - subset.width + 1,
        size=num_correlations,
    )

    subsets = test_case_subsets(
        num_correlations=num_correlations,
        center=subset,
        data=moving_image,
        x_shifts=x_shifts,
        y_shifts=y_shifts,
    )

    # replicate, expand and stack to number of correlations
    # here we treat each separate aoi as a new channel to leverage pytorch speed so batch size is actually the number of channels in the tensor
    aois = np.tile(aoi, (1, num_correlations, 1, 1))  # only repeat only dim = 1

    return aois, subsets, x_shifts, y_shifts


def pytorch_xcorr(
    aois: NDArray,
    subsets: NDArray,
    window: ScanWindow,
    subset: Subset,
    known_shift_indices: list,
    device: torch.device,
) -> Result:
    """TODO: Documentation."""
    # convert numpy array to tensors
    aois = torch.from_numpy(aois)  # overwrite
    subsets = torch.from_numpy(subsets)  # overwrite
    # measure execution time
    start_time = time.time()
    # send data to device
    if device == torch.device("cuda"):
        aois = aois.to(device)
        subsets = subsets.to(device)
    # use the groups functionality and correct tensor shaping from above in order to leverage parallelization under the hood without having to do a for loop. We only want to apply each subset kernel to one aoi. Calling without groups parameter would correlate each subset kernel to each aoi, so we rearrange batches and channels in the inputs to avoid this.
    convolution = F.conv2d(aois, subsets, groups=aois.size(1))

    if device == torch.device("cuda"):
        torch.cuda.synchronize()
    end_time = time.time()

    calc_time = end_time - start_time

    validation_time_start = time.time()
    error_fraction, accuracy_msg = correlation_accuracy(
        data=convolution,
        window=window,
        subset=subset,
        known_shift_indices=known_shift_indices,
    )
    validation_time_end = time.time()
    validation_time = validation_time_end - validation_time_start

    result = Result(
        num_correlations=len(known_shift_indices),
        output=accuracy_msg,
        error_fraction=error_fraction,
        calc_time=calc_time,
        validation_time=validation_time,
    )

    return result


def correlation_accuracy(
    data: torch.Tensor | NDArray,
    window: ScanWindow,
    subset: Subset,
    known_shift_indices: list,
) -> Tuple[float, str]:
    """TODO: documentation."""
    found_shift_indices = []
    match data:
        case _ if isinstance(data, torch.Tensor):
            # Loop over the second dimension (channel dimension)
            for i in range(data.size(1)):  # Iterate over channels (dimension 1)
                # Find the max value and its index for the spatial dimensions (81x81)
                _max_value = torch.max(data[:, i, :, :])  # Find the max value
                max_index = torch.argmax(
                    data[:, i, :, :]
                )  # Find the flattened index of the max value

                # Convert the flattened index to 2D spatial indices (row, col)
                row, col = divmod(
                    max_index.item(), data.size(3)
                )  # tensor.size(3) is the width (81)
                # Now convert the row and column into pixel shifts from the center of the aoi, not from the top left corner
                row -= window.top
                col -= window.left

                # Append the pair of indices (row, col) to the list
                found_shift_indices.append((row, col))
        case _ if isinstance(data, np.ndarray):
            pass

    msg = "\n\tSearch window:"
    msg += f"\n\t\tleft:\t{window.left} pixels"
    msg += f"\n\t\tright:\t{window.right} pixels"
    msg += f"\n\t\ttop:\t{window.top} pixels"
    msg += f"\n\t\tbottom:\t{window.bottom} pixels"
    msg += "\n\tSubset size:"
    msg += f"\n\t\twidth:\t{subset.width} pixels"
    msg += f"\n\t\theight:\t{subset.height} pixels"
    if found_shift_indices == known_shift_indices:
        output = f"Good subset size and search window, expected shifts found!{msg}\n"
        error_fraction = 0
    else:
        error_count = 0
        for i in range(len(known_shift_indices)):
            if known_shift_indices[i] != found_shift_indices[i]:
                error_count += 1
                # print(
                #     f"Known: {known_shift_indices[i]}, Found: {found_shift_indices[i]}"
                # )
        error_fraction = error_count / len(known_shift_indices)
        msg += f"\n\t\Error Rate:\t{error_fraction * 100}% ({error_count} of {len(known_shift_indices)})"
        output = f"Bad subset size or search window{msg}"

    return error_fraction, output


def warm_up(device: torch.device) -> None:
    """TODO: Documentation."""
    num_correlations = 10
    # create the data
    tile_path = Path(__file__).parent.parent.parent.joinpath(
        "test_data", "test_tile.tif"
    )
    print(f"Device warmup: {device}")
    print(f"  with test image: {tile_path}")
    window = ScanWindow(
        top=20,
        bottom=20,
        left=20,
        right=20,
    )
    preprocess_method = CrossCorrelationMethod.ZNCC
    aoi_center = PixelCoordinate(x=100, y=100)
    subset = Subset(
        width=5, height=5, origin=PixelCoordinate(x=window.left, y=window.top)
    )

    aois, subsets, x_shifts, y_shifts = test_case_data(
        tile_path=tile_path,
        window=window,
        preprocess_method=preprocess_method,
        aoi_center=aoi_center,
        num_correlations=num_correlations,
        subset=subset,
    )

    known_shift_indices = list(zip(y_shifts.tolist(), x_shifts.tolist()))

    # do pytorch approach
    _result = pytorch_xcorr(
        aois=aois,
        subsets=subsets,
        window=window,
        subset=subset,
        known_shift_indices=known_shift_indices,
        device=device,
    )
    # print(f"  {result.output}")


if __name__ == "__main__":
    # method = exp.Device.GPU
    method = exp.Device.CPU

    # methods = [exp.Device.GPU, exp.Device.CPU]
    methods = [exp.Device.CPU]
    for method in methods:
        if method == exp.Device.GPU:
            if torch.cuda.is_available():
                device = torch.device("cuda")
                correlation_amounts = [10**x for x in range(1, 5)]
                # correlation_amounts.extend([12_000, 15_000, 20_000, 50_000])
            else:
                msg = "GPU is specified but not available."
                # raise ValueError(msg)
        if method == exp.Device.CPU:
            device = torch.device("cpu")
            correlation_amounts = [10**x for x in range(1, 5)]
            # correlation_amounts.extend([12_000, 15_000, 20_000, 50_000])

        warm_up(device=device)

        correlation_amounts = [1_000 + 500 * x for x in range(0, 19)]
        correlation_amounts.extend([10_000 + 500 * x for x in range(1, 11)])
        correlation_amounts.extend([16_000 + 1000 * x for x in range(0, 10)])
        correlation_amounts.extend([27_500 + x * 2500 for x in range(0, 10)])

        # correlation_amounts = [1000, 2000, 3000]
        # print(correlation_amounts)

        execution_times = []
        creation_times = []
        validation_times = []
        total_times = []
        error_rates = []

        # subset_size = 35
        SUBSET_SIZE: Final[int] = 35

        num_correlations = 10_000
        subset_sizes = np.arange(3, 50 + 1)
        print(subset_sizes)
        # for num_correlations in correlation_amounts:
        for subset_size in subset_sizes:
            total_start_time = time.time()
            # print(f"Num Correlations: {num_correlations}")

            # create the data
            tile_path = Path(__file__).parent.parent.parent.joinpath(
                "test_data",
                "msem_test_tile.tif",  # "test_tile.tif"
            )
            window = ScanWindow(
                top=60,
                bottom=60,
                left=60,
                right=60,
            )
            preprocess_method = CrossCorrelationMethod.ZNCC
            aoi_center = PixelCoordinate(x=100, y=100)
            subset = Subset(
                width=SUBSET_SIZE,
                height=SUBSET_SIZE,
                origin=PixelCoordinate(x=window.left, y=window.top),
            )

            start_time = time.time()
            aois, subsets, x_shifts, y_shifts = test_case_data(
                tile_path=tile_path,
                window=window,
                preprocess_method=preprocess_method,
                aoi_center=aoi_center,
                num_correlations=num_correlations,
                subset=subset,
            )

            known_shift_indices = list(zip(y_shifts.tolist(), x_shifts.tolist()))

            end_time = time.time()
            creation_time = end_time - start_time
            creation_times.append(creation_time)

            # do pytorch approach
            result = pytorch_xcorr(
                aois=aois,
                subsets=subsets,
                window=window,
                subset=subset,
                known_shift_indices=known_shift_indices,
                device=device,
            )
            total_end_time = time.time()
            total_time = total_end_time - total_start_time
            total_times.append(total_time)
            execution_times.append(result.calc_time)
            validation_times.append(result.validation_time)
            error_rates.append(result.error_fraction)
            # print(
            #     f"\tExecution time: {result.calc_time:.6f} seconds, Error Rate: {result.error_fraction*100}%"
            # )
            # print({result.output})
        print(f"Device: {device}")
        print("Correlation amounts:")
        print(correlation_amounts)
        print("Array creation times:")
        print(creation_times)
        print("XCorr times:")
        print(execution_times)
        print("Validation times:")
        print(validation_times)
        print("Total times:")
        print(total_times)
        print("Error rates (fraction):")
        print(error_rates)
