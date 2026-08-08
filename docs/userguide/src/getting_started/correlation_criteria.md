# Correlation Criteria

Cross-correlation itself can be computed two ways: directly in the
**spatial domain** — literally sliding the kernel over the search area and
summing a per-position inner product, as shown below — or in the **Fourier
domain** via the fast Fourier transform (FFT), which is what `locate`
actually does (see [Fourier Domain](#fourier-domain), below). Both compute
the same underlying quantity, but at very different cost: $O(n^2)$ for the
sliding sum, evaluated at every candidate offset, against $O(n \log n)$
for the FFT, with $n$ the number of pixels — a gap that widens sharply as
images grow beyond this page's small teaching examples.

## Spatial Domain

[Cross Correlation (CC)](./cross_correlation.md) walks through the
geometry of locating a point: the kernel/search-area vector chain, solved
by finding where their cross-correlation is maximized. This page covers
what "cross-correlation" actually means as a formula — several related
criteria are used in the spatial domain, differing in how each responds
to brightness and contrast differences between the kernel $f$ and a
candidate window $g$ — a same-sized window of the search area at one
particular offset — summed pixelwise over index $i$:

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

*Invariance* describes whether or not a correlation is robust or insensitive to changes in brightness and/or contrast.

* For brightness, which is additive, subtracting each side's own mean cancels any constant **added** to that side, making "Zero-mean" approaches effective.
* For contrast, which is multiplicative, dividing by each side's own norm cancels any constant **scaling** of that side, making "Normalized" approaches effective.

Whether a criterion performs each of those two cancellations determines its invariance:

| Method | Invariant to brightness (additive) | Invariant to contrast (multiplicative) | Robustness |
|:---|:---:|:---:|:---|
| CC | ❌ No | ❌ No | Least robust — neither cancellation |
| NCC | ❌ No | ✅ Yes | Only robust to contrast changes |
| ZCC | ✅ Yes | ❌ No | Only robust to brightness changes |
| ZNCC | ✅ Yes | ✅ Yes | Most robust |

ZNCC combines ZCC's mean-subtraction (brightness invariance) with NCC's
norm-division (contrast invariance), which is why it's the standard choice
in most DIC implementations — including `dictk.translation.locate`'s own
underlying `skimage.registration.phase_cross_correlation` call (see
[Fourier Domain](#fourier-domain), below).

Neither cancellation helps against *nonlinear* or
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
correlation surface rather than just its peak — see [Correlation
Visualization](./correlation_visualization.md) for what those surfaces
look like on the kernel and search area established in [Cross Correlation
(CC)](./cross_correlation.md).

Next: [Correlation Visualization](./correlation_visualization.md)
visualizes these four correlation criteria in detail; the Fourier Domain
section below explains the route `locate` itself actually takes.

## Fourier Domain

[Correlation Visualization](./correlation_visualization.md) computes CC
directly in the spatial domain: a literal sliding sum, one value per
candidate offset. The
**convolution theorem** gives an equivalent route: multiplying the two
images' Fourier transforms (one of them conjugated) and inverse-transforming
the product yields that same correlation, all at once, for every offset —
without ever explicitly sliding a window. This is exactly what
[`dictk.translation.locate`](../api/dictk/translation.html#locate) does
internally, via
[`skimage.registration.phase_cross_correlation`](https://scikit-image.org/docs/stable/api/skimage.registration.html#skimage.registration.phase_cross_correlation).
The appeal isn't a different answer — it's speed: a fast Fourier transform
(FFT) costs $O(n \log n)$ per image, against the sliding sum's $O(n^2)$
per candidate offset — decisive once images grow beyond this page's small
teaching example.

`reference_image`, `p0`, `current_image`, `kernel`, and `search` are the
same as in [Correlation Visualization](./correlation_visualization.md):

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

`locate` pads `kernel` to `search`'s own shape before comparing them — the
same padding used here:

```python
import numpy as np

pad_height = search.shape[0] - kernel.shape[0]
pad_width = search.shape[1] - kernel.shape[1]
kernel_padded = np.pad(kernel.astype(np.float64), ((0, pad_height), (0, pad_width)))

image_product = np.fft.fft2(search.astype(np.float64)) * np.fft.fft2(kernel_padded).conj()
fft_surface = np.fft.ifft2(image_product).real

dy, dx = np.unravel_index(np.argmax(fft_surface), fft_surface.shape)
print(f"FFT-domain peak offset (dx, dy) = ({dx}, {dy})")
```

```text
<!-- cmdrun python3 -c "import numpy as np; from dictk.image import read, translate, PixelCoordinate, subimage; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); pad_height = search.shape[0] - kernel.shape[0]; pad_width = search.shape[1] - kernel.shape[1]; kernel_padded = np.pad(kernel.astype(np.float64), ((0, pad_height), (0, pad_width))); image_product = np.fft.fft2(search.astype(np.float64)) * np.fft.fft2(kernel_padded).conj(); fft_surface = np.fft.ifft2(image_product).real; dy, dx = np.unravel_index(np.argmax(fft_surface), fft_surface.shape); print(f'FFT-domain peak offset (dx, dy) = ({dx}, {dy})')" -->
```

That peak, $(19, 33)$, matches $\boldsymbol{r}_{SK/\mathcal{S}}$ exactly —
the same offset [Correlation Visualization](./correlation_visualization.md)'s
`cc()` surface and `locate` itself both find. That agreement is about the peak's
*location* only, not the two surfaces' values: `fft_surface` here is the
**circular** correlation over the full padded extent (`search`'s own
shape, `100x100`), while `cc()` returns **valid** positions only (a smaller
`51x51` array, no wraparound) — the two arrays don't share a shape and
`np.allclose` between them wouldn't be meaningful. `locate` differs a
second way too: it doesn't use this raw, unnormalized cross-power
spectrum — it passes `normalization="phase"` to
`phase_cross_correlation`, dividing that spectrum by its own magnitude at
every frequency before inverting it (see the extensive comment in
[`locate`'s source](../api/dictk/translation.html#locate) for why). Both
differences change the surface's numeric character; neither changes where
its peak lands here.

### Windowing

The FFT implicitly treats an image as one period of an infinitely-repeating
signal. If the content doesn't tile seamlessly — the general case, since
nothing arranged `search`'s edges to match up — that discontinuity leaks
energy across many frequencies rather than the few the underlying content
actually has, an effect called **spectral leakage**. In a correlation
surface, leakage broadens and can shift the peak, hurting the precision
`locate` is built to provide.

**Windowing** counters this by tapering an image's edges toward zero
before transforming it, so the (still discontinuous, but now near-zero)
seam contributes far less energy. Two standard 1D windows, applied to an
image by taking the outer product of a window with itself along each axis:

$$w_{\rm Hann}(n) = 0.5 \left(1 - \cos\left(\frac{2\pi n}{N - 1}\right)\right)$$

$$w_{\rm Hamming}(n) = 0.54 - 0.46 \cos\left(\frac{2\pi n}{N - 1}\right)$$

for $n = 0, \ldots, N-1$ across a window of length $N$. Hann tapers all the
way to exactly zero at both ends; Hamming stops short (around $0.08$),
trading a little residual discontinuity for a narrower main lobe in the
transformed signal.

Windowing is **not implemented in `dictk`** — this section is a description
of the technique for context, not a feature. `dictk.translation.locate`
does not apply any windowing, and there is no `window()`-style function in
this codebase yet.