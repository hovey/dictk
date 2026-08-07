# Correlation Criteria

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

## Invariance and Robustness

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
underlying `skimage.registration.phase_cross_correlation` call (see [CC via
FFT](./cc_fft.md)).

Neither cancellation helps against *nonlinear* or
*spatially-varying* brightness/contrast (a shadow crossing part of the
kernel, sensor saturation) — none of the four criteria above address that.

## Brightness and Contrast Invariance in Practice

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
the kernel and search area established in [Cross Correlation
(CC)](./cross_correlation.md).

Next: [CC Visualization](./cc_visualization.md) computes and plots these
four correlation criteria as heatmaps, and [CC via
FFT](./cc_fft.md) explains the Fourier-domain route `locate` actually
takes.
