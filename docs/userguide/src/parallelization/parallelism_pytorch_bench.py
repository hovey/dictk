"""Parallelism with PyTorch: rerun Timing at Scale's own ladder on a
batched PyTorch correlation, on this machine (Apple M1 Pro, 32GB RAM,
10 cores -- see parallelism_pytorch.md's own Test Machine section),
across every device this machine offers.

Timing at Scale (9.3) tracked one point per `dictk.grid.locate_subpixel`
call, and every call ran its own FFT. This script replaces that inner
loop entirely. It stacks many search windows into one tensor, many
kernels into another, and correlates all of them in a single
`F.conv2d` call -- the grouped-convolution trick hdic's own
`xcorr_pytorch.py` established (see parallelism_pytorch.md for the
attribution and the shape derivation).

Not part of the dictk package -- a standalone, one-time measurement
script, matching timing_at_scale_bench.py's and parallelization_bench.py's
own precedent. Its output (parallelism_pytorch_bench.csv,
parallelism_pytorch_bench.png) is committed alongside it rather than
regenerated on every book build.

dictk itself does not depend on PyTorch, and this script does not change
that. It guards its own imports and exits with a message rather than a
traceback when torch is missing. See torch_require below.

Geometry is imported from timing_at_scale_bench, never redefined here.
Same kernel margin, same stretch factor, same origin fraction, same
spacing, same rosta parameters, same geometric ladder. A number this
script produces is only comparable to 9.3's if the geometry underneath
it is identical, so it is taken from 9.3's own module rather than
copied.

Stopping rules (read before changing the ladder): 9.3's own 1800-second
per-tier wall clock is NOT reused. macOS gives no catchable MemoryError,
so 9.3 had no better option. A GPU does: it raises a real, catchable
out-of-memory exception. This script therefore stops on three
conditions, in priority order --

  1. A caught out-of-memory error. Search windows are chunkable, so
     chunking alone never runs out. The two full images are not
     chunkable; both stay resident for the whole size. That unchunkable
     residency is what eventually fails, and _memory_predict reports the
     prediction before each size so the measurement can confirm or
     contradict it.
  2. The predicted-cost gate. Compute grows faster than memory here, so
     the ladder turns impractical before it turns impossible. Each size
     predicts its own cost from the PREVIOUS size's measured throughput.
     A prediction past COST_BUDGET_S stops that device, and the
     prediction is written to the CSV with the throughput it came from.
  3. WATCHDOG_S, a harness safety net only. It exists so an unattended
     run cannot hang forever on a wedged GPU driver. It is set far past
     anything the cost gate would allow. If it ever fires, that is a
     harness problem to investigate, not a finding about scaling --
     unlike 9.3, where the timeout WAS the finding.

Must be a real module, not `python3 -c` -- the controller re-invokes
this same file as a subprocess per (width, device).

Re-run with: python3 parallelism_pytorch_bench.py
Run the correctness gates alone:
    python3 parallelism_pytorch_bench.py --check
Re-run a single (width, device) directly:
    python3 parallelism_pytorch_bench.py --worker 3149 mps
"""

import csv
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from dictk.grid import generate, locate, locate_subpixel
from dictk.image import PixelCoordinate, stretch
from dictk.rosta import rosta

# Geometry comes from 9.3's own module, never redefined here -- see the
# module docstring for why. Importing it also keeps this script honest if
# 9.3's ladder is ever retuned: both pages move together, or neither does.
import timing_at_scale_bench as bench

CSV_PATH = Path(__file__).parent / "parallelism_pytorch_bench.csv"
PNG_PATH = Path(__file__).parent / "parallelism_pytorch_bench.png"
TIMING_CSV = Path(__file__).parent / "timing_at_scale_bench.csv"

DEVICES = ("cpu", "mps", "cuda")

# Chunk budget, in GB of device allocation per batch. Deliberately well
# under this machine's own ~26.8GB MPS working set: the two full images
# stay resident for the whole size on top of whatever a chunk holds, and
# a chunk allocates its windows, its correlation surfaces, and its
# kernels all at once. 4GB leaves room for all of that at every size the
# ladder reaches.
CHUNK_BUDGET_GB = 4.0

# Predicted-cost gate. A size whose predicted wall time exceeds this,
# extrapolated from the previous size's own measured throughput, is not
# attempted -- the prediction is recorded instead. One hour is a
# deliberate choice, not a tuned constant: it is long enough that every
# size the ladder can actually finish gets measured, and short enough
# that the two sizes past this machine's practical limit (roughly 10
# hours and 104 hours of arithmetic, by the FLOP estimate on the page)
# are reported rather than run.
COST_BUDGET_S = 3600.0

