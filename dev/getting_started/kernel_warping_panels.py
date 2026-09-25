"""Side-by-side illustration of the kernel `locate`/`locate_subpixel`
match (left) against the kernel `locate_warp` warps (right), on one
point under an exaggerated affine deformation.

First sweeps 30 random fractional shifts under that deformation and
reports each function's median error. The figure then uses the shift
whose three errors sit closest to those medians, so the example is
typical, not hand-picked.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from scipy.ndimage import affine_transform

from dictk import translation, warp
from dictk.image import PixelCoordinate, read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

# Deformation gradient in (x, y) order: 7% stretch along x plus 0.05
# shear, exaggerated beyond this page's 2% so the warp is visible, with
# distinct values so each one is easy to spot in the printed matrices.
# 15% with 0.15 shear defeats the whole-pixel starting match for about
# a third of shifts; 7% with 0.05 shear defeats none of the 30 below.
F = np.array([[1.07, 0.05], [0.0, 1.0]])
POINT = PixelCoordinate(x=150, y=150)
MARGIN = 13
SEARCH_MARGIN = 25
SHIFT_COUNT = 30
DOT_COUNT = 10
ZOOM = 34

reference_image = read(path="astronaut0.png")
pivot = np.array([POINT.x, POINT.y], dtype=np.float64)
# affine_transform maps each output (row, column) back to its input
# position, so it takes the inverse deformation, in (y, x) order.
inverse = np.linalg.inv(F)[::-1, ::-1]


def deformed(shift):
    offset = pivot[::-1] - inverse @ (pivot[::-1] + shift[::-1])
    return affine_transform(
        reference_image.astype(np.float64), inverse, offset=offset, order=5
    )


def tracked(current_image):
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
    return (
        translation.locate(**kwargs),
        translation.locate_subpixel(**kwargs),
        warp.locate(**kwargs),
        warp.fit(**kwargs),
    )


names = ["`locate`", "`locate_subpixel`", "`locate_warp`"]
# Rounded to 0.01 px, so each shift prints exactly as used.
shifts = np.round(
    np.random.default_rng(0).uniform([4, 2], [8, 6], size=(SHIFT_COUNT, 2)), 2
)
errors = np.array(
    [
        [
            np.hypot(*(np.array([f.x, f.y]) - pivot - shift))
            for f in tracked(deformed(shift))[:3]
        ]
        for shift in shifts
    ]
)
medians = np.median(errors, axis=0)
print(f"Across {SHIFT_COUNT} random fractional shifts:")
print()
print("| Function | Smallest error (px) | Median error (px) | Largest error (px) |")
print("|---|---|---|---|")
for name, smallest, median, largest in zip(
    names, errors.min(axis=0), medians, errors.max(axis=0)
):
    print(f"| {name} | {smallest:.3f} | {median:.3f} | {largest:.3f} |")

typical = int(np.argmin((np.abs(errors - medians) / medians).sum(axis=1)))
TRANSLATION = shifts[typical]
current_image = deformed(TRANSLATION)
true_position = pivot + TRANSLATION
found_locate, found_subpixel, found_warp, fitted = tracked(current_image)

print()
print(
    f"The most typical shift, ({TRANSLATION[0]:.2f}, {TRANSLATION[1]:.2f}) px, "
    f"puts the true position at ({true_position[0]:.2f}, {true_position[1]:.2f}):"
)
print()
print("| Function | Found $x$ | Found $y$ | Error (px) |")
print("|---|---|---|---|")
for name, found in zip(names, [found_locate, found_subpixel, found_warp]):
    error = np.hypot(found.x - true_position[0], found.y - true_position[1])
    print(f"| {name} | {found.x:.3f} | {found.y:.3f} | {error:.3f} |")

rigid = np.array(
    [
        [1.0, 0.0, found_subpixel.x - POINT.x],
        [0.0, 1.0, found_subpixel.y - POINT.y],
        [0.0, 0.0, 1.0],
    ]
)
true = np.eye(3)
true[:2, :2] = F
true[:2, 2] = TRANSLATION


def latex(matrix, exact):
    """`matrix` as a LaTeX bmatrix. Entries where `exact` is True are
    fixed by construction and print as given (`1`, `0`, `1.15`), not
    padded to four decimals."""
    rows = [
        " & ".join(
            f"{value:g}" if fixed else f"{value:.4f}"
            for value, fixed in zip(row, fixed_row)
        )
        for row, fixed_row in zip(matrix, exact)
    ]
    return "\\begin{bmatrix}" + " \\\\ ".join(rows) + "\\end{bmatrix}"


bottom_row = np.zeros((3, 3), dtype=bool)
bottom_row[2] = True
rigid_exact = bottom_row.copy()
rigid_exact[:2, :2] = True
for name, matrix, exact, note in [
    (r"locate\_subpixel", rigid, rigid_exact, r" \quad (u_x = u_y = v_x = v_y = 0)"),
    (r"locate\_warp", fitted, bottom_row, ""),
    ("true", true, np.ones((3, 3), dtype=bool), ""),
]:
    print()
    print("$$")
    print(f"\\boldsymbol{{W}}_\\text{{{name}}} = {latex(matrix, exact)}{note}")
    print("$$")

offsets = np.linspace(-MARGIN, MARGIN, DOT_COUNT)
grid = np.array([(dx, dy) for dy in offsets for dx in offsets])
square = np.array(
    [[-MARGIN, -MARGIN], [MARGIN, -MARGIN], [MARGIN, MARGIN], [-MARGIN, MARGIN]]
)

fig, (left, right) = plt.subplots(1, 2, figsize=(10, 5.2), constrained_layout=True)
for ax in (left, right):
    ax.imshow(current_image, cmap="gray", vmin=0, vmax=255)
    ax.set_xlim(pivot[0] - ZOOM, pivot[0] + ZOOM)
    ax.set_ylim(pivot[1] + ZOOM, pivot[1] - ZOOM)
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")
    ax.add_patch(
        Polygon(
            pivot + square,
            fill=False,
            edgecolor="white",
            linestyle="--",
            linewidth=1.5,
        )
    )
    ax.plot(*true_position, marker="+", color="red", markersize=14, mew=2)

for ax, found, corners, dots, title in [
    (
        left,
        found_subpixel,
        square,
        grid,
        "locate, locate_subpixel: rigid square kernel",
    ),
    (
        right,
        found_warp,
        square @ fitted[:2, :2].T,
        grid @ fitted[:2, :2].T,
        "locate_warp: affine-warped kernel",
    ),
]:
    center = np.array([found.x, found.y])
    ax.annotate(
        "",
        xy=center,
        xytext=pivot,
        arrowprops=dict(arrowstyle="-|>", color="orange", linewidth=2),
    )
    ax.add_patch(Polygon(center + corners, fill=False, edgecolor="orange", linewidth=2))
    ax.scatter(*(center + dots).T, s=8, color="orange")
    ax.set_title(title)

fig.savefig("kernel_warping_panels.png", dpi=300)
