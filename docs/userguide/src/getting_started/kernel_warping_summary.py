"""Summary of Kernel Warping's progression as one HTML table: `locate`,
VIC-2D, `locate_subpixel`, and `locate_warp` on `image.stretch`'s
bilinear image, then `locate_warp` on a quintic-spline image. Reports the
mean and standard deviation of each tracker's x error and of its E11.
"""

import csv

import numpy as np
from scipy.ndimage import map_coordinates

from dictk.element import gauss_point_log_strains
from dictk.grid import elements, generate, locate, locate_subpixel, locate_warp
from dictk.image import PixelCoordinate, read, stretch

FACTOR_X = 1.02

reference_image = read(path="astronaut0.png")
height, width = reference_image.shape
ys, xs = np.mgrid[0:height, 0:width].astype(np.float64)
bilinear_image = stretch(arr=reference_image, factor_x=FACTOR_X)
quintic_image = map_coordinates(
    reference_image.astype(np.float64), [ys, xs / FACTOR_X], order=5
)
points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)
element_indices = elements(count_x=53, count_y=54)
true_x = np.array([p.x * FACTOR_X for p in points])


def track(tracker, image, **extra):
    return tracker(
        reference_image=reference_image,
        current_image=image,
        reference_points=points,
        kernel_margin_width=13,
        kernel_margin_height=13,
        search_margin_width=25,
        search_margin_height=25,
        **extra,
    )


def statistics(found):
    error_x = np.array([f.x for f in found]) - true_x
    strains = (
        np.array(
            [
                strain[0, 0]
                for element in element_indices
                for strain in gauss_point_log_strains(
                    reference_points=[points[i] for i in element],
                    current_points=[found[i] for i in element],
                )
            ]
        )
        * 1e6
    )
    return (
        error_x.mean(),
        error_x.std(),
        (error_x.min(), error_x.max()),
        strains.mean(),
        strains.std(),
    )


with open("../verification/simple_stretch_vic_out.csv") as f:
    rows = [{k.strip(' "'): v for k, v in row.items()} for row in csv.DictReader(f)]
valid = [r for r in rows if float(r["sigma"]) != -1]
vic_error_x = np.array(
    [float(r["x"]) + float(r["u"]) - FACTOR_X * float(r["x"]) for r in valid]
)
vic_strain = np.array([float(r["exx"]) * 1e6 for r in valid])

columns = [
    ("<code>locate</code>", statistics(track(locate, bilinear_image)), ""),
    (
        "VIC-2D",
        (
            vic_error_x.mean(),
            vic_error_x.std(),
            (vic_error_x.min(), vic_error_x.max()),
            vic_strain.mean(),
            vic_strain.std(),
        ),
        "",
    ),
    (
        "<code>locate_subpixel</code>",
        statistics(track(locate_subpixel, bilinear_image, upsample_factor=100)),
        "",
    ),
    ("<code>locate_warp</code>", statistics(track(locate_warp, bilinear_image)), ""),
    (
        "<code>locate_warp</code>, quintic image",
        statistics(track(locate_warp, quintic_image)),
        ' class="unreachable"',
    ),
]


def range_format(bounds):
    decimals = 2 if max(abs(b) for b in bounds) >= 0.1 else 3
    low, high = bounds
    return f"[{low:+.{decimals}f}, {high:+.{decimals}f}]"


labels = [
    ("Mean $x$ error (px)", lambda v: f"{v:+.4f}" if round(v, 4) else "0.0000"),
    ("Std $x$ error (px)", lambda v: f"{v:.4f}"),
    ("$x$ error range (px)", range_format),
    ("Mean $E_{11}$ (microstrain)", lambda v: f"{v:.0f}"),
    ("Std $E_{11}$ (microstrain)", lambda v: f"{v:.0f}"),
]
figure_rows = {
    0: (
        "$x$ error Figure",
        {
            "VIC-2D": "./simple_stretch.html#fig-vic-x-error-histogram",
            "<code>locate_subpixel</code>": "./high_point_density.html#fig-hpd-x-error-histogram",
            "<code>locate_warp</code>": "#fig-kw-x-error-histogram",
        },
    ),
    3: (
        "$E_{11}$ Figure",
        {
            "VIC-2D": "./simple_stretch.html#fig-vic-exx-histogram",
            "<code>locate_subpixel</code>": "./high_point_density.html#fig-hpd-strain-histogram",
        },
    ),
}

print('<table class="progression">')
print("<thead><tr><th></th>", end="")
for name, _, css in columns:
    print(f"<th{css}>{name}</th>", end="")
print("</tr></thead>")
print("<tbody>")
for row, (label, fmt) in enumerate(labels):
    if row in figure_rows:
        figure_label, targets = figure_rows[row]
        print(f"<tr><td>{figure_label}</td>", end="")
        for name, _, css in columns:
            link = f'<a href="{targets[name]}">Figure</a>' if name in targets else ""
            print(f"<td{css}>{link}</td>", end="")
        print("</tr>")
    print(f"<tr><td>{label}</td>", end="")
    for _, values, css in columns:
        print(f"<td{css}>{fmt(values[row])}</td>", end="")
    print("</tr>")
print("</tbody>")
print("</table>")
