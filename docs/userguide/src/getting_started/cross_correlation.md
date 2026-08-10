# Cross Correlation (CC)

**Cross-correlation** can be used to find where point $P$ in the `reference_image`
can be found in the `current_image`.

There are many different *implementations* of cross-correlation.  We discuss
the varied implementations in [Correlation Criteria](./correlation_criteria.md).
For now, it is sufficient to know only that cross-correlation is used to locate a point in a current
image given a known location of that same point in a reference image.
The current focus is to make the subordinate concepts underlying 
cross-correlation be well-defined and well-illustrated.

Let the **kernel** (also called a **subset**, **filter**, or
**convolution matrix**) be a rectangular region of `reference_image` centered on
$\boldsymbol{p}_0$, the vector that locates point $P$ from origin $O$ in the `reference_image`.
The kernel is a small, distinctive patch of the reference image
content that we want to locate within a subsequent image.

In the **needle in a haystack** idiom, the kernel is the needle, and the
haystack is `current_image`. To keep the search tractable, we don't
search the entire haystack — we constrain it to a **search area** (also
called the **area of interest (AOI)**, **search window**, or **scanning zone**).
The search area is a subimage of the `current_image`, centered on a `search_center`, which is a guess of roughly where $P$ ended up, not the answer
itself. 

While there are techniques derived from macro deformation metrics that can
provide a good first guess for the `search_center`, for simplicity, and since
the deformations are small, we reuse $\boldsymbol{p}_0$ itself as the `search_center`
in this example.

