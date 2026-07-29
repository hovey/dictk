# CC Visualization

[Cross Correlation (CC)](./cross_correlation.md) introduced four spatial-domain
correlation criteria — CC, NCC, ZCC, and ZNCC — as formulas. This page computes
and visualizes all four as heatmaps, on the same kernel and search area
established there, using [`dictk.correlation`](../api/dictk/correlation.html)'s
`cc`, `ncc`, `zcc`, and `zncc` functions.

`reference_image`, `p0`, `current_image`, `kernel_margin`, and
`search_margin` are the same as in [Cross
Correlation (CC)](./cross_correlation.md); `kernel` and `search` are the raw
subimage arrays those margins describe:

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

Each function returns the full correlation surface — one value per
candidate offset, not just its peak:

```python
from dictk.correlation import cc, ncc, zcc, zncc
from dictk.image import correlation_surfaces_plot

cc_surface = cc(kernel=kernel, search=search)
ncc_surface = ncc(kernel=kernel, search=search)
zcc_surface = zcc(kernel=kernel, search=search)
zncc_surface = zncc(kernel=kernel, search=search)

correlation_surfaces_plot(
    cc=cc_surface,
    ncc=ncc_surface,
    zcc=zcc_surface,
    zncc=zncc_surface,
    path="cc_visualization_surfaces.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate, subimage, correlation_surfaces_plot; from dictk.correlation import cc, ncc, zcc, zncc; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); kernel_margin = 25; kernel = subimage(image=reference_image, origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin), width=2 * kernel_margin, height=2 * kernel_margin); search_margin = 50; search_center = p0; search = subimage(image=current_image, origin=PixelCoordinate(x=search_center.x - search_margin, y=search_center.y - search_margin), width=2 * search_margin, height=2 * search_margin); cc_surface = cc(kernel=kernel, search=search); ncc_surface = ncc(kernel=kernel, search=search); zcc_surface = zcc(kernel=kernel, search=search); zncc_surface = zncc(kernel=kernel, search=search); correlation_surfaces_plot(cc=cc_surface, ncc=ncc_surface, zcc=zcc_surface, zncc=zncc_surface, path='cc_visualization_surfaces.png'); print('Saved: cc_visualization_surfaces.png')" -->
```

<figure>
    <img src="cc_visualization_surfaces.png" alt="four heatmap panels comparing the CC, NCC, ZCC, and ZNCC correlation surfaces for the same kernel and search area, each with a colorbar and a red X marking its own peak" />
    <figcaption>The CC, NCC, ZCC, and ZNCC correlation surfaces for the kernel and search area established in <a href="./cross_correlation.html">Cross Correlation (CC)</a>. Each panel's horizontal/vertical axes are the candidate offset $(\Delta x, \Delta y)$ — not an absolute image position — and its own colorbar shows that criterion's own value range (CC's raw sum has arbitrary units and grows with image brightness; NCC/ZNCC are bounded to $[-1, 1]$ by construction). The red &times; in each panel marks that surface's own peak.</figcaption>
</figure>

Despite the very different value ranges, all four panels peak at the same
offset, $\boldsymbol{r}_{SK/\mathcal{S}} = (19, 33)$ pixels — matching the
value already found by
[`locate`](../api/dictk/translation.html#locate) in [Cross Correlation
(CC)](./cross_correlation.md#locating-the-point). That agreement isn't a
coincidence: `kernel` and `search` here have identical brightness and
contrast (both come from the same `checkerboard0.png`, only translated),
so nothing distinguishes CC from the criteria built to tolerate brightness
or contrast differences it can't. The next page, [CC via
FFT](./cc_fft.md), explains why `locate` computes this same underlying
quantity in the Fourier domain rather than by sliding a kernel across
every position directly, as done here.
