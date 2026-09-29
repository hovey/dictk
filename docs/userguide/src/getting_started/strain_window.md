# Strain Window

[Kernel Warping](./kernel_warping.md) cut the $E_{11}$ standard
deviation of the 2862-point grid to 1161 microstrain. VIC-2D's own
measurement of the same stretch has a standard deviation of 1385
microstrain. That page also ran an exploratory test. A 15x15-point
least-squares window cut the 1161 to 39 microstrain.

This page derives that window. Each strain comes from a fit to a
neighborhood of tracked points. The fit averages the tracking error
over the neighborhood before it takes a derivative. The price is
spatial resolution. The derivation puts a number on both sides of that
trade.

## Local Displacement Model

The tracked points sit on a regular reference grid with spacing $h$.
Point $i$ has reference position $\mathbf{X}_i$ and tracked current
position $\mathbf{x}_i$. Its displacement is
$\mathbf{u}_i = \mathbf{x}_i - \mathbf{X}_i$.

A window holds $n \times n$ points, with $n = 2m + 1$. It centers on
point $c$. Its **extent** is $nh$. For $n = 15$ and $h = 5$ px, the
extent is 75 px. The distance between the two outermost points along
one axis is $(n - 1)h = 70$ px. Every "window spanning" figure in this
book uses the extent $nh$.

Point $k$ in the window has local coordinates

$$
\mathbf{s}_k = \mathbf{X}_k - \mathbf{X}_c = h\,(j_k,\; l_k),
\qquad j_k,\, l_k \in \{-m, \dots, m\}.
$$

Each displacement component $\alpha \in \{x, y\}$ gets an affine fit:

$$
u_\alpha(\mathbf{s}) \approx a_\alpha + H_{\alpha x}\, s_x + H_{\alpha y}\, s_y .
$$

The coefficients $H_{\alpha\beta}$ form the displacement gradient
$\mathbf{H} = \partial \mathbf{u} / \partial \mathbf{X}$ at the window
center. The fit uses reference coordinates, so $\mathbf{H}$ is the
Lagrangian gradient. The deformation gradient follows directly:

$$
\mathbf{F} = \mathbf{I} + \mathbf{H} .
$$

Fitting the current positions $x_\alpha$ instead gives $\mathbf{F}$ as
the slope. Both routes agree, because $\mathbf{X}$ is exactly affine in
$\mathbf{s}$.

## Least-Squares Estimator

Stack the $n^2$ window points. The design matrix
$\mathbf{A} \in \mathbb{R}^{n^2 \times 3}$ has one row
$(1,\; s_{x,k},\; s_{y,k})$ per point. The vector $\mathbf{u}_\alpha$
holds component $\alpha$ of the $n^2$ displacements. The weights
$w_k$ fill the diagonal matrix $\mathbf{W}$. The fit minimizes

$$
\sum_{k} w_k \left( u_{\alpha,k} - \mathbf{A}_k\, \boldsymbol{\theta}_\alpha \right)^2,
\qquad
\boldsymbol{\theta}_\alpha =
\begin{pmatrix} a_\alpha \\ H_{\alpha x} \\ H_{\alpha y} \end{pmatrix}.
$$

The normal equations give the solution:

$$
\boldsymbol{\theta}_\alpha =
\left( \mathbf{A}^\top \mathbf{W} \mathbf{A} \right)^{-1}
\mathbf{A}^\top \mathbf{W}\, \mathbf{u}_\alpha .
$$

The grid is regular, so the matrix
$\left( \mathbf{A}^\top \mathbf{W} \mathbf{A} \right)^{-1} \mathbf{A}^\top \mathbf{W}$
depends only on $n$, $h$, and $\mathbf{W}$. It does not depend on the
images.

### Uniform Weights

This page sets $w_k = 1$ for every point. Uniform weights give a
closed-form answer and the lowest variance for independent errors. A
tent or Gaussian weight would reduce the influence of the boundary
points of each window. Both are candidate refinements for a later
stage. Neither appears here.

