# Synthetic Dislocation

[Discontinuities](./discontinuities.md) already built the plain-photo
version of this jump. Here we have added a speckle pattern, so the
correlation has something to track:

```python
import dictk
from dictk.image import combine, crack_dislocation, write

speckle = dictk.rosta(width=300, height=300, density=0.5)
photo = dictk.astronaut(width=300, height=300)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=4.0)

write(arr=reference_image, path="synthetic_dislocation_reference.png")
write(arr=current_image, path="synthetic_dislocation_current.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import combine, crack_dislocation, write; speckle = dictk.rosta(width=300, height=300, density=0.5); photo = dictk.astronaut(width=300, height=300); reference_image = combine(a=speckle, b=photo); current_image = crack_dislocation(arr=reference_image, offset=4.0); write(arr=reference_image, path='synthetic_dislocation_reference.png'); write(arr=current_image, path='synthetic_dislocation_current.png'); print('Saved: synthetic_dislocation_reference.png, synthetic_dislocation_current.png')" -->
```

Synthetic Dislocation | Image
--- | ---
Original<br>[synthetic_dislocation_reference.png](synthetic_dislocation_reference.png) | ![original](synthetic_dislocation_reference.png)
offset=4 pixels<br>[synthetic_dislocation_current.png](synthetic_dislocation_current.png) | ![crack dislocation](synthetic_dislocation_current.png)

Both carry the same `rosta` speckle pattern — only the dislocation
differs. [Discontinuities](./discontinuities.md)'s plain-photo version
showed the geometry alone; this pair is what a correlation actually
sees.

## A Window Straddling the Crack

Place a kernel window centered exactly on the crack: `x = 150`, the
image's own vertical midline, where the dislocation splits left from
right. A window there doesn't sit cleanly on one side. It contains both
true displacements at once: $\delta y =$ +4 pixels on its left half, $\delta y =$ -4 pixels on its
right. $\delta x =$ 0 pixels for all pixels in the current image.

> Recall that `dictk`'s own y-axis points down the page, not up (see [Multi-Point Motion](./multi_point_motion.md#verification-against-vic-2d) for this same sign convention). So +4 here means the left half shifts *down*. -4 means the right half shifts *up*.

```python
from dictk.plot import subimage_comparison_plot

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
    path="synthetic_dislocation_kernel.png",
)
```

```text
<!-- cmdrun python3 synthetic_dislocation_kernel.py -->
```

<figure>
    <img src="synthetic_dislocation_kernel.png" alt="the kernel window as a green box centered at x=150, y=150 on reference_image, with the extracted kernel subimage shown alongside it" />
    <figcaption>The kernel window (green box), a 50x50 pixel region of <code>reference_image</code> centered on the crack at $\boldsymbol{p}_0 = (150, 150)$, with origin $\boldsymbol{r}_{OK/\mathcal{F}} = (125, 125)$ pixels (green dot). Because the window straddles the crack instead of sitting on one side of it, it contains pixels from both displacements on the left and right halves of the current image. This follows the nomenclature and convention established in <a href="./cross_correlation.html#kernel">Cross Correlation (CC)</a>.</figcaption>
</figure>

```python
from dictk.image import subimage, PixelCoordinate
from dictk.correlation import zncc
from dictk.plot import spatial_correlation_quadrant_plot, phase_correlation_quadrant_plot

p0 = PixelCoordinate(x=150, y=150)
kernel_margin, search_margin = 25, 45
kernel = subimage(
    image=reference_image,
    origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin),
    width=2 * kernel_margin, height=2 * kernel_margin,
)
search = subimage(
    image=current_image,
    origin=PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin),
    width=2 * search_margin, height=2 * search_margin,
)

spatial_correlation_quadrant_plot(
    kernel=kernel, search=search,
    correlation_surface=zncc(kernel=kernel, search=search),
    title="Zero-mean Normalized Cross-Correlation (ZNCC)",
    path="synthetic_dislocation_zncc.png",
)
phase_correlation_quadrant_plot(
    kernel=kernel, search=search,
    title="Phase Correlation (FFT)",
    path="synthetic_dislocation_phase.png",
)
```

```text
<!-- cmdrun python3 synthetic_dislocation_quadrant.py -->
```

