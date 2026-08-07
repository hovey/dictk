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

## TODO: spatial-domain vs. Fourier-domain surfaces

The four correlation surfaces above all come from `dictk.correlation`'s
spatial-domain (sliding-window, "valid") formulas — the same ones [Cross
Correlation (CC)](./cross_correlation.md) defines. [CC via
FFT](./cc_fft.md) computes an equivalent quantity a second way, in the
Fourier domain via the convolution theorem, but that page's demo is a
standalone script, not something this page's figures can select yet.

**Design decision, already settled:** a domain selector does *not* belong
inside `correlation_quadrant_plot()` itself. That function already treats
`correlation_surface` as an opaque 2D array — it takes its `argmax` and
plots whatever shape comes in, so it works identically regardless of which
domain produced that array (spatial-domain surfaces are smaller, "valid"
size; Fourier-domain surfaces are the same size as `search`, and can show
periodic wraparound peaks — neither changes how the function itself
behaves). A domain enum belongs in the **parameter list of the function
that computes the surface**, decided by the caller before
`correlation_quadrant_plot()` is ever called — mirroring how the reference
tooling this figure layout is based on keeps its own FFT-based
registration computation and its composite-figure plotting as two
separate functions, not one.

**Scope, once this gets picked back up** (see the sizing discussion two
sections up, and the standing memory note to revisit once this page's
Padding/Windowing content is fleshed out):

1. **CC via Fourier domain — small.** Already effectively written: [CC via
   FFT](./cc_fft.md)'s manual demo and `dictk.translation.locate`'s own
   internal kernel-padding both already zero-pad the kernel up to
   `search`'s shape and take the cross-power spectrum this needs. Mostly
   lifting existing, working code into a proper `dictk.correlation`-style
   function.
2. **Optional windowing — small, isolated.** A Hann/Hamming 2D window
   (outer product of a 1D window with itself), applied to `kernel` and
   `search` before the FFT, exactly as [CC via FFT](./cc_fft.md#windowing)
   already describes conceptually but doesn't implement
   (`dictk` has no `window()`-style function yet). Self-contained —
   doesn't touch anything else.
3. **NCC/ZCC/ZNCC via Fourier domain — genuinely harder.** The convolution
   theorem gives raw (CC-style) correlation almost for free via FFT, but
   *normalized* correlation needs each candidate window's own local
   sum-of-squares, which isn't a single FFT product — it needs a separate
   running-sum/box-filter computation (the standard reference is Lewis,
   "Fast Normalized Cross-Correlation," using cumulative sums or an
   auxiliary convolution to get local sums efficiently). ZCC is a smaller
   step up (mean-subtraction can ride along with the same FFT trick, since
   it's still just an additive shift) but NCC/ZNCC are real algorithm
   work, not refactoring.

**Illustrative sketch only** (not implemented, not wired up — matches the
same "sketch, don't build yet" pattern
[Parallelization](./parallelization.md) uses for its own
`ProcessPoolExecutor` example) of where the domain/windowing selection
would actually live:

```python
from enum import Enum

class CorrelationDomain(Enum):
    SPATIAL = "spatial"    # dictk.correlation's existing sliding-window formulas
    FOURIER = "fourier"    # convolution-theorem / FFT equivalent

class WindowingMethod(Enum):
    HANN = "hann"
    HAMMING = "hamming"

def correlation_surface(
    *,
    kernel: np.ndarray,
    search: np.ndarray,
    method: Literal["cc", "ncc", "zcc", "zncc"],
    domain: CorrelationDomain = CorrelationDomain.SPATIAL,
    windowing: WindowingMethod | None = None,  # Fourier domain only
) -> np.ndarray:
    ...  # returns the surface; correlation_quadrant_plot() itself never changes
```

Not scheduled work — don't start on this without Chad raising it again.