A full window is symmetric about its center. So
$\sum_k s_{x,k} = \sum_k s_{y,k} = \sum_k s_{x,k} s_{y,k} = 0$, and
$\mathbf{A}^\top \mathbf{A}$ becomes diagonal. Each gradient component
reduces to one sum:

$$
H_{\alpha x} =
\frac{\sum_k s_{x,k}\, u_{\alpha,k}}{\sum_k s_{x,k}^2},
\qquad
\sum_k s_{x,k}^2 = h^2\, n\, \frac{m(m+1)(2m+1)}{3}
= \frac{h^2 n^2\, m(m+1)}{3}.
$$

The $y$ component follows by symmetry. This estimator is a derivative
kernel along one axis and a box average along the other.

## Strain

The strain measures reuse $\mathbf{F}$ from the previous section.
Green-Lagrange strain is

$$
\mathbf{E} = \tfrac{1}{2} \left( \mathbf{F}^\top \mathbf{F} - \mathbf{I} \right).
$$

Log strain, also called Hencky strain, is

$$
\mathbf{E}_{\log} = \ln \mathbf{U},
\qquad
\mathbf{U} = \sqrt{\mathbf{F}^\top \mathbf{F}} .
$$

This page reports log strain, to match the figures on the pages before
it.

Each window yields one strain tensor, at the window center. A Q4
element from [Finite Element Method](./finite_element_method.md)
yields four, one per Gauss point.

A Q4 element is the zero-redundancy case of this model. It fits 4
nodal displacements with 4 bilinear coefficients. It interpolates and
averages nothing. A window fits $n^2$ displacements with 3
coefficients. For $n = 15$, that is 225 displacements per 3
coefficients. The redundancy does the averaging.

## Noise Gain

Suppose the tracked displacements carry independent errors with
variance $\sigma^2$. The estimator's variance follows from the
diagonal $\mathbf{A}^\top \mathbf{A}$:

$$
\operatorname{Var}(H_{\alpha x}) =
\frac{\sigma^2}{\sum_k s_{x,k}^2} =
\frac{3\,\sigma^2}{h^2 n^2\, m(m+1)}.
$$

The standard deviation is

$$
\operatorname{std}(H_{\alpha x}) =
\frac{\sigma}{h} \cdot \frac{1}{n} \sqrt{\frac{3}{m(m+1)}}
\;\approx\; \frac{\sqrt{12}\,\sigma}{h\, n^2}.
$$

The baseline is a Q4 element with side $h$, evaluated at a Gauss point
($\eta = \pm 1/\sqrt{3}$). Its gradient is
$\tfrac{1}{h}\left[a(u_2 - u_1) + b(u_3 - u_4)\right]$
with $a + b = 1$ and $a^2 + b^2 = \tfrac{2}{3}$. So its standard
deviation is $\sqrt{4/3}\,\sigma/h = 1.155\,\sigma/h$.

| Window points $n$ | Window std, in units of $\sigma/h$ | Reduction vs Q4 |
|---|---|---|
| 3 | 0.408 | 2.8x |
| 5 | 0.141 | 8.2x |
| 7 | 0.0714 | 16x |
| 9 | 0.0430 | 27x |
| 11 | 0.0287 | 40x |
| 15 | 0.0154 | 75x |

Independent errors would cut Kernel Warping's 1161 microstrain to
about 16 at $n = 15$. The exploratory test measured 39. The gap has
one likely cause. The tracking error is a spatially correlated wave,
and a window averages a wave less completely than it averages
independent noise. The next section quantifies how much of the wave
survives.

## Bias and Resolution

A window reduces variance and adds bias. Two results size the bias.

**Cubic term.** Let the true field be $u = \tfrac{c}{6}\, s^3$, with
$c = \partial^3 u / \partial X^3$. The true gradient at the center is
0. The fitted slope is

