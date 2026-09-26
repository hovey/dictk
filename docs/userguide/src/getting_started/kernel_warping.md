# Kernel Warping

[High Point Density](./high_point_density.md) left a wide strain
distribution unexplained. Its 11024 Gauss points ranged from about
-16400 to 106100 microstrain. VIC-2D's own measurements of the same
stretch stayed between about 17300 and 23100. That page blamed element
size: a fixed tracking error, divided by a small $L$, becomes a large
strain error.

That explanation leaves out the tracking error's shape. This page
measures the error against each point's known true position. The $x$ error
follows a wave, about ±0.13 px tall, tied to where each point's true
position falls within its pixel. That wave explains High Point Density's
vertical stripes.
This page introduces `locate_warp`, a subpixel method different from
`locate_subpixel`. It cuts the $x$ error's standard deviation from
0.109 px to 0.008 px. Relative
to the `locate_subpixel` baseline, `locate_warp` shrinks the strain
spread by a factor of 14, from a standard deviation of 16531 to 1161
microstrain.

## Pixel Locking

The subject 2% stretch sends every reference point to a new known $x$ location,
$x = 1.02\,X$ ($y = Y$ remains constant for all points). High Point
Density's own `locate_subpixel` call already tracked all 2862 of those
points. Subtracting each point's known true
position from its tracked one gives the tracking error:

<!-- cmdrun python3 kernel_warping_pixel_locking.py -->

<figure>
    <img src="kernel_warping_pixel_locking.png" alt="two panels. Left: x error of every tracked point plotted against the fractional part of its true x position, gray dots with black binned means tracing one full sine-like cycle, about -0.14 px near 0.3 and +0.12 px near 0.7, crossing zero near 0.5. Right: x error along one grid row against true x, oscillating between about -0.18 and +0.17 px, with dotted vertical lines every 51 px marking where each cycle begins" />
    <figcaption>Left: each point's $x$ error against the fractional part of its true $x$ (gray), with the mean of each tenth of a pixel (black). Right: the same error along row 27 of the grid, at $y = 151$ px. Row 27 is the middle of the grid's 54 rows, chosen to stay clear of the image's top and bottom edges. The wave depends only on $x$, so every row shows it. Each row's error correlates 0.82 to 0.94 with the average over all rows. Row 27 sits at the low end, 0.82. So this panel shows the least regular of the 54 rows. Dotted lines mark every 51 px, the distance over which the true position's fractional part completes one cycle.</figcaption>
</figure>

