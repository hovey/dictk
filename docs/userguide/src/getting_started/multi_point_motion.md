# Multi-Point Motion

[Single Point Motion](./single_point_motion.md) tracked exactly one point,
$P$, between a reference and current image. Real digital image correlation
work needs to track *many* points at once — a whole collection of tracked
points is exactly what a **finite element mesh**'s nodes are built from.
This page shows how to track many points simultaneously, and motivates the
connection to the **Finite Element Method (FEM)**.

## Point Grid

A grid of points spans some number of points along $x$ and along $y$,
with some spacing between adjacent points along each axis.
[`dictk.grid.generate`](../api/dictk/grid.html#generate) builds one: the
count of points along $x$ and along $y$ need not be equal, and the
spacing along $x$ and along $y$ need not be equal either — this is a
general rectangular collection of points, not necessarily a square or
uniformly-spaced one.

This page reuses `astronaut0`, the speckle pattern combined with the
astronaut photograph introduced in [Image
Generation](./image_generation.md#speckle--astronaut) — the same kind of
reference image [Single Point Motion](./single_point_motion.md) used
`checkerboard0` for, just a different one, to keep some visual variety
across this guide:

```python
from dictk.image import read, PixelCoordinate, point_grid_plot
from dictk.grid import generate

reference_image = read(path="astronaut0.png")

points = generate(
    origin=PixelCoordinate(x=50, y=50),
    count_x=5,
    count_y=4,
    spacing_x=45,
    spacing_y=55,
)
point_grid_plot(
    image=reference_image,
    points=points,
    figsize=(6.4, 4.8),
    path="multi_point_motion_grid.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, point_grid_plot; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=5, count_y=4, spacing_x=45, spacing_y=55); point_grid_plot(image=reference_image, points=points, figsize=(6.4, 4.8), path='multi_point_motion_grid.png'); print('Saved: multi_point_motion_grid.png')" -->
```

<figure>
    <img src="multi_point_motion_grid.png" alt="reference image astronaut0 with a 5x4 grid of 20 numbered points overlaid, labeled 00 through 19 in row-major order" />
    <figcaption>Reference image <code>astronaut0</code> with a 5x4 grid of 20 points (<code>count_x=5</code>, <code>count_y=4</code>), spaced 45 pixels apart along $x$ and 55 pixels apart along $y$ (<code>spacing_x=45</code>, <code>spacing_y=55</code>), labeled 00-19 in row-major order (top-left to bottom-right).</figcaption>
</figure>

## Finite Element Method

A finite element mesh is a collection of **nodes** (points) connected into
**elements** — small regions used to interpolate a quantity of interest
(e.g. displacement) across the whole domain. The point grid above is
exactly the kind of nodal point collection a mesh needs: to build a mesh
that tracks how an object deforms, first find where every one of its
nodes moved to.

[`dictk.grid.locate`](../api/dictk/grid.html#locate) does this: it calls
[`dictk.translation.locate`](../api/dictk/translation.html#locate) once
per point, returning every found position in one batched call, in the
same order as the points given to it. Reusing the same rigid-body
translation [Single Point Motion](./single_point_motion.md) introduced
($\delta \boldsymbol{p} = (-6, 8)$ pixels), now applied to `astronaut0` and
every point in the grid at once:

```python
from dictk.image import translate
from dictk.grid import locate

dx, dy = -6, 8
current_image = translate(arr=reference_image, dx=dx, dy=dy)

found = locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=15,
    kernel_margin_height=15,
    search_margin_width=30,
    search_margin_height=30,
)
point_grid_plot(
    image=current_image,
    points=found,
    figsize=(6.4, 4.8),
    path="multi_point_motion_found.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, point_grid_plot; from dictk.grid import generate, locate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=5, count_y=4, spacing_x=45, spacing_y=55); dx, dy = -6, 8; current_image = translate(arr=reference_image, dx=dx, dy=dy); found = locate(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=15, kernel_margin_height=15, search_margin_width=30, search_margin_height=30); point_grid_plot(image=current_image, points=found, figsize=(6.4, 4.8), path='multi_point_motion_found.png'); print('Saved: multi_point_motion_found.png')" -->
```

<figure>
    <img src="multi_point_motion_found.png" alt="current image astronaut0 shifted by (-6, 8) pixels, with the 20 found points overlaid at their new positions, still labeled 00 through 19" />
    <figcaption>Current image, translated by $\delta \boldsymbol{p} = (-6, 8)$ pixels, with all 20 points' found positions -- every one recovers the same known displacement, confirming rigid-body motion across the whole grid at once, not just at a single point.</figcaption>
</figure>

Choosing a kernel size relative to point spacing is a tradeoff: a kernel
needs to be large enough to contain enough distinctive texture to locate
reliably, but small enough that neighboring kernels don't just duplicate
each other's content. A common rule of thumb (with no hard requirement
behind it) is to space points roughly half a kernel's side length apart,
close to the `kernel_margin_width=15`/`spacing_x=45` ratio used above.

Once every node's current position is known, an actual finite element
mesh still needs one more thing this page doesn't provide: **element
connectivity** — which nodes join together into which elements. Building
that connectivity, and the element formulation it enables (shape
functions, strain, stress), is future work, not implemented here.
