# Windowing

The FFT implicitly treats an image as one period of an
infinitely-repeating signal. If the content doesn't tile seamlessly, which is the
general case since nothing arranges an image's edges to match up, that
discontinuity leaks energy across many frequencies rather than the few
the underlying content actually has, an effect called **spectral
leakage**. In a correlation surface, leakage broadens and can shift the
peak, hurting the precision
[`dictk.translation.locate`](../api/dictk/translation.html#locate) is
built to provide.

**Windowing** counters this by tapering an image's edges toward zero
before transforming it, so the (still discontinuous, but now near-zero)
seam contributes far less energy. Two standard 1D windows, applied to an
image by taking the outer product of a window with itself along each
axis:

$$w_{\rm Hann}(n) = 0.5 \left(1 - \cos\left(\frac{2\pi n}{N - 1}\right)\right)$$

$$w_{\rm Hamming}(n) = 0.54 - 0.46 \cos\left(\frac{2\pi n}{N - 1}\right)$$

for $n = 0, \ldots, N-1$ across a window of length $N$. Hann tapers all the
way to exactly zero at both ends; Hamming stops short (around $0.08$),
trading a little residual discontinuity for a narrower main lobe in the
transformed signal.

See Harris FJ. "On the use of windows for harmonic analysis with the
discrete Fourier transform." Proceedings of the IEEE 1978;66(1):51-83.

## `window()`

[`dictk.correlation.window`](../api/dictk/correlation.html#window)
applies either taper to a 2D array. This reuses `kernel` from [Cross
Correlation (CC)](./cross_correlation.md) and the [Fourier
Domain](./correlation_criteria.md#fourier-domain) section of Correlation
Criteria — the same `checkerboard0`, `p0`, and `kernel_margin` — to show
what tapering actually does to an image before it's passed to an FFT:

```python
import numpy as np
from dictk.image import read, PixelCoordinate, subimage, write
from dictk.correlation import window, WindowingMethod

reference_image = read(path="checkerboard0.png")
p0 = PixelCoordinate(x=100, y=75)
kernel_margin = 25
kernel = subimage(
    image=reference_image,
    origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin),
    width=2 * kernel_margin,
    height=2 * kernel_margin,
)
write(arr=kernel, path="windowing_kernel_original.png")

kernel_hann = window(arr=kernel, method=WindowingMethod.HANN)
write(arr=kernel_hann.astype(np.uint8), path="windowing_kernel_hann.png")

kernel_hamming = window(arr=kernel, method=WindowingMethod.HAMMING)
write(arr=kernel_hamming.astype(np.uint8), path="windowing_kernel_hamming.png")
```

```text
<!-- cmdrun python3 -c "import numpy as np; from dictk.image import read, PixelCoordinate, subimage, write; from dictk.correlation import window, WindowingMethod; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); write(arr=kernel, path='windowing_kernel_original.png'); kernel_hann = window(arr=kernel, method=WindowingMethod.HANN); write(arr=kernel_hann.astype(np.uint8), path='windowing_kernel_hann.png'); kernel_hamming = window(arr=kernel, method=WindowingMethod.HAMMING); write(arr=kernel_hamming.astype(np.uint8), path='windowing_kernel_hamming.png'); print('Saved: windowing_kernel_original.png, windowing_kernel_hann.png, windowing_kernel_hamming.png')" -->
```

none (original) | Hann | Hamming
--- | --- | ---
![original kernel](windowing_kernel_original.png) | ![Hann-windowed kernel](windowing_kernel_hann.png) | ![Hamming-windowed kernel](windowing_kernel_hamming.png)

Every edge fades toward black; Hann's corners go fully black (tapers to
exactly 0), while Hamming's stay a faint gray (tapers to $0.08 \times
0.08 \approx 0.006$ of the original corner pixel, the product of both
axes' own $0.08$ edge value).

## Windowing in `phase_correlation()`

[`dictk.correlation.phase_correlation`](../api/dictk/correlation.html#phase_correlation)
takes an optional `windowing` parameter: when given, both `kernel` and
`search` are passed through `window()` before the existing pad/FFT steps.
Default `None` applies no windowing, matching every earlier page in this
book that calls `phase_correlation` without it. See [Correlation
Visualization](./correlation_visualization.md#phase-correlation) for
this in action -- No Windowing, Hann Windowing, and Hamming Windowing
each get their own worked example there, run on the same `kernel`/
`search` pair as the rest of that page, plus a
[Peak Prominence](./correlation_visualization.md#peak-prominence)
comparison quantifying what windowing actually buys, alongside CC,
NCC, ZCC, and ZNCC.

**Not yet wired up:** `windowing` lives on `phase_correlation()` only.
[`dictk.translation.locate`](../api/dictk/translation.html#locate) --
the function every worked example in this book actually calls to find a
point -- does not accept a `windowing` parameter and applies none.