The left panel shows the error depends on where the true position sits
within its pixel. Points just past a whole pixel read low. Points just
short of the next whole pixel read high. Points at an exact half pixel
read about right. This is **pixel locking**: a subpixel estimator's
answer drifts toward whole-pixel values. `locate_subpixel` refines the
peak of an upsampled phase correlation surface. That surface comes from
a zero-padded kernel, and its peak shifts in a way that depends on the
true fractional position. About half of this wave's size comes
from how the stretched image itself was made: `image.stretch` uses
bilinear interpolation. [The Residual
Wave](#the-residual-wave) separates the two causes.

The right panel shows why this matters for strain. Every reference
position $X$ on the grid is a whole pixel. So the true position,
$x = 1.02\,X = X + 0.02\,X$, has the same fractional part as
$0.02\,X$. That fractional part climbs from 0 to 1, then wraps back to
0, each time $0.02\,X$ grows by 1. That takes
$\Delta X = 1 / 0.02 = 50$ reference pixels. The stretch scales those
50 px by 1.02, so one cycle spans $1.02 \times 50 = 51$ pixels in the
current image. So the bias itself forms a wave
along $x$, about 0.13 px tall and 51 px long. Strain measures the slope
of displacement. The slope of that wave swings to about
$\pm 0.13 \cdot 2\pi / 51 \approx \pm 0.016$, or 16000 microstrain.
That matches the scale of High Point Density's measured standard
deviation, 16531 microstrain. The same wave explains the vertical stripes
in that page's field figure, one stripe pair per cycle.

It also explains why
[Simple Stretch Revisited](./simple_stretch.html#simple-stretch-revisited)
never saw this. That page spaced its points 50 px apart, one full bias
cycle. Every true position landed on a whole pixel, so every node sat
at the same point on the wave. High Point Density's 5 px spacing spread
the nodes across the whole wave, and the error showed up in every
element.

## Inverse Compositional Gauss-Newton

Commercial DIC codes such as VIC-2D warp the kernel itself, instead of
refining a correlation peak (as done by `locate_subpixel`).
[`dictk.grid.locate_warp`](../api/dictk/grid.html#locate_warp) warps
the kernel too, as VIC-2D does. It works in two stages.

First, [`dictk.translation.locate`](../api/dictk/translation.html#locate)
finds the nearest whole pixel. Second, **inverse compositional
Gauss-Newton (IC-GN)** refines it. IC-GN lets the reference kernel
deform by an affine warp, $\boldsymbol{W}$, with six
parameters: $u$, $u_x$, $u_y$, $v$,
$v_x$, and $v_y$. $u$ and $v$ are the displacements along $x$ and $y$.
The subscripts mark their gradients across the kernel, so
$u_x = \partial u / \partial x$ and $v_y = \partial v / \partial y$:

$$
\boldsymbol{W}(\Delta x, \Delta y; \boldsymbol{p}) =
\begin{bmatrix}
1 + u_x & u_y & u \\
v_x & 1 + v_y & v \\
0 & 0 & 1
\end{bmatrix}
\begin{bmatrix} \Delta x \\ \Delta y \\ 1 \end{bmatrix},
\qquad
\boldsymbol{p} = (u, u_x, u_y, v, v_x, v_y).
$$

Here $(\Delta x, \Delta y)$ labels each pixel of the reference kernel
by its fixed offset from the kernel's center, from $-13$ to $+13$ px
here. The warp maps each such pixel to its position in the current
image. IC-GN searches for the $\boldsymbol{p}$ that minimizes the
zero-normalized sum of squared differences (ZNSSD) between the
reference kernel $f$ and the current image sampled through the warp,
$g$:

$$
C(\boldsymbol{p}) = \sum_{\Delta x, \Delta y}
\left[ \frac{f - \bar{f}}{\lVert f - \bar{f} \rVert}
- \frac{g(\boldsymbol{W}) - \bar{g}}{\lVert g - \bar{g} \rVert} \right]^2 .
$$

Each iteration solves for a small update $\Delta\boldsymbol{p}$ to
the *reference* kernel. It then composes that update's inverse into the
current warp, $\boldsymbol{W} \leftarrow \boldsymbol{W} \circ
\boldsymbol{W}(\Delta\boldsymbol{p})^{-1}$. The inverse compositional
form puts all gradient work on $f$. It computes the Hessian once per
point, not once per iteration. Cubic B-splines sample $g$ at the
warped, fractional positions. The tracked position is the warp's own
translation, $(u, v)$.

### Deriving the Update

Four steps lead from $C(\boldsymbol{p})$ to the update IC-GN applies.
[`dictk.warp`](../api/dictk/warp.html)'s refinement follows them in
order. Below, $\boldsymbol{\xi} = (\Delta x, \Delta y)$ names one
pixel's offset in the kernel, and every sum runs over all
$(2 \cdot 13 + 1)^2 = 729$ pixels.

**1. Reduce ZNSSD to least squares.** Write $\tilde{f} = f - \bar{f}$
and $\tilde{g} = g - \bar{g}$ for the zero-mean kernels. Expanding the
square in $C$ gives

$$
C(\boldsymbol{p}) = 2 - 2\,
\frac{\sum \tilde{f}\,\tilde{g}}{\lVert \tilde{f} \rVert\, \lVert \tilde{g} \rVert}
= 2\,\bigl[1 - \mathrm{ZNCC}(\boldsymbol{p})\bigr].
$$

So minimizing $C$ maximizes ZNCC, the criterion from [Correlation
Criteria](./correlation_criteria.md). $C$ runs from 0, a perfect
match, to 4. Multiplying $C$ by the constant $\lVert \tilde{f} \rVert^2$
leaves its minimizer unchanged:

$$
\lVert \tilde{f} \rVert^2\, C(\boldsymbol{p})
= \sum_{\boldsymbol{\xi}} \bigl[\tilde{f}(\boldsymbol{\xi}) - \lambda\, \tilde{g}(\boldsymbol{\xi}; \boldsymbol{p})\bigr]^2,
\qquad
\lambda = \frac{\lVert \tilde{f} \rVert}{\lVert \tilde{g} \rVert}.
$$

**2. Put the increment on the reference kernel.** A forward, additive
Gauss-Newton step would perturb the current side,
$g(\boldsymbol{W}(\boldsymbol{\xi}; \boldsymbol{p} + \Delta\boldsymbol{p}))$.
Its linearization needs the gradient of $g$ at the warped positions.
Those positions move every iteration, so the 6x6 Hessian would need
rebuilding every iteration too. The inverse compositional form
perturbs $f$ instead. It seeks the incremental warp
$\boldsymbol{W}(\boldsymbol{\xi}; \Delta\boldsymbol{p})$ that makes the
reference kernel match the current one:

$$
\min_{\Delta\boldsymbol{p}}\; \sum_{\boldsymbol{\xi}}
\bigl[\tilde{f}(\boldsymbol{W}(\boldsymbol{\xi}; \Delta\boldsymbol{p}))
- \lambda\, \tilde{g}(\boldsymbol{\xi}; \boldsymbol{p})\bigr]^2 .
$$

If $f \circ \boldsymbol{W}(\Delta\boldsymbol{p})$ matches
$g \circ \boldsymbol{W}(\boldsymbol{p})$, then $f$ matches
$g \circ \boldsymbol{W}(\boldsymbol{p}) \circ \boldsymbol{W}(\Delta\boldsymbol{p})^{-1}$.
That gives the update,
$\boldsymbol{W}(\boldsymbol{p}) \leftarrow \boldsymbol{W}(\boldsymbol{p}) \circ \boldsymbol{W}(\Delta\boldsymbol{p})^{-1}$.
In the $3 \times 3$ matrix form above, composition is matrix
multiplication. At convergence, $\Delta\boldsymbol{p} = \boldsymbol{0}$,
and the two forms share the same minimum.

**3. Linearize about $\Delta\boldsymbol{p} = \boldsymbol{0}$.**
$\boldsymbol{W}(\boldsymbol{\xi}; \boldsymbol{0})$ is the identity, so
a first-order Taylor expansion gives

$$
f(\boldsymbol{W}(\boldsymbol{\xi}; \Delta\boldsymbol{p}))
\approx f(\boldsymbol{\xi})
+ \nabla f(\boldsymbol{\xi})\,
\frac{\partial \boldsymbol{W}}{\partial \boldsymbol{p}}\,
\Delta\boldsymbol{p},
\qquad
\frac{\partial \boldsymbol{W}}{\partial \boldsymbol{p}} =
\begin{bmatrix}
1 & \Delta x & \Delta y & 0 & 0 & 0 \\
0 & 0 & 0 & 1 & \Delta x & \Delta y
\end{bmatrix},
$$

with $\nabla f = (f_x, f_y)$, the reference image's gradient. The
product is one row of six numbers per pixel, its steepest-descent row:

$$
\boldsymbol{s}(\boldsymbol{\xi}) =
\bigl[\, f_x,\; f_x \Delta x,\; f_x \Delta y,\;
f_y,\; f_y \Delta x,\; f_y \Delta y \,\bigr].
$$

The expansion holds $\bar{f}$ and $\lVert \tilde{f} \rVert$ fixed. That
approximation vanishes as $\Delta\boldsymbol{p} \to \boldsymbol{0}$.

[Figure](#fig-steepest-descent) shows the six components of
$\boldsymbol{s}$ as images, for the reference kernel at $(150, 150)$.
[Rigid Versus Warped Kernel](#rigid-versus-warped-kernel) below tracks
that same kernel. The $u$ and $v$ images are the
image gradient itself. The other four multiply that gradient by
$\Delta x$ or $\Delta y$. So they vanish along the kernel's center
column or center row. A pixel 13 px from the center weighs 13 times
more than a pixel 1 px from it. The kernel's edges carry the
information about stretch and shear.

<!-- cmdrun python3 kernel_warping_steepest.py -->

<figure id="fig-steepest-descent">
    <img src="kernel_warping_steepest.png" alt="six square heat maps, 27 by 27 pixels each, in two rows of three, colored blue for negative and red for positive with white at zero. Top row: f_x, f_x times delta x, f_x times delta y. Bottom row: f_y, f_y times delta x, f_y times delta y. The f_x and f_y panels show speckle-scale structure everywhere. The four weighted panels fade to white along the center row or column and grow strongest toward the kernel edges" />
    <figcaption>The six steepest-descent images for the reference kernel at $(150, 150)$, one per component of $\boldsymbol{p} = (u, u_x, u_y, v, v_x, v_y)$. Each panel uses its own symmetric color scale. The Hessian $\boldsymbol{H}$ sums products of these six images, pixel by pixel.</figcaption>
</figure>

**4. Solve the normal equations.** Define the residual
$r(\boldsymbol{\xi}) = \lambda\, \tilde{g}(\boldsymbol{\xi}; \boldsymbol{p}) - \tilde{f}(\boldsymbol{\xi})$.
Substituting step 3 into step 2 leaves a linear least-squares problem,

$$
\min_{\Delta\boldsymbol{p}}\; \sum_{\boldsymbol{\xi}}
\bigl[\boldsymbol{s}(\boldsymbol{\xi})\, \Delta\boldsymbol{p} - r(\boldsymbol{\xi})\bigr]^2 .
$$

Setting its gradient with respect to $\Delta\boldsymbol{p}$ to zero
gives

$$
\boldsymbol{H}\, \Delta\boldsymbol{p} = \sum_{\boldsymbol{\xi}} \boldsymbol{s}(\boldsymbol{\xi})^{\top} r(\boldsymbol{\xi}),
\qquad
\boldsymbol{H} = \sum_{\boldsymbol{\xi}} \boldsymbol{s}(\boldsymbol{\xi})^{\top} \boldsymbol{s}(\boldsymbol{\xi}).
$$

$\boldsymbol{H}$ is $6 \times 6$. It depends only on $f$ and
$\boldsymbol{\xi}$, never on $\boldsymbol{p}$. So IC-GN builds and
inverts it once per point, before the first iteration. That is the
payoff of step 2.

**Iterating.** The first $\boldsymbol{p}$ comes from `locate`'s
whole-pixel answer: $u$ and $v$ take its displacement, and all four
gradient terms start at zero. Each iteration then does five things:

1. Sample $g$ at the 729 warped positions with cubic B-splines.
2. Form $\tilde{g}$, $\lambda$, and the residual $r$.
3. Solve for $\Delta\boldsymbol{p} = \boldsymbol{H}^{-1} \sum \boldsymbol{s}^{\top} r$.
4. Build $\boldsymbol{W}(\Delta\boldsymbol{p})$, invert that $3 \times 3$
   matrix, and compose it into $\boldsymbol{W}(\boldsymbol{p})$.
5. Stop once every component of $\Delta\boldsymbol{p}$ falls below
   $10^{-6}$, or after 50 iterations.

One example shows those iterations in action: the point at
$(150, 150)$, under a 7% stretch, a 0.05 shear, and a $(6.43, 4.92)$ px
shift. [Rigid Versus Warped Kernel](#rigid-versus-warped-kernel) below
explains how that example was chosen.
[`dictk.warp.fit`](../api/dictk/warp.html#fit) with `max_iterations`
set to $k$ returns the warp after $k$ iterations. Iteration 0 is
`locate`'s whole-pixel start. [Figure](#fig-ic-gn-residuals) shows the
residual after each iteration, and [Figure](#fig-ic-gn-convergence)
the error:

<!-- cmdrun python3 kernel_warping_iterations.py -->

<figure id="fig-ic-gn-residuals">
    <img src="kernel_warping_residuals.png" alt="four square heat maps of the residual r, 27 by 27 pixels each, on one shared blue-white-red color scale from about -130 to 130. At k = 0, with C = 0.18, strong red and blue speckles cover the kernel. At k = 1, 2, and 3, with C = 0.0022, 0.0012, and 0.0012, the maps are almost entirely white" />
    <figcaption>The residual $r = \lambda \tilde{g} - \tilde{f}$ after $k$ iterations, on one shared color scale, with each panel's ZNSSD $C$ in its title. At $k = 0$, the whole-pixel start, speckle structure fills the kernel. One iteration removes it.</figcaption>
</figure>

<figure id="fig-ic-gn-convergence">
    <img src="kernel_warping_convergence.png" alt="two line plots against iteration k from 0 to 9, both with logarithmic vertical axes. Left, translation error: 0.44 px at k = 0, 0.018 px at k = 1, then flat near 0.003 px from k = 2 on. Right, gradient error: 0.07 at k = 0, falling steadily to about 0.00012 by k = 6, then flat" />
    <figcaption>Error against iteration $k$. Left: the distance from the fitted translation to the true shift $(6.43, 4.92)$. Right: the largest difference between the fitted gradient terms and the true deformation, $1.07$ stretch and $0.05$ shear.</figcaption>
</figure>

One iteration cuts $C$ from 0.18 to 0.0022, and the translation error
from 0.44 px to 0.018 px. By $k = 2$, $C$ levels off at 0.0012, and the
translation error settles at about 0.003 px. The gradient terms take
until $k = 6$ to settle, at about $1.2 \times 10^{-4}$. IC-GN reaches
its exact final warp after 9 iterations, far below the 50-iteration
cap.

Neither error reaches zero. This example's current image comes from a
quintic spline, while IC-GN samples it with a cubic one. That mismatch
sets the 0.003 px floor. [Rigid Versus Warped
Kernel](#rigid-versus-warped-kernel) below finds the same 0.003 px as
`locate_warp`'s median error across 30 shifts.

### Rigid Versus Warped Kernel

`locate` and `locate_subpixel` never warp their kernel. Each cuts an
axis-aligned square from `reference_image`. Each slides that square,
unchanged, across the search area. The only thing either one finds is
a translation. In contrast, `locate_warp` finds how the kernel
translates and deforms.

One point, at $(150, 150)$, under an exaggerated deformation shows the
difference. The current image stretches 7% along $x$ and shears by
0.05. The 7% stretch is 3.5 times this page's 2%, large enough to see
the warp.

A shift then moves the point by a fractional number of pixels. A
whole-pixel shift would hand `locate` an exact answer by construction,
since `locate` only returns whole pixels. So the first table tracks
the point under 30 random fractional shifts, each between 4 and 8 px
along $x$ and between 2 and 6 px along $y$. [Figure](#fig-kernel-panels) uses the one
shift whose three errors sit closest to the three median errors in
that table. The second table tracks that shift. Then come the warp
matrices, $\boldsymbol{W}$, from `locate_subpixel` and `locate_warp`,
followed by the true one:

<!-- cmdrun python3 kernel_warping_panels.py -->

<figure id="fig-kernel-panels">
    <img src="kernel_warping_panels.png" alt="two zoomed panels of the same deformed speckle image around one point. In both, a dashed white square marks the reference kernel at (150, 150), an orange arrow points to the tracked position, and a red cross marks the true position at (156.43, 154.92). Left: an orange axis-aligned square with a 10x10 grid of orange dots, the same shape as the reference square, moved by the arrow. Right: an orange parallelogram, slightly wider than the square and leaning right toward the bottom, with its 10x10 grid of dots stretched and sheared to match" />
    <figcaption>Both panels show the deformed image around one point. The dashed white square marks the reference kernel at its original position. The orange arrow points to each function's tracked position, and the red cross marks the true one. Left: <code>locate</code> and <code>locate_subpixel</code> move the square without changing its shape (drawn at <code>locate_subpixel</code>'s position). Right: <code>locate_warp</code> also stretches and shears the kernel. Its outline and sample points use the warp IC-GN fitted, $\boldsymbol{W}_\text{locate\_warp}$.</figcaption>
</figure>

Across all 30 shifts, `locate` misses by a median 0.462 px, since it
rounds to a whole pixel. `locate_subpixel` misses by a median 0.105
px, because its rigid square no longer matches the stretched and
sheared content. `locate_warp` misses by a median 0.003 px, about 35
times smaller than `locate_subpixel`'s. Even `locate_warp`'s largest
miss over all 30 shifts, 0.006 px, is about 9 times smaller than
`locate_subpixel`'s smallest, 0.054 px.

$\boldsymbol{W}_\text{locate\_subpixel}$ keeps an identity block in
its upper left. A rigid kernel can only translate, so its four
gradient terms stay at zero. $\boldsymbol{W}_\text{locate\_warp}$ is
the warp IC-GN fitted.
[`dictk.warp.fit`](../api/dictk/warp.html#fit) returns it directly.
Its gradient block matches $\boldsymbol{W}_\text{true}$ to within
0.0001. Its translation matches to within 0.003 px.

Two things remove the bias. The spline samples the image itself at
fractional positions, so no correlation peak needs interpolating. The
affine warp also lets the kernel stretch along with the material,
instead of forcing a rigid match. The call mirrors `locate_subpixel`,
with the same grid and margins:

```python
from dictk.grid import locate_warp

found = locate_warp(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
)
```

The same fractional-position error curve, now for both trackers:

<!-- cmdrun python3 kernel_warping_bias.py -->

<figure>
    <img src="kernel_warping_bias.png" alt="mean x error against the fractional part of true x for two trackers. locate_subpixel, circles, swings from about -0.14 to +0.12 px. locate_warp, squares, stays within about 0.01 px of zero across the whole pixel" />
    <figcaption>Mean $x$ error per tenth of a pixel, for <code>locate_subpixel</code> (circles) and <code>locate_warp</code> (squares), across all 2862 points.</figcaption>
</figure>

The error standard deviation falls from 0.109 px to 0.008 px. The
table lists both run times. For all 2862 points they differ by less
than a second. A residual wave,
about 0.01 px tall, remains. [The Residual Wave](#the-residual-wave)
traces it to the test image.

## Strain at Full Density, Again

High Point Density's strain pipeline stays the same:
[`dictk.grid.elements`](../api/dictk/grid.html#elements) for
connectivity, then
[`gauss_point_log_strains`](../api/dictk/element.html#gauss_point_log_strains)
at each Gauss point. Only the tracked positions change:

<!-- cmdrun python3 kernel_warping_strain.py -->

The spread falls from 16531 to 1161 microstrain. The range now sits
where VIC-2D's does. Of the 11024 Gauss points, 97.4% land inside
VIC-2D's own colorbar range, up from 9.5%. The standard deviation,
1161 microstrain, comes in under VIC-2D's 1385. The element code is
unchanged from High Point Density, so the tracker accounts for the
whole drop from 16531 to 1161 microstrain.

<figure>
    <div style="display: flex; gap: 1em;">
        <a href="../verification/simple_stretch_result_vic.png" target="_blank" rel="noopener" style="flex: 1 1 0; min-width: 0;">
            <img src="../verification/simple_stretch_result_vic.png" alt="VIC-2D's measured exx field, colorbar 17560 to 22360 microstrain, a striped pattern in VIC-2D's own 16-band magenta-blue-cyan-green-yellow-orange-red color scale" style="width: 100%;" />
        </a>
        <a href="kernel_warping_strain_vic_colorbar.png" target="_blank" rel="noopener" style="flex: 1 1 0; min-width: 0;">
            <img src="kernel_warping_strain_vic_colorbar.png" alt="dictk's own E11 field from locate_warp, on the same 17560-22360 microstrain range and VIC-2D's 16-band colormap, showing the full range of colors in narrow vertical stripes, with almost no clipped solid magenta or solid red" style="width: 100%;" />
        </a>
    </div>
    <figcaption>VIC-2D's $e_{xx}$ (left) and <code>dictk</code>'s $E_{11}$ from <code>locate_warp</code> (right). Both use `17560`-`22360` microstrain and VIC-2D's own 16-band color scale. In High Point Density's version of the right panel, only 9.5% of the Gauss points fell inside this range. The rest clipped to solid magenta or solid red. This one uses the whole scale.</figcaption>
</figure>

<figure>
    <img src="kernel_warping_strain_histogram.png" alt="two overlaid normalized histograms of log strain in microstrain. dictk, gray filled, one broad peak from about 17000 to 23000 centered near 20000. VIC-2D, black outline, five separated clusters over the same 17300 to 23100 range. A dashed red line at 19803 microstrain" />
    <figcaption>Distribution of <code>dictk</code>'s $E_{11}$ from <code>locate_warp</code> (gray, 11024 Gauss points) and VIC-2D's $e_{xx}$ (black outline, 2682 points), each normalized to unit area. The dashed red line marks $\ln(1.02) \approx 19803$ microstrain.</figcaption>
</figure>

The two distributions now cover the same range. Their shapes still
differ. VIC-2D's splits into five clusters. `dictk`'s forms one broad
peak. Both fields keep vertical stripes. Both tools measured the
same bilinear images, and [The Residual Wave](#the-residual-wave)
below shows those images carry a distortion of their own, tied to each
point's fractional position. Each tracker responds to it differently.

Neither result is smoothed. Commercial codes usually also apply a
**strain window**, fitting displacement over a neighborhood of points
before differentiating. That trades spatial resolution for a smaller strain spread. A 15x15-point
window, spanning 75 px here, cut `locate_warp`'s spread from 1161 to
39 microstrain in an exploratory test. [Path Forward](./path_forward.md) records it as a next step.
Fixing the bias first matters. A window spanning a whole bias cycle
would also flatten High Point Density's stripes. That averaging would
hide the error while leaving it in the tracked positions.

## The Residual Wave

`locate_warp`'s leftover 0.01 px wave starts outside the tracker.
`dictk.image.stretch` builds the current image with bilinear
interpolation. Bilinear interpolation moves content by a fractional
pixel, and it also blurs that content. The blur depends on the
fraction. A whole-pixel position gets none, and a half-pixel position
gets the most. So the stretched image differs from a true
stretch, by an amount that follows each point's fractional position.
Any tracker reads that difference as a position-dependent error. The
table below measures how large.

A quintic spline has no fraction-dependent blur like bilinear
interpolation's. It builds a second version of the same 2% stretch.
Tracking both versions shows how much of each tracker's error came
from the image:

<!-- cmdrun python3 kernel_warping_generator.py -->

With the quintic-spline image, `locate_warp`'s $x$ error falls from 0.008 px
to 0.0015 px. Its strain spread falls from 1161 to 260 microstrain. Removing
the generator's distortion cuts IC-GN's $x$ error by a factor of 5. `locate_subpixel` improves
too, from 0.109 px to 0.057 px, but its strain spread stays above 10000
microstrain. About half of phase correlation's error came from the
generator. The other half belongs to the tracker.

Every other figure on this page keeps `image.stretch`. VIC-2D measured
those same bilinear images, so the comparison with VIC-2D stays fair.
`dictk`'s own tests of fractional translation avoid the generator
entirely. They shift a smoothed speckle image by an exact fraction of
a pixel, in the Fourier domain. There, `locate_warp` recovers every
tested shift to within 0.005 px, and beats `locate_subpixel` every
time.

Continue to [Strain Window](./strain_window.md).

### `kernel_warping_pixel_locking.py`

```python
<!-- cmdrun cat kernel_warping_pixel_locking.py -->
```

### `kernel_warping_panels.py`

```python
<!-- cmdrun cat kernel_warping_panels.py -->
```

### `kernel_warping_steepest.py`

```python
<!-- cmdrun cat kernel_warping_steepest.py -->
```

### `kernel_warping_iterations.py`

```python
<!-- cmdrun cat kernel_warping_iterations.py -->
```

### `kernel_warping_bias.py`

```python
<!-- cmdrun cat kernel_warping_bias.py -->
```

### `kernel_warping_strain.py`

```python
<!-- cmdrun cat kernel_warping_strain.py -->
```

### `kernel_warping_generator.py`

```python
<!-- cmdrun cat kernel_warping_generator.py -->
```