# Harness safety net ONLY -- see the module docstring's own stopping-rules
# note. This must never be the reason a result is reported. Four hours is
# far past COST_BUDGET_S, so a size that fires this one has hung rather
# than merely run long.
WATCHDOG_S = 4 * 3600


def torch_require():
    """Imports torch, or exits with a message instead of a traceback.

    dictk does not depend on PyTorch. This script does. A missing
    install is an ordinary, expected situation for someone reading the
    book, so it gets an explanation rather than an ImportError.
    """
    try:
        import torch
        import torch.nn.functional as functional
    except ImportError:
        print(
            "PyTorch is required to run this benchmark, and is not installed.\n"
            "\n"
            "dictk itself does not depend on PyTorch. This standalone\n"
            "benchmark script does, and it is the only thing in the book\n"
            "that does.\n"
            "\n"
            "Install it with:\n"
            "    uv pip install torch\n"
            "\n"
            "Platform-specific builds (CUDA, ROCm, CPU-only):\n"
            "    https://pytorch.org/get-started/locally/",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return torch, functional


def device_select(*, prefer: str):
    """Resolves `prefer` to a real torch device, or exits explaining why
    it cannot.

    Returns `(device, sync)`. `sync` blocks until queued work on that
    device has actually finished. GPU work is submitted asynchronously,
    so a timer that doesn't call it measures queue submission rather
    than computation.

    This never silently falls back to CPU. hdic's own xcorr_pytorch.py
    fell back with a printed warning, which is how a CPU measurement
    ends up labeled as a GPU one. A results table that mislabels its own
    device is worse than a missing row.
    """
    torch, _ = torch_require()

    # No machine ever offers both accelerators. "mps" is macOS only, and
    # only on Apple silicon (M1 and later) -- never Linux, never Windows,
    # not even an Intel Mac. "cuda" needs an NVIDIA card, which in practice
    # means Linux or Windows, since Apple dropped NVIDIA support years ago.
    # "cpu" is the only entry every platform always has.
    available = ["cpu"]
    if torch.backends.mps.is_available():
        available.append("mps")
    if torch.cuda.is_available():
        available.append("cuda")

    if prefer not in available:
        if prefer == "mps":
            why = (
                "this machine is not Apple silicon, or this torch build\n"
                "  has no Metal support"
                if not torch.backends.mps.is_built()
                else "torch was built with Metal support, but no MPS device\n"
                "  is available here"
            )
        elif prefer == "cuda":
            why = "no CUDA device is visible to torch on this machine"
        else:
            why = "unrecognized device name"
        print(
            f"Device '{prefer}' was requested and is not available.\n"
            f"  Reason: {why}\n"
            f"  This machine offers: {', '.join(available)}\n"
            f"  Platform: {platform.platform()}\n"
            f"  torch: {torch.__version__}\n"
            "\n"
            "Not falling back to another device -- a timing labeled with\n"
            "the wrong device would corrupt this benchmark's own results.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    device = torch.device(prefer)
    if prefer == "cuda":
        sync = torch.cuda.synchronize
    elif prefer == "mps":
        sync = torch.mps.synchronize
    else:

        def sync():
            return None

    return device, sync


def device_budget_gb(*, prefer: str) -> float:
    """How much memory this device will admit, in GB.

    MPS reports a recommended working set rather than the full unified
    pool -- Metal will refuse allocations past it even though the host
    has more RAM installed. CUDA reports its own card's total. CPU falls
    back to installed system memory.
    """
    torch, _ = torch_require()
    if prefer == "mps":
        return torch.mps.recommended_max_memory() / 1e9
    if prefer == "cuda":
        return torch.cuda.mem_get_info()[1] / 1e9
    if platform.system() == "Darwin":
        out = subprocess.run(
            ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True
        )
        return int(out.stdout.strip()) / 1e9
    return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9


def bytes_per_point(*, search: int, kernel: int) -> int:
    """Device bytes one point costs inside a chunk, as float32.

    Three allocations, not one: its search window, the correlation
    surface that window produces, and its kernel. The surface is nearly
    as large as the window itself, so counting only the window
    underestimates a chunk by roughly half.
    """
    out = search - kernel + 1
    return 4 * (search * search + out * out + kernel * kernel)


def chunk_size_for(*, search: int, kernel: int, budget_gb: float) -> int:
    """Largest point count whose chunk fits `budget_gb`."""
    return max(1, int(budget_gb * 1e9 // bytes_per_point(search=search, kernel=kernel)))


def image_resident_gb(*, width: int) -> float:
    """Device GB the two full images occupy, as float32.

    This is the part of the problem chunking cannot shrink. Both images
    stay resident for an entire size, because every chunk extracts its
    windows from them. When this alone exceeds the device budget, the
    size is impossible at any chunk size.
    """
    return 2 * width * width * 4 / 1e9


def _peak_rss_gb() -> float:
    """Peak resident set size so far, in GB. macOS reports ru_maxrss in
    bytes; Linux reports it in KB."""
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / 1e9 if platform.system() == "Darwin" else raw * 1024 / 1e9


def _append_row(
    *,
    width: int,
    points: int,
    device: str,
    chunk: int,
    stage: str,
    seconds: float,
    peak_rss_gb: float,
    note: str = "",
) -> None:
    """Appends and flushes one CSV row immediately -- not batched -- so a
    later crash loses nothing already measured. Same approach 9.3 used,
    for the same reason."""
    is_new = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(
                [
                    "width",
                    "points",
                    "device",
                    "chunk",
                    "stage",
                    "seconds",
                    "peak_rss_gb",
                    "note",
                ]
            )
        writer.writerow(
            [
                width,
                points,
                device,
                chunk,
                stage,
                f"{seconds:.6f}",
                f"{peak_rss_gb:.4f}",
                note,
            ]
        )
        f.flush()
        os.fsync(f.fileno())


def images_build(*, width: int) -> tuple[np.ndarray, np.ndarray]:
    """Reference and current image at this size, exactly as 9.3 built
    them: pure rosta speckle, rescaled dot size, 2% stretch in x."""
    dot_size, smoothness = bench.rosta_params_for(width)
    reference_image = rosta(
        width=width,
        height=width,
        dot_size=dot_size,
        smoothness=smoothness,
        density=bench.DENSITY,
    )
    current_image = stretch(arr=reference_image, factor_x=bench.FACTOR_X)
    return reference_image, current_image


def image_upload(*, image: np.ndarray, pad: int, device):
    """Uploads one image to the device, padded, as float32. Once.

    This is the allocation the memory section of parallelism_pytorch.md
    calls unchunkable. It is deliberately hoisted out of the chunk loop:
    a first version of this script rebuilt it inside `windows_extract`,
    which re-converted and re-uploaded the entire image twice per chunk.
    At the 3149px size that is 26 redundant uploads of a 40MB array, and
    it inflated the measured extraction cost by a wide margin. Build it
    once per size, index it many times.

    `pad` zero-fills a border wide enough that a window straddling an
    edge reads zeros rather than wrapping or raising. That matches
    `dictk.image.subimage`, which zero-fills outside the image, so a
    point near a border tracks the same way here as it does everywhere
    else in this book.
    """
    torch, functional = torch_require()
    return functional.pad(
        torch.from_numpy(np.ascontiguousarray(image)).to(torch.float32),
        (pad, pad, pad, pad),
    ).to(device)


def windows_extract(*, resident, origins_x, origins_y, size: int, pad: int):
    """Stacks one `size` x `size` window per origin into a single
    `(N, size, size)` tensor, cut from an already-resident padded image.

    The gather is advanced indexing, not a Python loop. This is the step
    that allocates a chunk's largest tensor, and on real DIC geometry it
    copies heavily overlapping data -- neighboring windows at 5px spacing
    share almost every pixel.
    """
    torch, _ = torch_require()
    device = resident.device
    rows = (origins_y + pad).reshape(-1, 1) + torch.arange(size, device=device)
    cols = (origins_x + pad).reshape(-1, 1) + torch.arange(size, device=device)
    return resident[rows[:, :, None], cols[:, None, :]]


def batch_correlate(*, kernels, windows):
    """Correlates each kernel against its own search window, in one call.

    Shapes, for N points, a `K` x `K` kernel and an `S` x `S` search
    window:

        windows -> (1, N, S, S)   N windows stacked as CHANNELS
        kernels -> (N, 1, K, K)   N kernels as N separate groups
        output  -> (1, N, S-K+1, S-K+1)

    `groups=N` is the load-bearing argument. It splits the N input
    channels into N groups of one, so kernel `i` sees window `i` and
    nothing else. Without it, conv2d would compute the full N x N cross
    product -- every kernel against every window -- which is both wrong
    and N times more work.

    `conv2d` is already cross-correlation. It does not flip the kernel
    the way a mathematical convolution does, so no flip is needed here.

    Both inputs are normalized to zero mean and unit standard deviation
    beforehand, once per window and once per kernel. That is hdic's own
    approach, and it makes a plain correlation behave like ZNCC. It is
    an approximation: true ZNCC recomputes local statistics at every
    sliding position, which costs two more conv2d passes. See
    parallelism_pytorch.md for what that approximation measurably costs.
    """
    _, functional = torch_require()
    kernels = (kernels - kernels.mean((1, 2), keepdim=True)) / kernels.std(
        (1, 2), keepdim=True
    ).clamp_min(1e-12)
    windows = (windows - windows.mean((1, 2), keepdim=True)) / windows.std(
        (1, 2), keepdim=True
    ).clamp_min(1e-12)
    return functional.conv2d(
        windows.unsqueeze(0), kernels.unsqueeze(1), groups=windows.shape[0]
    )[0]


def peaks_locate(*, surfaces):
    """Integer peak of every correlation surface, as `(rows, cols)`."""
    flat = surfaces.reshape(surfaces.shape[0], -1).argmax(dim=1)
    width = surfaces.shape[-1]
    return flat // width, flat % width


def peak_refine(*, surfaces, rows, cols):
    """Fractional offset of each peak, by a three-point parabolic fit.

    conv2d returns the whole correlation surface, not just its peak. The
    peak's true position is generally between samples, and fitting a
    parabola through the peak and its two neighbours recovers where:

        delta = 0.5 * (C[-1] - C[+1]) / (C[-1] - 2 C[0] + C[+1])

    applied independently per axis. One gather of each peak's
    neighbourhood, then arithmetic -- it batches exactly like the
    correlation does, and costs a small fraction of it.

    A parabolic fit exhibits peak locking: it pulls estimates slightly
    toward integer positions. parallelism_pytorch.md measures that bias
    directly rather than assuming its size.

    Peaks on a surface's own border have no neighbour on one side. Those
    are clamped inward, which biases them, but a peak on the border
    already means the search area was too small for that point.
    """
    torch, _ = torch_require()
    height, width = surfaces.shape[-2], surfaces.shape[-1]
    rows_in = rows.clamp(1, height - 2)
    cols_in = cols.clamp(1, width - 2)
    index = torch.arange(surfaces.shape[0], device=surfaces.device)

    def at(row_offset, col_offset):
        return surfaces[index, rows_in + row_offset, cols_in + col_offset]

    def delta(minus, center, plus):
        denominator = minus - 2 * center + plus
        return torch.where(
            denominator.abs() < 1e-12,
            torch.zeros_like(denominator),
            0.5 * (minus - plus) / denominator,
        )

    center = at(0, 0)
    return (
        delta(at(-1, 0), center, at(1, 0)),
        delta(at(0, -1), center, at(0, 1)),
    )


def track_batched(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    points,
    kernel_margin: int,
    search_margin: int,
    device_name: str,
    chunk: int,
    refine: bool = True,
):
    """Tracks every point through batched correlation, one chunk at a time.

    Returns `(xs, ys, timings)`. `timings` splits the work into `upload`,
    `extract`, `correlate` and `refine`. `upload` happens once per size;
    the other three are summed across chunks. That split is the point:
    the earlier work's own measurements found tensor creation costing five
    times what the correlation cost, and a single total would have hidden
    it completely.
    """
    torch, _ = torch_require()
    device, sync = device_select(prefer=device_name)

    kernel = 2 * kernel_margin
    search = 2 * search_margin
    xs = np.empty(len(points), dtype=np.float64)
    ys = np.empty(len(points), dtype=np.float64)
    timings = {"upload": 0.0, "extract": 0.0, "correlate": 0.0, "refine": 0.0}

    # Both images go to the device once, before any chunk runs. See
    # image_upload's own docstring for what building them per chunk
    # cost instead.
    sync()
    mark = time.perf_counter()
    reference_resident = image_upload(image=reference_image, pad=search, device=device)
    current_resident = image_upload(image=current_image, pad=search, device=device)
    points_x = torch.tensor([p.x for p in points], device=device)
    points_y = torch.tensor([p.y for p in points], device=device)
    sync()
    timings["upload"] += time.perf_counter() - mark

    for start in range(0, len(points), chunk):
        stop = min(start + chunk, len(points))
        chunk_x = points_x[start:stop]
        chunk_y = points_y[start:stop]

        sync()
        mark = time.perf_counter()
        kernels = windows_extract(
            resident=reference_resident,
            origins_x=chunk_x - kernel_margin,
            origins_y=chunk_y - kernel_margin,
            size=kernel,
            pad=search,
        )
        windows = windows_extract(
            resident=current_resident,
            origins_x=chunk_x - search_margin,
            origins_y=chunk_y - search_margin,
            size=search,
            pad=search,
        )
        sync()
        timings["extract"] += time.perf_counter() - mark

        mark = time.perf_counter()
        surfaces = batch_correlate(kernels=kernels, windows=windows)
        rows, cols = peaks_locate(surfaces=surfaces)
        sync()
        timings["correlate"] += time.perf_counter() - mark

        mark = time.perf_counter()
        if refine:
            row_delta, col_delta = peak_refine(surfaces=surfaces, rows=rows, cols=cols)
        else:
            row_delta = torch.zeros_like(rows, dtype=torch.float32)
            col_delta = torch.zeros_like(cols, dtype=torch.float32)
        found_x = (chunk_x - search_margin + cols + kernel_margin) + col_delta
        found_y = (chunk_y - search_margin + rows + kernel_margin) + row_delta
        sync()
        timings["refine"] += time.perf_counter() - mark

        xs[start:stop] = found_x.to("cpu").numpy()
        ys[start:stop] = found_y.to("cpu").numpy()

        del kernels, windows, surfaces
        if device_name == "mps":
            torch.mps.empty_cache()
        elif device_name == "cuda":
            torch.cuda.empty_cache()

    return xs, ys, timings


# Metal reports running out of memory in more than one way, and only one
# of them says "out of memory". A request past the allocator's remaining
# budget raises "MPS backend out of memory (MPS allocated: ..., max
# allowed: ...)". A single tensor past Metal's own per-buffer ceiling
# raises "Invalid buffer size: 3013.73 GiB" instead, which never uses the
# phrase at all. Both mean the same thing here -- the device would not
# give us the memory -- so both belong in this list. Found by deliberately
# forcing an oversized allocation rather than by trusting the first
# message to be the only one.
_OUT_OF_MEMORY_PHRASES = (
    "out of memory",
    "invalid buffer size",
    "can't allocate memory",
)


def _is_out_of_memory(error: BaseException) -> bool:
    """Whether `error` is a device out-of-memory report.

    CUDA raises a dedicated class. Metal raises a plain RuntimeError
    whose message names the condition, so on that backend the message
    text is the only signal available.
    """
    torch, _ = torch_require()
    if isinstance(error, getattr(torch, "OutOfMemoryError", ())):
        return True
    if not isinstance(error, RuntimeError):
        return False
    message = str(error).lower()
    return any(phrase in message for phrase in _OUT_OF_MEMORY_PHRASES)


def checks_run(*, width: int = bench.BASE_WIDTH) -> None:
    """Correctness gates. These run before any timing is trusted.

    Two questions, kept separate. Does the batched correlation find the
    same integer positions dictk.grid.locate already finds? And how close
    does the refined position land to the analytically known truth,
    compared with dictk.grid.locate_subpixel?
    """
    torch, _ = torch_require()
    reference_image, current_image = images_build(width=width)
    origin, count, search_margin = bench.grid_params(width)
    kernel_margin = bench.KERNEL_MARGIN
    points = generate(
        origin=PixelCoordinate(x=origin, y=origin),
        count_x=count,
        count_y=count,
        spacing_x=bench.SPACING,
        spacing_y=bench.SPACING,
    )
    truth_x = np.array([p.x for p in points], dtype=np.float64) * bench.FACTOR_X

    integer = locate(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=search_margin,
        search_margin_height=search_margin,
    )
    subpixel = locate_subpixel(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=search_margin,
        search_margin_height=search_margin,
        upsample_factor=bench.UPSAMPLE_FACTOR,
    )
    locate_x = np.array([p.x for p in integer], dtype=np.float64)
    locate_y = np.array([p.y for p in integer], dtype=np.float64)
    subpixel_x = np.array([p.x for p in subpixel], dtype=np.float64)

    chunk = chunk_size_for(
        search=2 * search_margin,
        kernel=2 * kernel_margin,
        budget_gb=CHUNK_BUDGET_GB,
    )

    print(f"Correctness gates at width={width}, {len(points):,} points")
    print(
        f"  kernel {2 * kernel_margin}x{2 * kernel_margin}, "
        f"search {2 * search_margin}x{2 * search_margin}, chunk {chunk:,}"
    )
    print(
        f"  grid.locate_subpixel MAE vs truth: "
        f"{np.abs(subpixel_x - truth_x).mean():.4f} px"
    )

    for device_name in DEVICES:
        try:
            device_select(prefer=device_name)
        except SystemExit:
            print(f"  {device_name}: unavailable, skipped")
            continue

        integer_x, integer_y, _ = track_batched(
            reference_image=reference_image,
            current_image=current_image,
            points=points,
            kernel_margin=kernel_margin,
            search_margin=search_margin,
            device_name=device_name,
            chunk=chunk,
            refine=False,
        )
        agree = int(((integer_x == locate_x) & (integer_y == locate_y)).sum())
        disagree = integer_x != locate_x
        fractional = np.abs(truth_x - np.floor(truth_x))

        refined_x, _, _ = track_batched(
            reference_image=reference_image,
            current_image=current_image,
            points=points,
            kernel_margin=kernel_margin,
            search_margin=search_margin,
            device_name=device_name,
            chunk=chunk,
            refine=True,
        )
        error = np.abs(refined_x - truth_x)
        parts = refined_x - np.floor(refined_x)
        histogram, _ = np.histogram(parts, bins=10, range=(0.0, 1.0))

        print(f"  {device_name}:")
        print(
            f"    integer agreement with grid.locate: {agree:,}/{len(points):,} "
            f"({100 * agree / len(points):.1f}%)"
        )
        if disagree.any():
            print(
                f"    disagreeing points' true fractional part: "
                f"{fractional[disagree].min():.3f}..{fractional[disagree].max():.3f} "
                f"(mean {fractional[disagree].mean():.3f})"
            )
        print(f"    refined MAE vs truth: {error.mean():.4f} px")
        print(
            f"    fractional-part histogram (flat would be "
            f"{len(points) // 10:,} each): {histogram.tolist()}"
        )


def work_units(*, width: int) -> float:
    """Multiply-accumulates one size costs, as a scaling proxy.

    Point count alone is the wrong predictor here. 9.3's ladder grows the
    search area alongside the point count, because a 2% stretch displaces
    a far edge further in a larger image (see Timing at Scale's own
    geometry table). Work per point therefore grows too. This counts
    both: output positions per point, times kernel pixels, times points.
    """
    _, count, search_margin = bench.grid_params(width)
    kernel = 2 * bench.KERNEL_MARGIN
    outputs = (2 * search_margin - kernel + 1) ** 2
    return float(count * count) * outputs * kernel * kernel


def size_run(*, width: int, device_name: str) -> None:
    """Runs one (width, device) rung and appends its rows.

    Records the memory prediction first, then attempts the size anyway.
    A prediction only earns its place if the measurement gets a chance to
    contradict it.
    """
    device_select(prefer=device_name)
    budget = device_budget_gb(prefer=device_name)
    resident = image_resident_gb(width=width)
    origin, count, search_margin = bench.grid_params(width)
    points_total = count * count
    chunk = chunk_size_for(
        search=2 * search_margin,
        kernel=2 * bench.KERNEL_MARGIN,
        budget_gb=CHUNK_BUDGET_GB,
    )

    _append_row(
        width=width,
        points=points_total,
        device=device_name,
        chunk=chunk,
        stage="predict_memory",
        seconds=float("nan"),
        peak_rss_gb=_peak_rss_gb(),
        note=f"images {resident:.2f}GB of {budget:.2f}GB budget"
        + (" EXCEEDS" if resident > budget else ""),
    )

    mark = time.perf_counter()
    reference_image, current_image = images_build(width=width)
    _append_row(
        width=width,
        points=0,
        device=device_name,
        chunk=chunk,
        stage="images",
        seconds=time.perf_counter() - mark,
        peak_rss_gb=_peak_rss_gb(),
    )

    points = generate(
        origin=PixelCoordinate(x=origin, y=origin),
        count_x=count,
        count_y=count,
        spacing_x=bench.SPACING,
        spacing_y=bench.SPACING,
    )

    mark = time.perf_counter()
    try:
        found_x, _, timings = track_batched(
            reference_image=reference_image,
            current_image=current_image,
            points=points,
            kernel_margin=bench.KERNEL_MARGIN,
            search_margin=search_margin,
            device_name=device_name,
            chunk=chunk,
        )
    except Exception as error:  # noqa: BLE001 -- re-raised below unless OOM
        if not _is_out_of_memory(error):
            raise
        _append_row(
            width=width,
            points=points_total,
            device=device_name,
            chunk=chunk,
            stage="FAILED_oom",
            seconds=time.perf_counter() - mark,
            peak_rss_gb=_peak_rss_gb(),
            note=str(error).replace("\n", " ")[:300],
        )
        print(f"  {device_name} @{width}px: OUT OF MEMORY (caught)")
        raise SystemExit(3)

    elapsed = time.perf_counter() - mark
    for stage, seconds in timings.items():
        _append_row(
            width=width,
            points=points_total,
            device=device_name,
            chunk=chunk,
            stage=stage,
            seconds=seconds,
            peak_rss_gb=_peak_rss_gb(),
        )
    _append_row(
        width=width,
        points=points_total,
        device=device_name,
        chunk=chunk,
        stage="total",
        seconds=elapsed,
        peak_rss_gb=_peak_rss_gb(),
        note=f"{points_total / elapsed:,.0f} points/s",
    )

    # Same sampled spot-check 9.3 used. A wrong search margin shows up
    # here before it shows up as a confusing shape in the timing plot.
    true_x = np.array([p.x for p in points], dtype=np.float64) * bench.FACTOR_X
    sample = np.random.default_rng(0).choice(
        len(points), size=min(50, len(points)), replace=False
    )
    worst = float(np.abs(found_x[sample] - true_x[sample]).max())
    if worst > 1.0:
        print(
            f"WARNING width={width} device={device_name}: sampled max tracking "
            f"error {worst:.2f}px -- search_margin may be too small here",
            file=sys.stderr,
        )


def _measured() -> dict[tuple[int, str], float]:
    """Every (width, device) total already measured, from the CSV."""
    if not CSV_PATH.exists():
        return {}
    with open(CSV_PATH) as f:
        return {
            (int(r["width"]), r["device"]): float(r["seconds"])
            for r in csv.DictReader(f)
            if r["stage"] == "total"
        }


def ladder_run() -> None:
    """Walks every device up the ladder, stopping each one on its own terms."""
    torch_require()
    measured = _measured()

    available = []
    for device_name in DEVICES:
        try:
            device_select(prefer=device_name)
        except SystemExit:
            print(f"Skipping {device_name}: not available on this machine")
            continue
        available.append(device_name)

    for device_name in available:
        budget = device_budget_gb(prefer=device_name)
        print(f"=== {device_name} (budget {budget:.1f}GB) ===")
        for width in bench._widths():
            _, count, _ = bench.grid_params(width)
            points_total = count * count

            if (width, device_name) in measured:
                print(f"  {width}px: already measured, skipping")
                continue

            # Stop 2: predicted-cost gate, from the previous size's own
            # measured rate on this same device. Reported, not run.
            previous = [w for w in bench._widths() if (w, device_name) in measured]
            if previous:
                last = previous[-1]
                rate = work_units(width=last) / measured[(last, device_name)]
                predicted = work_units(width=width) / rate
                if predicted > COST_BUDGET_S:
                    note = (
                        f"predicted {predicted:,.0f}s from {last}px rate "
                        f"({measured[(last, device_name)]:.1f}s), "
                        f"budget {COST_BUDGET_S:,.0f}s"
                    )
                    print(f"  {width}px: COST GATE -- {note}")
                    _append_row(
                        width=width,
                        points=points_total,
                        device=device_name,
                        chunk=0,
                        stage="STOPPED_cost_gate",
                        seconds=predicted,
                        peak_rss_gb=float("nan"),
                        note=note,
                    )
                    break

            try:
                result = subprocess.run(
                    [sys.executable, __file__, "--worker", str(width), device_name],
                    timeout=WATCHDOG_S,
                    capture_output=True,
                    text=True,
                )
            except subprocess.TimeoutExpired:
                # Harness event, not a scaling finding -- see the module
                # docstring. Reaching this means something hung.
                print(f"  {width}px: WATCHDOG FIRED after {WATCHDOG_S}s -- investigate")
                _append_row(
                    width=width,
                    points=points_total,
                    device=device_name,
                    chunk=0,
                    stage="HARNESS_watchdog",
                    seconds=float(WATCHDOG_S),
                    peak_rss_gb=float("nan"),
                    note="harness event, not a scaling result",
                )
                break

            if result.returncode != 0:
                print(f"  {width}px: stopped (returncode={result.returncode})")
                if result.stdout.strip():
                    print("   ", result.stdout.strip().splitlines()[-1])
                if result.returncode != 3:
                    print(result.stderr[-800:])
                    _append_row(
                        width=width,
                        points=points_total,
                        device=device_name,
                        chunk=0,
                        stage=f"FAILED_returncode_{result.returncode}",
                        seconds=float("nan"),
                        peak_rss_gb=float("nan"),
                        note=result.stderr.strip().splitlines()[-1][:200]
                        if result.stderr.strip()
                        else "",
                    )
                break

            measured = _measured()
            print(f"  {width}px: {measured[(width, device_name)]:.1f}s")
            if result.stderr.strip():
                print(f"    stderr: {result.stderr.strip()[-300:]}")

    print(f"Wrote {CSV_PATH}")


def summary_plot() -> None:
    """Two panels: this page's devices against 9.3's own executors, and
    where each size's time actually goes."""
    with open(CSV_PATH) as f:
        rows = list(csv.DictReader(f))

    figure, (ax_compare, ax_split) = plt.subplots(
        1, 2, figsize=(11, 4.5), constrained_layout=True
    )

    # Left: 9.3's committed CPU series, then this page's torch series on
    # the same axes. Comparing them is the whole point of the page.
    if TIMING_CSV.exists():
        with open(TIMING_CSV) as f:
            legacy = list(csv.DictReader(f))
        for stage, color, marker in [
            ("sequential", "tab:gray", "o"),
            ("threads", "tab:blue", "s"),
            ("processes", "tab:orange", "D"),
        ]:
            xs = [int(r["points"]) for r in legacy if r["stage"] == stage]
            ys = [float(r["seconds"]) for r in legacy if r["stage"] == stage]
            if xs:
                ax_compare.plot(
                    xs,
                    ys,
                    marker=marker,
                    color=color,
                    linestyle="--",
                    alpha=0.55,
                    label=f"9.3 {stage}",
                )

    for device_name, color, marker in [
        ("cpu", "tab:red", "o"),
        ("mps", "tab:green", "s"),
        ("cuda", "tab:purple", "D"),
    ]:
        pairs = sorted(
            (int(r["points"]), float(r["seconds"]))
            for r in rows
            if r["stage"] == "total" and r["device"] == device_name
        )
        if pairs:
            ax_compare.plot(
                [p for p, _ in pairs],
                [s for _, s in pairs],
                marker=marker,
                color=color,
                label=f"torch {device_name}",
            )

    ax_compare.set_xscale("log")
    ax_compare.set_yscale("log")
    ax_compare.set_xlabel("points (= correlations)")
    ax_compare.set_ylabel("seconds")
    ax_compare.set_title("Tracking cost: batched torch vs. 9.3's executors")
    ax_compare.legend(fontsize=7)

    # Right: where the time goes. hdic found extraction dominating its
    # own correlation five to one; this panel is what makes that visible
    # rather than hidden inside one total.
    for stage, color, marker in [
        ("upload", "tab:olive", "v"),
        ("extract", "tab:brown", "o"),
        ("correlate", "tab:cyan", "s"),
        ("refine", "tab:pink", "^"),
    ]:
        for device_name, style in (("cpu", "--"), ("mps", "-")):
            pairs = sorted(
                (int(r["points"]), float(r["seconds"]))
                for r in rows
                if r["stage"] == stage and r["device"] == device_name
            )
            if pairs:
                ax_split.plot(
                    [p for p, _ in pairs],
                    [s for _, s in pairs],
                    marker=marker,
                    color=color,
                    linestyle=style,
                    label=f"{device_name} {stage}",
                )
    ax_split.set_xscale("log")
    ax_split.set_yscale("log")
    ax_split.set_xlabel("points (= correlations)")
    ax_split.set_ylabel("seconds")
    ax_split.set_title("Where the time goes (solid mps, dashed cpu)")
    ax_split.legend(fontsize=7, ncol=2)

    stops = [
        f"{r['device']} @{r['width']}px: {r['stage'].split('_', 1)[-1]}"
        for r in rows
        if r["stage"].startswith(("STOPPED_", "FAILED_", "HARNESS_"))
    ]
    if stops:
        figure.suptitle("Ladder stopped: " + "; ".join(stops), fontsize=9, wrap=True)

    figure.savefig(PNG_PATH, dpi=300)
    plt.close(figure)
    print(f"Wrote {PNG_PATH}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        size_run(width=int(sys.argv[2]), device_name=sys.argv[3])
    elif len(sys.argv) == 2 and sys.argv[1] == "--check":
        checks_run()
    else:
        ladder_run()
        summary_plot()
