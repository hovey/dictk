"""Benchmark: sequential vs. threads vs. processes for
skimage.registration.phase_cross_correlation, at varying correlation
sizes and call counts.

Not part of the dictk package -- a standalone, one-time measurement
script, matching the convention simple_shear.py already sets. Its
output (parallelization_bench.csv, parallelization_bench.png) is
committed alongside it rather than regenerated on every book build: the
full sweep takes several minutes (the 1,000,000-call case alone runs
over a minute), far too slow for the live cmdrun re-execution every
other figure in this book uses. Parallelization.md prints this script's
full source inline (see its own "parallelization_bench.py" section) so
the numbers stay checkable even though they are not live.

Must be a real module, not `python3 -c` -- ProcessPoolExecutor needs a
real, importable, top-level function to hand to spawned workers, the
same constraint dictk.grid._locate_worker exists for.

Re-run with: python3 parallelization_bench.py
"""

import csv
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import matplotlib.pyplot as plt
import numpy as np
from skimage.registration import phase_cross_correlation

WORKERS = os.cpu_count()

CSV_PATH = "parallelization_bench.csv"
FIGURE_PATH = "parallelization_bench.png"

# Point count and correlation size are not independent in a real DIC
# problem -- a million-point mesh only makes sense with small subsets
# per point. Three scenarios instead of one brute-force grid, each
# answering a different question:
SCENARIOS = {
    # This book's own teaching scale (kernel/search sizes throughout
    # Single/Multi-Point Motion). Does point count alone ever create a
    # crossover, at a size this small?
    "book_scale": [(40, n) for n in [100, 1_000, 10_000, 100_000, 1_000_000]],
    # Few points, growing correlation size. Where does the threads
    # crossover actually sit, as a function of size alone?
    "large_subset": [(size, 16) for size in [200, 500, 1000, 2000]],
    # A more realistic finite element mesh: moderate subset size,
    # climbing point count. Does the processes-vs-threads balance shift
    # as point count grows?
    "realistic_mesh": [(100, n) for n in [1_000, 10_000, 100_000]]
    + [(200, n) for n in [1_000, 10_000, 100_000]],
}


def one(args: tuple[np.ndarray, np.ndarray]):
    """One correlation. Module-level and single-positional-argument on
    purpose -- see the module docstring."""
    kernel, search = args
    return phase_cross_correlation(kernel, search, normalization="phase")


def make_args(size: int, n_calls: int, seed: int = 42):
    """`n_calls` copies of the same random kernel/search pair at `size`.

    The same pair repeated, not `n_calls` distinct random pairs: this
    benchmark measures call overhead, not correlation accuracy, so
    identical inputs keep every call's own work identical too."""
    rng = np.random.default_rng(seed)
    kernel = rng.random((size, size))
    search = rng.random((size, size))
    return [(kernel, search)] * n_calls


def time_sequential(args) -> float:
    t0 = time.perf_counter()
    for x in args:
        one(x)
    return time.perf_counter() - t0


def time_threads(args) -> float:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(one, args))
    return time.perf_counter() - t0


def time_processes(args) -> float:
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(one, args))
    return time.perf_counter() - t0


def run_case(scenario: str, size: int, n_calls: int, writer: csv.DictWriter) -> None:
    args = make_args(size, n_calls)

    sequential_s = time_sequential(args)
    threads_s = time_threads(args)
    processes_s = time_processes(args)

    writer.writerow(
        {
            "scenario": scenario,
            "size": size,
            "n_calls": n_calls,
            "workers": WORKERS,
            "sequential_s": round(sequential_s, 5),
            "threads_s": round(threads_s, 5),
            "processes_s": round(processes_s, 5),
            "threads_speedup": round(sequential_s / threads_s, 3),
            "processes_speedup": round(sequential_s / processes_s, 3),
        }
    )
    print(
        f"[{scenario}] size={size:5d} n={n_calls:8d}  "
        f"sequential={sequential_s:8.3f}s  "
        f"threads={threads_s:8.3f}s (x{sequential_s / threads_s:5.2f})  "
        f"processes={processes_s:8.3f}s (x{sequential_s / processes_s:5.2f})",
        flush=True,
    )


def run_sweep() -> None:
    fieldnames = [
        "scenario",
        "size",
        "n_calls",
        "workers",
        "sequential_s",
        "threads_s",
        "processes_s",
        "threads_speedup",
        "processes_speedup",
    ]
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for scenario, cases in SCENARIOS.items():
            for size, n_calls in cases:
                run_case(scenario, size, n_calls, writer)
                f.flush()
    print(f"\nWrote {CSV_PATH}")


# Point counts to extrapolate speedup trends out to, tying directly to
# the "north star" scale in Path Forward (billions of correlations,
# staying under a trillion by design). Only scenarios whose x-axis is
# point count (book_scale, realistic_mesh) get this treatment --
# large_subset's x-axis is correlation *size*, and extrapolating a
# subset's side length out to a billion pixels isn't physical.
EXTRAPOLATION_TARGETS = [1_000_000, 1_000_000_000, 1_000_000_000_000]


