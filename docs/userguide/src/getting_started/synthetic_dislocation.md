# Synthetic Dislocation

[Discontinuities](./discontinuities.md) already built the plain-photo
version of this jump. Here it carries a speckle pattern, so a
correlation actually has something to track:

```python
import dictk
from dictk.image import combine, crack_dislocation

speckle = dictk.rosta(width=300, height=300, density=0.5)
photo = dictk.astronaut(width=300, height=300)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=4.0)
```

## A Window Straddling the Crack

Place a tracking window centered exactly on the crack: `x = 150`, the
image's own vertical midline, where the dislocation splits left from
right. A window there doesn't sit cleanly on one side. It contains both
true displacements at once: +4 pixels on its left half, -4 on its right.

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
    <figcaption>ZNCC's Correlation Surface panel: two comparably-tall peaks, not one, at (x=20, y=16) and (x=20, y=24), with heights 0.528 and 0.519. Both sit at the same x offset, 20, the center index that matches the crack's own zero horizontal shift. They differ only in y, by 8 pixels.</figcaption>
</figure>

<figure>
    <img src="synthetic_dislocation_phase.png" alt="Phase correlation quadrant plot: correlation surface is otherwise flat except for two isolated bright pixels at the same two locations the ZNCC surface found" />
    <figcaption>Phase correlation's Correlation Surface panel shows the same pattern as <a href="./correlation_visualization.html#phase-correlation">Phase Correlation</a>: flat except for one sharp pixel. Here, though, there are two sharp pixels, at (x=20, y=16) and (x=20, y=24) with heights 0.206 and 0.173, the same two locations ZNCC found.</figcaption>
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
