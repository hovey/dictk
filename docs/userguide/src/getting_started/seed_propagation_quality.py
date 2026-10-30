"""Can a wrong fit be detected? Reruns the sweep's 1470 fits, the same
49 stretch and shear combinations at the same 30 points, and records
each fit's final ZNSSD and IC-GN iteration count alongside its error.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import affine_transform

from dictk import translation, warp
from dictk.image import PixelCoordinate, read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

MARGIN = 13
SEARCH_MARGIN = 25
SAMPLE_COUNT = 30
MAX_ITERATIONS = 50
STRETCHES = np.round(np.arange(0.0, 0.31, 0.05), 2)
SHEARS = np.round(np.arange(0.0, 0.31, 0.05), 2)
MISS_LIMIT = 1.0

reference_image = read(path="astronaut0.png")
reference_gradients = warp._gradients(reference_image)
rng = np.random.default_rng(0)
pivots = rng.integers(40, 261, size=(SAMPLE_COUNT, 2)).astype(np.float64)
shifts = np.round(rng.uniform([4, 2], [8, 6], size=(SAMPLE_COUNT, 2)), 2)

errors, znssds, iterations, cells = [], [], [], []
for stretch in STRETCHES:
    for shear in SHEARS:
        inverse = np.linalg.inv(np.array([[1.0 + stretch, shear], [0.0, 1.0]]))
        inverse = inverse[::-1, ::-1]
        for pivot, shift in zip(pivots, shifts):
            point = PixelCoordinate(x=int(pivot[0]), y=int(pivot[1]))
            offset = pivot[::-1] - inverse @ (pivot[::-1] + shift[::-1])
            current_image = affine_transform(
                reference_image.astype(np.float64), inverse, offset=offset, order=5
            )
            seed = translation.locate(
                reference_image=reference_image,
                current_image=current_image,
                reference_point=point,
                search_center=point,
                kernel_margin_width=MARGIN,
                kernel_margin_height=MARGIN,
                search_margin_width=SEARCH_MARGIN,
                search_margin_height=SEARCH_MARGIN,
            )
            fitted, znssd, count = warp._refine(
                reference_image=reference_image,
                reference_gradients=reference_gradients,
                current_coefficients=warp._spline_coefficients(current_image),
                reference_point=point,
                initial_warp=warp._translation_warp(reference_point=point, start=seed),
                kernel_margin_width=MARGIN,
                kernel_margin_height=MARGIN,
                max_iterations=MAX_ITERATIONS,
                tolerance=1e-6,
            )
            errors.append(np.hypot(*(fitted[:2, 2] - shift)))
            znssds.append(znssd)
            iterations.append(count)
            cells.append((stretch, shear))

errors, znssds, iterations = map(np.array, (errors, znssds, iterations))
missed = errors > MISS_LIMIT
stalled = iterations == MAX_ITERATIONS

print(
    f"| Fit | Count | ZNSSD range | Median ZNSSD | Median iterations "
    rf"| Stopped at $n_{{\text{{MAX\_ITER}}}} = {MAX_ITERATIONS}$ |"
)
print("|---|---|---|---|---|---|")
for name, group in [("Correct", ~missed), ("Miss", missed)]:
    print(
        f"| {name} | {group.sum()} "
        f"| {znssds[group].min():.4f} to {znssds[group].max():.4f} "
        f"| {np.median(znssds[group]):.4f} "
        f"| {np.median(iterations[group]):.0f} "
        f"| {stalled[group].sum()} |"
    )
print()
print("The fits the iteration count misclassifies:")
print()
print("| Fit | Stretch | Shear | Error (px) | ZNSSD | Iterations |")
print("|---|---|---|---|---|---|")
for name, group in [
    ("Correct", ~missed & stalled),
    ("Miss", missed & ~stalled),
]:
    for k in np.flatnonzero(group):
        stretch, shear = cells[k]
        print(
            f"| {name} | {stretch:.0%} | {shear:.2f} | {errors[k]:.3f} "
            f"| {znssds[k]:.4f} | {iterations[k]} |"
        )

fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
bins = np.logspace(np.log10(znssds.min()) - 0.1, np.log10(znssds.max()) + 0.1, 60)
for group, color, label in [
    (~missed, "tab:blue", "correct fit"),
    (missed, "tab:orange", "miss"),
]:
    left.hist(znssds[group], bins=bins, color=color, alpha=0.8, label=label)
    right.hist(
        iterations[group],
        bins=np.arange(0.5, MAX_ITERATIONS + 1.5),
        color=color,
        alpha=0.8,
        label=label,
    )
left.set_xscale("log")
left.set_yscale("log")
left.set_xlabel("final ZNSSD")
left.set_ylabel("fits")
left.legend()
right.set_yscale("log")
right.set_xlabel("IC-GN iterations")
right.set_ylabel("fits")
right.legend()
fig.savefig("seed_propagation_quality.png", dpi=300)
