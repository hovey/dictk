# Single Point Motion

Consider a single point $P$, fixed to a physical location on the object
being imaged. In the **reference image** $i_0$, this point $P$ is located
at a *known* pixel location, for example $\boldsymbol{r}_{OP/\mathcal{F}} = (100, 75)$ pixels.
This vector, from the origin $O$ of the reference image frame $\mathcal{F}$
to the pixel point
$P$, locates the **reference configuration**.  For brevity, we will use
$\boldsymbol{p}_0$ to denote the fully explicit vector $\boldsymbol{r}_{OP/\mathcal{F}}$.

Next, the object is moved (e.g., translated, rotated, stretched, or deformed —
see [Image Transformation](./transformation.md)).  A second image $i_1$,
called the **current image**, is taken.  *Where is point $P$ from $i_0$ located
in $i_1$?*  We label point $P$'s *found* location in $i_1$ as $P'$.
For brevity, we will use $\boldsymbol{p}_1$
to denote the fully explicit vector $\boldsymbol{r}_{OP'/\mathcal{F}}$.

Note that the camera itself has not moved, only the object and any point of 
interest on the object have moved.  The origin $O$ and the reference frame $\mathcal{F}$
are the same across the two images $i_0$ and $i_1$.

The canonical problem solved by digital image correlation (DIC) is as follows:

* Given a point $P$ in image $i_0$, find the location of that same point $P'$ in image $i_1$.

Below, we motivate this canonical problem with a simple example of a single
point translation.  We first develop a manual solution to serve as the known
ground truth.  Then, we illustrate how 
[`dictk.translation.locate`](../api/dictk/translation.html#locate)
solves this problem numerically via DIC.

## Reference Configuration

The examples below reuse `checkerboard0`, the speckle pattern combined
with the checkerboard introduced in [Image
Generation](./image_generation.md#speckle--checkerboard).  This will be the
`reference_image`, matching `locate`'s own parameter name:

```python
from dictk.image import read, PixelCoordinate
from dictk.plot import point_plot, ArrowAnnotation

reference_image = read(path="checkerboard0.png")

p0 = PixelCoordinate(x=100, y=75)
point_plot(
    image=reference_image,
    arrows=[
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0), head=p0, color="orange", label=r"$\boldsymbol{p}_0$"
        )
    ],
    figsize=(6.4, 4.8),
    path="single_point_motion_p0.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate; from dictk.plot import point_plot, ArrowAnnotation; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); point_plot(image=reference_image, arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p0, color='orange', label=r'\$\\boldsymbol{p}_0\$')], figsize=(6.4, 4.8), path='single_point_motion_p0.png'); print('Saved: single_point_motion_p0.png')" -->
```

<figure>
    <img src="single_point_motion_p0.png" alt="reference image with reference configuration p0 marked by an orange arrow from the origin" />
    <figcaption>Reference image $i_0$ and reference configuration (orange arrow) $\boldsymbol{p}_0 = (100, 75)$ pixels.</figcaption>
</figure>

## Current Configuration and Displacement

For this page, the current image $i_1$ is generated with
[`dictk.image.translate`](../api/dictk/image.html#translate) (see [Image
Transformation](./transformation.md#pure-translation-rigid-body-motion)): every pixel of
`reference_image` shifts by the same `(dx, dy)`, a **rigid-body
translation**.  Because the whole
image moves together, point $P$'s new location follows directly:

```python
from dictk.image import translate

dx, dy = -6, 8
current_image = translate(arr=reference_image, dx=dx, dy=dy)
p1 = PixelCoordinate(x=p0.x + dx, y=p0.y + dy)  # ground truth, known here by construction
```

We define the **displacement** of the point $\delta \boldsymbol{p}$ as the
relative motion between the reference configuration $\boldsymbol{p}_0$ and
the current configuration $\boldsymbol{p}_1$, such that

$$\boldsymbol{p}_0 + \delta \boldsymbol{p} := \boldsymbol{p}_1 \implies \delta \boldsymbol{p} = \boldsymbol{p}_1 - \boldsymbol{p}_0$$

so with $\boldsymbol{p}_1 = (94, 83)$ and $\boldsymbol{p}_0 = (100, 75)$,

$$\delta \boldsymbol{p} = (94, 83) - (100, 75) = (-6, 8) \; \text{pixels}$$

```python
point_plot(
    image=current_image,
    arrows=[
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0), head=p0, color="orange", label=r"$\boldsymbol{p}_0$"
        ),
        ArrowAnnotation(
            tail=PixelCoordinate(x=0, y=0), head=p1, color="cyan", label=r"$\boldsymbol{p}_1$"
        ),
        ArrowAnnotation(
            tail=p0, head=p1, color="magenta", label=r"$\delta \boldsymbol{p}$"
        ),
    ],
    figsize=(6.4, 4.8),
    path="single_point_motion_p1_displacement.png",
)
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.plot import point_plot, ArrowAnnotation; reference_image = read(path='checkerboard0.png'); p0 = PixelCoordinate(x=100, y=75); current_image = translate(arr=reference_image, dx=-6, dy=8); p1 = PixelCoordinate(x=p0.x - 6, y=p0.y + 8); point_plot(image=current_image, arrows=[ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p0, color='orange', label=r'\$\\boldsymbol{p}_0\$'), ArrowAnnotation(tail=PixelCoordinate(x=0, y=0), head=p1, color='cyan', label=r'\$\\boldsymbol{p}_1\$'), ArrowAnnotation(tail=p0, head=p1, color='magenta', label=r'\$\delta \\boldsymbol{p}\$')], figsize=(6.4, 4.8), path='single_point_motion_p1_displacement.png'); print('Saved: single_point_motion_p1_displacement.png')" -->
```

<figure>
    <img src="single_point_motion_p1_displacement.png" alt="current image with reference configuration p0 marked by an orange arrow from the origin, current configuration p1 marked by a cyan arrow from the origin, and displacement marked by a magenta arrow from p0 to p1" />
    <figcaption>Current image $i_1$ with reference configuration (orange arrow) $\boldsymbol{p}_0 = (100, 75)$ pixels, current configuration (cyan arrow) $\boldsymbol{p}_1 = (94, 83)$ pixels, and displacement (magenta arrow) $\delta \boldsymbol{p} = (-6, 8)$ pixels.  Because the object has moved, the image shows a black margin on the top and right, with height 8 pixels and width 6 pixels, respectively, and cropping of the squares on the left and bottom of the image.</figcaption>
</figure>

In the example above, `p1` was only known in advance because we generated
`current_image` ourselves with a known `translate`. In practice, the
location $\boldsymbol{p}$ is unknown and found via DIC of a pair of images.

Below, we illustrate the canonical DIC process:

* Given a $\boldsymbol{p}_0$ in the `reference_image`, find $\boldsymbol{p}_1$
in the `current_image`.

The next page, [Cross Correlation (CC)](./cross_correlation.md), shows how the
`locate` function calculates $\boldsymbol{p}_1$ directly, using the
technique its name describes.
