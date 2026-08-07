# Cross Correlation (CC)

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

## Spatial Domain or Fourier Domain

Cross-correlation itself can be computed two ways: directly in the
**spatial domain** — literally sliding the kernel over the search area and
summing a per-position inner product, as shown below — or in the **Fourier
domain** via the fast Fourier transform (FFT), which is what `locate`
actually does (see [CC via FFT](./cc_fft.md)). Both compute the same
underlying quantity; the FFT method is simply a much faster way than the
sliding dot product approach.

## Correlation Criteria

Several related criteria are used in the spatial domain, differing in how
each responds to brightness and contrast differences between the kernel
$f$ and a candidate window $g$ — a same-sized window of the search area at
one particular offset — summed pixelwise over index $i$:

* **Cross-Correlation (CC)**

  $$C_{\rm CC} = \sum f_i g_i$$

* **Normalized Cross-Correlation (NCC)**

  $$C_{\rm NCC} = \frac{\sum f_i g_i}{\sqrt{\sum f_i^2 \sum g_i^2}}$$

* **Zero-mean Cross-Correlation (ZCC)**

  $$C_{\rm ZCC} = \sum (f_i - \bar{f})(g_i - \bar{g})$$

  where $\bar{f} = \frac{1}{n}\sum_{i=0}^{n-1} f_i$ and $\bar{g}$ likewise
  for $g$.

* **Zero-mean Normalized Cross-Correlation (ZNCC)**

  $$C_{\rm ZNCC} = \frac{\sum \bar{f}_i \bar{g}_i}{\sqrt{\sum \bar{f}_i^2 \sum \bar{g}_i^2}}$$

  where $\bar{f}_i = f_i - \bar{f}$ and $\bar{g}_i = g_i - \bar{g}$.

### Invariance and Robustness

*Invariant* is the more precise term here than *robust* or *insensitive*:
subtracting each side's own mean cancels any constant **added** to that
side — a brightness difference between $f$ and $g$, which is additive —
and dividing by each side's own norm cancels any constant **scaling** of
that side — a contrast difference, which is multiplicative. Whether a
criterion performs each of those two cancellations determines its
invariance:

| Method | Invariant to brightness (additive) | Invariant to contrast (multiplicative) | Robustness |
|:---|:---:|:---:|:---|
| CC | − | − | Least robust — neither cancellation |
| NCC | − | + | Partial — contrast only |
| ZCC | + | − | Partial — brightness only |
| ZNCC | + | + | Most robust — both |

ZNCC combines ZCC's mean-subtraction (brightness invariance) with NCC's
norm-division (contrast invariance), which is why it's the standard choice
in most DIC implementations — including `dictk.translation.locate`'s own
underlying `skimage.registration.phase_cross_correlation` call (see [CC via
FFT](./cc_fft.md)). Neither cancellation helps against *nonlinear* or
*spatially-varying* brightness/contrast (a shadow crossing part of the
kernel, sensor saturation) — none of the four criteria above address that.

### Brightness and Contrast Invariance in Practice

