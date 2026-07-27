# Subimage Generation

[`dictk.image.subimage`](../api/dictk/image.html#subimage) extracts a
rectangular crop from a source image: a `width` x `height` region whose
top-left corner sits at `origin`, expressed in the source image's own
pixel reference frame (top-left corner `(0, 0)`). `origin` may place the
requested region partially or completely outside the source image —
rather than raising an error, `subimage` fills whatever doesn't overlap
with black (zero) pixels, so the result is always a well-formed
`height x width` array. This is the building block later tutorials use to
pull a kernel or search area out of a larger reference/current image pair
around a point of interest.

## Reference image

The examples below reuse `astronaut0`, the speckle pattern combined with
the astronaut photo introduced in [Image
Generation](./image_generation.md#speckle--astronaut):

```python
import dictk
from dictk.image import combine, write

speckle = dictk.rosta(width=300, height=300, density=0.5)
photo = dictk.astronaut(width=300, height=300)
astronaut0 = combine(a=speckle, b=photo)
write(arr=astronaut0, path="astronaut0.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import combine, write; speckle = dictk.rosta(width=300, height=300, density=0.5); photo = dictk.astronaut(width=300, height=300); astronaut0 = combine(a=speckle, b=photo); write(arr=astronaut0, path='astronaut0.png'); print('Saved image: astronaut0.png')" -->
```

## Python API

[`dictk.image.PixelCoordinate`](../api/dictk/image.html#PixelCoordinate)
is a simple `(x, y)` NamedTuple used for `origin`.
[`dictk.image.subimage`](../api/dictk/image.html#subimage) itself
returns the cropped array directly, with no file written. The examples
below use
[`subimage_comparison_plot`](../api/dictk/image.html#subimage_comparison_plot),
which saves a two-panel figure: the left panel shows where the region
falls relative to the source image (blue/red boxes), and the right panel
shows the extracted result on its own, in its own local reference frame —
top-left corner `(0, 0)` — sharing the *same* axis limits as the left
panel so the two red boxes render at matching scale. It's built from two
smaller single-panel functions, also available individually:
[`subimage_bounds_plot`](../api/dictk/image.html#subimage_bounds_plot)
(the left panel alone) and
[`subimage_plot`](../api/dictk/image.html#subimage_plot) (the right
panel alone, but zoomed to the subimage's own size rather than sharing
the source image's scale).

### Square, fully inside

An 80x80 square region entirely within `astronaut0`'s 300x300 bounds.
[`subimage_comparison_plot`](../api/dictk/image.html#subimage_comparison_plot)
draws both panels side by side, sharing the *same* axis limits, so the
red box in the right panel renders at identical scale to the one on the
left — instead of the right panel zooming in to fit just the 80x80
crop:

```python
from dictk.image import PixelCoordinate, subimage_comparison_plot

origin = PixelCoordinate(x=100, y=40)
subimage_comparison_plot(image=astronaut0, origin=origin, width=80, height=80, path="subimage_comparison_80w_by_80h_at_100_40.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import PixelCoordinate, combine, subimage_comparison_plot; speckle = dictk.rosta(width=300, height=300, density=0.5); photo = dictk.astronaut(width=300, height=300); astronaut0 = combine(a=speckle, b=photo); origin = PixelCoordinate(x=100, y=40); subimage_comparison_plot(image=astronaut0, origin=origin, width=80, height=80, path='subimage_comparison_80w_by_80h_at_100_40.png'); print('Saved: subimage_comparison_80w_by_80h_at_100_40.png')" -->
```

<figure>
    <img src="subimage_comparison_80w_by_80h_at_100_40.png" alt="square subimage, fully inside, source and extraction side by side at matching scale" />
    <figcaption>Left: square subimage (80x80) at origin (100, 40), lying entirely within the source image bounds. The blue 'o' is the origin of the source image (0, 0); the red 'o' is the origin of the subimage in the source image's reference frame (100, 40). Right: the same subimage extracted on its own, in its own local reference frame — the red 'o' here is (0, 0).</figcaption>
</figure>

### Rectangle, fully inside

A 180x70 region — wider than it is tall — also entirely within the
source image bounds:

```python
from dictk.image import PixelCoordinate, subimage_comparison_plot

origin = PixelCoordinate(x=50, y=200)
subimage_comparison_plot(image=astronaut0, origin=origin, width=180, height=70, path="subimage_comparison_180w_by_70h_at_50_200.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import PixelCoordinate, combine, subimage_comparison_plot; speckle = dictk.rosta(width=300, height=300, density=0.5); photo = dictk.astronaut(width=300, height=300); astronaut0 = combine(a=speckle, b=photo); origin = PixelCoordinate(x=50, y=200); subimage_comparison_plot(image=astronaut0, origin=origin, width=180, height=70, path='subimage_comparison_180w_by_70h_at_50_200.png'); print('Saved: subimage_comparison_180w_by_70h_at_50_200.png')" -->
```

<figure>
    <img src="subimage_comparison_180w_by_70h_at_50_200.png" alt="rectangular subimage, fully inside, source and extraction side by side at matching scale" />
    <figcaption>Left: rectangular subimage (180x70) at origin (50, 200), lying entirely within the source image bounds. The blue 'o' is the origin of the source image (0, 0); the red 'o' is the origin of the subimage in the source image's reference frame (50, 200). Right: the same subimage extracted on its own, in its own local reference frame — the red 'o' here is (0, 0).</figcaption>
</figure>

### Partially outside

A 120x120 region with a negative origin, straddling the source image's
top-left corner. `subimage` fills the part of the region above and to
the left of the source with black:

```python
from dictk.image import PixelCoordinate, subimage_comparison_plot

origin = PixelCoordinate(x=-20, y=-40)
subimage_comparison_plot(image=astronaut0, origin=origin, width=120, height=120, path="subimage_comparison_120w_by_120h_at_-20_-40.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import PixelCoordinate, combine, subimage_comparison_plot; speckle = dictk.rosta(width=300, height=300, density=0.5); photo = dictk.astronaut(width=300, height=300); astronaut0 = combine(a=speckle, b=photo); origin = PixelCoordinate(x=-20, y=-40); subimage_comparison_plot(image=astronaut0, origin=origin, width=120, height=120, path='subimage_comparison_120w_by_120h_at_-20_-40.png'); print('Saved: subimage_comparison_120w_by_120h_at_-20_-40.png')" -->
```

<figure>
    <img src="subimage_comparison_120w_by_120h_at_-20_-40.png" alt="subimage partially outside bounds, source and extraction side by side at matching scale" />
    <figcaption>Left: subimage (120x120) at origin (-20, -40), lying partially outside the source image bounds (straddling its top-left corner). The blue 'o' is the origin of the source image (0, 0); the red 'o' is the origin of the subimage in the source image's reference frame (-20, -40). Right: the same subimage extracted on its own, in its own local reference frame — the red 'o' here is (0, 0); the black band along the top and left is zero-padding, where the requested region fell outside <code>astronaut0</code>.</figcaption>
</figure>

### Completely outside

A 40x100 region entirely beyond the source image's bounds — its x-range
(310 to 350) shares no pixels with the source's (0 to 300), so there is
no overlap at all and the result is entirely black:

```python
from dictk.image import PixelCoordinate, subimage_comparison_plot

origin = PixelCoordinate(x=310, y=250)
subimage_comparison_plot(image=astronaut0, origin=origin, width=40, height=100, path="subimage_comparison_40w_by_100h_at_310_250.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import PixelCoordinate, combine, subimage_comparison_plot; speckle = dictk.rosta(width=300, height=300, density=0.5); photo = dictk.astronaut(width=300, height=300); astronaut0 = combine(a=speckle, b=photo); origin = PixelCoordinate(x=310, y=250); subimage_comparison_plot(image=astronaut0, origin=origin, width=40, height=100, path='subimage_comparison_40w_by_100h_at_310_250.png'); print('Saved: subimage_comparison_40w_by_100h_at_310_250.png')" -->
```

<figure>
    <img src="subimage_comparison_40w_by_100h_at_310_250.png" alt="subimage completely outside bounds, source and extraction side by side at matching scale" />
    <figcaption>Left: subimage (40x100) at origin (310, 250), lying entirely outside the source image bounds. The blue 'o' is the origin of the source image (0, 0); the red 'o' is the origin of the subimage in the source image's reference frame (310, 250). Right: the same subimage extracted on its own, in its own local reference frame — the red 'o' here is (0, 0); entirely zero-padded black, since none of the requested region overlapped <code>astronaut0</code>.</figcaption>
</figure>