Because the kernel and search area are themselves **subimages** of a larger
image (see [Subimage Generation](./subimage.md#reference-frames)), each 
subimage has its **own** local frame:

* Let $\mathcal{K}$ be the reference frame of the kernel subimage.
* Let $\mathcal{S}$ be the reference frame of the search area subimage.

`reference_image`, `p0`, `current_image`, and `p1` are the same as in
[Single Point Motion](./single_point_motion.md#current-configuration-and-displacement):

```python
from dictk.image import read, translate, PixelCoordinate

reference_image = read(path="checkerboard0.png")
p0 = PixelCoordinate(x=100, y=75)
dx, dy = -6, 8
current_image = translate(arr=reference_image, dx=dx, dy=dy)
p1 = PixelCoordinate(x=p0.x + dx, y=p0.y + dy)
```

## Kernel

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
    figsize=(6.4, 4.8),
    path="single_point_motion_kernel.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, subimage_comparison_plot; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); kernel_margin = 25; kernel_origin = PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin); subimage_comparison_plot(image=reference_image, origin=kernel_origin, width=2 * kernel_margin, height=2 * kernel_margin, point=p0, point_color='orange', point_label='\$P\$', subimage_label='kernel', color='green', origin_label='\$K\$', source_origin_label='\$O\$', figsize=(6.4, 4.8), path='single_point_motion_kernel.png'); print('Saved: single_point_motion_kernel.png')" -->
```

<figure>
    <img src="single_point_motion_kernel.png" alt="kernel placement in the reference image with point P marked by an orange dot, and the extracted kernel itself with point P marked by an orange dot" />
    <figcaption>Left: the kernel (green box), a 50x50 region of <code>reference_image</code> centered on $\boldsymbol{p}_0$, with origin $\boldsymbol{r}_{OK/\mathcal{F}} = (75, 50)$ pixels (green dot); point $P$ itself is the orange dot at $\boldsymbol{p}_0 = (100, 75)$. Right: the extracted kernel, in its own local reference frame $\mathcal{K}$; the same point $P$ (orange dot) is now at $\boldsymbol{r}_{KP/\mathcal{K}} = (25, 25)$ pixels.</figcaption>
</figure>

The kernel has its own *local* coordinate system $\mathcal{K}$, with
origin $K$ at its top-left corner. Point $P$'s position is the same in
both frames, just expressed relative to a different origin:

$$\boldsymbol{r}_{OP/\mathcal{F}} = \boldsymbol{r}_{OK/\mathcal{F}} + \boldsymbol{r}_{KP/\mathcal{K}}$$

Since the kernel is centered on $\boldsymbol{p}_0$ with a 25-pixel margin,
$\boldsymbol{r}_{KP/\mathcal{K}} = (25, 25)$ pixels. Point $P$ always
sits at `(kernel_margin_width, kernel_margin_height)` within the kernel's
own frame, regardless of where the kernel came from in `reference_image`.

## Search Area

From `current_image`, extract the search area surrounding
`search_center` (here, $\boldsymbol{p}_0$ again, since it is currently our best guess), with a 50-pixel margin
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
    figsize=(6.4, 4.8),
    path="single_point_motion_search.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage_comparison_plot; reference_image = read(path='checkerboard0.png'); current_image = translate(arr=reference_image, dx=-6, dy=8); p0 = PixelCoordinate(x=100, y=75); search_margin = 50; search_center = p0; search_origin = PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin); subimage_comparison_plot(image=current_image, origin=search_origin, width=2 * search_margin, height=2 * search_margin, subimage_label='search area', origin_label='\$S\$', source_origin_label='\$O\$', figsize=(6.4, 4.8), path='single_point_motion_search.png'); print('Saved: single_point_motion_search.png')" -->
```

<figure>
    <img src="single_point_motion_search.png" alt="search area placement in the current image, and the extracted search area itself" />
    <figcaption>Left: the search area (red box), a 100x100 region of <code>current_image</code> centered on <code>search_center</code>, with origin $\boldsymbol{r}_{OS/\mathcal{F}} = (50, 25)$ pixels (red dot); the source image's own origin is labeled $O$, the search area's origin is labeled $S$. Right: the extracted search area on its own, in its own local reference frame $\mathcal{S}$, with origin $S$.</figcaption>
</figure>

The search area likewise has its own *local* frame $\mathcal{S}$, origin
$S$ at its top-left corner.  The location of $P'$ in the `current_image` is given by:

$$\boldsymbol{r}_{OP'/\mathcal{F}} = \boldsymbol{r}_{OS/\mathcal{F}} + \boldsymbol{r}_{SP'/\mathcal{S}}$$

The goal of the DIC process is to locate $P'$ by solving for the quantity
$\boldsymbol{r}_{SP'/\mathcal{S}}$.  The location of $P'$ in the search area's
local frame is the single unknown; all other vectors are known.

## Solution

The insight into the solution is to *further decompose*
$\boldsymbol{r}_{SP'/\mathcal{S}}$ into the sum of two additional vectors:

$$\boldsymbol{r}_{SP'/\mathcal{S}} = \boldsymbol{r}_{SK/\mathcal{S}} + \boldsymbol{r}_{KP/\mathcal{K}}$$

The second term, $\boldsymbol{r}_{KP/\mathcal{K}}$, is a known constant.  The first
term, $\boldsymbol{r}_{SK/\mathcal{S}}$, is unknown and can be calculated using
cross-correlation.  When the kernel and search area subimages align, their
cross-correlation is maximized.  We find the maximum cross-correlation to determine
$\boldsymbol{r}_{SK/\mathcal{S}}$ and thus calculate
$\boldsymbol{r}_{OP'/\mathcal{F}}$.

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
for $\boldsymbol{r}_{SK/\mathcal{S}}$. 
The `locate` function returns $\boldsymbol{p}_1$ directly (one does not assemble the
vector chain manually).

`phase_cross_correlation` is a Fourier-domain computation — every `locate`
call in this book takes that route under the hood, rather than sliding
the kernel across the search area one position at a time. [Correlation
Criteria](./correlation_criteria.md#fourier-domain) examines that
Fourier-domain implementation in greater depth, alongside the
spatial-domain CC, NCC, ZCC, and ZNCC criteria it complements.

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

## Windowing

`locate` also accepts an optional `windowing` parameter — the same one
[`dictk.correlation.phase_correlation`](../api/dictk/correlation.html#phase_correlation)
exposes, described in full on [Windowing](./windowing.md). Passing it
here reproduces the same point, still using only the two images and
$\boldsymbol{p}_0$:

```python
from dictk.correlation import WindowingMethod

found_hann = locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_point=p0,
    search_center=search_center,
    kernel_margin_width=kernel_margin,
    kernel_margin_height=kernel_margin,
    search_margin_width=search_margin,
    search_margin_height=search_margin,
    windowing=WindowingMethod.HANN,
)
print(f"found_hann = {found_hann}")
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.translation import locate; from dictk.correlation import WindowingMethod; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; search_margin = 50; search_center = p0; found_hann = locate(reference_image=reference_image, current_image=current_image, reference_point=p0, search_center=search_center, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=search_margin, search_margin_height=search_margin, windowing=WindowingMethod.HANN); print(f'found_hann = {found_hann}')" -->
```

`found_hann` matches `found` above exactly, $\boldsymbol{p}_1 = (94,
83)$ pixels — windowing changes the correlation surface `locate`
searches internally (see [Windowing](./windowing.md) and [Correlation
Visualization](./correlation_visualization.md#peak-prominence) for how
and why), not the answer, on this book's clean, noise-free synthetic
images.

## Visualizing the Solution

For illustration, we can back out $\boldsymbol{r}_{SK/\mathcal{S}}$ — the
one quantity `locate` finds via cross-correlation, everything else here
being known geometry — from `found` and the boxed equation above, and
draw the full chain $\boldsymbol{r}_{OS/\mathcal{F}} +
\boldsymbol{r}_{SK/\mathcal{S}} + \boldsymbol{r}_{KP/\mathcal{K}}$ on
`current_image`:

```python
from dictk.image import point_plot, ArrowAnnotation, BoxAnnotation, PointAnnotation

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
            head=found,
            color="cyan",
            label=r"$\boldsymbol{r}_{OP'/\mathcal{F}}$",
        ),
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0),
            head=search_origin,
            color="blue",
            label=r"$\boldsymbol{r}_{OS/\mathcal{F}}$: search area origin",
        ),
        ArrowAnnotation(
            tail=search_origin,
            head=kernel_found_origin,
            color="red",
            label=r"$\boldsymbol{r}_{SK/\mathcal{S}}$: kernel found in search area",
        ),
        ArrowAnnotation(
            tail=kernel_found_origin,
            head=found,
            color="green",
            label=r"$\boldsymbol{r}_{KP/\mathcal{K}}$: point within kernel",
        ),
    ],
    figsize=(6.4, 4.8),
    path="single_point_motion_solution_vectors.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, point_plot, ArrowAnnotation, BoxAnnotation, PointAnnotation; from dictk.translation import locate; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; search_margin = 50; search_center = p0; search_origin = PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin); found = locate(reference_image=reference_image, current_image=current_image, reference_point=p0, search_center=search_center, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=search_margin, search_margin_height=search_margin); r_sk = PixelCoordinate(x=found.x - search_origin.x - kernel_margin, y=found.y - search_origin.y - kernel_margin); kernel_found_origin = PixelCoordinate(x=search_origin.x + r_sk.x, y=search_origin.y + r_sk.y); image_height, image_width = current_image.shape; point_plot(image=current_image, boxes=[BoxAnnotation(origin=PixelCoordinate(x=0, y=0), width=image_width, height=image_height, color='blue', label='source image'), BoxAnnotation(origin=search_origin, width=2 * search_margin, height=2 * search_margin, color='red', label='search area'), BoxAnnotation(origin=kernel_found_origin, width=2 * kernel_margin, height=2 * kernel_margin, color='green', label='kernel')], points=[PointAnnotation(position=PixelCoordinate(x=0, y=0), label='\$O\$', color='blue'), PointAnnotation(position=search_origin, label='\$S\$', color='red'), PointAnnotation(position=kernel_found_origin, label='\$K\$', color='green'), PointAnnotation(position=found, label='\$P\$', color='black')], arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=found, color='cyan', label=r\"\$\boldsymbol{r}_{OP'/\mathcal{F}}\$\"), ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=search_origin, color='blue', label=r'\$\boldsymbol{r}_{OS/\mathcal{F}}\$: search area origin'), ArrowAnnotation(tail=search_origin, head=kernel_found_origin, color='red', label=r'\$\boldsymbol{r}_{SK/\mathcal{S}}\$: kernel found in search area'), ArrowAnnotation(tail=kernel_found_origin, head=found, color='green', label=r'\$\boldsymbol{r}_{KP/\mathcal{K}}\$: point within kernel')], figsize=(6.4, 4.8), path='single_point_motion_solution_vectors.png'); print('Saved: single_point_motion_solution_vectors.png')" -->
```

<figure>
    <img src="single_point_motion_solution_vectors.png" alt="chained vector solution: cyan shortcut arrow from origin directly to the found point, blue arrow from origin to search area origin, red arrow to the located kernel, green arrow to the found point, with a blue source-image box, a red search-area box, and a green kernel box drawn behind the arrows, and O, S, K, P labels drawn on top" />
    <figcaption>The current configuration $\boldsymbol{p}_1$ (tip of the cyan and green arrows) as the vector chain $\boldsymbol{r}_{OS/\mathcal{F}}$ (blue) $+\ \boldsymbol{r}_{SK/\mathcal{S}}$ (red) $+\ \boldsymbol{r}_{KP/\mathcal{K}}$ (green), equal to the direct shortcut $\boldsymbol{r}_{OP'/\mathcal{F}}$ (cyan), drawn on <code>current_image</code> — with the source image (blue box), search area (red box), and the kernel as found within it (green box) shown behind the arrows, each origin labeled: $O$, $S$, $K$, and the found point $P$.</figcaption>
</figure>

vector, value | description
:--- | ---
$\boldsymbol{r}_{OS/\mathcal{F}} = (50, 25)$ + | origin of the search area (blue arrow)
$\boldsymbol{r}_{SK/\mathcal{S}} = (19, 33)$ + | kernel located within the search area, from cross-correlation (red arrow)
$\boldsymbol{r}_{KP/\mathcal{K}} = (25, 25)$ = | point's fixed position within the kernel (green arrow)
$\boldsymbol{r}_{OP'/\mathcal{F}} = (94, 83)$ | current position $\boldsymbol{p}_1$, matching `found` above (cyan arrow)

> **NOTE:**
> Cross-correlation may be conceptualized as the sliding dot product of pixel
> values from the kernel with pixel values from the search area.  In this discussion
> we have described sliding the kernel across a stationary search area.
> The reverse, sliding the search area across a stationary kernel,
> is conceptually different but mathematically identical.  Both
> approaches yield the same result: $\boldsymbol{r}_{SK/\mathcal{S}}$, which
> locates the kernel frame in the search area frame.

Next: [Correlation Criteria](./correlation_criteria.md) defines the four
cross-correlation formulas and explains the Fourier-domain route `locate`
actually takes, and [Correlation
Visualization](./correlation_visualization.md) visualizes each of them on
this same kernel and search area.
