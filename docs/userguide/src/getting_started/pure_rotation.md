# Pure Rotation

[Path Forward](./path_forward.md#2026-08-11) names a direction worth
testing empirically: how large a rigid-body rotation angle can
`dictk`'s correlation-based tracking actually recover before it breaks
down? [Rigid Body Motion](./rigid_body_motion.md) and the polar
decomposition ($\boldsymbol{F} = \boldsymbol{R}\boldsymbol{U}$, see
[Continuum Mechanics](./continuum_mechanics.md#polar-decomposition))
already separate rotation from stretch in theory — a pure rotation
carries zero strain by construction. This page starts checking that
against real tracking, not just the closed-form math.

## The First Sweep

Reuse [Point Grid](./multi_point_motion.md#point-grid)'s 12 points and
sweep `rotate`'s `angle` upward. `rotate` pivots on the image's
top-left corner (0, 0), so each point's expected position after
rotation comes from the standard rotation matrix applied to its own
$(x, y)$ coordinate — not a fixed displacement, since points farther
from the pivot sweep a wider arc for the same angle. Size
`search_margin_width`/`search_margin_height` per angle so they always
comfortably contain the farthest point's displacement, the same
generous-margin approach [Recoverable Displacement
Range](./recoverable_displacement_range.md#the-first-sweep) used:

```python
from dictk.image import read, rotate, PixelCoordinate
from dictk.grid import generate, locate
import numpy as np

reference_image = read(path="astronaut0.png")
points = generate(
    origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55
)
kernel_margin = 20

def expected_position(pt, angle_deg):
    theta = np.deg2rad(angle_deg)
    c, s = np.cos(theta), np.sin(theta)
    x = c * pt.x - s * pt.y
    y = s * pt.x + c * pt.y
    return PixelCoordinate(x=int(round(x)), y=int(round(y)))

for angle in [0.5, 1, 1.5, 2, 3, 5, 8, 15]:
    current_image = rotate(arr=reference_image, angle=angle)
    expected = [expected_position(pt, angle) for pt in points]
    max_disp = max(max(abs(e.x - pt.x), abs(e.y - pt.y)) for pt, e in zip(points, expected))
    search_margin = max(int(max_disp) + 15, kernel_margin + 10)
    found = locate(
        reference_image=reference_image, current_image=current_image, reference_points=points,
        kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin,
        search_margin_width=search_margin, search_margin_height=search_margin,
    )
    n_match = sum(1 for f, e in zip(found, expected) if f == e)
    print(f"{angle}deg  search_margin={search_margin}  matched={n_match}/12")
```

<!-- cmdrun python3 -c "from dictk.image import read, rotate, PixelCoordinate; from dictk.grid import generate, locate; import numpy as np; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; expected_position = lambda pt, a: PixelCoordinate(x=int(round(np.cos(np.deg2rad(a))*pt.x - np.sin(np.deg2rad(a))*pt.y)), y=int(round(np.sin(np.deg2rad(a))*pt.x + np.cos(np.deg2rad(a))*pt.y))); print('| Angle (deg) | search_margin | Matched |'); print('|---|---|---|'); [print(f'| {angle} | {sm} | {nm}/12 |') for angle in [0.5, 1, 1.5, 2, 3, 5, 8, 15] for expected in [[expected_position(pt, angle) for pt in points]] for max_disp in [max(max(abs(e.x-pt.x), abs(e.y-pt.y)) for pt,e in zip(points, expected))] for sm in [max(int(max_disp)+15, kernel_margin+10)] for found in [locate(reference_image=reference_image, current_image=rotate(arr=reference_image, angle=angle), reference_points=points, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=sm, search_margin_height=sm)] for nm in [sum(1 for f,e in zip(found,expected) if f==e)]]" -->

Matching collapses even faster than [Recoverable Displacement
Range](./recoverable_displacement_range.md#the-first-sweep)'s stretch
sweep did — well under half the points still match by 2 degrees, and
none do by 8 degrees. `search_margin` is generous at every angle here,
so window size isn't the constraint. Path Forward's own framing already
names the likely reason: a large enough rotation doesn't just move a
point, it turns the kernel's own content around that point, and a
translation-only search can't follow content that's rotating, not just
sliding. That hypothesis isn't confirmed yet — a future pass should
check it directly, the same way Recoverable Displacement Range ruled
hypotheses in or out one at a time before finding its real cause.
