"""Compare the page's own displacement-field grid (43x43,
kernel_margin=25) against a VIC-2D-style denser grid (53x54,
kernel_margin=13, matching high_point_density.md's own convention):
same crack, same story, but does the smaller kernel change anything?
"""

import numpy as np

import dictk
from dictk.grid import generate, locate_subpixel
from dictk.image import PixelCoordinate, combine, crack_dislocation

WIDTH = HEIGHT = 300
OFFSET = 4.0

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)


def track(*, origin, count_x, count_y, spacing, kernel_margin, search_margin):
    points = generate(
        origin=origin,
        count_x=count_x,
        count_y=count_y,
        spacing_x=spacing,
        spacing_y=spacing,
    )
    clipped = sum(
        1
        for p in points
        if p.x - search_margin < 0
        or p.y - search_margin < 0
        or p.x + search_margin > WIDTH
        or p.y + search_margin > HEIGHT
    )
    found = locate_subpixel(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=search_margin,
        search_margin_height=search_margin,
        upsample_factor=100,
    )
    dy = np.array([f.y - p.y for f, p in zip(found, points)])
    return dy, clipped


def deviation(dy):
    return np.minimum(np.abs(dy - OFFSET), np.abs(dy + OFFSET))


CURRENT_KERNEL_MARGIN = 25
CURRENT_SEARCH_MARGIN = 45
dy_current, clipped_current = track(
    origin=PixelCoordinate(x=CURRENT_SEARCH_MARGIN, y=CURRENT_SEARCH_MARGIN),
    count_x=43,
    count_y=43,
    spacing=5,
    kernel_margin=CURRENT_KERNEL_MARGIN,
    search_margin=CURRENT_SEARCH_MARGIN,
)

VIC2D_STYLE_KERNEL_MARGIN = 13
VIC2D_STYLE_SEARCH_MARGIN = 25
dy_vic2d, clipped_vic2d = track(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing=5,
    kernel_margin=VIC2D_STYLE_KERNEL_MARGIN,
    search_margin=VIC2D_STYLE_SEARCH_MARGIN,
)

# Same density and origin as the current grid, but with the VIC-2D
# grid's own smaller kernel -- isolates the kernel-size effect from
# both point density and edge clipping (this grid clips nothing).
dy_isolated, clipped_isolated = track(
    origin=PixelCoordinate(x=CURRENT_SEARCH_MARGIN, y=CURRENT_SEARCH_MARGIN),
    count_x=43,
    count_y=43,
    spacing=5,
    kernel_margin=VIC2D_STYLE_KERNEL_MARGIN,
    search_margin=VIC2D_STYLE_SEARCH_MARGIN,
)

dev_current = deviation(dy_current)
dev_vic2d = deviation(dy_vic2d)
dev_isolated = deviation(dy_isolated)

print("| grid | points | kernel (px) | clipped | max dev (px) | mean dev (px) |")
print("|---|---|---|---|---|---|")
print(
    f"| Current (43x43, kernel_margin=25) | {len(dy_current)} | "
    f"{2 * CURRENT_KERNEL_MARGIN}x{2 * CURRENT_KERNEL_MARGIN} | {clipped_current} | "
    f"{dev_current.max():.4f} | {dev_current.mean():.4f} |"
)
print(
    f"| VIC-2D style (53x54, kernel_margin=13) | {len(dy_vic2d)} | "
    f"{2 * VIC2D_STYLE_KERNEL_MARGIN}x{2 * VIC2D_STYLE_KERNEL_MARGIN} | {clipped_vic2d} | "
    f"{dev_vic2d.max():.4f} | {dev_vic2d.mean():.4f} |"
)
print()

print("| grid | kernel (px) | clipped | max dev (px) | mean dev (px) |")
print("|---|---|---|---|---|")
print(
    f"| Current (43x43, kernel_margin=25) | "
    f"{2 * CURRENT_KERNEL_MARGIN}x{2 * CURRENT_KERNEL_MARGIN} | {clipped_current} | "
    f"{dev_current.max():.4f} | {dev_current.mean():.4f} |"
)
print(
    f"| Current density, VIC-2D kernel (43x43, kernel_margin=13) | "
    f"{2 * VIC2D_STYLE_KERNEL_MARGIN}x{2 * VIC2D_STYLE_KERNEL_MARGIN} | {clipped_isolated} | "
    f"{dev_isolated.max():.4f} | {dev_isolated.mean():.4f} |"
)
print(
    f"| VIC-2D style (53x54, kernel_margin=13) | "
    f"{2 * VIC2D_STYLE_KERNEL_MARGIN}x{2 * VIC2D_STYLE_KERNEL_MARGIN} | {clipped_vic2d} | "
    f"{dev_vic2d.max():.4f} | {dev_vic2d.mean():.4f} |"
)
