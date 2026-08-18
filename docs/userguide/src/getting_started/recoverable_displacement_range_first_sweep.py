"""The First Sweep: directly triggers the asymmetric-padding bug that
motivates the rest of Recoverable Displacement Range, using
`recoverable_displacement_range_uncentered_demo.py`'s `locate_uncentered`
-- the real, shipped `locate` has already been fixed and would not
reproduce this collapse.

Runs live on every book build, not from a committed snapshot.
"""

from dictk.image import PixelCoordinate, read, translate
from recoverable_displacement_range_uncentered_demo import locate_uncentered

if __name__ == "__main__":
    reference_image = read(path="astronaut0.png")
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin = 30
    search_margin = 180  # generous -- per Root Cause, size won't help here

    print("| dx | expected | found | match |")
    print("|---|---|---|---|")
    for dx in [10, 20, 25, 29, 30, 31, 40, 60, 90, 120]:
        current_image = translate(arr=reference_image, dx=dx, dy=0)
        expected = PixelCoordinate(x=p0.x + dx, y=p0.y)
        found = locate_uncentered(
            reference_image, current_image, p0, p0, kernel_margin, search_margin
        )
        print(
            f"| {dx} | ({expected.x},{expected.y}) | ({found.x},{found.y}) | {found == expected} |"
        )
