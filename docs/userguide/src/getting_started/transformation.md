# Image Transformation

Image deformations, also called *transformations* in the computer vision
literature (see Szeliski[^Szeliski_2022]), fall into the categories shown
below:

<figure>
    <img src="2d-planar-transformations.jpg" alt="2d-planar-transformations" />
    <figcaption>
        Figure: Categories of 2D planar transformations from Szeliski.
    </figcaption>
</figure>

## X-Axis Stretch

As a concrete example of the *similarity* category above,
[`dictk.imaging.stretch`](../api/dictk/imaging.html#stretch) applies a
uniaxial stretch along the x-axis: the image's top-left corner (x=0, y=0)
stays fixed, and content grows away from it, using backward mapping with
bilinear interpolation so the result has no gaps (unlike naively moving
each source pixel forward, which can leave holes). The four stretches
below range from a small, realistic deformation (5%, similar in magnitude
to a modest tensile strain in a materials test) up to a doubling (100%).

```python
import dictk
from dictk.imaging import stretch, write_image

photo = dictk.astronaut(300, 300)
write_image(photo, "astronaut_stretch_original.png")

stretch_5pct = stretch(photo, factor_x=1.05)
write_image(stretch_5pct, "astronaut_stretch_x_5pct.png")

stretch_10pct = stretch(photo, factor_x=1.10)
write_image(stretch_10pct, "astronaut_stretch_x_10pct.png")

stretch_50pct = stretch(photo, factor_x=1.50)
write_image(stretch_50pct, "astronaut_stretch_x_50pct.png")

stretch_100pct = stretch(photo, factor_x=2.00)
write_image(stretch_100pct, "astronaut_stretch_x_100pct.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.imaging import stretch, write_image; photo = dictk.astronaut(300, 300); write_image(photo, 'astronaut_stretch_original.png'); write_image(stretch(photo, factor_x=1.05), 'astronaut_stretch_x_5pct.png'); write_image(stretch(photo, factor_x=1.10), 'astronaut_stretch_x_10pct.png'); write_image(stretch(photo, factor_x=1.50), 'astronaut_stretch_x_50pct.png'); write_image(stretch(photo, factor_x=2.00), 'astronaut_stretch_x_100pct.png'); print('Saved: astronaut_stretch_original.png, astronaut_stretch_x_5pct.png, astronaut_stretch_x_10pct.png, astronaut_stretch_x_50pct.png, astronaut_stretch_x_100pct.png')" -->
```

Stretch | Image
--- | ---
Original | ![original](astronaut_stretch_original.png)
5% (factor_x=1.05) | ![5% x-axis stretch](astronaut_stretch_x_5pct.png)
10% (factor_x=1.10) | ![10% x-axis stretch](astronaut_stretch_x_10pct.png)
50% (factor_x=1.50) | ![50% x-axis stretch](astronaut_stretch_x_50pct.png)
100% (factor_x=2.00) | ![100% x-axis stretch](astronaut_stretch_x_100pct.png)

## References

[^Szeliski_2022]: Szeliski R. Computer vision: algorithms and applications, 2nd Edition, Springer Nature; 2022 Jan 3. [download](https://1drv.ms/b/c/3cc1bee5e2795295/IQBSP0s8pYRBRJArjzAAx3PbAcZ0PUh149lv7Z85uiBp-ms?e=FUynzc) (43 MB)
