# CC via FFT

[CC Visualization](./cc_visualization.md) computed CC directly in the
spatial domain: a literal sliding sum, one value per candidate offset. The
**convolution theorem** gives an equivalent route: multiplying the two
images' Fourier transforms (one of them conjugated) and inverse-transforming
the product yields that same correlation, all at once, for every offset —
without ever explicitly sliding a window. This is exactly what
[`dictk.translation.locate`](../api/dictk/translation.html#locate) does
internally, via
[`skimage.registration.phase_cross_correlation`](https://scikit-image.org/docs/stable/api/skimage.registration.html#skimage.registration.phase_cross_correlation).
The appeal isn't a different answer, it's speed: a fast Fourier transform
(FFT) costs $O(n \log n)$ per image, against the sliding sum's $O(n^2)$
per candidate offset — decisive once images grow beyond this page's small
teaching example.

`reference_image`, `p0`, `current_image`, `kernel`, and `search` are the
same as in [CC Visualization](./cc_visualization.md):

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
the same offset [CC Visualization](./cc_visualization.md)'s `cc()` surface
and `locate` itself both find. That agreement is about the peak's
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
its peak lands, here.

## Windowing

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

Windowing is **not implemented in dictk** — this section is a description
of the technique for context, not a feature. `dictk.translation.locate`
does not apply any windowing, and there is no `window()`-style function in
this codebase yet.