<figure>
    <img src="synthetic_dislocation_zncc.png" alt="ZNCC quadrant plot: correlation surface shows two separate bright yellow peaks, one near (20, 16) and one near (20, 24), rather than one" />
    <figcaption>ZNCC's Correlation Surface panel: two (not one) comparably-tall peaks at (x=20, y=16) and (x=20, y=24), with heights 0.528 and 0.519, respectively. Both sit at the same x offset, 20, the center index that matches the crack's own zero horizontal shift. They differ only in y, by 8 pixels.</figcaption>
</figure>

<figure>
    <img src="synthetic_dislocation_phase.png" alt="Phase correlation quadrant plot: correlation surface is otherwise flat except for two isolated bright pixels at the same two locations the ZNCC surface found" />
    <figcaption>Phase correlation's Correlation Surface panel shows the same pattern as <a href="./correlation_visualization.html#phase-correlation">Phase Correlation</a>: flat except for one sharp pixel. Here, though, there are two sharp pixels, at (x=20, y=16) and (x=20, y=24), with heights 0.206 and 0.173, respectively. These are the same two locations ZNCC found.</figcaption>
</figure>

Two comparably-tall peaks appear, not one, because a single-peak
correlation answer can't represent two different true displacements at
once. Neither is a false match. Each is exactly right for its own half
of the window. The peaks sit at `y=16` and `y=24`, straddling the
window's own zero-shift center (`y=20`) by exactly ∓4 pixels. That's the
same 4-pixel offset `crack_dislocation` applied. Their separation, 8
pixels, is exactly twice it. ZNCC (spatial) and phase correlation (FFT)
agree: both land on the same two peaks.

## Does This Hold in General?

One offset proving the point isn't enough to trust it. Sweeping
`crack_dislocation`'s offset from 1 to 32 pixels, and checking whether
each surface's two-peak separation still equals twice the offset:

<!-- cmdrun python3 synthetic_dislocation_sweep.py -->

<figure>
    <img src="synthetic_dislocation_sweep.png" alt="scatter plot of peak separation vs dislocation offset, both ZNCC circles and phase-correlation crosses landing exactly on a dashed separation-equals-two-times-offset reference line from 2 to 32 pixels" />
    <figcaption>Every offset from 2 to 32 pixels lands exactly on the separation = 2 x offset line, for both criteria. Only at offset=1 does ZNCC miss. There, the two peaks sit one pixel apart, too close for this integer-pixel surface to resolve as two separate local maxima. Phase correlation still resolves them at that offset.</figcaption>
</figure>

The encoding holds reliably across a 32x range of offsets, for both
criteria. One exception sits at the low end: once the two true
displacements are only a pixel apart, resolving them as two distinct
peaks runs into the same integer-pixel resolution limit [Subpixel
Accuracy](./subpixel_accuracy.md) already covers for a single peak.

## Moving the Window Off the Crack

Every result so far centers the window exactly on the crack, at
`x = 150`. What happens as that center slides away from it?

