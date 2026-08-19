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

<!-- cmdrun python3 -c "from dictk.image import PixelCoordinate; from dictk.grid import generate; points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); factor_x = 1.02; expected = [PixelCoordinate(x=int(p.x * factor_x), y=p.y) for p in points]; print('<table>'); print('<thead>'); print('<tr><th rowspan=\"2\">Point</th><th colspan=\"2\">Expected \$(x, y)\$</th></tr>'); print('<tr><th>\$x\$ (pixels)</th><th>\$y\$ (pixels)</th></tr>'); print('</thead>'); print('<tbody>'); [print(f'<tr><td>{i:02d}</td><td>{e.x}</td><td>{e.y}</td></tr>') for i, e in enumerate(expected)]; print('</tbody>'); print('</table>')" -->

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
[Recoverable Displacement Range](./recoverable_displacement_range.md) picks
up from here.

## Strain

Visualizing strain results is a combination of mathematical accuracy and
visual clarity. One might want to plot the "raw" data at the Gauss
points, since that is the location within the element where the FEA
solver actually calculates strain, making it the most accurate.
However, this manner of visualization causes jumps (discontinuities) at
element boundaries.

The professional standard is to calculate strain at the Gauss points,
extrapolate the results to the nodes, and then report the **nodal
average** from all adjacent elements to create a smooth contour plot.

For now, let's report the strain at the Gauss points.

`dictk` doesn't compute strain yet — [Finite Element
Method](./finite_element_method.md) covers the Q4 element formulation
and the deformation gradient $\boldsymbol{F}(\boldsymbol{X})$ strain is
built from, but no Gauss-point or mesh-level machinery exists in the
codebase to actually evaluate it on tracked points like the twelve
above. That's the next piece of work this page is waiting on.

## Data Download

Every image this page used is downloadable below, as a TIFF. Download
files individually, or all at once: one compressed zip file bundles
every full image (reference and current), every kernel, and every
search area.

```python
import zipfile
import imageio.v3 as iio

images = {"astronaut0.tiff": reference_image, "astronaut2.tiff": current_image}
for i, point in enumerate(points):
    origin = PixelCoordinate(x=point.x - kernel_margin, y=point.y - kernel_margin)
    images[f"kernel_{i:02d}.tiff"] = subimage(
        image=reference_image, origin=origin, width=2 * kernel_margin, height=2 * kernel_margin
    )
for i, point in enumerate(points):
    origin = PixelCoordinate(x=point.x - search_margin_width, y=point.y - search_margin_height)
    images[f"search_area_stretch_{i:02d}.tiff"] = subimage(
        image=current_image, origin=origin, width=2 * search_margin_width, height=2 * search_margin_height
    )

with zipfile.ZipFile("simple_stretch_data.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    for name, arr in images.items():
        zf.writestr(name, iio.imwrite("<bytes>", arr, extension=".tiff"))
```

<!-- cmdrun python3 -c "import zipfile, os; import imageio.v3 as iio; from dictk.image import read, PixelCoordinate, stretch, subimage; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; search_margin_width, search_margin_height = 48, 52; images = {'astronaut0.tiff': reference_image, 'astronaut2.tiff': current_image}; [images.__setitem__(f'kernel_{i:02d}.tiff', subimage(image=reference_image, origin=PixelCoordinate(x=p.x - kernel_margin, y=p.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin)) for i, p in enumerate(points)]; [images.__setitem__(f'search_area_stretch_{i:02d}.tiff', subimage(image=current_image, origin=PixelCoordinate(x=p.x - search_margin_width, y=p.y - search_margin_height), width=2 * search_margin_width, height=2 * search_margin_height)) for i, p in enumerate(points)]; zf = zipfile.ZipFile('simple_stretch_data.zip', 'w', zipfile.ZIP_DEFLATED); [zf.writestr(name, iio.imwrite('<bytes>', arr, extension='.tiff')) for name, arr in images.items()]; zf.close(); size_kb = os.path.getsize('simple_stretch_data.zip') / 1024; print(f'**Download all**: [simple_stretch_data.zip](simple_stretch_data.zip) ({len(images)} files, {size_kb:.0f} KB)')" -->

### Full Images

`astronaut0.tiff` is `reference_image` — identical to [Multi-Point
Motion's](./multi_point_motion.md#full-images) copy, since both pages
reuse the same reference image. `astronaut2.tiff` is `current_image`,
stretched by `factor_x=1.02` — named `astronaut2`, not `astronaut1`, to
stay distinct from Multi-Point Motion's *translated* current image,
which is a different file with different content:

```python
from dictk.image import write

write(arr=reference_image, path="astronaut0.tiff")
write(arr=current_image, path="astronaut2.tiff")
```

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch, write; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); write(arr=reference_image, path='astronaut0.tiff'); write(arr=current_image, path='astronaut2.tiff'); print('| File | Description |'); print('|---|---|'); print('| [astronaut0.tiff](astronaut0.tiff) | Reference image, 300x300 pixels (same as Multi-Point Motion) |'); print(f'| [astronaut2.tiff](astronaut2.tiff) | Current image, stretched by factor_x={factor_x} |')" -->

