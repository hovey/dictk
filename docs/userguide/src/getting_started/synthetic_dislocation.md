# Synthetic Dislocation

[Discontinuities](./discontinuities.md) already built the plain-photo
version of this jump. Here it carries a speckle pattern, so a
correlation actually has something to track:

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
Original | ![original](synthetic_dislocation_reference.png)
offset=4 pixels | ![crack dislocation](synthetic_dislocation_current.png)

Both carry the same `rosta` speckle pattern — only the dislocation
differs. [Discontinuities](./discontinuities.md)'s plain-photo version
showed the geometry alone; this pair is what a correlation actually
sees.

## A Window Straddling the Crack

Place a kernel window centered exactly on the crack: `x = 150`, the
image's own vertical midline, where the dislocation splits left from
right. A window there doesn't sit cleanly on one side. It contains both
true displacements at once: +4 pixels on its left half, -4 on its
right. `dictk`'s own y-axis points down the page, not up (see
[Multi-Point Motion](./multi_point_motion.md#verification-against-vic-2d)
for this same sign convention). So +4 here means the left half shifts
*down*. -4 means the right half shifts *up*.

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

Two comparably-tall peaks, not one, because a single-peak correlation
answer can't represent two different true displacements at once. Neither
peak is a false match. Each one is exactly right for its own half of the
window. The peaks sit at `y=16` and `y=24`, straddling the window's own
zero-shift center (`y=20`) by exactly ∓4 pixels. That's the same 4-pixel
offset `crack_dislocation` applied, and their separation, 8 pixels, is
exactly twice it. Both criteria agree: ZNCC (spatial) and phase
correlation (FFT) land on the same two peaks, at the same two positions.

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
criteria. One honest exception sits at the low end: once the two true
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

## What This Doesn't Do

This is a diagnostic. It doesn't fix anything. Nothing here located the
crack; a human already centered the window on it.
[Discontinuities](./discontinuities.md) names the open problem this
points toward: an algorithm that finds this signature on its own,
rather than a person choosing where to look.

Continue to [Experimental Dislocation](./experimental_dislocation.md) to
check whether the same signature survives on a real crack, where the
ground truth isn't known in advance.

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