`kernel_margin=25` sets a hard geometric boundary. Once the window's
center sits more than 25 pixels from the crack, the window no longer
touches both halves at all: it's `x <= 125` for a window entirely in
the left half, `x >= 175` for one entirely in the right. Sweeping
`x` from 100 to 200 and reading the ZNCC surface at both candidate
peak locations, Δy=+4 (the left half's own shift) and Δy=-4 (the
right half's own shift), at each step:

<!-- cmdrun python3 synthetic_dislocation_x_sweep.py -->

<figure>
    <img src="synthetic_dislocation_x_sweep.png" alt="line plot of ZNCC peak magnitude vs. window center x from 100 to 200: the left-half peak pins at exactly 1.0 until x=125, both peaks cross near x=148, then the right-half peak pins at exactly 1.0 from x=175 onward while the left-half peak fades to a fluctuating 0.2-0.3 band" />
    <figcaption>Peak magnitude vs. kernel window center x, dotted lines at x=125 and x=175 marking the geometric boundary, dashed line at x=150 marking the crack. Below x=125 there's exactly one peak, at Δy=+4, pinned at 1.0: the "lower" peak, further down the page. That confirms it's the only one present, not merely the tallest. Above x=175 the mirror image holds: one peak, at Δy=-4, pinned at 1.0. Between them, the two trade dominance smoothly, crossing near x=148, both close to 0.52 there, matching <a href="#a-window-straddling-the-crack">the single point already measured at x=150</a>.</figcaption>
</figure>

The line plot only reads two fixed points on the surface. The surface
itself tells the same story directly: the Correlation Surface panel at
five kernel window center positions, `x = 130, 140, 150, 160, 170`,
sharing one colorbar:

<!-- cmdrun python3 synthetic_dislocation_x_sweep_panels.py -->

<figure>
    <img src="synthetic_dislocation_x_sweep_panels.png" alt="five ZNCC Correlation Surface panels side by side at kernel window center x=130, 140, 150, 160, and 170, sharing one viridis colorbar from 0 to 1: a single bright peak near the bottom at x=130, a second peak emerging and growing through x=140 and x=150 where both are comparable, then the first peak fading while the second dominates by x=160 and x=170" />
    <figcaption>The Correlation Surface panel itself, at five kernel window center positions. At x=130 one peak, near the bottom, clearly dominates. A second, fainter peak sits just above it. The two left-most panels (x=130, x=140) circle that lower peak, at (x=20, y=24) px. By x=150 the two are close enough to call a tie; the argmax circle lands on whichever is barely taller. The two right-most panels (x=160, x=170) circle the upper peak instead, at (x=20, y=16) px. The roles have now fully reversed: it dominates, and the lower peak is nearly gone.</figcaption>
</figure>

ZNCC hits exactly 1.0, not just a high value, wherever the window sits
fully inside one half. That's not a coincidence: a window entirely
inside one half sees a pure integer-pixel rigid shift of identical
content. There's no interpolation error and nothing else to explain
away, so ZNCC reaches its exact theoretical maximum.

The two sides aren't quite mirror images once the window fully clears
the crack. Below x=125 the vanishing peak (Δy=-4) fades to 0.05-0.16.
Above x=175 the vanishing peak (Δy=+4) settles into a higher,
fluctuating 0.2-0.3 band instead, with a small bump near x=183. That
difference comes from the underlying speckle and photo content on
each side, not from the crack itself.

Straddling the crack is what makes two comparable peaks possible. Move
the window fully clear of it, in either direction, and only one peak
remains: a single, perfect match.

## Displacement Field

Every result so far reads one fixed point, or one line through the
image (`y = 150`, sweeping `x`). A grid of tracked points turns that
into a field: the same displacement each single measurement already
found, but everywhere at once, not just where a human chose to look.

`SEARCH_MARGIN = 45` sets how far each point's own search window
reaches from its own center. Starting the grid's own origin exactly
there keeps every point's search window fully inside the image, with no
edge effect competing with the crack for attention:

```python
from dictk.grid import generate, locate_subpixel

points = generate(
    origin=PixelCoordinate(x=SEARCH_MARGIN, y=SEARCH_MARGIN),
    count_x=43,
    count_y=43,
    spacing_x=5,
    spacing_y=5,
)
found = locate_subpixel(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
    upsample_factor=100,
)
```

```python
dx = [f.x - p.x for f, p in zip(found, points)]
dy = [f.y - p.y for f, p in zip(found, points)]
```

The `dy` field, painted over `current_image`:

```python
from dictk.plot import point_displacement_plot

point_displacement_plot(
    points=found,
    values=dy,
    label=r"Displacement, $\delta y$ (pixels)",
    image=current_image,
    dot_size=6,
    marker="s",
    cmap="coolwarm",
    path="synthetic_dislocation_displacement_field.png",
)
```

<figure>
    <img src="synthetic_dislocation_displacement_field.png" alt="displacement field: a dense grid of small square points colored by dy, split into a red (+4 pixel) region on the left half of the field and a blue (-4 pixel) region on the right half, with a sharp boundary between them right at the crack" />
    <figcaption>The <code>dy</code> field over all 1849 tracked points. Not a gradient: two flat colors, solid $\delta y = +4$ (left) and solid $\delta y = -4$ (right), meeting at a boundary within one grid column (5 pixels) of the crack at $x=150$, for every row.</figcaption>
</figure>

Zooming into that boundary shows small gaps: spots where the gray and
black speckle image shows through, neither red nor blue. None of the
1849 points are missing -- every one of the 43 columns holds all 43
rows, and every point gets a color. The gaps come from how the points
are drawn, not which ones are plotted.

`dot_size=6` sizes each square marker at only about a quarter of its
own 5-pixel grid cell. Every marker sits well short of its neighbors,
on every side, everywhere in the field -- the same small gap separates
every red neighbor, every blue neighbor, and every point at the
boundary. That gap is easy to miss where it sits between two markers of
the same color: a patch of speckle between two red squares blends into
the surrounding red, and the eye skips past it, reading as texture
rather than as a hole. The identical-sized gap between a red marker and
a blue one is unmistakable, flanked by two different colors instead of
one. The gaps aren't concentrated at the crack. They're everywhere.
Only at the crack does the color change on either side make them
visible.

`crack_dislocation` only ever moves pixels vertically, so `dx` should
come back trivially close to zero at every one of these 1849 points --
worth checking directly, not just assuming it from the one point
already measured:

<!-- cmdrun python3 synthetic_dislocation_displacement_field.py -->

### Displacement dx

`dx` does stay trivially small: every one of the 1849 points comes back
within 0.07 pixels of zero, well under a tenth of a pixel, as the first
table above shows. The full distribution, not just its extremes:

<figure>
    <img src="synthetic_dislocation_displacement_field_dx_histogram.png" alt="histogram of dx across all 1849 points: a single narrow peak centered at zero, spanning roughly -0.07 to 0.07 pixels, with a shaded band marking one std on either side of the mean and a dashed black line at the mean itself" />
    <figcaption>The <code>dx</code> distribution across all 1849 tracked points: a single peak centered on zero, no second mode. The shaded band marks one std on either side of the mean; the dashed line marks the mean itself. The 0.01-pixel steps are <code>upsample_factor=100</code>'s own subpixel quantization, the same effect <a href="./high_point_density.html">High Point Density</a> found for <code>dy</code>.</figcaption>
</figure>

### Displacement dy

That boundary in the field figure above is sharper than "Moving the
Window Off the Crack" would suggest. Windows straddle the crack for
every point with `125 < x < 175` -- 387 of the 1849 points here -- yet
none of them return a value between the two true displacements. Each
straddling window's correlation surface does hold two comparable peaks,
exactly as the earlier single-window measurement found, but
`locate_subpixel` still returns one location: whichever peak is taller.
Which one wins depends on how much of that window's own area sits on
each side of the crack, and that tips over almost exactly at the crack
itself, not gradually across the full 50-pixel span a straddling window
could in principle blur together.

Splitting `dy` on its own sign, rather than by `x` position, gives the
same two groups directly: 921 points read a positive displacement, 928
read a negative one, and none read zero. The second and third tables
above cover each group on its own.

The `+4` group:

<figure>
    <img src="synthetic_dislocation_displacement_field_dy_positive_histogram.png" alt="histogram of dy for the 921 points reading a positive displacement: a single narrow peak centered near 4.00 pixels, with a shaded band marking one std on either side of the mean and a dashed black line at the mean itself" />
    <figcaption>The <code>dy</code> distribution for the 921 points in the <code>+4</code> group: a single peak at 4.00 pixels, std 0.017 pixels -- the shaded band and dashed line mark that mean and its one-std spread directly.</figcaption>
</figure>

The `-4` group:

<figure>
    <img src="synthetic_dislocation_displacement_field_dy_negative_histogram.png" alt="histogram of dy for the 928 points reading a negative displacement: a single narrow peak centered near -4.00 pixels, with a shaded band marking one std on either side of the mean and a dashed black line at the mean itself" />
    <figcaption>The <code>dy</code> distribution for the 928 points in the <code>-4</code> group: a single peak at -4.00 pixels, std 0.016 pixels -- the shaded band and dashed line mark that mean and its one-std spread directly.</figcaption>
</figure>

Both groups are tight, single-mode distributions, each barely 0.15
pixels wide start to finish. The largest deviation from a clean $\pm 4$,
anywhere in either group including the 387 straddling points, is 0.09
pixels.

### VIC-2D-Style Point Density

[High Point Density](./high_point_density.md) verifies a denser grid --
`count_x=53, count_y=54, spacing_x=spacing_y=5`, with
`kernel_margin_width=kernel_margin_height=13`,
`search_margin_width=search_margin_height=25` -- against a real VIC-2D
run. That comparison is for a different experiment, though: a 2%
uniaxial stretch, not a crack. VIC-2D has never analyzed this page's
own crack-dislocation image pair, so nothing below is a VIC-2D result --
just the same grid density and kernel size, in VIC-2D's own style,
applied to this page's own crack instead. Does that same grid change
anything about the field above?

```python
CURRENT_KERNEL_MARGIN = 25
CURRENT_SEARCH_MARGIN = 45
points_current = generate(
    origin=PixelCoordinate(x=CURRENT_SEARCH_MARGIN, y=CURRENT_SEARCH_MARGIN),
    count_x=43,
    count_y=43,
    spacing_x=5,
    spacing_y=5,
)

VIC2D_STYLE_KERNEL_MARGIN = 13
VIC2D_STYLE_SEARCH_MARGIN = 25
points_vic2d = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)
```

<!-- cmdrun python3 synthetic_dislocation_grid_kernel_panels.py -->

<figure>
    <img src="synthetic_dislocation_grid_kernel_panels.png" alt="two panels side by side over the same reference image: the left shows the current 43x43 grid of bold orange dots with a green 50x50 pixel kernel box around its first point, labeled K at the box's origin and P at the point; the right shows the denser VIC-2D-style 53x54 grid with the same labeling around a smaller green 26x26 pixel kernel box" />
    <figcaption>The two grids from the code above, drawn over <code>reference_image</code>. Left: the current 43x43 grid (1849 points, 5-pixel spacing), with a green box around <code>points_current[0]</code> showing its 50x50 pixel kernel window (<code>kernel_margin=25</code>). Right: the denser VIC-2D-style 53x54 grid (2862 points, same 5-pixel spacing), with a green box around <code>points_vic2d[0]</code> showing its smaller 26x26 pixel kernel window (<code>kernel_margin=13</code>). In both, the box's origin $\boldsymbol{r}_{OK/\mathcal{F}}$ is marked $K$ (green dot) and its tracked point $P$ (orange dot), matching <a href="#a-window-straddling-the-crack">A Window Straddling the Crack</a>'s own labeling convention.</figcaption>
</figure>

<!-- cmdrun python3 synthetic_dislocation_displacement_field_vic2d.py -->

The first table above tracks the two grids as they'd actually run: the
VIC-2D-style grid finds more points, 2862 against 1849, but its own
smaller kernel window (26x26 pixels, against the current grid's 50x50)
roughly doubles the largest deviation from a clean $\pm4$: 0.19 pixels,
against 0.09. 362 of its 2862 points also sit close enough to the image
edge that their own search windows reach outside it.

Is that the point spacing? Both grids use the same 5-pixel spacing, so
no. The second table isolates the kernel size alone: it tracks the
current grid's own 1849-point layout, at the same edge-safe origin, but
with the VIC-2D grid's smaller kernel instead.

Isolating the kernel size alone already produces most of the
difference. It measures 0.16 pixels, against 0.19 for the full VIC-2D
grid and 0.09 for the current grid. The kernel window's side length
drives this difference, not point spacing and not the image edge.

A 26x26 pixel window captures a quarter of the speckle content a 50x50
pixel window captures. With less speckle content, cross-correlation
finds fewer unique features to match. It locks the subpixel position
less precisely. That weaker lock raises deviation at every point, even
a point whose own window never touches the crack. Edge clipping adds
further deviation on top: 0.16 pixels without it, 0.19 pixels with it.

## What This Doesn't Do

This is a diagnostic. It doesn't fix anything. Nothing here located the
crack; a human already centered the window on it.
[Discontinuities](./discontinuities.md) names the open problem this
points toward: an algorithm that finds this signature on its own,
rather than a person choosing where to look.

Continue to [Experimental Dislocation](./experimental_dislocation.md) to
check whether the same signature survives on a real crack, where the
ground truth isn't known in advance.

### `synthetic_dislocation_kernel.py`

```python
<!-- cmdrun cat synthetic_dislocation_kernel.py -->
```

### `synthetic_dislocation_quadrant.py`

```python
<!-- cmdrun cat synthetic_dislocation_quadrant.py -->
```

### `synthetic_dislocation_sweep.py`

```python
<!-- cmdrun cat synthetic_dislocation_sweep.py -->
```

### `synthetic_dislocation_x_sweep.py`

```python
<!-- cmdrun cat synthetic_dislocation_x_sweep.py -->
```

### `synthetic_dislocation_x_sweep_panels.py`

```python
<!-- cmdrun cat synthetic_dislocation_x_sweep_panels.py -->
```

### `synthetic_dislocation_displacement_field.py`

```python
<!-- cmdrun cat synthetic_dislocation_displacement_field.py -->
```

### `synthetic_dislocation_grid_kernel_panels.py`

```python
<!-- cmdrun cat synthetic_dislocation_grid_kernel_panels.py -->
```

### `synthetic_dislocation_displacement_field_vic2d.py`

```python
<!-- cmdrun cat synthetic_dislocation_displacement_field_vic2d.py -->
```
