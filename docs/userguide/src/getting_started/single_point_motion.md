# Single Point Motion

Consider a single point $P$, fixed to a physical location on the object
being imaged. In the **reference image** $i_0$, this point $P$ is located
at a *known* pixel location, for example $\boldsymbol{r}_{OP/\mathcal{F}} = (100, 75)$ pixels.
This vector, from the origin $O$ of the reference image frame $\mathcal{F}$
to the pixel point
$P$, locates the **reference configuration**.  For brevity, we will use
$\boldsymbol{p}_0$ to denote the fully explicit vector $\boldsymbol{r}_{OP/\mathcal{F}}$.

Next, the object is moved (e.g., translated, rotated, stretched, or deformed —
see [Image Transformation](./transformation.md)).  A second image $i_1$,
called the **current image**, is taken.  *Where is point $P$ from $i_0$ located
in $i_1$?*  We label point $P$'s *found* location in $i_1$ as $P'$.
For brevity, we will use $\boldsymbol{p}_1$
to denote the fully explicit vector $\boldsymbol{r}_{OP'/\mathcal{F}}$.

Note that the camera itself has not moved, only the object and any point of 
interest on the object have moved.  The origin $O$ and the reference frame $\mathcal{F}$
are the same across the two images $i_0$ and $i_1$.

The canonical problem solved by digital image correlation (DIC) is as follows:

* Given a point $P$ in image $i_0$, find the location of that same point $P'$ in image $i_1$.

Below, we motivate this canonical problem with a simple example of a single
point translation.  We first develop a manual solution to serve as the known
ground truth.  Then, we illustrate how 
[`dictk.translation.locate`](../api/dictk/translation.html#locate)
solves this problem numerically via DIC.

## Reference Configuration

The examples below reuse `checkerboard0`, the speckle pattern combined
with the checkerboard introduced in [Image
Generation](./image_generation.md#speckle--checkerboard).  This will be the
`reference_image`, matching `locate`'s own parameter name:

```python
from dictk.image import read, PixelCoordinate, point_plot, ArrowAnnotation

reference_image = read(path="checkerboard0.png")

p0 = PixelCoordinate(x=100, y=75)
point_plot(
    image=reference_image,
    arrows=[
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0), head=p0, color="orange", label=r"$\boldsymbol{p}_0$"
        )
    ],
    figsize=(6.4, 4.8),
    path="single_point_motion_p0.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, point_plot, ArrowAnnotation; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); point_plot(image=reference_image, arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p0, color='orange', label=r'\$\\boldsymbol{p}_0\$')], figsize=(6.4, 4.8), path='single_point_motion_p0.png'); print('Saved: single_point_motion_p0.png')" -->
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
translation**.  Because the whole
image moves together, point $P$'s new location follows directly:

```python
from dictk.image import translate

dx, dy = -6, 8
current_image = translate(arr=reference_image, dx=dx, dy=dy)
p1 = PixelCoordinate(x=p0.x + dx, y=p0.y + dy)  # ground truth, known here by construction
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
            tail=PixelCoordinate(x=0, y=0), head=p0, color="orange", label=r"$\boldsymbol{p}_0$"
        ),
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0), head=p1, color="cyan", label=r"$\boldsymbol{p}_1$"
        ),
        ArrowAnnotation(
            tail=p0, head=p1, color="magenta", label=r"$\delta \boldsymbol{p}$"
        ),
    ],
    figsize=(6.4, 4.8),
    path="single_point_motion_p1_displacement.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, point_plot, ArrowAnnotation; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); p1 = PixelCoordinate(x=p0.x - 6, y=p0.y + 8); point_plot(image=current_image, arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p0, color='orange', label=r'\$\\boldsymbol{p}_0\$'), ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p1, color='cyan', label=r'\$\\boldsymbol{p}_1\$'), ArrowAnnotation(tail=p0, head=p1, color='magenta', label=r'\$\delta \\boldsymbol{p}\$')], figsize=(6.4, 4.8), path='single_point_motion_p1_displacement.png'); print('Saved: single_point_motion_p1_displacement.png')" -->
```

<figure>
    <img src="single_point_motion_p1_displacement.png" alt="current image with reference configuration p0 marked by an orange arrow from the origin, current configuration p1 marked by a cyan arrow from the origin, and displacement marked by a magenta arrow from p0 to p1" />
    <figcaption>Current image $i_1$ with reference configuration (orange arrow) $\boldsymbol{p}_0 = (100, 75)$ pixels, current configuration (cyan arrow) $\boldsymbol{p}_1 = (94, 83)$ pixels, and displacement (magenta arrow) $\delta \boldsymbol{p} = (-6, 8)$ pixels.  Because the object has moved, the image shows a black margin on the top and right, with height 8 pixels and width 6 pixels, respectively, and cropping of the squares on the left and bottom of the image.</figcaption>
</figure>

In the example above, `p1` was only known in advance because we generated
`current_image` ourselves with a known `translate`. In practice, the
location $\boldsymbol{p}$ is unknown and found via DIC of a pair of images.

Below, we illustrate the canonical DIC process:

* Given a $\boldsymbol{p}_0$ in the `reference_image`, find $\boldsymbol{p}_1$
in the `current_image`.

We will see how the `locate` function calculates $\boldsymbol{p}_1$ directly.

## Cross-Correlation

The `locate` function uses **cross-correlation** to find where point $P$ in
the `reference_image` can be found in the `current_image`.
Let the **kernel** — also called a **subset**, **filter**, or **convolution
matrix** — be a rectangular region of `reference_image` centered on
$\boldsymbol{p}_0$. The kernel is a small, distinctive patch of the reference image
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
subimage has its own *local* frame:

* Let $\mathcal{K}$ be the reference frame of the kernel subimage.
* Let $\mathcal{S}$ be the reference frame of the search area subimage.

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

### Search Area

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

The search area likewise has its own local frame $\mathcal{S}$, origin
$S$ at its top-left corner.  The location of $P'$ in the `current_image` is given by:

$$\boldsymbol{r}_{OP'/\mathcal{F}} = \boldsymbol{r}_{OS/\mathcal{F}} + \boldsymbol{r}_{SP'/\mathcal{S}}$$

The goal of the DIC process is to locate $P'$ by solving for the quantity
$\boldsymbol{r}_{SP'/\mathcal{S}}$.  The location of $P'$ in the search area's
local frame is the single unknown; all other vectors are known.

### Solution

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