def _trend_line(ns, seq_times, other_times, targets):
    """Fit a linear time-vs-n trend (time = a*n + b) to `seq_times` and
    `other_times` independently, then extrapolate the *speedup ratio*
    (their fitted-time ratio) out to every target beyond the last real
    data point.

    Returns `(xs, speedups, marks)`: `xs`/`speedups` start at the last
    *measured* point (so a plotted dashed line picks up exactly where
    the solid measured line ends, no visual gap) and run through every
    target; `marks` is just the subset of targets genuinely beyond the
    measured range, for placing "predicted value" markers.
    """
    a_seq, b_seq = np.polyfit(ns, seq_times, 1)
    a_other, b_other = np.polyfit(ns, other_times, 1)
    last_n = ns[-1]
    marks = [t for t in targets if t > last_n]
    xs = [last_n] + marks
    speedups = [(a_seq * n + b_seq) / (a_other * n + b_other) for n in xs]
    return xs, speedups, marks


def _add_trend(ax, ns, seq_times, other_times, color):
    xs, speedups, marks = _trend_line(ns, seq_times, other_times, EXTRAPOLATION_TARGETS)
    ax.plot(xs, speedups, linestyle="--", color=color, linewidth=1.2)
    mark_speedups = speedups[-len(marks) :] if marks else []
    ax.plot(marks, mark_speedups, linestyle="none", marker="x", color=color, markersize=7, markeredgewidth=1.5)
    for n, s in zip(marks, mark_speedups):
        ax.annotate(
            f"{s:.2f}x",
            (n, s),
            textcoords="offset points",
            xytext=(4, 4),
            fontsize=7,
            color=color,
        )


def plot_summary() -> None:
    with open(CSV_PATH) as f:
        rows = list(csv.DictReader(f))

    with plt.rc_context({"font.family": "serif", "mathtext.fontset": "cm"}):
        fig, axes = plt.subplots(3, 1, figsize=(7, 15), constrained_layout=True)

        panels = [
            (axes[0], "book_scale", "n_calls", "point count (size=40 fixed)", "log", True),
            (
                axes[1],
                "large_subset",
                "size",
                "correlation size (n=16 fixed)",
                "linear",
                False,
            ),
            (
                axes[2],
                "realistic_mesh",
                "n_calls",
                "point count (size=100 or 200)",
                "log",
                True,
            ),
        ]
        for ax, scenario, xkey, xlabel, xscale, extrapolate in panels:
            data = [r for r in rows if r["scenario"] == scenario]
            if scenario == "realistic_mesh":
                for size, marker in [("100", "o"), ("200", "s")]:
                    sub = [r for r in data if r["size"] == size]
                    xs = [int(r[xkey]) for r in sub]
                    ax.plot(
                        xs,
                        [float(r["threads_speedup"]) for r in sub],
                        marker=marker,
                        color="tab:blue",
                        label=f"threads (size={size})",
                    )
                    ax.plot(
                        xs,
                        [float(r["processes_speedup"]) for r in sub],
                        marker=marker,
                        color="tab:orange",
                        label=f"processes (size={size})",
                    )
                    if extrapolate:
                        seq = [float(r["sequential_s"]) for r in sub]
                        thr = [float(r["threads_s"]) for r in sub]
                        proc = [float(r["processes_s"]) for r in sub]
                        _add_trend(ax, xs, seq, thr, "tab:blue")
                        _add_trend(ax, xs, seq, proc, "tab:orange")
            else:
                xs = [int(r[xkey]) for r in data]
                ax.plot(
                    xs,
                    [float(r["threads_speedup"]) for r in data],
                    marker="o",
                    color="tab:blue",
                    label="threads",
                )
                ax.plot(
                    xs,
                    [float(r["processes_speedup"]) for r in data],
                    marker="o",
                    color="tab:orange",
                    label="processes",
                )
                if extrapolate:
                    seq = [float(r["sequential_s"]) for r in data]
                    thr = [float(r["threads_s"]) for r in data]
                    proc = [float(r["processes_s"]) for r in data]
                    _add_trend(ax, xs, seq, thr, "tab:blue")
                    _add_trend(ax, xs, seq, proc, "tab:orange")
            ax.axhline(
                1.0,
                color="black",
                linestyle="--",
                linewidth=1,
                label="sequential (baseline)",
            )
            ax.set_xscale(xscale)
            if extrapolate:
                # Headroom so the rightmost "N.NNx" annotation (at the
                # 10^12 target) doesn't clip against the panel edge.
                ax.set_xlim(right=ax.get_xlim()[1] * 3)
            ax.set_xlabel(xlabel)
            ax.set_ylabel("speedup vs sequential")
            ax.set_title(scenario)
            handles, labels = ax.get_legend_handles_labels()
            if extrapolate:
                from matplotlib.lines import Line2D

                handles += [
                    Line2D([0], [0], color="gray", marker="o", linestyle="-", label="measured"),
                    Line2D([0], [0], color="gray", marker="x", linestyle="--", label="trend (extrapolated)"),
                ]
            ax.legend(handles=handles, fontsize=7)

        fig.savefig(FIGURE_PATH, dpi=300)
        plt.close(fig)
    print(f"Wrote {FIGURE_PATH}")


if __name__ == "__main__":
    run_sweep()
    plot_summary()
