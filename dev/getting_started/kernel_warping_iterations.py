"""IC-GN iteration by iteration, on Kernel Warping's panel-figure example:
the point at (150, 150) under a 7% stretch, 0.05 shear, and the typical
shift (6.43, 4.92) that kernel_warping_panels.py selects. warp.fit with
max_iterations=k returns the warp after k iterations. Iteration 0 is the
whole-pixel start from translation.locate.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import affine_transform, map_coordinates

from dictk import translation, warp
from dictk.image import PixelCoordinate, read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

F = np.array([[1.07, 0.05], [0.0, 1.0]])
SHIFT = np.array([6.43, 4.92])
POINT = PixelCoordinate(x=150, y=150)
MARGIN = 13
SEARCH_MARGIN = 25
RESIDUAL_ITERATIONS = [0, 1, 2, 3]

reference_image = read(path="astronaut0.png").astype(np.float64)
pivot = np.array([POINT.x, POINT.y], dtype=np.float64)
inverse = np.linalg.inv(F)[::-1, ::-1]
offset = pivot[::-1] - inverse @ (pivot[::-1] + SHIFT[::-1])
current_image = affine_transform(reference_image, inverse, offset=offset, order=5)
kwargs = dict(
    reference_image=reference_image,
    current_image=current_image,
    reference_point=POINT,
    search_center=POINT,
    kernel_margin_width=MARGIN,
    kernel_margin_height=MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)

dy, dx = np.mgrid[-MARGIN : MARGIN + 1, -MARGIN : MARGIN + 1].astype(np.float64)
f = reference_image[
    POINT.y - MARGIN : POINT.y + MARGIN + 1, POINT.x - MARGIN : POINT.x + MARGIN + 1
]
f_tilde = f - f.mean()


def warp_at(iterations):
    if iterations == 0:
        start = translation.locate(**kwargs)
        return np.array(
            [[1.0, 0.0, start.x - POINT.x], [0.0, 1.0, start.y - POINT.y], [0, 0, 1.0]]
        )
    return warp.fit(**kwargs, max_iterations=iterations)


def residual(matrix):
    xs = POINT.x + matrix[0, 0] * dx + matrix[0, 1] * dy + matrix[0, 2]
    ys = POINT.y + matrix[1, 0] * dx + matrix[1, 1] * dy + matrix[1, 2]
    g = map_coordinates(current_image, [ys, xs], order=3)
    g_tilde = g - g.mean()
    znssd = np.sum(
        (f_tilde / np.linalg.norm(f_tilde) - g_tilde / np.linalg.norm(g_tilde)) ** 2
    )
    scale = np.linalg.norm(f_tilde) / np.linalg.norm(g_tilde)
    return scale * g_tilde - f_tilde, znssd


final = warp.fit(**kwargs)
iterations = [0]
while not np.allclose(warp_at(iterations[-1]), final, rtol=0, atol=1e-12):
    iterations.append(iterations[-1] + 1)
records = []
for k in iterations:
    matrix = warp_at(k)
    r, znssd = residual(matrix)
    translation_error = np.hypot(*(matrix[:2, 2] - SHIFT))
    gradient_error = np.abs(matrix[:2, :2] - F).max()
    records.append((k, znssd, translation_error, gradient_error, r))

print(f"IC-GN reaches its final warp after {iterations[-1]} iterations:")
print()
print("| Iteration $k$ | ZNSSD $C$ | Translation error (px) | Gradient error |")
print("|---|---|---|---|")
for k, znssd, translation_error, gradient_error, _ in records:
    print(f"| {k} | {znssd:.2e} | {translation_error:.2e} | {gradient_error:.2e} |")

shown = [record for record in records if record[0] in RESIDUAL_ITERATIONS]
limit = np.abs(shown[0][4]).max()
fig, axes = plt.subplots(
    1, len(shown), figsize=(10, 3.1), constrained_layout=True, squeeze=False
)
extent = (-MARGIN - 0.5, MARGIN + 0.5, MARGIN + 0.5, -MARGIN - 0.5)
for ax, (k, znssd, _, _, r) in zip(axes.flat, shown):
    image = ax.imshow(r, cmap="RdBu_r", vmin=-limit, vmax=limit, extent=extent)
    ax.set_title(f"$k = {k}$,  $C = {znssd:.2g}$")
    ax.set_xlabel(r"$\Delta x$ (px)")
axes.flat[0].set_ylabel(r"$\Delta y$ (px)")
fig.colorbar(image, ax=axes.flat[-1], shrink=0.85, label="residual $r$")
fig.savefig("kernel_warping_residuals.png", dpi=200)

ks = [record[0] for record in records]
fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
left.semilogy(ks, [record[2] for record in records], "o-", color="black")
left.set_title("translation error")
left.set_ylabel("error (px)")
right.semilogy(ks, [record[3] for record in records], "o-", color="black")
right.set_title("gradient error")
right.set_ylabel(r"largest $|W_{ij} - F_{ij}|$")
for ax in (left, right):
    ax.set_xlabel("iteration $k$")
    ax.set_xticks(ks)
    ax.grid(True, which="major", color="0.85", linewidth=0.8)
fig.savefig("kernel_warping_convergence.png", dpi=200)
