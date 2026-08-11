# Simple Stretch

[Multi-Point Motion](./multi_point_motion.md) tracked a grid of points under
**rigid-body translation** — every point moves by the same $(\delta x, \delta
y)$, so [Single Point Motion](./single_point_motion.md)'s known-integer-pixel
trick (choosing $\delta \boldsymbol{p} = (-6, 8)$ so the ground truth is exact,
not a sub-pixel estimate) carried over for free. A **stretch** is the next
step up in complexity: a genuine deformation, not just a rigid shift, where
different points move by different amounts. Getting the same exact-integer
ground truth here takes more care.

[`dictk.image.stretch`](../api/dictk/image.html#stretch) applies a uniaxial
or biaxial stretch pivoting at the image's origin $(0, 0)$: a point at $(x,
y)$ moves to $(x \cdot \text{factor}_x,\ y \cdot \text{factor}_y)$. Fixing
$\text{factor}_y = 1.0$ isolates the stretch to $x$ alone, so every point's
$y$ stays exactly as-is — the only question is which $\text{factor}_x$
values keep every point's *new* $x$ an integer too, rather than landing
between pixels.

## Choosing an Integer-Safe Stretch Factor

[Point Grid](./multi_point_motion.md#point-grid)'s 12 points span only three
distinct $x$ values: 50, 100, and 150. Writing the stretch as a percentage
$p$, $\text{factor}_x = (100 + p) / 100$, and the new $x$ is:

$$x \cdot \frac{100 + p}{100}$$

For $x = 100$, this is just $100 + p$ — always an integer, for any integer
$p$. But $x = 50$ and $x = 150$ both carry a factor of $\frac{1}{2}$ once
divided by 100, so $(100 + p)$ itself must be even for *those* points to
land on an integer — which means $p$ must be even. Odd percentages (1%, 3%,
5%, ...) always leave $x = 50$ and $x = 150$ on a half-pixel.

That parity argument is exact in real-number math, but `factor_x` is a
64-bit float at runtime, and not every value that's mathematically an
integer survives that arithmetic unscathed — 1.1, for example, has no exact
binary floating-point representation, so `50 * 1.1` doesn't land on exactly
`55.0` even though the true product is. Checking every even percentage
directly against `dictk`'s actual points, rather than trusting the parity
argument alone:

```python
from dictk.image import PixelCoordinate
from dictk.grid import generate

points = generate(
    origin=PixelCoordinate(x=50, y=50),
    count_x=3,
    count_y=4,
    spacing_x=50,
    spacing_y=55,
)
xs = sorted({point.x for point in points})

for p in range(1, 21):
    factor = (100 + p) / 100
    exact = all((x * factor).is_integer() for x in xs)
    print(f"{p:2d}%  factor={factor!r}  all-integer={exact}")
```

```text
<!-- cmdrun python3 -c "from dictk.image import PixelCoordinate; from dictk.grid import generate; points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); xs = sorted({point.x for point in points}); [print(f'{p:2d}%  factor={(100 + p) / 100!r}  all-integer={all((x * ((100 + p) / 100)).is_integer() for x in xs)}') for p in range(1, 21)]" -->
```

The parity argument is necessary but not sufficient: every odd percentage
fails as predicted, but so do several even ones (10%, 12%, 14%, 16%) purely
from floating-point representation error, not the underlying math. Of the
percentages that survive both checks, **2% is the smallest** — the least
aggressive stretch that still keeps every point's ground-truth position an
exact pixel, with `factor_x = 1.02` giving new $x$ values of 51, 102, and
153.

## Applying the Stretch

Reuse `points` and `reference_image` from [Point
Grid](./multi_point_motion.md#point-grid).
[`dictk.image.stretch`](../api/dictk/image.html#stretch) builds `current_image`:

```python
from dictk.image import read, stretch, PixelCoordinate

reference_image = read(path="astronaut0.png")
factor_x = 1.02
current_image = stretch(arr=reference_image, factor_x=factor_x)
```

`factor_y` defaults to `1.0`. Every point's $y$ stays fixed. Only $x$
changes, and by a different amount for each point:

```python
expected = [
    PixelCoordinate(x=int(point.x * factor_x), y=point.y)
    for point in points
]
```

```text
<!-- cmdrun python3 -c "from dictk.image import PixelCoordinate; from dictk.grid import generate; points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); factor_x = 1.02; expected = [PixelCoordinate(x=int(p.x * factor_x), y=p.y) for p in points]; print('| Point | expected x | expected y |'); print('|---|---|---|'); [print(f'| {i:02d} | {e.x} | {e.y} |') for i, e in enumerate(expected)]" -->
```

This is a real deformation, not a rigid shift. [Multi-Point
Motion](./multi_point_motion.md) moved every point by the same $(\delta x,
\delta y)$. A stretch moves each point by a different amount. A point at
$x = 50$ moves 1 pixel. A point at $x = 150$ moves 3 pixels. The grid
spreads apart under the stretch. It does not translate as one block.

## Locating the Stretched Grid

[`dictk.grid.locate`](../api/dictk/grid.html#locate) tracks the stretched
grid the same way it tracked the translated one in [Tracking the
Grid](./multi_point_motion.md#tracking-the-grid). Reuse the same kernel
and search-area margins:

```python
from dictk.grid import locate

found = locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=20,
    kernel_margin_height=20,
    search_margin_width=48,
    search_margin_height=52,
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch; from dictk.grid import generate, locate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); expected = [PixelCoordinate(x=int(p.x * factor_x), y=p.y) for p in points]; found = locate(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52); print('Point  found        expected     match'); [print(f'{i:02d}     {f.x:4d},{f.y:<4d}   {e.x:4d},{e.y:<4d}   {f == e}') for i, (f, e) in enumerate(zip(found, expected))]" -->
```

```python
from dictk.image import point_grid_plot

point_grid_plot(
    image=current_image,
    points=found,
    color="orange",
    figsize=(6.4, 4.8),
    path="simple_stretch_current.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch, point_grid_plot; from dictk.grid import generate, locate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); found = locate(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52); point_grid_plot(image=current_image, points=found, color='orange', figsize=(6.4, 4.8), path='simple_stretch_current.png'); print('Saved: simple_stretch_current.png')" -->
```

<figure>
    <img src="simple_stretch_current.png" alt="stretched current image astronaut0 with the 12 found points overlaid in orange, still labeled 00 through 11" />
    <figcaption>The stretched current image, with all 12 found positions marked. Every found position matches its expected stretched position exactly.</figcaption>
</figure>

Every found position matches the expected stretched position exactly.
The stretch introduces no sub-pixel error at these 12 points. [Multi-Point
Motion](./multi_point_motion.md) established this exact-integer guarantee
for rigid translation. This page confirms it holds under a real
deformation too.

Twelve points, twelve independent correlations, whether the underlying
motion is a rigid shift or a stretch:
[Parallelization](./parallelization.md) picks up from here.