$$
H_{\text{fit}} =
\frac{c}{6}\, \frac{\sum s^4}{\sum s^2} =
\frac{c\, h^2\, (3m^2 + 3m - 1)}{30}.
$$

The standard deviation from the previous section falls as $n^{-2}$.
This bias grows as $n^2$. The mean squared error, variance plus
squared bias, therefore has a minimum. Its window size depends on the
field's third derivative and on $\sigma$.

A quadratic fit gives the same center slope as the affine fit. A
quadratic term is even about the center, and the slope is odd. In a
symmetric window, the two are orthogonal. Only a cubic fit removes
the bias above, and it raises the variance.

**Frequency response.** Take $u = A \sin(kX)$ and a window half-width
$a = mh$. In the continuum limit, the ratio of the fitted slope to
the true slope at the window center is

$$
T(k) = \frac{3\left( \sin(ka) - ka \cos(ka) \right)}{(ka)^3}
\;\approx\; 1 - \frac{(ka)^2}{10}
\quad \text{for } ka \ll 1.
$$

The small-$ka$ limit matches the cubic bias above.

[Kernel Warping](./kernel_warping.md) found a bias wave in
`locate_subpixel` with a 51 px period. Its wavenumber is
$k = 2\pi / 51$. For $n = 15$ and $h = 5$ px, the discrete sum
gives $T = -0.017$. The window keeps 1.7% of that wave's slope, and
reverses its sign. The window's 75 px extent spans 1.5 periods of that
wave. A fractional number of periods leaves a residue in the fit, and
$T$ sizes that residue.

## Window Edges

Near the grid boundary, the window truncates. Every tracked point
keeps a strain. The affine fit uses the general normal equations,
because $\mathbf{A}^\top \mathbf{A}$ is no longer diagonal.

Truncation costs precision in two ways. Take the $x$ gradient of a
window that lost its $-x$ half, with $m + 1$ columns left.

**Variance.** The slope variance is $\sigma^2$ divided by
$\sum_k (s_{x,k} - \bar{s}_x)^2$. That sum falls from
$h^2 n\, m(m+1)(2m+1)/3$ to $h^2 n\, m(m+1)(m+2)/12$. The standard
deviation rises by the factor

$$
\sqrt{\frac{4(2m + 1)}{m + 2}} .
$$

At $m = 7$, the factor is 2.58. At a corner, the window loses half its
rows too. The factor becomes

$$
\sqrt{\frac{4(2m + 1)^2}{(m + 1)(m + 2)}},
$$

which is 3.54 at $m = 7$.

In units of $\sigma/h$, the standard deviation is 0.0154 in the
interior, 0.0398 on an edge, and 0.0545 at a corner. The Q4 element
gives 1.155. The edge value is 29 times lower than that. The corner
value is 21 times lower.

**Location.** For a field that is quadratic, $u = \tfrac{\kappa}{2}\, s^2$,
an affine fit returns the true gradient at the window's centroid, not
at its center. This holds for any point set symmetric about its own
centroid, and a truncated window is one. Its centroid sits $mh/2$
from the window's center. At $m = 7$ and
$h = 5$ px, that shift is 17.5 px. The strain error at an edge point is
$\kappa \cdot mh/2$, with $\kappa = \partial^2 u / \partial X^2$.

Uniform stretch has $\kappa = 0$, so this bias vanishes there. A field
with curvature near an edge does show it.

## Overlapping Windows

A window can step by 1 point, so every tracked point gets a strain. Or
it can step by $n$ points, so no two windows share a point.

At a step of 1, neighboring windows share $n^2 - n$ of their $n^2$
points. For $n = 15$, that is 210 of 225. Their errors correlate. The
standard deviation across the field then describes the spread of the
strain field. It does not describe the uncertainty of independent
measurements. Every spread quoted on this page will name its step.

Continue to [Discontinuities](./discontinuities.md).