The table above is a formula-level guarantee, verified here on
[`astronaut0`](./image_generation.md#speckle--astronaut) — the
speckle-over-photograph image used from [Multi-Point
Motion](./multi_point_motion.md) onward — rather than taken on faith.
Extract a kernel from `astronaut0` unmodified, then compare it against a
search area from a translated *and* brightness-shifted copy of the same
image, using [`dictk.image.brightness`](../api/dictk/image.html#brightness)
with a small enough factor that no pixel clips at 255 (clipping is a
genuine loss of information no correlation criterion can see past, and
would contaminate this test):

```python
from dictk.image import read, translate, brightness, PixelCoordinate, subimage
from dictk.correlation import cc, ncc, zcc, zncc

astronaut0 = read(path="astronaut0.png")
p0 = PixelCoordinate(x=100, y=100)
kernel_margin, search_margin = 25, 50
kernel = subimage(image=astronaut0, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin)

dx, dy = -6, 8
current_baseline = translate(arr=astronaut0, dx=dx, dy=dy)
current_bright = brightness(arr=current_baseline, factor=1.01)  # +1.275 per pixel, no clipping here

search_origin = PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin)
baseline_search = subimage(image=current_baseline, origin=search_origin, width=2 * search_margin, height=2 * search_margin)
bright_search = subimage(image=current_bright, origin=search_origin, width=2 * search_margin, height=2 * search_margin)

for name, fn in [("CC", cc), ("NCC", ncc), ("ZCC", zcc), ("ZNCC", zncc)]:
    baseline_peak = fn(kernel=kernel, search=baseline_search).max()
    bright_peak = fn(kernel=kernel, search=bright_search).max()
    pct_change = (bright_peak - baseline_peak) / abs(baseline_peak) * 100
    print(f"{name}: peak value change under brightness shift = {pct_change:+.4f}%")
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, brightness, PixelCoordinate, subimage; from dictk.correlation import cc, ncc, zcc, zncc; astronaut0 = read(path='astronaut0.png'); p0 = PixelCoordinate(x=100, y=100); kernel_margin, search_margin = 25, 50; kernel = subimage(image=astronaut0, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); dx, dy = -6, 8; current_baseline = translate(arr=astronaut0, dx=dx, dy=dy); current_bright = brightness(arr=current_baseline, factor=1.01); search_origin = PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin); baseline_search = subimage(image=current_baseline, origin=search_origin, width=2 * search_margin, height=2 * search_margin); bright_search = subimage(image=current_bright, origin=search_origin, width=2 * search_margin, height=2 * search_margin); [print(f'{name}: peak value change under brightness shift = {(fn(kernel=kernel, search=bright_search).max() - fn(kernel=kernel, search=baseline_search).max()) / abs(fn(kernel=kernel, search=baseline_search).max()) * 100:+.4f}%') for name, fn in [('CC', cc), ('NCC', ncc), ('ZCC', zcc), ('ZNCC', zncc)]]" -->
```

ZCC and ZNCC come back at exactly `+0.0000%` — bit-for-bit unchanged, as
the formula guarantees for any brightness shift small enough to avoid
clipping. CC and NCC both drift, confirming they are not brightness
invariant — even though, on `astronaut0`'s strong, distinctive texture,
that drift isn't large enough to move *where* the peak lands, only its
*value*. That value-only distinction still matters in practice: it's what
makes CC's raw magnitude unsafe to compare across different points or
lighting conditions in a [Multi-Point Motion](./multi_point_motion.md)
grid, even on images where its peak still happens to land in the right
place for any one point in isolation.

A parallel contrast test — [`dictk.image.contrast`](../api/dictk/image.html#contrast)
instead of `brightness`, same `astronaut0` kernel/search pair — shows the
other pairing:

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, contrast, PixelCoordinate, subimage; from dictk.correlation import cc, ncc, zcc, zncc; astronaut0 = read(path='astronaut0.png'); p0 = PixelCoordinate(x=100, y=100); kernel_margin, search_margin = 25, 50; kernel = subimage(image=astronaut0, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); dx, dy = -6, 8; current_baseline = translate(arr=astronaut0, dx=dx, dy=dy); current_contrast = contrast(arr=current_baseline, factor=1.02); search_origin = PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin); baseline_search = subimage(image=current_baseline, origin=search_origin, width=2 * search_margin, height=2 * search_margin); contrast_search = subimage(image=current_contrast, origin=search_origin, width=2 * search_margin, height=2 * search_margin); [print(f'{name}: peak value change under contrast shift = {(fn(kernel=kernel, search=contrast_search).max() - fn(kernel=kernel, search=baseline_search).max()) / abs(fn(kernel=kernel, search=baseline_search).max()) * 100:+.4f}%') for name, fn in [('CC', cc), ('NCC', ncc), ('ZCC', zcc), ('ZNCC', zncc)]]" -->
```

NCC drifts about 40x less than CC does (`-0.0052%` vs `+0.2194%`), and ZNCC
about 900x less than ZCC does (`-0.0021%` vs `+1.8999%`). Not perfectly
bit-exact like the brightness case, because `contrast` scales around the
*image's own mean* rather than performing a pure multiplicative gain,
which mixes in a small secondary additive term — but the qualitative
result matches the table: contrast invariance belongs to NCC and ZNCC, not
CC or ZCC.

See Pan B, Xie H, Wang Z. "[Equivalence of digital image correlation
criteria for pattern
matching](https://opg.optica.org/ao/viewmedia.cfm?uri=ao-49-28-5501)."
*Applied Optics* 2010;49(28):5501-9.
[[download]](https://1drv.ms/b/c/3cc1bee5e2795295/IQDjuSdmrbpZT71uMkNXOaC4ATCYsBI1RAntZaKOURqobsI?e=65MdBH)
[`dictk.correlation`](../api/dictk/correlation.html) implements all four as
standalone functions (`cc`, `ncc`, `zcc`, `zncc`), each returning the full
correlation surface rather than just its peak — see [CC
Visualization](./cc_visualization.md) for what those surfaces look like on
the kernel and search area established above.

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

Next: [CC Visualization](./cc_visualization.md) computes and plots the four
correlation criteria above as heatmaps on this same kernel and search area,
and [CC via FFT](./cc_fft.md) explains the Fourier-domain route `locate`
actually takes.
