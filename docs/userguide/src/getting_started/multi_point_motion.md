# Multi-Point Motion

[Single Point Motion](./single_point_motion.md) tracked exactly one point,
$P$, between a reference and current image. Digital image correlation was
illustrated in the context of that single point.  Now, we turn to consider
*many* points at once.
A collection of tracked
points will serve as the **nodes** of a finite element mesh.
This page shows how to track many points simultaneously, and motivates the
connection to the **Finite Element Method (FEM)**.

## Point Grid

A **grid** is an ordered, sequential collection of points, arranged in a rectilinear
pattern. 
The function [`dictk.grid.generate`](../api/dictk/grid.html#generate) creates
a grid that spans some number of points along $x$ and along $y$,
with some spacing between adjacent points along each axis.
The count of points along $x$ and along $y$ need not be equal, and the
spacing along $x$ and along $y$ need not be equal either. The grid is a
general rectangular collection of points, not necessarily a square or
uniformly-spaced one. `spacing_x` and `spacing_y` are in pixels.

This page uses `astronaut0`, the speckle pattern combined with the
astronaut photograph introduced in [Image
Generation](./image_generation.md#speckle--astronaut).

```python
from dictk.image import read, PixelCoordinate
from dictk.plot import point_grid_plot
from dictk.grid import generate

reference_image = read(path="astronaut0.png")

points = generate(
    origin=PixelCoordinate(x=50, y=50),
    count_x=3,
    count_y=4,
    spacing_x=50,
    spacing_y=55,
)
point_grid_plot(
    image=reference_image,
    points=points,
    color="orange",
    figsize=(6.4, 4.8),
    path="multi_point_motion_grid.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate; from dictk.plot import point_grid_plot; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); point_grid_plot(image=reference_image, points=points, color='orange', figsize=(6.4, 4.8), path='multi_point_motion_grid.png'); print('Saved: multi_point_motion_grid.png')" -->
```

<figure>
    <img src="multi_point_motion_grid.png" alt="reference image astronaut0 with a 3x4 grid of 12 numbered points overlaid in orange, labeled 00 through 11 in row-major order" />
    <figcaption>Reference image <code>astronaut0</code> with a 3x4 grid of 12 points (<code>count_x=3</code>, <code>count_y=4</code>), spaced 50 pixels apart along $x$ and 55 pixels apart along $y$ (<code>spacing_x=50</code>, <code>spacing_y=55</code>), labeled 00-11 in row-major order (top-left to bottom-right).</figcaption>
</figure>

The reference coordinates $(X, Y)$ in pixels for each point follow:

<!-- cmdrun python3 -c "from dictk.image import PixelCoordinate; from dictk.grid import generate; points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); print('<table>'); print('<thead>'); print('<tr><th rowspan=\"2\">Point</th><th colspan=\"2\">Reference Configuration \$(X, Y)\$</th></tr>'); print('<tr><th>\$X\$ (pixels)</th><th>\$Y\$ (pixels)</th></tr>'); print('</thead>'); print('<tbody>'); [print(f'<tr><td>{i:02d}</td><td>{p.x}</td><td>{p.y}</td></tr>') for i, p in enumerate(points)]; print('</tbody>'); print('</table>')" -->

`dx, dy = -6, 8` is the same known rigid-body displacement that [Single Point
Motion](./single_point_motion.md#current-configuration-and-displacement)
gave `checkerboard0`. Applying it to `astronaut0` produces `current_image`:

```python
from dictk.image import translate

dx, dy = -6, 8
current_image = translate(arr=reference_image, dx=dx, dy=dy)
```

Every point will need a **kernel** (the patch of `reference_image` used to
identify it) and a **search area** (the region of `current_image` searched
for a match). Before tracking the grid, it helps to see both relative to
the point spacing.
[`dictk.plot.point_grid_boxes_plot`](../api/dictk/plot.html#point_grid_boxes_plot)
draws one box type per call, so kernel and search area each get their own
figure — each point's own box gets its own color and its own legend
entry (`kernel 00`, `kernel 01`, ..., `kernel 11`), cycling through a
12-color palette (using matplotlib's Tableau colormap):

```python
from dictk.plot import point_grid_boxes_plot

point_grid_boxes_plot(
    image=reference_image,
    points=points,
    margin_width=20,
    margin_height=20,
    label_prefix="kernel",
    figsize=(6.4, 4.8),
    path="multi_point_motion_kernels.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate; from dictk.plot import point_grid_boxes_plot; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); point_grid_boxes_plot(image=reference_image, points=points, margin_width=20, margin_height=20, label_prefix='kernel', figsize=(6.4, 4.8), path='multi_point_motion_kernels.png'); print('Saved: multi_point_motion_kernels.png')" -->
```

<figure>
    <img src="multi_point_motion_kernels.png" alt="reference image astronaut0 with each of the 12 points' kernel boxes overlaid, each in its own color, labeled kernel 00 through kernel 11" />
    <figcaption>Every point's kernel, each in its own color (<code>margin_width=20</code>, <code>margin_height=20</code>).</figcaption>
</figure>

The kernel comes from `reference_image`. The search area comes from
`current_image` instead — still centered on each point's *reference*
position (`search_centers` defaults to `reference_points`), since the
point's true displacement is exactly what tracking is trying to find:

```python
point_grid_boxes_plot(
    image=current_image,
    points=points,
    margin_width=48,
    margin_height=52,
    label_prefix="search area",
    figsize=(6.4, 4.8),
    path="multi_point_motion_search.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.plot import point_grid_boxes_plot; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); dx, dy = -6, 8; current_image = translate(arr=reference_image, dx=dx, dy=dy); point_grid_boxes_plot(image=current_image, points=points, margin_width=48, margin_height=52, label_prefix='search area', figsize=(6.4, 4.8), path='multi_point_motion_search.png'); print('Saved: multi_point_motion_search.png')" -->
```

<figure>
    <img src="multi_point_motion_search.png" alt="current image astronaut0, shifted by (-6, 8) pixels, with each of the 12 points' search-area boxes overlaid, each in its own color, labeled search area 00 through search area 11" />
    <figcaption>Every point's search area, each in its own color (<code>margin_width=48</code>, <code>margin_height=52</code>), drawn on <code>current_image</code> — the region actually searched — and still centered on each point's reference position.</figcaption>
</figure>

## Tracking the Grid

Choosing a kernel size relative to point spacing is a tradeoff: a kernel
needs to be large enough to contain enough distinctive texture to locate
reliably, but small enough that neighboring kernels don't just duplicate
each other's content.

A common rule of thumb (with no hard requirement
behind it) is to space points roughly half a kernel's side length apart.
A kernel's full side length is twice its margin, so `kernel_margin_width`
and `kernel_margin_height` are themselves already exactly half that side
length — meaning the **rule of thumb** reduces to a simple comparison: **each
margin should be close to the point spacing itself**, without exceeding it (past
that point, neighboring kernels start overlapping).

The point spacing above is 50 pixels in $x$ and 55 pixels in $y$
(`spacing_x=50`, `spacing_y=55`). Keeping the kernel isotropic (a single
margin for both axes, `kernel_margin_width=kernel_margin_height`) means
the *smaller* of the two spacings is the binding constraint: a margin
greater than 25 pixels would overlap its $x$-neighbor, since $2 \times 25 = 50$ is
already the full spacing in $x$. That value, 25, is therefore the largest isotropic
margin with zero overlap — but right at that ceiling, adjacent kernels
touch exactly, sharing a boundary with no gap at all. 

The kernel figure
above backs off from that ceiling on purpose: `kernel_margin_width=20`,
`kernel_margin_height=20`, leaving a clear 10-pixel gap in $x$ and a
15-pixel gap in $y$, comfortably inside the no-overlap ceiling in both
directions, so every kernel's own boundary reads as visibly separate from
its neighbors', not merely non-overlapping.

The two numbers side by side make the relationship exact, not just
described:

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from dictk.image import PixelCoordinate

p0, p1, p2 = PixelCoordinate(x=50, y=50), PixelCoordinate(x=100, y=50), PixelCoordinate(x=150, y=50)
kernel_margin = 20

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, ax = plt.subplots(figsize=(7, 3.2), constrained_layout=True)

for p, label in [(p0, "00"), (p1, "01"), (p2, "02")]:
    ax.plot(p.x, p.y, "o", color="black", markersize=4)
    ax.annotate(label, (p.x, p.y), textcoords="offset points", xytext=(6, 6), fontsize=8)

for p in (p0, p1):
    ax.add_patch(patches.Rectangle(
        (p.x - kernel_margin, p.y - kernel_margin),
        2 * kernel_margin, 2 * kernel_margin,
        edgecolor="green", facecolor="none", linewidth=1.5,
    ))

box_top = p0.y - kernel_margin      # 30
box_bottom = p0.y + kernel_margin   # 70

# 50-pixel point spacing. The dashed guide lines start near each point
# (nearly touching its marker) and run down through its kernel box to
# the dimension line just below the boxes. Arrow flush with the dashed
# lines (shrinkA/shrinkB=0); label centered at the true midpoint between
# the box bottom and the dimension line.
dim_y = box_bottom + 8
for p in (p0, p1):
    ax.plot([p.x, p.x], [p.y + 3, dim_y], color="gray", linestyle="--", linewidth=0.8)
ax.annotate("", xy=(p0.x, dim_y), xytext=(p1.x, dim_y), arrowprops=dict(arrowstyle="<->", color="black", shrinkA=0, shrinkB=0))
ax.text((p0.x + p1.x) / 2, (box_bottom + dim_y) / 2, "50 px", ha="center", va="center", fontsize=9)

# 40-pixel kernel width, flush with the box's own left/right edges
# (shrinkA/shrinkB=0 so the arrow isn't inset from those edges).
top_y = box_top - 10
ax.annotate("", xy=(p0.x - kernel_margin, top_y), xytext=(p0.x + kernel_margin, top_y), arrowprops=dict(arrowstyle="<->", color="green", shrinkA=0, shrinkB=0))
ax.text(p0.x, top_y - 4, "40 px", ha="center", va="bottom", fontsize=8, color="green")

# 10-pixel gap between the two kernels' facing edges, moved up to the
# boxes' shared top edge, flush with the box's own edges (shrinkA/
# shrinkB=0), with the label on top of the dimension line.
gap_y = box_top - 2
ax.annotate("", xy=(p0.x + kernel_margin, gap_y), xytext=(p1.x - kernel_margin, gap_y), arrowprops=dict(arrowstyle="<->", color="tab:red", shrinkA=0, shrinkB=0))
ax.text(p0.x + kernel_margin + (p1.x - kernel_margin - (p0.x + kernel_margin)) / 2, gap_y - 4, "10 px", ha="center", va="bottom", fontsize=7, color="tab:red")

ax.set_xlim(15, 175)
ax.set_ylim(84, 8)

# Tick marks: 50/100/150 in x (the point positions), 40 pixels apart
# starting at 20; every 10 pixels in y, but text labels only at
# 30/50/70 (the box's top edge, the point row, and the box's bottom
# edge) -- a tight range with no dead space below the boxes, since the
# dimension line sits just beneath them.
xticks = list(range(20, 161, 10))
ax.set_xticks(xticks)
ax.set_xticklabels([str(v) if v in (50, 100, 150) else "" for v in xticks])
yticks = list(range(20, 81, 10))
ax.set_yticks(yticks)
ax.set_yticklabels([str(v) if v in (30, 50, 70) else "" for v in yticks])

ax.set_xlabel("x (pixels)")
ax.set_ylabel("y (pixels)")
ax.set_aspect("equal")
fig.savefig("multi_point_motion_spacing.png", dpi=300)
```

```text
<!-- cmdrun python3 -c "import matplotlib.pyplot as plt; import matplotlib.patches as patches; from dictk.image import PixelCoordinate; p0, p1, p2 = PixelCoordinate(x=50, y=50), PixelCoordinate(x=100, y=50), PixelCoordinate(x=150, y=50); kernel_margin = 20; plt.rcParams.update({'font.family': 'serif', 'mathtext.fontset': 'cm'}); fig, ax = plt.subplots(figsize=(7, 3.2), constrained_layout=True); [ (ax.plot(p.x, p.y, 'o', color='black', markersize=4), ax.annotate(label, (p.x, p.y), textcoords='offset points', xytext=(6, 6), fontsize=8)) for p, label in [(p0, '00'), (p1, '01'), (p2, '02')] ]; [ax.add_patch(patches.Rectangle((p.x - kernel_margin, p.y - kernel_margin), 2 * kernel_margin, 2 * kernel_margin, edgecolor='green', facecolor='none', linewidth=1.5)) for p in (p0, p1)]; box_top = p0.y - kernel_margin; box_bottom = p0.y + kernel_margin; dim_y = box_bottom + 8; [ax.plot([p.x, p.x], [p.y + 3, dim_y], color='gray', linestyle='--', linewidth=0.8) for p in (p0, p1)]; ax.annotate('', xy=(p0.x, dim_y), xytext=(p1.x, dim_y), arrowprops=dict(arrowstyle='<->', color='black', shrinkA=0, shrinkB=0)); ax.text((p0.x + p1.x) / 2, (box_bottom + dim_y) / 2, '50 px', ha='center', va='center', fontsize=9); top_y = box_top - 10; ax.annotate('', xy=(p0.x - kernel_margin, top_y), xytext=(p0.x + kernel_margin, top_y), arrowprops=dict(arrowstyle='<->', color='green', shrinkA=0, shrinkB=0)); ax.text(p0.x, top_y - 4, '40 px', ha='center', va='bottom', fontsize=8, color='green'); gap_y = box_top - 2; ax.annotate('', xy=(p0.x + kernel_margin, gap_y), xytext=(p1.x - kernel_margin, gap_y), arrowprops=dict(arrowstyle='<->', color='tab:red', shrinkA=0, shrinkB=0)); ax.text(p0.x + kernel_margin + (p1.x - kernel_margin - (p0.x + kernel_margin)) / 2, gap_y - 4, '10 px', ha='center', va='bottom', fontsize=7, color='tab:red'); ax.set_xlim(15, 175); ax.set_ylim(84, 8); xticks = list(range(20, 161, 10)); ax.set_xticks(xticks); ax.set_xticklabels([str(v) if v in (50, 100, 150) else '' for v in xticks]); yticks = list(range(20, 81, 10)); ax.set_yticks(yticks); ax.set_yticklabels([str(v) if v in (30, 50, 70) else '' for v in yticks]); ax.set_xlabel('x (pixels)'); ax.set_ylabel('y (pixels)'); ax.set_aspect('equal'); fig.savefig('multi_point_motion_spacing.png', dpi=300); print('Saved: multi_point_motion_spacing.png')" -->
```

<figure>
    <img src="multi_point_motion_spacing.png" alt="two green 40x40 pixel kernel boxes centered on points 00 and 01, 50 pixels apart, with a third point 02 shown for context; dimension arrows show 40 px across each kernel, 50 px between point centers, and 10 px in the gap between the two kernels' facing edges" />
    <figcaption>Points 00 and 01, 50 pixels apart, each with its own 40x40 kernel (green). The 10-pixel gap between the two boxes is exactly $50 - 40$ — the point spacing minus the kernel's own full side length, with nothing left over to round away.</figcaption>
</figure>

Nothing requires the kernel to be isotropic — `dictk` supports an
independent margin per axis just as easily. The equal `20`/`20` above is
a deliberate choice to illustrate that `dictk` supports both isotropic and
non-isotropic margins, not a consequence of `spacing_x` and `spacing_y`
being unequal forcing one shape or the other.

The search area, by contrast, keeps a clearly
non-isotropic shape: `search_margin_width=48`, `search_margin_height=52`
— just under the point spacing itself, comfortably containing the known
$(-6, 8)$-pixel displacement with plenty of room to spare, while staying
just shy of `spacing_x`/`spacing_y` rather than matching them outright.

That much slack still means search areas overlap their neighbors heavily
and run off the image at the edges, which is harmless:
[`subimage`](../api/dictk/image.html#subimage) zero-pads whatever falls
outside `current_image`. Unlike kernels, search areas that overlap cost
nothing aside from redundant computation; there's no accuracy downside to
searching the same region for two different points.

One important practical detail: `phase_cross_correlation`
requires the kernel and search area to be exactly the same shape. So
[`dictk.translation.locate`](../api/dictk/translation.html#locate) doesn't
crop the search area down to the kernel's size; rather, it zero-pads the kernel up to match the search area's size. Here a
40x40 kernel is zero-padded up to the search area's 96x104 size.

> **Note:** In practice, kernel size has little effect on FFT runtime once a search area is chosen — the transform zero-pads the kernel up to match the search area's own size. Shrinking an already-small kernel further doesn't make the correlation any faster.

[Single Point Motion](./single_point_motion.md#current-configuration-and-displacement)
confirmed that a single point's found position matches a known
displacement exactly. Reuse `current_image` from [Point
Grid](#point-grid) — the same $\delta \boldsymbol{p} = (-6, 8)$-pixel
displacement. The same idea, applied to all 12 points in the grid at
once, is exactly what a real DIC workflow looks like.

[`dictk.grid.locate`](../api/dictk/grid.html#locate) tracks all 12 points
in one call. It doesn't do the correlation itself — it calls
[`dictk.translation.locate`](../api/dictk/translation.html#locate) once
per point, and *that* function is `dictk`'s actual FFT-based DIC engine: for
each point it extracts a kernel from `reference_image` and a search area
from `current_image`, then locates the kernel within the search area via
`skimage.registration.phase_cross_correlation` — FFT-based phase
cross-correlation, not a spatial-domain sliding-window search (see
[Correlation Criteria](./correlation_criteria.md#fourier-domain) for the
single-point version of this same technique).
Twelve points means twelve independent calls into that engine, using the
same kernel and search-area sizes visualized above:

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
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.grid import generate, locate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); dx, dy = -6, 8; current_image = translate(arr=reference_image, dx=dx, dy=dy); found = locate(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52); expected = [PixelCoordinate(x=p.x + dx, y=p.y + dy) for p in points]; print('Point  found        expected     match'); [print(f'{i:02d}    {f.x:4d},{f.y:<4d}   {e.x:4d},{e.y:<4d}     {f == e}') for i, (f, e) in enumerate(zip(found, expected))]" -->
```

Every one of the 12 found positions matches `reference_points[i] + (dx,
dy)` exactly — not approximately, the same exact-integer-pixel guarantee
[Single Point Motion](./single_point_motion.md) established for one point,
now confirmed across the whole grid at once:

```python
from dictk.plot import point_grid_plot

point_grid_plot(
    image=current_image,
    points=found,
    color="orange",
    figsize=(6.4, 4.8),
    path="multi_point_motion_found.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.plot import point_grid_plot; from dictk.grid import generate, locate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); dx, dy = -6, 8; current_image = translate(arr=reference_image, dx=dx, dy=dy); found = locate(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52); point_grid_plot(image=current_image, points=found, color='orange', figsize=(6.4, 4.8), path='multi_point_motion_found.png'); print('Saved: multi_point_motion_found.png')" -->
```

<figure>
    <img src="multi_point_motion_found.png" alt="current image astronaut0 shifted by (-6, 8) pixels, with the 12 found points overlaid in orange at their new positions, still labeled 00 through 11" />
    <figcaption>Current image, translated by $\delta \boldsymbol{p} = (-6, 8)$ pixels, with all 12 points' found positions — every one recovers the same known displacement, confirming rigid-body motion across the whole grid at once, not just at a single point.</figcaption>
</figure>

That every point was found exactly is expected, not a coincidence: the
kernel margins above were chosen to roughly follow the rule of thumb, not
to violate it. What the rule of thumb actually buys is robustness, not
correctness on an easy case like this one — a kernel needs enough
distinctive texture to locate reliably, and `astronaut0` is a clean,
synthetic image with strong texture everywhere and no noise. A smaller,
more aggressively undersized kernel would likely still have worked here
too; it's on real, noisier imagery, or content with repetitive texture,
that a larger kernel's extra context resolves an ambiguity a smaller one
can't.

## Data Download

Every image this page used is downloadable below, as a TIFF. Download
files individually, or all at once: one compressed zip file bundles
every full image (reference and current), every kernel, and every
search area.

```python
import zipfile
import imageio.v3 as iio

images = {"astronaut0.tiff": reference_image, "astronaut1.tiff": current_image}
for i, point in enumerate(points):
    origin = PixelCoordinate(x=point.x - kernel_margin, y=point.y - kernel_margin)
    images[f"kernel_{i:02d}.tiff"] = subimage(
        image=reference_image, origin=origin, width=2 * kernel_margin, height=2 * kernel_margin
    )
for i, point in enumerate(points):
    origin = PixelCoordinate(x=point.x - search_margin_width, y=point.y - search_margin_height)
    images[f"search_area_{i:02d}.tiff"] = subimage(
        image=current_image, origin=origin, width=2 * search_margin_width, height=2 * search_margin_height
    )

with zipfile.ZipFile("multi_point_motion_data.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    for name, arr in images.items():
        zf.writestr(name, iio.imwrite("<bytes>", arr, extension=".tiff"))
```

<!-- cmdrun python3 -c "import zipfile, os; import imageio.v3 as iio; from dictk.image import read, translate, PixelCoordinate, subimage; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); dx, dy = -6, 8; current_image = translate(arr=reference_image, dx=dx, dy=dy); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; search_margin_width, search_margin_height = 48, 52; images = {'astronaut0.tiff': reference_image, 'astronaut1.tiff': current_image}; [images.__setitem__(f'kernel_{i:02d}.tiff', subimage(image=reference_image, origin=PixelCoordinate(x=p.x - kernel_margin, y=p.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin)) for i, p in enumerate(points)]; [images.__setitem__(f'search_area_{i:02d}.tiff', subimage(image=current_image, origin=PixelCoordinate(x=p.x - search_margin_width, y=p.y - search_margin_height), width=2 * search_margin_width, height=2 * search_margin_height)) for i, p in enumerate(points)]; zf = zipfile.ZipFile('multi_point_motion_data.zip', 'w', zipfile.ZIP_DEFLATED); [zf.writestr(name, iio.imwrite('<bytes>', arr, extension='.tiff')) for name, arr in images.items()]; zf.close(); size_kb = os.path.getsize('multi_point_motion_data.zip') / 1024; print(f'**Download all**: [multi_point_motion_data.zip](multi_point_motion_data.zip) ({len(images)} files, {size_kb:.0f} KB)')" -->

### Full Images

* `astronaut0.tiff` is `reference_image`.
* `astronaut1.tiff` is `current_image` — `reference_image` displaced down and to the left by $\delta \boldsymbol{p} = (-6, 8)$ pixels, the same displacement [Tracking the Grid](#tracking-the-grid) tracked:

```python
from dictk.image import write

write(arr=reference_image, path="astronaut0.tiff")
write(arr=current_image, path="astronaut1.tiff")
```

<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, write; reference_image = read(path='astronaut0.png'); dx, dy = -6, 8; current_image = translate(arr=reference_image, dx=dx, dy=dy); write(arr=reference_image, path='astronaut0.tiff'); write(arr=current_image, path='astronaut1.tiff'); print('| File | Description |'); print('|---|---|'); print('| [astronaut0.tiff](astronaut0.tiff) | Reference image, 300x300 pixels |'); print(f'| [astronaut1.tiff](astronaut1.tiff) | Current image, displaced by (dx, dy) = ({dx}, {dy}) pixels |')" -->

### Kernels

Every point's kernel, extracted from `reference_image` — the same 12
boxes shown in [Point Grid](#point-grid) (`kernel_margin_width=20`,
`kernel_margin_height=20`, 40x40 pixels each):

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

Every point's search area, extracted from `current_image` — not
`reference_image`, since a search area is always a region of the current
image (see [Point Grid](#point-grid)). The same 12 boxes shown there
(`search_margin_width=48`, `search_margin_height=52`, 96x104 pixels
each), still centered on each point's *reference* position:

```python
search_margin_width, search_margin_height = 48, 52
for i, point in enumerate(points):
    origin = PixelCoordinate(x=point.x - search_margin_width, y=point.y - search_margin_height)
    search_area = subimage(image=current_image, origin=origin, width=2 * search_margin_width, height=2 * search_margin_height)
    write(arr=search_area, path=f"search_area_{i:02d}.tiff")
```

<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage, write; from dictk.grid import generate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); dx, dy = -6, 8; current_image = translate(arr=reference_image, dx=dx, dy=dy); search_margin_width, search_margin_height = 48, 52; print('| File | Point | Origin (pixels) |'); print('|---|---|---|'); [ (lambda origin, search_area: (write(arr=search_area, path=f'search_area_{i:02d}.tiff'), print(f'| [search_area_{i:02d}.tiff](search_area_{i:02d}.tiff) | {i:02d} | ({origin.x}, {origin.y}) |')))(PixelCoordinate(x=p.x - search_margin_width, y=p.y - search_margin_height), subimage(image=current_image, origin=PixelCoordinate(x=p.x - search_margin_width, y=p.y - search_margin_height), width=2 * search_margin_width, height=2 * search_margin_height)) for i, p in enumerate(points) ]" -->

## Verification Against VIC-2D

In this section, we run this page's own `dx = -6`, `dy = 8` example through
[VIC-2D](https://www.correlatedsolutions.com/vic-2d/) (Correlated Solutions, Inc.),
a widely used commercial DIC package, to verify agreement with `dictk`.

<figure>
    <div style="display: flex; gap: 1em;">
        <a href="../verification/multi_point_motion_U_result_vic.png" target="_blank" rel="noopener" style="flex: 1 1 0; min-width: 0;">
            <img src="../verification/multi_point_motion_U_result_vic.png" alt="VIC-2D's recovered U (x-displacement) field for the dx=-6, dy=8 example, showing a uniform displacement of -6 pixels across the specimen" style="width: 100%;" />
        </a>
        <a href="../verification/multi_point_motion_V_result_vic.png" target="_blank" rel="noopener" style="flex: 1 1 0; min-width: 0;">
            <img src="../verification/multi_point_motion_V_result_vic.png" alt="VIC-2D's recovered V (y-displacement) field for the dx=-6, dy=8 example, showing a uniform displacement of -8 pixels across the specimen in VIC-2D's own sign convention" style="width: 100%;" />
        </a>
    </div>
    <figcaption>VIC-2D's own verified displacement fields for this page's <code>dx = -6</code>, <code>dy = 8</code> example (click either image for the full-size version): <code>U</code>, the x-axis displacement, uniformly -6 pixels (left, <code>multi_point_motion_U</code>); <code>V</code>, the y-axis displacement, uniformly -8 pixels (right, <code>multi_point_motion_V</code>) — VIC-2D's own $y$-axis points opposite <code>dictk</code>'s, so its sign is flipped from this page's <code>dy = 8</code> even though both describe the identical physical motion.</figcaption>
</figure>

Across the 2861 subsets VIC-2D correlated successfully (109 more, all
along the image's outer edge, fell outside the shifted current image and
were masked out rather than reported), `U` ranges from exactly $-6.0000$
to $-5.9998$ px and `V` from $-8.0003$ to $-8.0000$ px, in VIC-2D's own
$(U, V)$ columns (`u_c`/`v_c` in the raw output below). VIC-2D's own `V`
is measured with positive pointing up the page, opposite `dictk`'s
downward-positive $y$-axis. Once that sign difference is reconciled,
VIC-2D's result matches `dictk`'s own $-6$/$8$ px ground truth exactly.

The full, subset-by-subset VIC-2D output, 
[`multi_point_motion_vic_out.csv`](../verification/multi_point_motion_vic_out.csv), 
is available for closer inspection: every subset's position, displacement,
strain, and correlation quality metrics, not just the two summary fields
shown above. It carries two displacement column pairs: `u_c`/`v_c`
(VIC-2D's own convention, matching the two figures above exactly) and a
second `u`/`v` pair already expressed with `v`'s sign flipped to match
`dictk`'s downward-positive $y$ — `u`/`v` land on $-6$/$8$ px directly,
with no sign reconciliation needed to compare against `dictk`'s ground
truth.

## Next Steps

This page tracked rigid-body translation. Every point moved by the same
amount. [Simple Stretch](./simple_stretch.md) is next. It tracks a stretching
deformation, where each point moves by a different amount in the $x$ direction.