### Kernels

Kernels are unchanged from [Multi-Point
Motion](./multi_point_motion.md#kernels): the stretch only ever moves
`current_image`, and a kernel always comes from `reference_image`.
Regenerated here, byte-for-byte identical, for a self-contained download
set:

```python
from dictk.image import subimage, write

kernel_margin = 20
for i, point in enumerate(points):
    origin = PixelCoordinate(x=point.x - kernel_margin, y=point.y - kernel_margin)
    kernel = subimage(image=reference_image, origin=origin, width=2 * kernel_margin, height=2 * kernel_margin)
    write(arr=kernel, path=f"kernel_{i:02d}.tiff")
```

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, subimage, write; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; print('| File | Point | Origin (pixels) |'); print('|---|---|---|'); [ (lambda origin, kernel: (write(arr=kernel, path=f'kernel_{i:02d}.tiff'), print(f'| [kernel_{i:02d}.tiff](kernel_{i:02d}.tiff) | {i:02d} | ({origin.x}, {origin.y}) |')))(PixelCoordinate(x=p.x - kernel_margin, y=p.y - kernel_margin), subimage(image=reference_image, origin=PixelCoordinate(x=p.x - kernel_margin, y=p.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin)) for i, p in enumerate(points) ]" -->

### Search Areas

Search areas, unlike kernels, *are* different from Multi-Point Motion's:
they come from this page's `current_image` — the stretched one, not the
translated one. Named `search_area_stretch_*` to keep the two sets of
files distinct, still centered on each point's reference position:

```python
search_margin_width, search_margin_height = 48, 52
for i, point in enumerate(points):
    origin = PixelCoordinate(x=point.x - search_margin_width, y=point.y - search_margin_height)
    search_area = subimage(image=current_image, origin=origin, width=2 * search_margin_width, height=2 * search_margin_height)
    write(arr=search_area, path=f"search_area_stretch_{i:02d}.tiff")
```

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch, subimage, write; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); search_margin_width, search_margin_height = 48, 52; print('| File | Point | Origin (pixels) |'); print('|---|---|---|'); [ (lambda origin, search_area: (write(arr=search_area, path=f'search_area_stretch_{i:02d}.tiff'), print(f'| [search_area_stretch_{i:02d}.tiff](search_area_stretch_{i:02d}.tiff) | {i:02d} | ({origin.x}, {origin.y}) |')))(PixelCoordinate(x=p.x - search_margin_width, y=p.y - search_margin_height), subimage(image=current_image, origin=PixelCoordinate(x=p.x - search_margin_width, y=p.y - search_margin_height), width=2 * search_margin_width, height=2 * search_margin_height)) for i, p in enumerate(points) ]" -->

## Verification Against VIC-2D

[Path Forward](./path_forward.md#2026-08-11) names a direction worth
pursuing: running this book's own synthetic datasets through established
DIC software, and comparing directly against `dictk`'s own results. This
page's own `factor_x = 1.02` stretch was run through
[VIC-2D](https://www.correlatedsolutions.com/vic-2d/) (Correlated
Solutions, Inc.), independently of `dictk`. Unlike [Multi-Point
Motion](./multi_point_motion.md#verification-against-vic-2d)'s
comparison, this one isn't against a `dictk`-computed value —
`dictk` doesn't compute strain anywhere on this page yet, only
displacement — so it's checked directly against the closed-form
analytical strain a `factor_x = 1.02` stretch implies instead:

<figure>
    <a href="../verification/simple_stretch_result_vic.png" target="_blank" rel="noopener">
        <img src="../verification/simple_stretch_result_vic.png" alt="VIC-2D's measured exx (logarithmic Euler strain) field for the factor_x=1.02 stretch example, a striped noisy pattern averaging around 19900 microstrain, with a horizontal extensometer line annotated E0: 19905.2 microstrain" />
    </a>
    <figcaption>VIC-2D's own measured $e_{xx}$ (logarithmic/Euler strain) field for this page's <code>factor_x = 1.02</code> stretch (click to enlarge). The horizontal line is VIC-2D's own extensometer annotation, reading 19905.2 microstrain along that path.</figcaption>
</figure>

Across the 2682 subsets VIC-2D correlated successfully (180 more,
along the image's outer edge, masked out), $e_{xx}$ averages
19875.8 microstrain — close to, but noisier than,
[Multi-Point Motion](./multi_point_motion.md#verification-against-vic-2d)'s
displacement match, since strain is a spatial derivative of already-noisy
per-point displacement data, not a directly measured quantity. The
analytical logarithmic (true/Euler) strain a `factor_x = 1.02` stretch
implies is $\ln(1.02) \approx 19802.6$ microstrain —
VIC-2D's own mean lands within 0.4% of it.

The full, subset-by-subset VIC-2D output —
[`simple_stretch_vic_out.csv`](../verification/simple_stretch_vic_out.csv)
— is available for closer inspection: every subset's position,
displacement, strain, and correlation quality metrics, not just the
summary field shown above.
