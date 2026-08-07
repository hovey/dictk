# CC Visualization (v2)

[CC Visualization](./cc_visualization.md) compares all four correlation
criteria side by side as heatmaps, sharing one figure. This page instead
shows each criterion on its own, in a four-panel composite reproducing a
reference composite-figure layout used in prior DIC tooling, via
[`dictk.image.spatial_correlation_quadrant_plot`](../api/dictk/image.html#spatial_correlation_quadrant_plot):
the search area with the found kernel marked (**Fixed Image**), the kernel
itself zero-padded to the search area's shape (**Moving Image**), the full
correlation surface, and a zoomed **Solution Vicinity** around its peak —
closer to how a single registration result is typically inspected in
practice than a side-by-side comparison of criteria.

`reference_image`, `p0`, `current_image`, `kernel_margin`, `search_margin`,
`kernel`, and `search` are the same as in [Cross Correlation
(CC)](./cross_correlation.md) and [CC Visualization](./cc_visualization.md):

```python
from dictk.image import read, translate, PixelCoordinate, subimage

reference_image = read(path="checkerboard0.png")
p0 = PixelCoordinate(x=100, y=75)
current_image = translate(arr=reference_image, dx=-6, dy=8)

kernel_margin = 25
kernel = subimage(
    image=reference_image,
    origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin),
    width=2 * kernel_margin,
    height=2 * kernel_margin,
)

search_margin = 50
search_center = p0
search = subimage(
    image=current_image,
    origin=PixelCoordinate(
        x=search_center.x - search_margin, y=search_center.y - search_margin
    ),
    width=2 * search_margin,
    height=2 * search_margin,
)
```

Unlike [CC Visualization](./cc_visualization.md)'s panels, whose axes are
the candidate offset $(\Delta x, \Delta y)$ alone, the Fixed Image panel
below plots the search area in its own pixel frame $\mathcal{S}$, with a
yellow dashed box marking where the kernel was found and red/green dashed
guide lines through that box's origin — the same $\boldsymbol{r}_{SK/\mathcal{S}}$
quantity [Cross Correlation (CC)](./cross_correlation.md#solution) solves
for by hand.

## Cross-Correlation (CC)

```python
from dictk.correlation import cc
from dictk.image import spatial_correlation_quadrant_plot

spatial_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    correlation_surface=cc(kernel=kernel, search=search),
    title="Cross-Correlation (CC)",
    path="cc_visualization_v2_cc.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage, spatial_correlation_quadrant_plot; from dictk.correlation import cc; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); spatial_correlation_quadrant_plot(kernel=kernel, search=search, correlation_surface=cc(kernel=kernel, search=search), title='Cross-Correlation (CC)', path='cc_visualization_v2_cc.png'); print('Saved: cc_visualization_v2_cc.png')" -->
```

<figure>
    <img src="cc_visualization_v2_cc.png" alt="four-panel composite: fixed image with the found kernel boxed in yellow and red/green guide lines, the zero-padded moving image, the CC correlation surface, and a zoomed solution vicinity around its peak" />
    <figcaption>CC's quadrant composite. checkerboard0's tiled pattern repeats every ~25 pixels, so the correlation-surface panel shows more than one strong local peak within its own (smaller, "valid") range — CC has no way to prefer the true one over its look-alikes beyond raw magnitude, unlike the normalized criteria below.</figcaption>
</figure>

## Normalized Cross-Correlation (NCC)

```python
from dictk.correlation import ncc

spatial_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    correlation_surface=ncc(kernel=kernel, search=search),
    title="Normalized Cross-Correlation (NCC)",
    path="cc_visualization_v2_ncc.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage, spatial_correlation_quadrant_plot; from dictk.correlation import ncc; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); spatial_correlation_quadrant_plot(kernel=kernel, search=search, correlation_surface=ncc(kernel=kernel, search=search), title='Normalized Cross-Correlation (NCC)', path='cc_visualization_v2_ncc.png'); print('Saved: cc_visualization_v2_ncc.png')" -->
```

<figure>
    <img src="cc_visualization_v2_ncc.png" alt="four-panel composite for NCC: fixed image with the found kernel boxed in yellow and red/green guide lines, the zero-padded moving image, the NCC correlation surface, and a zoomed solution vicinity around its peak" />
    <figcaption>NCC's quadrant composite, bounded to $[-1, 1]$ by construction — visible in the colorbar range compared to CC's arbitrary raw units above.</figcaption>
</figure>

## Zero-mean Cross-Correlation (ZCC)

```python
from dictk.correlation import zcc

spatial_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    correlation_surface=zcc(kernel=kernel, search=search),
    title="Zero-mean Cross-Correlation (ZCC)",
    path="cc_visualization_v2_zcc.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage, spatial_correlation_quadrant_plot; from dictk.correlation import zcc; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); spatial_correlation_quadrant_plot(kernel=kernel, search=search, correlation_surface=zcc(kernel=kernel, search=search), title='Zero-mean Cross-Correlation (ZCC)', path='cc_visualization_v2_zcc.png'); print('Saved: cc_visualization_v2_zcc.png')" -->
```

<figure>
    <img src="cc_visualization_v2_zcc.png" alt="four-panel composite for ZCC: fixed image with the found kernel boxed in yellow and red/green guide lines, the zero-padded moving image, the ZCC correlation surface, and a zoomed solution vicinity around its peak" />
    <figcaption>ZCC's quadrant composite — raw units like CC's (mean-subtraction alone doesn't bound the range), but brightness-invariant per <a href="./cross_correlation.html#invariance-and-robustness">Cross Correlation (CC)</a>'s table.</figcaption>
</figure>

## Zero-mean Normalized Cross-Correlation (ZNCC)

```python
from dictk.correlation import zncc

spatial_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    correlation_surface=zncc(kernel=kernel, search=search),
    title="Zero-mean Normalized Cross-Correlation (ZNCC)",
    path="cc_visualization_v2_zncc.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage, spatial_correlation_quadrant_plot; from dictk.correlation import zncc; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); spatial_correlation_quadrant_plot(kernel=kernel, search=search, correlation_surface=zncc(kernel=kernel, search=search), title='Zero-mean Normalized Cross-Correlation (ZNCC)', path='cc_visualization_v2_zncc.png'); print('Saved: cc_visualization_v2_zncc.png')" -->
```

<figure>
    <img src="cc_visualization_v2_zncc.png" alt="four-panel composite for ZNCC: fixed image with the found kernel boxed in yellow and red/green guide lines, the zero-padded moving image, the ZNCC correlation surface, and a zoomed solution vicinity around its peak" />
    <figcaption>ZNCC's quadrant composite — both bounded to $[-1, 1]$ and invariant to brightness and contrast, which is why <code>dictk.translation.locate</code>'s own underlying <code>skimage.registration.phase_cross_correlation</code> call is built on the same combination (see <a href="./cc_fft.html">CC via FFT</a>).</figcaption>
</figure>

All four land on the same peak, $\boldsymbol{r}_{SK/\mathcal{S}} = (19,
33)$ pixels, since `kernel` and `search` here share identical brightness
and contrast (both come from `checkerboard0.png`, only translated) — the
same reason [CC Visualization](./cc_visualization.md) gives for its own
matching peaks. What differs between the four is what each panel's
colorbar reveals about *how safely* that peak can be trusted once
brightness or contrast do differ, as [Cross Correlation
(CC)](./cross_correlation.md#invariance-and-robustness) covers in detail.

## Phase Correlation

Every panel above comes from a spatial-domain criterion —
[`dictk.correlation`](../api/dictk/correlation.html)'s `cc`/`ncc`/`zcc`/
`zncc`, sliding `kernel` over `search` one window at a time. There's a
second way to get an equivalent answer: all at once, in the Fourier
domain, via
[`dictk.correlation.phase_correlation`](../api/dictk/correlation.html#phase_correlation)
— the same computation
[`dictk.translation.locate`](../api/dictk/translation.html#locate) already
runs internally via `skimage.registration.phase_cross_correlation`. Unlike
its spatial-domain siblings, there's only one Fourier-domain flavor here,
so [`phase_correlation_quadrant_plot`](../api/dictk/image.html#phase_correlation_quadrant_plot)
takes `kernel`/`search` directly rather than a pre-computed surface — no
method to choose, nothing to compute beforehand:

```python
from dictk.image import phase_correlation_quadrant_plot

phase_correlation_quadrant_plot(
    kernel=kernel,
    search=search,
    path="cc_visualization_v2_phase.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage, phase_correlation_quadrant_plot; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); phase_correlation_quadrant_plot(kernel=kernel, search=search, path='cc_visualization_v2_phase.png'); print('Saved: cc_visualization_v2_phase.png')" -->
```

<figure>
    <img src="cc_visualization_v2_phase.png" alt="four-panel composite for phase correlation: fixed image with the found kernel boxed in yellow and red/green guide lines, the zero-padded moving image, a correlation surface that is essentially flat except for one sharp isolated peak, and a zoomed solution vicinity around that peak" />
    <figcaption>Phase correlation's quadrant composite. Same peak, $(19, 33)$, as every criterion above — but the correlation-surface panel looks nothing like them: essentially flat/uniform everywhere except one crisp, isolated cell, rather than the broader, multi-peaked terrain CC/NCC/ZCC/ZNCC show on this same tiled <code>checkerboard0.png</code>.</figcaption>
</figure>

That sharpness isn't just a visual impression — the peak's *prominence*
(how many standard deviations above the surface's own mean the peak sits,
a scale-independent way to compare surfaces with very different raw
units) is dramatically higher:

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage; from dictk.correlation import cc, ncc, zcc, zncc, phase_correlation; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); [print(f'{name}: prominence (peak z-score) = {(fn(kernel=kernel, search=search).max() - fn(kernel=kernel, search=search).mean()) / fn(kernel=kernel, search=search).std():.2f}') for name, fn in [('CC', cc), ('NCC', ncc), ('ZCC', zcc), ('ZNCC', zncc), ('Phase correlation', phase_correlation)]]" -->
```

Phase correlation's peak stands roughly seven times taller above its own
background, relative to the surface's own spread, than even ZNCC — the
most robust of the four spatial criteria. That sharpness, not just
brightness/contrast invariance, is a second, independent reason
`dictk.translation.locate` is built on phase correlation rather than a
spatial-domain criterion: a sharper peak is easier to locate with
confidence and precision, and harder to confuse with a nearby runner-up.

## TODO: windowing for phase correlation

The "spatial vs. Fourier domain" question this section used to scope is
resolved and shipped: `dictk.correlation.phase_correlation()` and
[`phase_correlation_quadrant_plot`](#phase-correlation) above are both
implemented. That resolution took a different shape than originally
sketched here, worth recording:

- **The domain-selector design decision** (an enum belongs in the
  parameter list of the function that *computes* the surface, decided by
  the caller, never inside the plotting function itself) held up exactly
  as reasoned — but rather than one generic `correlation_surface(method,
  domain, ...)` dispatcher, it became two separate, plainly-named public
  functions,
  [`spatial_correlation_quadrant_plot`](../api/dictk/image.html#spatial_correlation_quadrant_plot)
  and
  [`phase_correlation_quadrant_plot`](../api/dictk/image.html#phase_correlation_quadrant_plot),
  each with their own complete docstring rather than one shared,
  parameterized entry point.
- **"CC via Fourier domain," as originally scoped, was never built.**
  `phase_correlation()` reproduces the exact computation
  `dictk.translation.locate()` already runs in production instead — a
  different (and better) technique than raw unnormalized CC-via-FFT,
  landing in the same "robust to both brightness and contrast" tier as
  ZNCC (see [Cross Correlation
  (CC)](./cross_correlation.md#invariance-and-robustness)) and, as shown
  above, with a dramatically sharper peak than any spatial-domain
  criterion, ZNCC included.
- **"NCC/ZCC/ZNCC via Fourier domain," the genuinely hard piece, is now
  moot.** That work only existed to give the Fourier domain the same
  four-way choice the spatial domain has. Adopting phase correlation as
  the *one* Fourier-domain flavor sidesteps it entirely — no per-method
  local-sum-of-squares algorithm (Lewis's Fast Normalized
  Cross-Correlation) is needed, since there's no per-method choice to
  support.

**What's still open:** windowing. [CC via FFT](./cc_fft.md#windowing)
describes Hann/Hamming windowing conceptually — tapering `kernel`/
`search`'s edges toward zero before the FFT, to reduce spectral leakage
from content that doesn't tile seamlessly — but doesn't implement it.
`dictk` has no `window()`-style function yet, and `phase_correlation()`
applies none today.

**Illustrative sketch only** (not implemented, not wired up — matches the
same "sketch, don't build yet" pattern
[Parallelization](./parallelization.md) uses for its own
`ProcessPoolExecutor` example) of where a future `windowing` parameter
would land:

```python
from enum import Enum

class WindowingMethod(Enum):
    HANN = "hann"
    HAMMING = "hamming"

def phase_correlation(
    *,
    kernel: np.ndarray,
    search: np.ndarray,
    windowing: WindowingMethod | None = None,
) -> np.ndarray:
    ...  # unchanged behavior when windowing=None; new when set
```

Not scheduled work — don't start on this without Chad raising it again.
