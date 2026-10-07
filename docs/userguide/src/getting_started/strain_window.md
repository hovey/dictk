# Strain Window

[Kernel Warping](./kernel_warping.md) cut the $E_{11}$ standard
deviation of the 2862-point grid to 1161 microstrain. VIC-2D's own
measurement of the same stretch has a standard deviation of 1385
microstrain. That page also ran an exploratory test. A 15x15-point
least-squares window cut the 1161 to 39 microstrain.

This page derives that window.

1. Every tracked point has a tracking error.
2. A strain needs a derivative, and a derivative amplifies those errors.
3. A window fits one straight line to many points. The line averages their errors, so the strain error drops.
4. The line assumes the strain is uniform across the whole window.
   * With 15x15 points at 5 px spacing, the window covers 75 px. If the real strain changes inside those 75 px, the fit blurs that change into one number.
   * A larger window averages more errors and blurs more of the real field. A smaller window does the reverse.

The derivation climbs in three steps. A row of 3 points shows the
idea with 3 numbers. A 3x3 window adds the second axis. A general
window with $n = 2m + 1$ points per side repeats the 3x3 steps with 1
replaced by $m$.

## Notation

| Symbol | Meaning |
|---|---|
| $h$ | grid spacing, in px |
| $m$ | window half-width, in points: the window reaches $m$ points out from its center along each axis |
| $n = 2m + 1$ | points per window side |
| $q,\ p$ | column and row of a point within the window, each from $-m$ to $m$ |
| $qh,\ ph$ | the point's $x$ and $y$ position relative to the window center, in px |
| $u,\ v$ | tracked $X$ and $Y$ displacement, in px |
| $u_{q,p}$ | $u$ at column $q$ and row $p$ |
| $u_c$ | fitted $u$ at the window center |
| $\partial u / \partial X,\ \partial u / \partial Y$ | fitted gradient of $u$ at the window center |
| $\boldsymbol{\nabla}_0\,\boldsymbol{u}$ | the $2 \times 2$ displacement gradient, as in [Finite Element Method](./finite_element_method.md#displacement-gradient) |
| $\sigma$ | standard deviation of each point's tracking error, in px |

In an image,

* $x$ runs across the page from left to right. The
displacement $u$ points in the $x$ direction. Column $q$ grows from
left to right.
* $y$ runs down the page from top to bottom. The
displacement $v$ points in the $y$ direction. Row $p$ grows from top to
bottom.

The steps below illustrate a fit for $u$. The fit for $v$ is an analogous process.

## 1D Example

Consider three points on the $x$ axis centered locally at the middle point, with relative $x$ coordinates $[-h, 0, h]$ pixels.
Each of these points has tracked displacements $[u_{-1}, u_0, u_1]$. 
Let $q$ be the index of the points $[-1, 0, 1]$.

Fit a straight line through the displacements. Point $q$ sits at
$x = qh$ pixels relative to the middle point, so the line predicts

$$
u_q \approx u_c + \frac{\partial u}{\partial X}\, q h .
$$

The slope of the line is $\partial u / \partial X$. The intercept of
the line is $u_c$, the fitted displacement at the middle point, where
$q = 0$.

That is two unknowns, $u_c$ and $\partial u / \partial X$, for three
points. Least squares picks the two unknowns that minimize the sum of
the three squared residuals:

$$
\begin{aligned}
R &= \sum_{q=-1}^{1} \left( u_q - u_c - \frac{\partial u}{\partial X}\, q h \right)^2 \\
&= \left( u_{-1} - u_c + \frac{\partial u}{\partial X}\, h \right)^2
+ \left( u_0 - u_c \right)^2
+ \left( u_1 - u_c - \frac{\partial u}{\partial X}\, h \right)^2 .
\end{aligned}
$$

At the minimum, the derivative of $R$ with respect to each unknown is
zero. The derivative with respect to $u_c$ is

$$
\frac{\partial R}{\partial u_c}
= -2 \sum_{q} \left( u_q - u_c - \frac{\partial u}{\partial X}\, q h \right) = 0 .
$$

Rearranged, that gives the first normal equation:

$$
u_c \sum_q 1 + \frac{\partial u}{\partial X}\, h \sum_q q = \sum_q u_q .
$$

The derivative with respect to the slope $\partial u / \partial X$ is

$$
\frac{\partial R}{\partial (\partial u / \partial X)}
= -2 \sum_{q} q h \left( u_q - u_c - \frac{\partial u}{\partial X}\, q h \right) = 0 .
$$

Dividing by $-2$ and rearranging gives the second normal equation:

$$
u_c\, h \sum_q q + \frac{\partial u}{\partial X}\, h^2 \sum_q q^2 = h \sum_q q\, u_q .
$$

In matrix form, the two normal equations are

$$
\begin{bmatrix} \sum_q 1 & h \sum_q q \\ h \sum_q q & h^2 \sum_q q^2 \end{bmatrix}
\begin{Bmatrix} u_c \\ \partial u / \partial X \end{Bmatrix}
=
\begin{Bmatrix} \sum_q u_q \\ h \sum_q q\, u_q \end{Bmatrix}.
$$

The sums are $\sum_q 1 = 3$, $\sum_q q = -1 + 0 + 1 = 0$, and
$\sum_q q^2 = 1 + 0 + 1 = 2$. So the matrix is

$$
\begin{bmatrix} 3 & 0 \\ 0 & 2h^2 \end{bmatrix}.
$$

The zero off the diagonal decouples the two unknowns:

$$
u_c = \frac{u_{-1} + u_0 + u_1}{3},
\qquad
\frac{\partial u}{\partial X} = \frac{h\,(-u_{-1} + u_1)}{2h^2}
= \frac{u_1 - u_{-1}}{2h}.
$$

The slope is the central difference. The middle point gets zero
weight in it.

### Noise

How much does tracking error move the slope? Work it out in six steps.

**Step 1: model the error.** Each tracked displacement is the true
displacement plus an error:

$$
u_q = u_q^{\text{true}} + e_q .
$$

The three errors $e_{-1}$, $e_0$, and $e_1$ are independent. Each has
mean 0 and standard deviation $\sigma$, so each has variance
$\sigma^2$.

**Step 2: find the error in the slope.** Substitute step 1 into the
slope:

$$
\frac{\partial u}{\partial X}
= \frac{u_1 - u_{-1}}{2h}
= \underbrace{\frac{u_1^{\text{true}} - u_{-1}^{\text{true}}}{2h}}_{\text{true slope}}
+ \underbrace{\frac{e_1 - e_{-1}}{2h}}_{\text{slope error}} .
$$

The true part has no randomness. So the slope's variance is the
variance of the slope error alone. The middle point's error $e_0$
does not appear, because the middle point has zero weight.

**Step 3: recall two variance rules.** For a constant $c$ and
independent errors $e_a$ and $e_b$:

$$
\operatorname{Var}(c\, e_a) = c^2 \operatorname{Var}(e_a),
\qquad
\operatorname{Var}(e_a \pm e_b) = \operatorname{Var}(e_a) + \operatorname{Var}(e_b).
$$

Variances add for a difference too, because the sign flips with $c = -1$
and $c^2 = 1$.

**Step 4: apply the first rule to each term.** The slope error has
two terms, $e_1 / 2h$ and $-e_{-1} / 2h$. Each one is an error scaled by
$c = \pm 1/(2h)$:

$$
\operatorname{Var}\!\left(\frac{e_1}{2h}\right)
= \operatorname{Var}\!\left(\frac{-e_{-1}}{2h}\right)
= \frac{\sigma^2}{4h^2} .
$$

**Step 5: apply the second rule to add them.**

$$
\operatorname{Var}\!\left(\frac{\partial u}{\partial X}\right)
= \frac{\sigma^2}{4h^2} + \frac{\sigma^2}{4h^2}
= \frac{\sigma^2}{2h^2} .
$$

**Step 6: take the square root.** The standard deviation is

$$
\operatorname{std}\!\left(\frac{\partial u}{\partial X}\right)
= \frac{\sigma}{\sqrt{2}\, h}
= 0.707\, \frac{\sigma}{h} .
$$

For example, take $\sigma = 0.01$ px and $h = 5$ px. The slope's
standard deviation is $0.707 \times 0.01 / 5 = 0.00141$, or 1414
microstrain.

The slope uses only 2 of the 3 points. The 3x3 window below averages
three such rows.

## 2D Example

The smallest square window with a center point holds 3x3 = 9 points.
It is the general window with $m = 1$.

### Setup

The points sit on a grid with spacing $h$. Point $(q, p)$ sits
at $x = qh$ and $y = ph$ pixels relative to the center point $(0, 0)$.
The window fits a plane through the 9 tracked displacements:

$$
u_{q,p} \approx u_c + \frac{\partial u}{\partial X}\, q h + \frac{\partial u}{\partial Y}\, p h .
$$

That is three unknowns, $u_c$, $\partial u / \partial X$, and
$\partial u / \partial Y$, for nine points.

### Normal Equations

Least squares minimizes the sum of the nine squared residuals:

$$
R = \sum_{q=-1}^{1} \sum_{p=-1}^{1}
\left( u_{q,p} - u_c - \frac{\partial u}{\partial X}\, q h - \frac{\partial u}{\partial Y}\, p h \right)^2 .
$$

As in the [1D Example](#1d-example), each derivative of $R$ is zero
at the minimum. Write $r_{q,p}$ for the residual inside the
parentheses. The three derivatives are

$$
\begin{aligned}
\frac{\partial R}{\partial u_c} &= -2 \sum_{q,p} r_{q,p} = 0, \\[1em]
\frac{\partial R}{\partial (\partial u / \partial X)} &= -2 \sum_{q,p} q h\, r_{q,p} = 0, \\[1em]
\frac{\partial R}{\partial (\partial u / \partial Y)} &= -2 \sum_{q,p} p h\, r_{q,p} = 0 .
\end{aligned}
$$

Dividing each by $-2$ and rearranging gives three normal equations. In
matrix form, they are

$$
\begin{bmatrix}
\sum 1 & h \sum q & h \sum p \\
h \sum q & h^2 \sum q^2 & h^2 \sum q p \\
h \sum p & h^2 \sum q p & h^2 \sum p^2
\end{bmatrix}
\begin{Bmatrix} u_c \\ \partial u / \partial X \\ \partial u / \partial Y \end{Bmatrix}
=
\begin{Bmatrix} \sum u_{q,p} \\ h \sum q\, u_{q,p} \\ h \sum p\, u_{q,p} \end{Bmatrix}.
$$

Each sum runs over the 9 points:

- $\sum 1 = 9$.
- $\sum q = 0$. Three points sit at each of $q = -1$, $0$, and $1$, so
  they cancel. $\sum p = 0$ for the same reason.
- $\sum q p = 0$. Flipping $q$ to $-q$ flips the product's sign, so
  the points cancel in pairs.
- $\sum q^2 = 3 + 0 + 3 = 6$. $\sum p^2 = 6$ for the same reason.

So the matrix is

$$
\begin{bmatrix} 9 & 0 & 0 \\ 0 & 6h^2 & 0 \\ 0 & 0 & 6h^2 \end{bmatrix}.
$$

The matrix is diagonal, so each unknown solves on its own.

### Solution

Each unknown divides one right-side entry by one diagonal entry:

$$
\begin{aligned}
u_c &= \frac{1}{9} \sum_{q,p} u_{q,p}, \\[1em]
\frac{\partial u}{\partial X} &= \frac{h \sum q\, u_{q,p}}{6h^2}
= \frac{1}{6h}\sum_{q,p} q\, u_{q,p}, \\[1em]
\frac{\partial u}{\partial Y} &= \frac{h \sum p\, u_{q,p}}{6h^2}
= \frac{1}{6h}\sum_{q,p} p\, u_{q,p}.
\end{aligned}
$$

[Figure](#fig-sw-3x3-layout) draws the weights. In
$\partial u / \partial X$, the right column enters with $+1$, the left
column with $-1$, and the middle column with 0. Group the sum by row.
Each row contributes $u_{1,p} - u_{-1,p}$, so

$$
\frac{\partial u}{\partial X}
= \frac{1}{3} \sum_{p=-1}^{1} \frac{u_{1,p} - u_{-1,p}}{2h}.
$$

That is the mean of three central differences, one per row. The window
differentiates along $X$ and averages along $Y$.

<figure id="fig-sw-3x3-layout">
    <img src="strain_window_3x3_layout.png" alt="three square panels, each a 3 by 3 grid of dots with column q and row p from -1 to 1. The left panel shows 9 orange dots labeled with their (q, p) index, with a ring around the center (0, 0). The middle panel shows the weights for du/dX: -1 in red for the left column, 0 in gray for the middle column, +1 in blue for the right column. The right panel shows the weights for du/dY: -1 in red for the top row, 0 in gray for the middle row, +1 in blue for the bottom row" />
    <figcaption>The 3x3 window. Left: the 9 points, indexed by column $q$ and row $p$. Middle: the weight of each point in $\partial u / \partial X$, in units of $1/(6h)$. Right: the weight of each point in $\partial u / \partial Y$, in the same units.</figcaption>
</figure>

### One Noisy Draw

The grid spacing is $h = 5$ px. The true field is $u_c = 0.3$ px, $\partial u / \partial X = 0.02$,
and $\partial u / \partial Y = 0.01$. Each tracked displacement gets
an independent Gaussian error with $\sigma = 0.01$ px. That $\sigma$
is illustrative. It is not measured from a tracker. A tracker's
errors also correlate between neighboring points, as
[Noise in a General Window](#noise-in-a-general-window) shows.

The script draws 10,000 sets of 9 errors with random seed 0. The table
shows the draw whose $\partial u / \partial X$ error sits closest to
the median error of the 10,000.

<!-- cmdrun python3 strain_window_3x3.py -->

[Figure](#fig-sw-3x3-fit) plots that draw on the left. The right
panel is the histogram of $\partial u / \partial X$ over all 10,000
draws.

<figure id="fig-sw-3x3-fit">
    <img src="strain_window_3x3_fit.png" alt="two panels. Left: nine tracked x displacements in pixels against x = qh from -5 to 5 px, colored by row, with a solid black fitted line of slope 0.01944 and a dashed red true line of slope 0.02. Right: a histogram of the fitted du/dX over 10000 draws, centered on the true value of 20000 microstrain, with a blue band of plus or minus 819 microstrain for the 3x3 window and a wider pale red band of plus or minus 2309 microstrain for a Q4 element" />
    <figcaption>Left: the draw from the table. Each point shows $u$ minus the fitted $(\partial u / \partial Y)\, ph$, which removes the row offset. The solid black line is the fit, and the dashed red line is the truth. Right: fitted $\partial u / \partial X$ over 10,000 draws, in microstrain. The blue band is $\pm 1$ standard deviation of the 3x3 window. The pale red band is $\pm 1$ standard deviation of a Q4 element, from the formula in <a href="#q4-baseline">Q4 Baseline</a>.</figcaption>
</figure>

### Noise in the 3x3 Window

The solution writes $\partial u / \partial X$ as a weighted sum
$\sum w_{q,p}\, u_{q,p}$ with $w_{q,p} = q / 6h$. Independent errors
give

$$
\operatorname{Var}\!\left(\frac{\partial u}{\partial X}\right)
= \sigma^2 \sum_{q,p} w_{q,p}^2
= \sigma^2\, \frac{6}{(6h)^2}
= \frac{\sigma^2}{6h^2}.
$$

The standard deviation is $\sigma / (\sqrt{6}\, h) = 0.408\,\sigma / h$.
The row of three points gave $0.707\,\sigma / h$. Averaging three
independent rows divides that by $\sqrt{3}$, and
$0.707 / \sqrt{3} = 0.408$. For $\sigma = 0.01$ px and $h = 5$ px, the
formula gives 816 microstrain. The 10,000 draws give 819.

### Q4 Baseline

[Finite Element Method](./finite_element_method.md) computes strain
from Q4 elements. Take a square Q4 element with side $h$. Its nodes 1
to 4 sit at $(\xi, \eta) = (-1, -1)$, $(1, -1)$, $(1, 1)$, and
$(-1, 1)$. At a Gauss point, its
gradient is

$$
\frac{\partial u}{\partial X}
= \frac{1}{h}\left[ g_1 (u_2 - u_1) + g_2 (u_3 - u_4) \right],
\qquad
g_{1,2} = \frac{1 \mp 1/\sqrt{3}}{2}.
$$

So $g_1 + g_2 = 1$ and $g_1^2 + g_2^2 = 2/3$. Each node enters once,
with weight $\pm g_1 / h$ or $\pm g_2 / h$. The variance is
$2 (g_1^2 + g_2^2)\, \sigma^2 / h^2 = \tfrac{4}{3}\, \sigma^2 / h^2$,
and the standard deviation is $1.155\,\sigma / h$. For
$\sigma = 0.01$ px and $h = 5$ px, that is 2309 microstrain, 2.8 times
the 3x3 window's 816.

## General Window

A general window holds $n \times n$ points, with $n = 2m + 1$. The
steps match the 3x3 window's. Each one ends by setting $m = 1$, which
recovers the 3x3 result.

### Setup

Columns $q$ and rows $p$ each run from $-m$ to $m$. The fit is the
same plane:

$$
u_{q,p} \approx u_c + \frac{\partial u}{\partial X}\, q h + \frac{\partial u}{\partial Y}\, p h .
$$

That is three unknowns for $n^2$ points. For $n = 15$ and $h = 5$ px,
the window holds 225 points. Its **extent** is $nh = 75$ px, because
each point stands for a cell $h$ wide. The two outermost points sit
$(n - 1)h = 70$ px apart. Every "window spanning" figure in this book
uses the extent $nh$.

### Normal Equations

The residual sum $R$, its derivatives, and the matrix form match the
3x3 window's. Only the limits change: every sum now runs from $-m$ to
$m$. One sum appears repeatedly. Call it $S_m$:

$$
S_m = \sum_{q=-m}^{m} q^2 = \frac{m(m+1)(2m+1)}{3}.
$$

The window's sums follow from it:

- $\sum 1 = n^2$.
- $\sum q = \sum p = \sum q p = 0$, by the same cancellations as the
  3x3 window.
- $\sum q^2 = n\, S_m$, because each of the $n$ rows contributes
  $S_m$. $\sum p^2$ is the same.

So the matrix is

$$
\begin{bmatrix} n^2 & 0 & 0 \\ 0 & h^2 n S_m & 0 \\ 0 & 0 & h^2 n S_m \end{bmatrix}.
$$

At $m = 1$: $n = 3$ and $S_1 = 2$, so the diagonal is
$(9,\; 6h^2,\; 6h^2)$.

### Solution

$$
u_c = \frac{1}{n^2} \sum_{q,p} u_{q,p},
\qquad
\frac{\partial u}{\partial X} = \frac{h \sum q\, u_{q,p}}{h^2 n S_m}
= \sum_{q,p} w_{q,p}\, u_{q,p},
\qquad
w_{q,p} = \frac{q}{h\, n\, S_m}.
$$

$\partial u / \partial Y$ uses $p$ in place of $q$. At $m = 1$, the
weight is $q / (6h)$.

The weight grows linearly with $q$. The outermost columns, at
$q = \pm m$, carry the largest weights. A displacement $mh$ from the
center changes by $mh$ times any change in slope, so it constrains the
slope $m$ times as tightly as a point at $q = \pm 1$. The weight does not depend on $p$.
So the estimator fits one line per row and averages the $n$ row
slopes. [Figure](#fig-sw-stencils) shows the weights for $m = 1$, 2,
and 3. The script also solves the normal equations directly and
compares:

<!-- cmdrun python3 strain_window_stencils.py -->

<figure id="fig-sw-stencils">
    <img src="strain_window_stencils.png" alt="three square heat maps of du/dX weights for windows of 3 by 3, 5 by 5, and 7 by 7 points. Each cell shows its column index q, from red negative values on the left through white zero in the middle column to blue positive values on the right. Every row is identical. The panel titles give the weights as q over 6h, q over 50h, and q over 196h" />
    <figcaption>The weight of each point in $\partial u / \partial X$ for $m = 1$, 2, and 3. Each cell shows $q$. The title gives the weight, $q / (h\, n\, S_m)$. The square marks the window center.</figcaption>
</figure>

The weights depend only on $m$ and $h$. They do not depend on the
images. So one set of weights serves every interior window, and for
both $u$ and $v$.

### Noise in a General Window

Independent errors give

$$
\operatorname{Var}\!\left(\frac{\partial u}{\partial X}\right)
= \sigma^2 \sum_{q,p} w_{q,p}^2
= \sigma^2\, \frac{n\, S_m}{(h\, n\, S_m)^2}
= \frac{\sigma^2}{h^2\, n\, S_m}
= \frac{3\,\sigma^2}{h^2 n^2\, m(m+1)}.
$$

The standard deviation is

$$
\operatorname{std}\!\left(\frac{\partial u}{\partial X}\right)
= \frac{\sigma}{h} \cdot \frac{1}{n} \sqrt{\frac{3}{m(m+1)}}
\;\approx\; \frac{\sqrt{12}\,\sigma}{h\, n^2}
\quad \text{for large } m.
$$

At $m = 1$, it is $\sigma / (\sqrt{6}\, h)$. The standard deviation
falls as $n^{-2}$. Each row's line fit contributes $n^{-3/2}$. A row
has $n$ points, and its outer points sit $mh$ from the center, so
$S_m$ grows as $m^3$. Averaging the $n$ rows contributes the remaining
$n^{-1/2}$.

The table compares the formula with 4000 random draws per window and
with the Q4 element's $1.155\,\sigma / h$. [Figure](#fig-sw-noise)
plots the same comparison for $n$ from 3 to 21:

<!-- cmdrun python3 strain_window_noise.py -->

<figure id="fig-sw-noise">
    <img src="strain_window_noise.png" alt="log-scale plot of the standard deviation of du/dX, in units of sigma over h, against window points per side n from 3 to 21. A black formula curve falls from 0.41 at n = 3 to 0.008 at n = 21. Blue Monte Carlo dots sit on the curve. A dashed red horizontal line marks the Q4 element at 1.155" />
    <figcaption>Standard deviation of $\partial u / \partial X$ for independent errors, in units of $\sigma / h$, against $n$. The black curve is the formula. The blue dots are 4000 random draws per window. The dashed red line is a Q4 element.</figcaption>
</figure>

If the tracking errors were independent, the 75x reduction at
$n = 15$ would cut Kernel Warping's 1161 microstrain to 15.5. The
exploratory test measured 39, 2.5 times more. The tracking error is
not independent. [Kernel Warping](./kernel_warping.md) found a wave
with a 51 px period. Points 5 px apart sit 35° apart on that wave's
cycle, so their errors correlate at $\cos 35° = 0.82$.
[Frequency Response](#frequency-response) computes the fraction of a
wave's slope that a window passes.

## From Gradient to Strain

Fitting $u$ and $v$ gives the four components of the displacement
gradient at the window center:

$$
\boldsymbol{\nabla}_0\,\boldsymbol{u} =
\begin{bmatrix}
\partial u / \partial X & \partial u / \partial Y \\
\partial v / \partial X & \partial v / \partial Y
\end{bmatrix}.
$$

The fit uses reference positions $qh$ and $ph$, so this is the
Lagrangian gradient. The rest follows
[Continuum Mechanics](./continuum_mechanics.md):

$$
\boldsymbol{F} = \boldsymbol{I} + \boldsymbol{\nabla}_0\,\boldsymbol{u},
\qquad
\boldsymbol{U} = \sqrt{\boldsymbol{F}^\top \boldsymbol{F}},
\qquad
\boldsymbol{E}^{(0)} = \ln \boldsymbol{U}.
$$

This page reports the log strain $\boldsymbol{E}^{(0)}$, to match the
figures on the pages before it. The fit is linear in the
displacements. The strain is not, because $\boldsymbol{U}$ and
$\ln$ are nonlinear. So the noise formulas above hold exactly for
$\boldsymbol{\nabla}_0\,\boldsymbol{u}$. They hold for strain to first
order, which covers the 2% stretch on these pages.

Fitting the current positions $\boldsymbol{x}$ instead of $u$ and $v$
gives $\boldsymbol{F}$ directly as the slope. Both routes agree,
because the reference positions $qh$ and $ph$ are exactly linear in
$q$ and $p$.

Each window yields one strain tensor, at its center. A Q4 element
yields four, one per Gauss point. A Q4 element also has no
redundancy. Its 4 nodal displacements fix its 4 bilinear coefficients
exactly, so it averages nothing. A 15x15 window fits 225 displacements
with 3 coefficients. That redundancy does the averaging.

### Uniform Weights

Every point here gets the same weight in the sum of squared residuals.
For independent errors with equal variance, uniform weights give the
lowest variance of any linear unbiased estimator. A tent or Gaussian
weight would reduce the influence of each window's outer points. Both
are candidate refinements for a later stage. Neither appears here.

## Bias and Resolution

A window reduces variance and adds bias. Two results size the bias.

**Cubic term.** Let the true field be
$u_{q,p} = \tfrac{1}{6}\, u'''\, (qh)^3$, with
$u''' = \partial^3 u / \partial X^3$. The true gradient at the center
is 0. The fitted slope is

$$
\frac{\partial u}{\partial X}\bigg|_{\text{fit}}
= \frac{h \sum q\, u_{q,p}}{h^2 \sum q^2}
= \frac{u'''}{6}\, h^2\, \frac{\sum q^4}{\sum q^2}
= \frac{u'''\, h^2\, (3m^2 + 3m - 1)}{30}.
$$

At $m = 1$, that is $u''' h^2 / 6$. The standard deviation falls as
$n^{-2}$, and this bias grows as $n^2$. So the mean squared error,
variance plus squared bias, has a minimum. The window size at that
minimum depends on $u'''$ and on $\sigma$.

A quadratic fit gives the same center slope as the affine fit. A
quadratic term is even about the center, and the slope weight $q$ is
odd. In a symmetric window, the two are orthogonal. Only a cubic fit
removes the bias above, and it raises the variance.

### Frequency Response

Take $u = b \sin(kX)$, with wavenumber $k = 2\pi / \text{period}$.
The window's half-width is $a = nh/2$, half its extent. In the
continuum limit, the ratio of the fitted slope to the true slope at
the window center is

$$
T(k) = \frac{3\left( \sin z - z \cos z \right)}{z^3}
\;\approx\; 1 - \frac{z^2}{10}
\quad \text{for } z \ll 1,
\qquad z = ka = \frac{knh}{2}.
$$

The small-$z$ limit matches the cubic bias above. At $m = 7$, the two
slope errors agree within 1%.

[Figure](#fig-sw-frequency) plots $T$ against the wave period for
$n = 15$ and $h = 5$ px. [Kernel Warping](./kernel_warping.md) found a
bias wave in `locate_subpixel` with a 51 px period:

<!-- cmdrun python3 strain_window_frequency.py -->

So the window keeps 1.7% of that wave's slope, and reverses its sign.
The 51 px period sits 1.4 px below the zero crossing at 52.4 px. The
1.7% holds for that period only. A wave with a 94 px period keeps half its slope. A wave with a
230 px period keeps 90%.

<figure id="fig-sw-frequency">
    <img src="strain_window_frequency.png" alt="plot of T, fitted slope over true slope, against wave period from 20 to 400 px for a 15 by 15 window at 5 px spacing. A black continuum curve and a dashed blue discrete curve overlap. Both oscillate near zero below 60 px, cross zero near 52 px, and rise toward 1, reaching 0.9 near 230 px. A red dot marks the 51 px wave at T = -0.017. A dotted vertical line marks the 75 px window extent" />
    <figcaption>Frequency response of a 15x15 window at $h = 5$ px. The black curve is the continuum formula with $a = nh/2$. The dashed blue curve is the discrete least-squares fit. The red dot marks Kernel Warping's 51 px bias wave. The dotted line marks the 75 px window extent.</figcaption>
</figure>

## Window Edges

Near the grid boundary, the window truncates. Every tracked point
still gets a strain. A truncated window loses the cancellations, so
$\sum q$ and $\sum p$ no longer vanish. The matrix is no longer
diagonal, and the fit solves the full $3 \times 3$ normal equations.
[Figure](#fig-sw-edges) shows interior, edge, and corner windows for
$m = 3$.

<figure id="fig-sw-edges">
    <img src="strain_window_edges.png" alt="three panels showing a 7 by 7 window near the top-left corner of a grid of gray dots, with the area outside the grid shaded. Interior: 49 filled orange points, the window center and centroid coincide, std factor 1.00. Edge: the window centers on a point in the left column, 21 points fall outside the grid as hollow circles, 28 remain, the red centroid cross sits 1.5 columns right of the center, std factor 2.37. Corner: 33 points fall outside, 16 remain, the centroid sits 1.5 columns right and 1.5 rows down, std factor 3.13" />
    <figcaption>Interior, edge, and corner windows for $m = 3$. Filled points enter the fit. Hollow points fall outside the grid. The square marks the window center, where the strain is reported. The red cross marks the centroid of the kept points, where the fit measures the gradient. Each title gives the standard deviation of $\partial u / \partial X$ relative to the interior window.</figcaption>
</figure>

Truncation costs precision in two ways. Take the $X$ gradient of a
window that lost its $-X$ half, with $m + 1$ columns left.

**Variance.** The slope variance is $\sigma^2$ divided by
$h^2 \sum (q - \bar{q})^2$, where $\bar{q}$ is the mean column of the
kept points. That sum falls from $h^2 n\, S_m$ to
$h^2 n\, m(m+1)(m+2)/12$. The standard deviation rises by the factor

$$
\sqrt{\frac{4(2m + 1)}{m + 2}} .
$$

At $m = 7$, the factor is 2.58. At a corner, the window also keeps only
$m + 1$ rows. The factor becomes

$$
\sqrt{\frac{4(2m + 1)^2}{(m + 1)(m + 2)}},
$$

which is 3.54 at $m = 7$. At $m = 3$, the factors are 2.37 and 3.13,
as [Figure](#fig-sw-edges) shows.

In units of $\sigma/h$, a 15x15 window's standard deviation is 0.0154
in the interior, 0.0398 on an edge, and 0.0545 at a corner. The Q4
element gives 1.155. The edge value is 29 times lower than that. The
corner value is 21 times lower.

**Location.** Take a quadratic field, $u_{q,p} = \tfrac{1}{2}\, u''\, (qh)^2$,
with $u'' = \partial^2 u / \partial X^2$. An affine fit returns the
true gradient at the centroid of the kept points, not at the window
center. This holds for any point set symmetric about its own centroid,
and a truncated window is one. The centroid sits $mh/2$ from the
window center. At $m = 7$ and $h = 5$ px, that shift is 17.5 px. The
gradient error at an edge point is $u'' \cdot mh/2$.

Uniform stretch has $u'' = 0$, so this bias vanishes there. A field
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
