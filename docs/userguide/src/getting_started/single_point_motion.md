# Single Point Motion

Consider a single point $P$, fixed to a physical location on the object
being imaged. In the **reference image** $i_0$, this point is at a known
pixel location $\boldsymbol{r}_{OP/\mathcal{F}} = (100, 75)$ pixels — we
use the shorthand $\boldsymbol{p}_0$ for this **reference configuration**.
Between the reference image and a later **current image** $i_1$, the
object (and therefore $P$) may move. Finding $P$'s new location
$\boldsymbol{p}_1$ — its **current configuration** — in $i_1$, given only
$\boldsymbol{p}_0$, is the problem this page works through, using
[`dictk.translation.locate`](../api/dictk/translation.html#locate).

## Reference Configuration

The examples below reuse `checkerboard0`, the speckle pattern combined
with the checkerboard introduced in [Image
Generation](./image_generation.md#speckle--checkerboard) — here called
`reference_image`, matching `locate`'s own parameter name:

```python
from dictk.image import read, PixelCoordinate, point_plot, ArrowAnnotation

reference_image = read(path="checkerboard0.png")

p0 = PixelCoordinate(x=100, y=75)
point_plot(
    image=reference_image,
    arrows=[
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0), head=p0, color="orange", label="p0"
        )
    ],
    path="single_point_motion_p0.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, point_plot, ArrowAnnotation; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); point_plot(image=reference_image, arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p0, color='orange', label='p0')], path='single_point_motion_p0.png'); print('Saved: single_point_motion_p0.png')" -->
```

<figure>
    <img src="single_point_motion_p0.png" alt="reference image with reference configuration p0 marked by an orange arrow from the origin" />
    <figcaption>Reference image $i_0$ and reference configuration (orange arrow) $\boldsymbol{p}_0 = (100, 75)$ pixels.</figcaption>
</figure>

## Current Configuration and Displacement

For this page, the current image $i_1$ is generated with
[`dictk.image.translate`](../api/dictk/image.html#translate) (see [Image
Transformation](./transformation.md#pure-translation-rigid-body-motion)): every pixel of
`reference_image` shifts by the same `(dx, dy)`, a **rigid body
translation** — one of the simplest deformation categories (see [Image
Transformation](./transformation.md) for the full set). Because the whole
image moves together, point $P$'s new location follows directly:

```python
from dictk.image import translate

current_image = translate(arr=reference_image, dx=-6, dy=8)
p1 = PixelCoordinate(x=p0.x - 6, y=p0.y + 8)  # ground truth, known here by construction
```

We define the **displacement** of the point $\delta \boldsymbol{p}$ as the
relative motion between the reference configuration $\boldsymbol{p}_0$ and
the current configuration $\boldsymbol{p}_1$, such that

$$\boldsymbol{p}_0 + \delta \boldsymbol{p} := \boldsymbol{p}_1 \implies \delta \boldsymbol{p} = \boldsymbol{p}_1 - \boldsymbol{p}_0$$

so with $\boldsymbol{p}_1 = (94, 83)$ and $\boldsymbol{p}_0 = (100, 75)$,

$$\delta \boldsymbol{p} = (94, 83) - (100, 75) = (-6, 8) \; \text{pixels}$$

```python
point_plot(
    image=current_image,
    arrows=[
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0), head=p1, color="cyan", label="p1"
        ),
        ArrowAnnotation(tail=p0, head=p1, color="magenta", label="displacement"),
    ],
    path="single_point_motion_p1_displacement.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, point_plot, ArrowAnnotation; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); p1 = PixelCoordinate(x=p0.x - 6, y=p0.y + 8); point_plot(image=current_image, arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p1, color='cyan', label='p1'), ArrowAnnotation(tail=p0, head=p1, color='magenta', label='displacement')], path='single_point_motion_p1_displacement.png'); print('Saved: single_point_motion_p1_displacement.png')" -->
```

<figure>
    <img src="single_point_motion_p1_displacement.png" alt="current image with current configuration p1 marked by a cyan arrow from the origin, and displacement marked by a magenta arrow from p0 to p1" />
    <figcaption>Current image $i_1$ with current configuration (cyan arrow) $\boldsymbol{p}_1 = (94, 83)$ pixels, and displacement (magenta arrow) $\delta \boldsymbol{p} = (-6, 8)$ pixels.</figcaption>
</figure>

Of course, `p1` above was only known in advance because we generated
`current_image` ourselves with a known `translate`. In practice — a real
pair of DIC images — $\boldsymbol{p}_1$ is exactly what's unknown and
needs to be found. The rest of this page finds it using only
`reference_image`, `current_image`, and $\boldsymbol{p}_0$, the same
information available in the real case, to demonstrate that `locate`
recovers it correctly.

## Cross-Correlation

We use **cross-correlation** to find where point $P$ moved to. Let the
**kernel** — also called a **subset**, **filter**, or **convolution
matrix** — be a rectangular region of `reference_image` centered on
$\boldsymbol{p}_0$. The kernel is a small, distinctive patch of image
content that we want to locate within a subsequent image.

In the **needle in a haystack** idiom, the kernel is the needle, and the
haystack is `current_image`. To keep the search tractable, we don't
search the entire haystack — we constrain it to a **search area** (also
called a **search window**, **scanning zone**, or **area of interest
(AOI)**), a larger rectangular region of `current_image` centered on a
`search_center` — a guess of roughly where $P$ ended up, not the answer
itself. Here, with no better guess available, we reuse $\boldsymbol{p}_0$
itself as `search_center`.

Both the kernel and search area are themselves **subimages** of a larger
image — see [Subimage Generation](./subimage.md#reference-frames), where
every subimage has its own local frame. This page needs two such
subimages at once, so rather than reusing that page's generic
$\mathcal{G}$, each gets its own label below: $\mathcal{K}$ for the
kernel, $\mathcal{S}$ for the search area.

### Kernel

From `reference_image`, extract the kernel surrounding $\boldsymbol{p}_0$,
with a 25-pixel margin on every side (50x50 total):

```python
from dictk.image import subimage_comparison_plot

kernel_margin = 25
kernel_origin = PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin)
subimage_comparison_plot(
    image=reference_image,
    origin=kernel_origin,
    width=2 * kernel_margin,
    height=2 * kernel_margin,
    point=p0,
    point_color="orange",
    point_label="$P$",
    subimage_label="kernel",
    color="green",
    origin_label="$K$",
    source_origin_label="$O$",
    path="single_point_motion_kernel.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, subimage_comparison_plot; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); kernel_margin = 25; kernel_origin = PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin); subimage_comparison_plot(image=reference_image, origin=kernel_origin, width=2 * kernel_margin, height=2 * kernel_margin, point=p0, point_color='orange', point_label='\$P\$', subimage_label='kernel', color='green', origin_label='\$K\$', source_origin_label='\$O\$', path='single_point_motion_kernel.png'); print('Saved: single_point_motion_kernel.png')" -->
```

<figure>
    <img src="single_point_motion_kernel.png" alt="kernel placement in the reference image with point P marked by an orange dot, and the extracted kernel itself with point P marked by an orange dot" />
    <figcaption>Left: the kernel (green box), a 50x50 region of <code>reference_image</code> centered on $\boldsymbol{p}_0$, with origin $\boldsymbol{r}_{OK/\mathcal{F}} = (75, 50)$ pixels (green 'o'); point $P$ itself is the orange dot at $\boldsymbol{p}_0 = (100, 75)$. Right: the extracted kernel on its own, in its own local reference frame $\mathcal{K}$; the same point $P$ (orange dot) is now at $\boldsymbol{r}_{KP/\mathcal{K}} = (25, 25)$.</figcaption>
</figure>

The kernel has its own *local* coordinate system $\mathcal{K}$, with
origin $K$ at its top-left corner. Point $P$'s position is the same in
both frames, just expressed relative to a different origin:

$$\boldsymbol{r}_{OP/\mathcal{F}} = \boldsymbol{r}_{OK/\mathcal{F}} + \boldsymbol{r}_{KP/\mathcal{K}}$$

Since the kernel is centered on $\boldsymbol{p}_0$ with a 25-pixel margin,
$\boldsymbol{r}_{KP/\mathcal{K}} = (25, 25)$ pixels — point $P$ always
sits at `(kernel_margin_width, kernel_margin_height)` within the kernel's
own frame, regardless of where the kernel came from in `reference_image`.

### Search Area

From `current_image`, extract the search area surrounding
`search_center` (here, $\boldsymbol{p}_0$ again), with a 50-pixel margin
on every side (100x100 total):

```python
search_margin = 50
search_center = p0
search_origin = PixelCoordinate(
    x=search_center.x - search_margin, y=search_center.y - search_margin
)
subimage_comparison_plot(
    image=current_image,
    origin=search_origin,
    width=2 * search_margin,
    height=2 * search_margin,
    subimage_label="search area",
    origin_label="$S$",
    source_origin_label="$O$",
    path="single_point_motion_search.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage_comparison_plot; reference_image = read(path='checkerboard0.png'); current_image = translate(arr=reference_image, dx=-6, dy=8); p0 = PixelCoordinate(x=100, y=75); search_margin = 50; search_center = p0; search_origin = PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin); subimage_comparison_plot(image=current_image, origin=search_origin, width=2 * search_margin, height=2 * search_margin, subimage_label='search area', origin_label='\$S\$', source_origin_label='\$O\$', path='single_point_motion_search.png'); print('Saved: single_point_motion_search.png')" -->
```

<figure>
    <img src="single_point_motion_search.png" alt="search area placement in the current image, and the extracted search area itself" />
    <figcaption>Left: the search area (red box), a 100x100 region of <code>current_image</code> centered on <code>search_center</code>, with origin $\boldsymbol{r}_{OS/\mathcal{F}} = (50, 25)$ pixels (red 'o'); the source image's own origin is labeled $O$, the search area's origin is labeled $S$. Right: the extracted search area on its own, in its own local reference frame $\mathcal{S}$, with origin $S$ labeled.</figcaption>
</figure>

The search area likewise has its own local frame $\mathcal{S}$, origin
$S$ at its top-left corner:

$$\boldsymbol{r}_{OP'/\mathcal{F}} = \boldsymbol{r}_{OS/\mathcal{F}} + \boldsymbol{r}_{SP'/\mathcal{S}}$$

where $P'$ is point $P$'s current position — what we're trying to find.
$\boldsymbol{r}_{SP'/\mathcal{S}}$, its position within the search area's
local frame, is still unknown at this point.

### Solution

Cross-correlation fixes the search area and finds where the kernel's
content best aligns within it — the kernel's own origin $K$, located
relative to the search area's origin $S$: $\boldsymbol{r}_{SK/\mathcal{S}}$.
Once $K$ is located, $P$'s position within the search area follows from
the same kernel-local offset found above:

$$\boldsymbol{r}_{SP'/\mathcal{S}} = \boldsymbol{r}_{SK/\mathcal{S}} + \boldsymbol{r}_{KP/\mathcal{K}}$$

Substituting into the search area's equation gives the full chain from
the shared origin $O$ to $P'$:

$$
\boxed{
\boldsymbol{r}_{OP'/\mathcal{F}}
=
\boldsymbol{r}_{OS/\mathcal{F}}
+
\boldsymbol{r}_{SK/\mathcal{S}}
+
\boldsymbol{r}_{KP/\mathcal{K}}
}
$$

This is exactly what
[`dictk.translation.locate`](../api/dictk/translation.html#locate) computes
internally — via
[`skimage.registration.phase_cross_correlation`](https://scikit-image.org/docs/stable/api/skimage.registration.html#skimage.registration.phase_cross_correlation)
for $\boldsymbol{r}_{SK/\mathcal{S}}$ — so as a caller, you don't assemble
this chain by hand; `locate` returns $\boldsymbol{p}_1$ directly.

## Locating the Point

```python
from dictk.translation import locate

found = locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_point=p0,
    search_center=search_center,
    kernel_margin_width=kernel_margin,
    kernel_margin_height=kernel_margin,
    search_margin_width=search_margin,
    search_margin_height=search_margin,
)
print(f"found = {found}")
print(f"displacement = ({found.x - p0.x}, {found.y - p0.y})")
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.translation import locate; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; search_margin = 50; search_center = p0; found = locate(reference_image=reference_image, current_image=current_image, reference_point=p0, search_center=search_center, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=search_margin, search_margin_height=search_margin); print(f'found = {found}'); print(f'displacement = ({found.x - p0.x}, {found.y - p0.y})')" -->
```

`found` matches the ground-truth $\boldsymbol{p}_1 = (94, 83)$ pixels from
earlier, recovering the known displacement $\delta \boldsymbol{p} = (-6, 8)$
pixels using only the two images and $\boldsymbol{p}_0$ — exactly the
information available for a real (not synthetically generated) image
pair.

## Visualizing the Solution

For illustration, we can back out $\boldsymbol{r}_{SK/\mathcal{S}}$ — the
one quantity `locate` finds via cross-correlation, everything else here
being known geometry — from `found` and the boxed equation above, and
draw the full chain $\boldsymbol{r}_{OS/\mathcal{F}} +
\boldsymbol{r}_{SK/\mathcal{S}} + \boldsymbol{r}_{KP/\mathcal{K}}$ on
`current_image`:

```python
from dictk.image import BoxAnnotation, PointAnnotation

r_sk = PixelCoordinate(
    x=found.x - search_origin.x - kernel_margin,
    y=found.y - search_origin.y - kernel_margin,
)
kernel_found_origin = PixelCoordinate(
    x=search_origin.x + r_sk.x, y=search_origin.y + r_sk.y
)
image_height, image_width = current_image.shape
point_plot(
    image=current_image,
    boxes=[
        BoxAnnotation(
            origin=PixelCoordinate(x=0, y=0),
            width=image_width,
            height=image_height,
            color="blue",
            label="source image",
        ),
        BoxAnnotation(
            origin=search_origin,
            width=2 * search_margin,
            height=2 * search_margin,
            color="red",
            label="search area",
        ),
        BoxAnnotation(
            origin=kernel_found_origin,
            width=2 * kernel_margin,
            height=2 * kernel_margin,
            color="green",
            label="kernel",
        ),
    ],
    points=[
        PointAnnotation(position=PixelCoordinate(x=0, y=0), label="$O$", color="blue"),
        PointAnnotation(position=search_origin, label="$S$", color="red"),
        PointAnnotation(position=kernel_found_origin, label="$K$", color="green"),
        PointAnnotation(position=found, label="$P$", color="black"),
    ],
    arrows=[
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0),
            head=search_origin,
            color="blue",
            label="r_OS: search area origin",
        ),
        ArrowAnnotation(
            tail=search_origin,
            head=kernel_found_origin,
            color="orange",
            label="r_SK: kernel found in search area",
        ),
        ArrowAnnotation(
            tail=kernel_found_origin,
            head=found,
            color="black",
            label="r_KP: point within kernel",
        ),
    ],
    legend=False,
    path="single_point_motion_solution_vectors.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, point_plot, ArrowAnnotation, BoxAnnotation, PointAnnotation; from dictk.translation import locate; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; search_margin = 50; search_center = p0; search_origin = PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin); found = locate(reference_image=reference_image, current_image=current_image, reference_point=p0, search_center=search_center, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=search_margin, search_margin_height=search_margin); r_sk = PixelCoordinate(x=found.x - search_origin.x - kernel_margin, y=found.y - search_origin.y - kernel_margin); kernel_found_origin = PixelCoordinate(x=search_origin.x + r_sk.x, y=search_origin.y + r_sk.y); image_height, image_width = current_image.shape; point_plot(image=current_image, boxes=[BoxAnnotation(origin=PixelCoordinate(x=0, y=0), width=image_width, height=image_height, color='blue', label='source image'), BoxAnnotation(origin=search_origin, width=2 * search_margin, height=2 * search_margin, color='red', label='search area'), BoxAnnotation(origin=kernel_found_origin, width=2 * kernel_margin, height=2 * kernel_margin, color='green', label='kernel')], points=[PointAnnotation(position=PixelCoordinate(x=0, y=0), label='\$O\$', color='blue'), PointAnnotation(position=search_origin, label='\$S\$', color='red'), PointAnnotation(position=kernel_found_origin, label='\$K\$', color='green'), PointAnnotation(position=found, label='\$P\$', color='black')], arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=search_origin, color='blue', label='r_OS: search area origin'), ArrowAnnotation(tail=search_origin, head=kernel_found_origin, color='orange', label='r_SK: kernel found in search area'), ArrowAnnotation(tail=kernel_found_origin, head=found, color='black', label='r_KP: point within kernel')], legend=False, path='single_point_motion_solution_vectors.png'); print('Saved: single_point_motion_solution_vectors.png')" -->
```

<figure>
    <img src="single_point_motion_solution_vectors.png" alt="chained vector solution: blue arrow from origin to search area origin, orange arrow to the located kernel, black arrow to the found point, with a blue source-image box, a red search-area box, and a green kernel box drawn behind the arrows, and O, S, K, P labels drawn on top" />
    <figcaption>The current configuration $\boldsymbol{p}_1$ (tip of the black arrow) as the vector chain $\boldsymbol{r}_{OS/\mathcal{F}}$ (blue) $+\ \boldsymbol{r}_{SK/\mathcal{S}}$ (orange) $+\ \boldsymbol{r}_{KP/\mathcal{K}}$ (black), drawn on <code>current_image</code> — with the source image (blue box), search area (red box), and the kernel as found within it (green box) shown behind the arrows, each origin labeled: $O$, $S$, $K$, and the found point $P$.</figcaption>
</figure>

vector, value | description
:--- | ---
$\boldsymbol{r}_{OS/\mathcal{F}} = (50, 25)$ + | origin of the search area (blue arrow)
$\boldsymbol{r}_{SK/\mathcal{S}} = (19, 33)$ + | kernel located within the search area, from cross-correlation (orange arrow)
$\boldsymbol{r}_{KP/\mathcal{K}} = (25, 25)$ = | point's fixed position within the kernel (black arrow)
$\boldsymbol{r}_{OP'/\mathcal{F}} = (94, 83)$ | current position $\boldsymbol{p}_1$, matching `found` above
