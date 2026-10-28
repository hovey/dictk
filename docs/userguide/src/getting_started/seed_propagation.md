# Seed Propagation

[Kernel Warping](./kernel_warping.md) added `locate_warp`, which tracks
each point in two stages. IC-GN, the second stage, refines a warp one
iteration at a time, so it needs a warp to start from. That starting
warp is the *seed*.

The first stage builds the seed.
[`dictk.translation.locate`](../api/dictk/translation.html#locate) cuts
a rigid, square kernel around the point in the reference image. It
phase-correlates that kernel against a search area of the current
image. The correlation surface peaks at the whole-pixel displacement
$(u_0, v_0)$ where the rigid kernel best matches. The seed takes that
displacement and sets all four gradient terms of
[Kernel Warping's](./kernel_warping.md#inverse-compositional-gauss-newton)
$\boldsymbol{p} = (u, u_x, u_y, v, v_x, v_y)$ to zero:

$$
\boldsymbol{p}_0 = (u_0, 0, 0, v_0, 0, 0).
$$

The seed is a rigid, whole-pixel guess. IC-GN adds the fractional
displacement, the stretch, and the shear. Under Kernel Warping's 2%
stretch, every seed on its 2862 points landed within 1 px of the true
position:

<!-- cmdrun python3 seed_propagation_kernel_warping_seeds.py -->

IC-GN then refined every point to within 0.024 px. But, when deformation grows
large, the error in this initial displacement $(u_0, v_0)$ can grow,
causing IC-GN to converge to an incorrect answer.

[Figure](#fig-sp-seed) shows a correct seed and a defeated seed, both
under a 15% stretch and a 0.15 shear. A defeated seed lands more than
1 px from the true displacement:

<!-- cmdrun python3 seed_propagation_seed.py -->

<figure id="fig-sp-seed">
    <img src="seed_propagation_seed.png" alt="a two-by-three grid of panels. Top row, a correct seed at point (78, 219): a reference-image close-up with a dashed white square kernel around a red dot; a noisy phase-correlation surface over u and v from -25 to 25 px whose brightest cell, boxed in orange at (8, 3), sits beside a red cross; a current-image close-up where a dashed orange square and a solid orange parallelogram overlap around a red cross, titled IC-GN misses by 0.001 px. Bottom row, a defeated seed at point (56, 43): the same layout, but the boxed peak sits at (-12, 16), far from the red cross, and in the current image the solid orange outline is a large distorted shape far from the red cross, titled IC-GN misses by 28.718 px" />
    <figcaption>Two seeds under a 15% stretch and a 0.15 shear. Left: the reference kernel around each point. Middle: <code>translation.locate</code>'s phase-correlation surface over the search area. The orange box marks its highest peak, the seed $(u_0, v_0)$, and the red cross marks the true displacement. Right: the current image, with the seed's rigid square (dashed) and IC-GN's final warp (solid). Top: at $(78, 219)$, the peak lands at $(8, 3)$, 0.50 px from the true $(7.74, 3.43)$, and IC-GN converges to within 0.001 px. Bottom: at $(56, 43)$, no peak stands out at the true $(5.94, 5.56)$. The highest peak lands at $(-12, 16)$, and IC-GN converges 28.718 px away. Each row's point has the seed error nearest the median among the sweep's correct seeds (top) or defeated seeds (bottom), as described in <a href="#the-sweep">The Sweep</a>.</figcaption>
</figure>

A defeated seed lands on the wrong speckles. IC-GN starts from there
and converges to a wrong warp. `locate_warp` raises no error when that
happens.

## The Sweep

The sweep maps where seeds fail across a grid of 49 combinations of
seven stretch values and seven shear values. It stretches the image
along $x$ by 0% to 30%, and shears it by 0 to 0.30, both in steps of
0.05. Each combination tracks the same 30 points, so the sweep runs
$30 \times 49 = 1470$ fits. Each point sits at a
random position at least 40 px from every edge of the 300x300
`astronaut0` image. Each point also gets its own random fractional
shift. The shifts fall between 4 and 8 px along $x$ and between 2 and
6 px along $y$, the same range [Rigid Versus Warped
Kernel](./kernel_warping.md#rigid-versus-warped-kernel) used.

<!-- cmdrun python3 seed_propagation_points.py -->

<figure id="fig-sp-points">
    <img src="seed_propagation_points.png" alt="two panels. Left: the 300 by 300 astronaut0 speckle image with a dashed white square inset 40 px from each edge, 30 orange dots scattered inside it, and one red dot at (217, 256). Right: a close-up of the deformed image around that red dot. A dashed white square marks the reference kernel centered on the dot. A dotted orange parallelogram, wider than the square and leaning right toward the bottom, shares the square's center. A solid orange copy of that parallelogram sits down and to the right, at the end of an orange arrow from the dot to a red cross" />
    <figcaption>Left: the 30 reference points on <code>astronaut0</code>, each at least 40 px inside the dashed square. Right: the red point under a 15% stretch and a 0.15 shear, drawn over the current image. The dashed white square is the reference kernel. The dotted orange parallelogram is that kernel deformed about the point, so its center stays put. The solid orange parallelogram adds the point's shift, (5.66, 4.94) px, and the red cross marks the true position. This point's shift sits nearest the median of the 30 shifts.</figcaption>
</figure>

The sweep builds a separate current image for each point. Each image
stretches and shears about that point as a fixed center, so the
deformation itself never moves the point. [Figure](#fig-sp-points)'s
right panel shows this: the dotted parallelogram keeps the reference
kernel's center. The point then moves by its shift alone, at most 10 px.
The 25 px search margin around a 13 px kernel margin leaves 12 px of
travel. The search area always contains the true position. Any failure
comes from the rigid kernel's mismatch.

The sweep uses 30 random points because a single point alone can
mislead.
Kernel Warping's point at $(150, 150)$, swept alone, failed fewer seeds
at 20% stretch with a 0.15 shear (14 of 30 shifts) than with no shear
(28). The 30 random points show no such dip. They fail 29 and 26 seeds at those
two cells.

A seed fails when it lands more than 1 px from the true position. A
correct whole-pixel match lands within a 0.71 px radius (0.5 pixel in
the $x$-axis, 0.5 pixel in the $y$-axis,
$0.71 \approx \sqrt{0.5^2 + 0.5^2}$). A `locate_warp` result misses
when it lands more than 1 px away.

## Where the Seed Breaks

<!-- cmdrun python3 seed_propagation_baseline.py -->

Both counts stay at zero up to a 5% stretch with a 0.05 shear. From
there they rise along both axes. A 10% stretch alone fails 8 seeds,
and `locate_warp` misses 5 points. A 0.10 shear alone fails 1 seed,
and `locate_warp` misses 1 point. At 15%, the two come closer. A 15%
stretch alone fails 20 seeds and misses 13 points. A 0.15 shear alone
fails 15 seeds and misses 9 points. At 20% stretch, `locate_warp`
misses at least 22 of 30 points at every shear.

Under a 15% stretch and a 0.15 shear, the 30 random points fail 22
seeds, and `locate_warp` misses 20. Kernel Warping's single point at
$(150, 150)$ failed 11 seeds and missed 8, out of 30 shifts, at the
same deformation.

Each miss lands far from the true position. Of all 1470 fits, 1469
land either within 0.02 px of the true position or more than 2.87 px
from it. The one exception lands 0.267 px off, at 25% stretch and 0.10
shear. A miss puts the point on the wrong speckles, and
`locate_warp`'s return value looks the same as a correct one.

Across the sweep, the seed fails 1095 times. IC-GN pulls 123 of those
seeds back to the right position. At a 0.15 shear alone, it pulls back
6 of the 15. The other 972 failed seeds become misses. No miss starts
from a correct seed. Every miss traces back to a failed seed, so the
fix belongs at the seed, not in IC-GN.

## Detecting a Miss

For each point, `locate_warp` returns only the tracked position
$(x, y)$ in the current image, in pixels, as a `SubpixelCoordinate`.
A miss 28.718 px off looks the same as a correct fit 0.001 px off.
Inside `locate_warp`, IC-GN computes two more numbers, but
`locate_warp` discards both. The first is the final ZNSSD, [Kernel
Warping's](./kernel_warping.md#inverse-compositional-gauss-newton)
$C(\boldsymbol{p})$. It measures how well the warped kernel matches the
current image:

* A ZNSSD of 0 is a perfect score.
* A ZNSSD of 4 is the worst score, reached when the current image
  shows the kernel with its contrast inverted.

The second is the iteration count. IC-GN stops once every update falls below $10^{-6}$,
or after $n_{\text{MAX\_ITER}} = 50$ updates.

The script below reruns all 1470 fits from the sweep and records both
numbers for each fit. A fit is correct when it lands within 1 px of the
true position:

<!-- cmdrun python3 seed_propagation_quality.py -->

<figure id="fig-sp-quality">
    <img src="seed_propagation_quality.png" alt="two histograms with logarithmic count axes, correct fits in blue and misses in orange. Left, final ZNSSD on a logarithmic axis from 1e-6 to about 3: the blue correct fits cluster between 1e-4 and 1e-2 with one fit near 0.1, the orange misses cluster between 0.7 and 3, and no fit falls between 0.1 and 0.7. Right, IC-GN iterations from 0 to 50: the blue correct fits peak near 10 iterations with a thin tail to 46 and a small bar of 4 at 50, and the orange misses form one tall bar of 971 at 50 plus one fit at 43" />
    <figcaption>Final ZNSSD (left) and IC-GN iteration count (right) for the sweep's 1470 fits: 498 correct fits (blue) and 972 misses (orange). Both count axes are logarithmic, so single fits stay visible. A miss lands more than 1 px from the true position.</figcaption>
</figure>

ZNSSD separates the two groups with no overlap. Correct fits score at
most 0.0995, and misses score at least 0.6952. Any threshold between
those two values flags all 972 misses and none of the 498 correct fits.
In [ZNCC](./correlation_criteria.md) terms, $\text{ZNCC} = 1 - C/2$, so
every correct fit keeps a ZNCC of at least 0.950, and every miss stays
at or below 0.652.

The 0.0995 belongs to the one fit from [Where the Seed
Breaks](#where-the-seed-breaks) that landed 0.267 px off. That fit
counts as correct under the 1 px rule.

The iteration count separates the groups almost as well. Correct fits
took a median of 11 iterations. 971 of the 972 misses ran all 50
without converging. The count misclassifies 5 fits. Four correct fits
also ran all 50 iterations. Three of those four landed within 0.005 px,
but their updates never all fell below $10^{-6}$. The fourth is the
0.267 px fit. One miss, at a 30% stretch and a 0.05 shear, converged
after 43 iterations, 26.704 px off. Its ZNSSD of 1.3003 still flags it.

Every miss the iteration count flags, ZNSSD also flags. On this sweep,
the iteration count adds nothing that ZNSSD does not already show. The
result comes from one image, one 27x27 kernel, and a 50-iteration cap.
Another speckle pattern could narrow the gap between 0.0995 and 0.6952.

Continue to [Postprocessing](./postprocessing.md).

### `seed_propagation_quality.py`

<details>
<summary>Show the code</summary>

```python
<!-- cmdrun cat seed_propagation_quality.py -->
```

</details>

### `seed_propagation_kernel_warping_seeds.py`

<details>
<summary>Show the code</summary>

```python
<!-- cmdrun cat seed_propagation_kernel_warping_seeds.py -->
```

</details>

### `seed_propagation_seed.py`

<details>
<summary>Show the code</summary>

```python
<!-- cmdrun cat seed_propagation_seed.py -->
```

</details>

### `seed_propagation_points.py`

<details>
<summary>Show the code</summary>

```python
<!-- cmdrun cat seed_propagation_points.py -->
```

</details>

### `seed_propagation_baseline.py`

<details>
<summary>Show the code</summary>

```python
<!-- cmdrun cat seed_propagation_baseline.py -->
```

</details>
