# Subpixel Accuracy

[`dictk.translation.locate`](../api/dictk/translation.html#locate)'s
own docstring has said this from the start: "Integer-pixel precision
only; subpixel refinement is out of scope for now." [Simple Stretch
Revisited](./simple_stretch.html#simple-stretch-revisited) found the
concrete case where that limitation actually bites. At VIC-2D's own
point density — 5 pixels apart — most points' true stretched position
isn't an integer at all. `locate` can only ever report a whole pixel,
so it's necessarily wrong by some amount for those points. That's not
a tracking failure. It's the wrong question being asked.

## What `locate` Actually Rounds Away

`skimage.registration.phase_cross_correlation`, the FFT-based
correlation `locate` runs, doesn't only find whole-pixel peaks. Its own
`upsample_factor` parameter refines that peak to within `1 /
upsample_factor` of a pixel. `locate` never uses it — every result gets
truncated to the nearest whole pixel with `int()` before it's returned.

[`dictk.translation.locate_subpixel`](../api/dictk/translation.html#locate_subpixel)
and its batch counterpart,
[`dictk.grid.locate_subpixel`](../api/dictk/grid.html#locate_subpixel),
are new, separate functions — not a parameter added to `locate` itself,
so `locate`'s own return type never changes shape based on an argument.
They pass `upsample_factor` straight through, and return the refined
position directly, undiscarded, as a
[`dictk.image.SubpixelCoordinate`](../api/dictk/image.html#SubpixelCoordinate)
— the same `(x, y)` shape as `PixelCoordinate`, but `float`, not `int`.

## Measuring the Difference

Reusing Simple Stretch Revisited's own scenario — `astronaut0.png`,
`factor_x = 1.02` — at VIC-2D's own 5-pixel spacing across the whole
image, 2862 points:

```python
from dictk.grid import generate, locate, locate_subpixel

points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)
true_x = [point.x * factor_x for point in points]

integer_found = locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=20,
    kernel_margin_height=20,
    search_margin_width=48,
    search_margin_height=52,
)
subpixel_found = locate_subpixel(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=20,
    kernel_margin_height=20,
    search_margin_width=48,
    search_margin_height=52,
    upsample_factor=10,
)
```

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch; from dictk.grid import generate, locate, locate_subpixel; import numpy as np; reference_image = read(path='astronaut0.png'); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); points = generate(origin=PixelCoordinate(x=18, y=16), count_x=53, count_y=54, spacing_x=5, spacing_y=5); true_x = np.array([p.x * factor_x for p in points]); kwargs = dict(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52); integer_found = locate(**kwargs); exact = sum(1 for f, p in zip(integer_found, points) if f.x == int(p.x * factor_x)); integer_err = np.array([abs(f.x - tx) for f, tx in zip(integer_found, true_x)]); print('| Method | Mean abs error (px) | Max abs error (px) |'); print('|---|---|---|'); print(f'| \`locate()\` (integer, truncated) | {integer_err.mean():.4f} | {integer_err.max():.4f} |'); [ (lambda found: print(f'| \`locate_subpixel(upsample_factor={uf})\` | {np.array([abs(f.x - tx) for f, tx in zip(found, true_x)]).mean():.4f} | {np.array([abs(f.x - tx) for f, tx in zip(found, true_x)]).max():.4f} |'))(locate_subpixel(**kwargs, upsample_factor=uf)) for uf in [1, 10, 100] ]; print(); print(f'\`locate()\` lands on the exact expected integer pixel for {exact}/{len(points)} points ({100*exact/len(points):.0f}%) — the same interpolation confound Simple Stretch Revisited found and worked around, not a new one.')" -->

`upsample_factor=1` matches `locate`'s own error exactly — no
refinement requested, none applied. `upsample_factor=10` cuts the mean
error by roughly a third. `upsample_factor=100` barely improves on
`10` — diminishing returns past that point, for this scenario.

## Why This Isn't "Fixing" the Exact-Match Problem

`upsample_factor` does not make `locate`'s own truncated answer more
often correct. If the true target is `64.26`, no amount of refinement
turns that into a whole number — `locate_subpixel` reports something
close to `64.26` itself, not `64` or `65` more reliably. [Simple
Stretch Revisited](./simple_stretch.html#simple-stretch-revisited)
solved a different problem: it kept every point's $x$ restricted to
values where the true target genuinely *is* an integer, so `locate`
could report it exactly. This page accepts that most targets, at this
density, aren't integers at all, and asks how close tracking gets to
the real one instead. Two different, both legitimate, answers to the
same density problem.

This closes [Path Forward](./path_forward.html#postponed)'s own
Postponed subpixel-accuracy item — real displacements don't land on
exact pixels, and now `dictk` has a way to track them without
pretending otherwise. High Point Density picks this up next, at a
density Simple Stretch Revisited's own integer-safety constraint
couldn't reach.
