# Strain Window

[Kernel Warping](./kernel_warping.md) cut the $E_{11}$ standard
deviation of the 2862-point grid to 1161 microstrain. VIC-2D's own
measurement of the same stretch has a standard deviation of 1385
microstrain. That page also ran an exploratory test. A 15x15-point
least-squares window cut the 1161 microstrain to 39 microstrain.

This page derives that window.

1. Every tracked point has a tracking error.
2. A strain needs a derivative, and a derivative amplifies those errors.
3. A window fits one straight line to many points. The line averages their errors, so the strain error drops.
4. The line assumes the strain is uniform across the whole window.
   * With 15x15 points at 5 px spacing, the window covers 75 px. If the real strain changes inside those 75 px, the fit blurs that change into one number.
   * A larger window averages more errors and blurs more of the real field. A smaller window does the reverse.

This derivation proceeds in three steps. A row of 3 points shows the
idea with 3 numbers. A 3x3 window adds the second axis. A general
window with $n = 2m + 1$ points per side repeats the 3x3 steps with 1
replaced by $m$.

## Notation

| Symbol | Units | Meaning |
|---|---|---|
| $h$ | px | grid spacing |
| $m$ | points | window half-width: the window reaches $m$ points out from its center along each axis |
| $n = 2m + 1$ | points | points per window side, always odd so the window centers on a tracked point |
| $c,\ r$ | points | column and row of a point within the window, each from $-m$ to $m$ |
| $ch,\ rh$ | px | the point's $X$ and $Y$ position relative to the window center |
| $u,\ v$ | px | tracked $X$ and $Y$ displacement |
| $u_{c,r}$ | px | $u$ at column $c$ and row $r$ |
| $\hat{u}_0$ | px | fitted $u$ at the window center |
| $\partial u / \partial X,\ \partial u / \partial Y$ | dimensionless | fitted gradient of $u$ at the window center |
| $w^X_{c,r},\ w^Y_{c,r}$ | 1/px | weight of $u_{c,r}$ in the fitted $\partial u / \partial X$ and $\partial u / \partial Y$ |
| $\boldsymbol{\nabla}_0\,\boldsymbol{u}$ | dimensionless | the $2 \times 2$ displacement gradient, as in [Finite Element Method](./finite_element_method.md#displacement-gradient) |
| $\sigma$ | px | standard deviation of each point's tracking error |

In an image,

* $X$ runs across the page from left to right. The
displacement $u$ points in the $X$ direction. Column $c$ grows from
left to right.
* $Y$ runs down the page from top to bottom. The
displacement $v$ points in the $Y$ direction. Row $r$ grows from top to
bottom.

The steps below fit $u$. [Fit for $v$](#fit-for-v) shows why the fit
for $v$ uses the same weights.

## 1D Example

Consider three points on the $X$ axis centered locally at the middle point, with relative $X$ coordinates $[-h, 0, h]$ pixels.
Each of these points has tracked displacements $[u_{-1}, u_0, u_1]$. 
Let $c$ be the index of the points $[-1, 0, 1]$.
[Figure](#fig-sw-1d) shows the three points and their displacements.

<!-- cmdrun python3 strain_window_1d.py -->

<figure id="fig-sw-1d">
    <img src="strain_window_1d.png" alt="three filled orange dots on a horizontal X axis at X = -h, 0, and h, labeled below with index c = -1, 0, and 1. Two gray double arrows mark the equal spacing h between neighboring dots. Above each dot, an orange arrow points right to a hollow orange dot at the displaced position. The arrows are labeled u_-1, u_0, and u_1, and grow longer from left to right" />
    <figcaption>The 1D Example. Filled dots mark the reference positions $X = ch$. Hollow dots mark the displaced positions $x = X + u_c = ch + u_c$. The displacements are illustrative, 0.30, 0.52, and 0.58 times $h$.</figcaption>
</figure>

Fit a straight line through the displacements. Point $c$ sits at
$X = ch$ pixels relative to the middle point, so the line predicts

$$
u_c \approx \hat{u}_0 + \frac{\partial u}{\partial X}\, c h .
\label{eq-sw-1d-model}
$$

The slope of the line is $\partial u / \partial X$. The intercept of
the line is $\hat{u}_0$, the fitted displacement at the middle point, where
$c = 0$.
[Figure](#fig-sw-1d-fit) shows the line through the three displacements
of [Figure](#fig-sw-1d).

<!-- cmdrun python3 strain_window_1d_fit.py -->

<figure id="fig-sw-1d-fit">
    <img src="strain_window_1d_fit.png" alt="plot of displacement u against position X, with X ticks at -h, 0, and h and u ticks at 0.30h, 0.52h, and 0.58h. Three orange dots mark u_-1, u_0, and u_1. A black fitted line passes just above u_-1 and u_1 and below u_0. A hollow square on the line at X = 0 marks the intercept u-hat_0. A blue right triangle under the line, between -h and 0, marks a run delta X and a rise du/dX times delta X. Short dashed red segments join each dot to the line" />
    <figcaption>The least-squares line through the three displacements of <a href="#fig-sw-1d">Figure</a>. The hollow square marks the intercept $\hat{u}_0 = 0.467h$. The blue triangle shows the slope $\partial u / \partial X = 0.14$. The dashed red segments are the residuals: $-0.027h$, $+0.053h$, and $-0.027h$.</figcaption>
</figure>

That is two unknowns, $\hat{u}_0$ and $\partial u / \partial X$, for three
points. Least squares picks the two unknowns that minimize the sum of
the three squared residuals:

$$
\begin{aligned}
R &= \sum_{c=-1}^{1} \left( u_c - \hat{u}_0 - \frac{\partial u}{\partial X}\, c h \right)^2 \\
&= \left( u_{-1} - \hat{u}_0 + \frac{\partial u}{\partial X}\, h \right)^2
+ \left( u_0 - \hat{u}_0 \right)^2
+ \left( u_1 - \hat{u}_0 - \frac{\partial u}{\partial X}\, h \right)^2 .
\end{aligned}
$$

At the minimum, the derivative of $R$ with respect to each unknown is
zero. The derivative with respect to $\hat{u}_0$ is

$$
\frac{\partial R}{\partial \hat{u}_0}
= -2 \sum_{c} \left( u_c - \hat{u}_0 - \frac{\partial u}{\partial X}\, c h \right) = 0 .
$$

Rearranged, that gives the first normal equation:

$$
\hat{u}_0 \sum_c 1 + \frac{\partial u}{\partial X}\, h \sum_c c = \sum_c u_c .
$$

The derivative with respect to the slope $\partial u / \partial X$ is

$$
\frac{\partial R}{\partial (\partial u / \partial X)}
= -2 \sum_{c} c h \left( u_c - \hat{u}_0 - \frac{\partial u}{\partial X}\, c h \right) = 0 .
$$

Dividing by $-2$ and rearranging gives the second normal equation:

$$
\hat{u}_0\, h \sum_c c + \frac{\partial u}{\partial X}\, h^2 \sum_c c^2 = h \sum_c c\, u_c .
$$

In matrix form, the two normal equations are

$$
\begin{bmatrix} \sum_c 1 & h \sum_c c \\ h \sum_c c & h^2 \sum_c c^2 \end{bmatrix}
\begin{Bmatrix} \hat{u}_0 \\ \partial u / \partial X \end{Bmatrix}
=
\begin{Bmatrix} \sum_c u_c \\ h \sum_c c\, u_c \end{Bmatrix}.
$$

The sums are $\sum_c 1 = 3$, $\sum_c c = -1 + 0 + 1 = 0$, and
$\sum_c c^2 = 1 + 0 + 1 = 2$. So the matrix is

$$
\begin{bmatrix} 3 & 0 \\ 0 & 2h^2 \end{bmatrix}.
$$

The zero off the diagonal decouples the two unknowns:

$$
\boxed{
\begin{aligned}
\hat{u}_0 &= \frac{u_{-1} + u_0 + u_1}{3}, \\[1em]
\frac{\partial u}{\partial X} &= \frac{h\,(-u_{-1} + u_1)}{2h^2}
= \frac{u_1 - u_{-1}}{2h}.
\end{aligned}
}
\label{eq-sw-1d-solution}
$$

The slope is the central difference. The middle point gets zero
weight in it.

### Noise

How much does tracking error move the slope? Work it out in six steps.

**Step 1: model the error.** Each tracked displacement is the true
displacement plus an error:

$$
u_c = u_c^{\text{true}} + e_c .
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

**Step 3: recall two variance rules.** For a constant $\alpha$ and
independent errors $e_a$ and $e_b$:

$$
\begin{aligned}
\operatorname{Var}(\alpha\, e_a) &= \alpha^2 \operatorname{Var}(e_a), \\[1em]
\operatorname{Var}(e_a \pm e_b) &= \operatorname{Var}(e_a) + \operatorname{Var}(e_b).
\end{aligned}
$$

Variances add for a difference too, because the sign flips with $\alpha = -1$
and $\alpha^2 = 1$.

**Step 4: apply the first rule to each term.** The slope error has
two terms, $e_1 / 2h$ and $-e_{-1} / 2h$. Each one is an error scaled by
$\alpha = \pm 1/(2h)$:

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
\label{eq-sw-1d-std}
$$

For example, take $\sigma = 0.01$ px and $h = 5$ px. The slope's
standard deviation is $0.707 \times 0.01 / 5 = 0.00141$, or 1414
microstrain.

A slope's noise reads as strain noise because, at small strain,
$E_{11} \approx \partial u / \partial X$. For a uniaxial stretch,
$E_{11} = \ln(1 + \partial u / \partial X)$, so
$dE_{11} / d(\partial u / \partial X) = 1 / (1 + \partial u / \partial X)$.
At the 2% stretch on these pages, that factor is $1 / 1.02 = 0.98$. So
log strain noise runs 2% below slope noise. This page quotes slope
noise. [From Gradient to Strain](#from-gradient-to-strain) gives the
full chain from slopes to strain.

The slope uses only 2 of the 3 points. The 3x3 window below averages
three such rows.

## Q4 Baseline

[Finite Element Method](./finite_element_method.md) computes strain
from Q4 elements. Every strain on the earlier pages comes from them.
This section derives a Q4 element's noise. The window sections below
compare against it, for two reasons.

* **Q4 is the method `dictk` uses now.** [Kernel
  Warping](./kernel_warping.md) measured its 1161 microstrain spread
  with
  [`gauss_point_log_strains`](../api/dictk/element.html#gauss_point_log_strains),
  which evaluates Q4 elements. A window must beat that to earn a place
  in `dictk`.
* **Q4 sets the unit of improvement.** The 1D slope's noise scales
  with $\sigma / h$. The Q4 element's and the window's do too. One
  number for each turns every comparison into a ratio.

### Gauss-Point Gradient

Take a square Q4 element with side $L$. Its nodes 1 to 4 sit at
$(\xi, \eta) = (-1, -1)$, $(1, -1)$, $(1, 1)$, and $(-1, 1)$. At the
two Gauss points with $\eta = +1/\sqrt{3}$, its gradient is

$$
\begin{aligned}
\frac{\partial u}{\partial X}
&= \frac{1}{L}\left[ g_1 (u_2 - u_1) + g_2 (u_3 - u_4) \right], \\[1em]
g_{1,2} &= \frac{1 \mp 1/\sqrt{3}}{2}.
\end{aligned}
\label{eq-sw-q4}
$$

So $g_1 = 0.211$ and $g_2 = 0.789$. The edge nearer the Gauss point
gets the larger weight. The two Gauss points at
$\eta = -1/\sqrt{3}$ swap $g_1$ and $g_2$. [Figure](#fig-sw-q4-element)
shows the weights. The script computes them with `dictk.element`.

<!-- cmdrun python3 strain_window_q4_element.py -->

<figure id="fig-sw-q4-element">
    <img src="strain_window_q4_element.png" alt="a square Q4 element in local coordinates xi and eta from -1 to 1. Four large colored circles mark the nodes. Node 1 at (-1, -1) shows -0.211 in red, node 2 at (+1, -1) shows +0.211 in blue, node 3 at (+1, +1) shows +0.789 in blue, and node 4 at (-1, +1) shows -0.789 in red. Two blue crosses mark the Gauss points at eta = +1/sqrt(3). Two smaller gray crosses mark the Gauss points at eta = -1/sqrt(3)" />
    <figcaption>Weight of each node in $\partial u / \partial X$ at the Gauss points with $\eta = +1/\sqrt{3}$, the blue crosses, in units of $1/L$. Red weights are negative and blue weights are positive. The top nodes sit nearer these Gauss points, so they carry 0.789. The bottom nodes carry 0.211.</figcaption>
</figure>

### Q4 Noise

The weights satisfy $g_1 + g_2 = 1$ and $g_1^2 + g_2^2 = 2/3$. Each
node enters once, with weight $\pm g_1 / L$ or $\pm g_2 / L$. The
variance rules from the 1D Example's [Noise](#noise) give

$$
\operatorname{std}\!\left(\frac{\partial u}{\partial X}\right)
= \frac{\sigma}{L} \sqrt{2 \left( g_1^2 + g_2^2 \right)}
= \frac{2}{\sqrt{3}}\, \frac{\sigma}{L}
= 1.155\, \frac{\sigma}{L}.
\label{eq-sw-q4-std}
$$

All four Gauss points give the same value, because each one uses the
same four weights in a different order.

The earlier pages build each Q4 element from 4 neighboring tracked
points, so $L = h$. The standard deviation is then $1.155\,\sigma / h$.
For $\sigma = 0.01$ px and $h = 5$ px, that is 2309 microstrain. The
1D Example's central difference gives 1414 microstrain at the same
$\sigma$ and $h$. The [2D Example](#2d-example) compares the 3x3
window with both.

## 2D Example

The smallest square window with a center point holds 3x3 = 9 points.
It is the general window with $m = 1$.

### Setup

The points sit on a grid with spacing $h$. Point $(c, r)$ sits
at $X = ch$ and $Y = rh$ pixels relative to the center point $(0, 0)$.
The window fits a plane through the 9 tracked displacements:

$$
u_{c,r} \approx \hat{u}_0 + \frac{\partial u}{\partial X}\, c h + \frac{\partial u}{\partial Y}\, r h .
\label{eq-sw-2d-model}
$$

That is three unknowns, $\hat{u}_0$, $\partial u / \partial X$, and
$\partial u / \partial Y$, for nine points.
[Figure](#fig-sw-2d-fit) shows the plane through nine displacements.
It extends [Figure](#fig-sw-1d-fit) from a line to a plane.

<!-- cmdrun python3 strain_window_2d_fit.py -->

<figure id="fig-sw-2d-fit">
    <img src="strain_window_2d_fit.png" alt="3D plot of displacement u above a 3 by 3 grid of gray dots on the X-Y floor, with X and Y ticks at -h, 0, and h. A faint blue tilted plane rises toward positive X and positive Y. Nine orange dots sit above the grid points, each joined to the plane by a short dashed red segment, some above the plane and some below. Each orange dot carries its label, u_c,r, from u_-1,-1 to u_1,1. A very light gray rectangle on the floor is the plane's shadow, parallel to the x and y axes, and it covers all nine gray dots. Gray shadows of the plane's lines cross the floor through the dots, darker for the two bold center lines. Two bold blue lines cross the plane through its center, labeled du/dX along x and du/dY along y. A hollow blue square at the crossing marks u-hat_0" />
    <figcaption>The least-squares plane through nine displacements on the 3x3 grid. The hollow square marks the intercept $\hat{u}_0 = 0.469h$. The bold blue line along $X$ has slope $\partial u / \partial X = 0.124$. The bold blue line along $Y$ has slope $\partial u / \partial Y = 0.093$. The dashed red segments are the residuals, from $0.033h$ to $0.101h$ in magnitude. The displacements are illustrative. They sample a true plane with intercept $0.47h$ and slopes $0.14$ in $X$ and $0.07$ in $Y$. Each one adds a Gaussian error with $\sigma = 0.065h$, drawn with random seed 107.</figcaption>
</figure>

### Normal Equations

Least squares minimizes the sum of the nine squared residuals:

$$
R = \sum_{c=-1}^{1} \sum_{r=-1}^{1}
\left( u_{c,r} - \hat{u}_0 - \frac{\partial u}{\partial X}\, c h - \frac{\partial u}{\partial Y}\, r h \right)^2 .
$$

As in the [1D Example](#1d-example), each derivative of $R$ is zero
at the minimum. Write $\hat{e}_{c,r}$ for the residual inside the
parentheses. The three derivatives are

$$
\begin{aligned}
\frac{\partial R}{\partial \hat{u}_0} &= -2 \sum_{c,r} \hat{e}_{c,r} = 0, \\[1em]
\frac{\partial R}{\partial (\partial u / \partial X)} &= -2 \sum_{c,r} c h\, \hat{e}_{c,r} = 0, \\[1em]
\frac{\partial R}{\partial (\partial u / \partial Y)} &= -2 \sum_{c,r} r h\, \hat{e}_{c,r} = 0 .
\end{aligned}
$$

Dividing each by $-2$ and rearranging gives three normal equations. In
matrix form, they are

$$
\begin{bmatrix}
\sum 1 & h \sum c & h \sum r \\
h \sum c & h^2 \sum c^2 & h^2 \sum c r \\
h \sum r & h^2 \sum c r & h^2 \sum r^2
\end{bmatrix}
\begin{Bmatrix} \hat{u}_0 \\ \partial u / \partial X \\ \partial u / \partial Y \end{Bmatrix}
=
\begin{Bmatrix} \sum u_{c,r} \\ h \sum c\, u_{c,r} \\ h \sum r\, u_{c,r} \end{Bmatrix}.
\label{eq-sw-2d-normal}
$$

Each sum runs over the 9 points:

- $\sum 1 = 9$.
- $\sum c = 0$. Three points sit at each of $c = -1$, $0$, and $1$, so
  they cancel. $\sum r = 0$ for the same reason.
- $\sum c r = 0$. Flipping $c$ to $-c$ flips the product's sign, so
  the points cancel in pairs.
- $\sum c^2 = 3 + 0 + 3 = 6$. $\sum r^2 = 6$ for the same reason.

So the matrix is

$$
\begin{bmatrix} 9 & 0 & 0 \\ 0 & 6h^2 & 0 \\ 0 & 0 & 6h^2 \end{bmatrix}.
$$

The matrix is diagonal, so each unknown solves on its own.

### Solution

Each unknown divides one right-side entry by one diagonal entry:

$$
\boxed{
\begin{aligned}
\hat{u}_0 &= \frac{1}{9} \sum_{c,r} u_{c,r}, \\[1em]
\frac{\partial u}{\partial X} &= \frac{h \sum c\, u_{c,r}}{6h^2}
= \frac{1}{6h}\sum_{c,r} c\, u_{c,r}, \\[1em]
\frac{\partial u}{\partial Y} &= \frac{h \sum r\, u_{c,r}}{6h^2}
= \frac{1}{6h}\sum_{c,r} r\, u_{c,r}.
\end{aligned}
}
\label{eq-sw-3x3-solution}
$$

[Figure](#fig-sw-3x3-layout) draws the weights. In
$\partial u / \partial X$, the right column enters with $+1$, the left
column with $-1$, and the middle column with 0. Group the sum by row.
Each row contributes $u_{1,r} - u_{-1,r}$. In
$\partial u / \partial Y$, the bottom row enters with $+1$, the top
row with $-1$, and the middle row with 0. Group that sum by column.
Each column contributes $u_{c,1} - u_{c,-1}$. So

$$
\begin{aligned}
\frac{\partial u}{\partial X}
&= \frac{1}{3} \sum_{r=-1}^{1} \frac{u_{1,r} - u_{-1,r}}{2h}, \\[1em]
\frac{\partial u}{\partial Y}
&= \frac{1}{3} \sum_{c=-1}^{1} \frac{u_{c,1} - u_{c,-1}}{2h}.
\end{aligned}
$$

* $\partial u / \partial X$ is the mean of three central differences,
  one per row. The window differentiates along $X$ and averages along
  $Y$.
* $\partial u / \partial Y$ is the mean of three central differences,
  one per column. The window differentiates along $Y$ and averages along
  $X$.

<figure id="fig-sw-3x3-layout">
    <img src="strain_window_3x3_layout.png" alt="three square panels, each a 3 by 3 grid of dots with column c and row r from -1 to 1. The left panel shows 9 orange dots labeled with their (c, r) index, with a ring around the center (0, 0). The middle panel shows the weights for du/dX: -1 in red for the left column, 0 in gray for the middle column, +1 in blue for the right column. The right panel shows the weights for du/dY: -1 in red for the top row, 0 in gray for the middle row, +1 in blue for the bottom row" />
    <figcaption>The 3x3 window. Left: the 9 points, indexed by column $c$ and row $r$. Middle: the weight of each point in $\partial u / \partial X$, in units of $1/(6h)$. Right: the weight of each point in $\partial u / \partial Y$, in the same units.</figcaption>
</figure>

### Fit for $v$

Every entry of the matrix in the normal equations is a sum over $c$,
$r$, and $h$. No entry holds a displacement. So the fit for $v$ uses
the same matrix. Only the right side changes, from $u_{c,r}$ to
$v_{c,r}$. The same diagonal entries give

$$
\boxed{
\begin{aligned}
\hat{v}_0 &= \frac{1}{9} \sum_{c,r} v_{c,r}, \\[1em]
\frac{\partial v}{\partial X} &= \frac{1}{6h}\sum_{c,r} c\, v_{c,r}, \\[1em]
\frac{\partial v}{\partial Y} &= \frac{1}{6h}\sum_{c,r} r\, v_{c,r}.
\end{aligned}
}
\label{eq-sw-3x3-solution-v}
$$

The weights match [Figure](#fig-sw-3x3-layout). They multiply $v$
instead of $u$.

### One Noisy Draw

The grid spacing is $h = 5$ px. The true field is $u_{0,0}^{\text{true}} = 0.3$ px, $\partial u / \partial X = 0.02$,
and $\partial u / \partial Y = 0.01$. Each tracked displacement gets
an independent Gaussian error with $\sigma = 0.01$ px. That $\sigma$
is illustrative. It is not measured from a tracker. A tracker's
errors also correlate between neighboring points, as
[Noise in a General Window](#noise-in-a-general-window) shows.

A Monte Carlo simulation checks the 3x3 window's noise. The script
draws 10,000 sets of 9 errors with random seed 0. The table
shows the draw whose $\partial u / \partial X$ error sits closest to
the median error of the 10,000.

<!-- cmdrun python3 strain_window_3x3.py -->

[Figure](#fig-sw-3x3-fit) plots that draw on the left. The right
panel is the histogram of $\partial u / \partial X$ over all 10,000
draws.

<figure id="fig-sw-3x3-fit">
    <img src="strain_window_3x3_fit.png" alt="two panels. Left: nine tracked X displacements in pixels against X = ch from -5 to 5 px, colored by row, with a solid black fitted line of slope 0.01944 and a dashed red true line of slope 0.02. Right: a histogram of the fitted du/dX over 10000 Monte Carlo draws, centered on the true value of 20000 microstrain, with a blue band of plus or minus 819 microstrain for the 3x3 window and a wider pale red band of plus or minus 2309 microstrain for a Q4 element" />
    <figcaption>Left: the draw from the table. Each point shows $u$ minus the fitted $(\partial u / \partial Y)\, rh$, which removes the row offset. The solid black line is the fit, and the dashed red line is the truth. Right: fitted $\partial u / \partial X$ over 10,000 Monte Carlo draws, in microstrain. The blue band is $\pm 1$ standard deviation of the 3x3 window. The pale red band is $\pm 1$ standard deviation of a Q4 element, from the formula in <a href="#q4-baseline">Q4 Baseline</a>.</figcaption>
</figure>

### Noise in the 3x3 Window

The solution writes $\partial u / \partial X$ as a weighted sum
$\sum w^X_{c,r}\, u_{c,r}$ with $w^X_{c,r} = c / (6h)$. Independent errors
give

$$
\operatorname{Var}\!\left(\frac{\partial u}{\partial X}\right)
= \sigma^2 \sum_{c,r} \left(w^X_{c,r}\right)^2
= \sigma^2\, \frac{6}{(6h)^2}
= \frac{\sigma^2}{6h^2}.
\label{eq-sw-3x3-variance}
$$

The standard deviation is $\sigma / (\sqrt{6}\, h) = 0.408\,\sigma / h$.
The row of three points gave $0.707\,\sigma / h$. Averaging three
independent rows divides that by $\sqrt{3}$, and
$0.707 / \sqrt{3} = 0.408$. For $\sigma = 0.01$ px and $h = 5$ px, the
formula gives 816 microstrain. The 10,000 Monte Carlo draws give 819 microstrain.

The weights for $\partial u / \partial Y$ are $r / (6h)$. Their
squares sum to the same $6 / (6h)^2$, so $\partial u / \partial Y$
also has standard deviation $0.408\,\sigma / h$. The fit for $v$
uses the same weights. If the errors in $v$ have the same $\sigma$,
$\partial v / \partial X$ and $\partial v / \partial Y$ have
$0.408\,\sigma / h$ too.

## General Window

A general window holds $n \times n$ points, with $n = 2m + 1$. The
steps match the 3x3 window's. Each one ends by setting $m = 1$, which
recovers the 3x3 result.

### Setup

Columns $c$ and rows $r$ each run from $-m$ to $m$. The fit is the
same plane:

$$
u_{c,r} \approx \hat{u}_0 + \frac{\partial u}{\partial X}\, c h + \frac{\partial u}{\partial Y}\, r h .
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
S_m = \sum_{c=-m}^{m} c^2 = \frac{m(m+1)(2m+1)}{3}.
\label{eq-sw-sm}
$$

The window's sums follow from it:

- $\sum 1 = n^2$.
- $\sum c = \sum r = \sum c r = 0$, by the same cancellations as the
  3x3 window.
- $\sum c^2 = n\, S_m$, because each of the $n$ rows contributes
  $S_m$. $\sum r^2$ is the same.

So the matrix is

$$
\begin{bmatrix} n^2 & 0 & 0 \\ 0 & h^2 n S_m & 0 \\ 0 & 0 & h^2 n S_m \end{bmatrix}.
$$

At $m = 1$: $n = 3$ and $S_1 = 2$, so the diagonal is
$(9,\; 6h^2,\; 6h^2)$.

### Solution

$$
\boxed{
\begin{aligned}
\hat{u}_0 &= \frac{1}{n^2} \sum_{c,r} u_{c,r}, \\[1em]
\frac{\partial u}{\partial X} &= \frac{h \sum c\, u_{c,r}}{h^2 n S_m}
= \sum_{c,r} w^X_{c,r}\, u_{c,r}, \\[1em]
\frac{\partial u}{\partial Y} &= \frac{h \sum r\, u_{c,r}}{h^2 n S_m}
= \sum_{c,r} w^Y_{c,r}\, u_{c,r}, \\[1em]
\hat{v}_0 &= \frac{1}{n^2} \sum_{c,r} v_{c,r}, \\[1em]
\frac{\partial v}{\partial X} &= \sum_{c,r} w^X_{c,r}\, v_{c,r}, \\[1em]
\frac{\partial v}{\partial Y} &= \sum_{c,r} w^Y_{c,r}\, v_{c,r}, \\[1em]
w^X_{c,r} &= \frac{c}{h\, n\, S_m}, \\[1em]
w^Y_{c,r} &= \frac{r}{h\, n\, S_m}.
\end{aligned}
}
\label{eq-sw-general-solution}
$$

At $m = 1$, the weights are $w^X_{c,r} = c / (6h)$ and
$w^Y_{c,r} = r / (6h)$.

The weight grows linearly with $c$. The outermost columns, at
$c = \pm m$, carry the largest weights. A displacement $mh$ from the
center changes by $mh$ times any change in slope, so it constrains the
slope $m$ times as tightly as a point at $c = \pm 1$. The weight does not depend on $r$.
So the estimator fits one line per row and averages the $n$ row
slopes. [Figure](#fig-sw-stencils) shows the weights for $m = 1$, 2,
and 3. The script also solves the normal equations directly and
compares:

<!-- cmdrun python3 strain_window_stencils.py -->

<figure id="fig-sw-stencils">
    <img src="strain_window_stencils.png" alt="three square heat maps of du/dX weights for windows of 3 by 3, 5 by 5, and 7 by 7 points. Each cell shows its column index c, from red negative values on the left through white zero in the middle column to blue positive values on the right. Every row is identical. The panel titles give the weights as c over 6h, c over 50h, and c over 196h" />
    <figcaption>The weight of each point in $\partial u / \partial X$ for $m = 1$, 2, and 3. Each cell shows $c$. The title gives the weight, $c / (h\, n\, S_m)$. The square marks the window center.</figcaption>
</figure>

The weights depend only on $m$ and $h$. They do not depend on the
images. So one set of weights serves every interior window, and for
both $u$ and $v$.

### Noise in a General Window

Independent errors give

$$
\operatorname{Var}\!\left(\frac{\partial u}{\partial X}\right)
= \sigma^2 \sum_{c,r} \left(w^X_{c,r}\right)^2
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
\label{eq-sw-general-std}
$$

At $m = 1$, it is $\sigma / (\sqrt{6}\, h)$. The standard deviation
falls as $n^{-2}$. Each row's line fit contributes $n^{-3/2}$. A row
has $n$ points, and its outer points sit $mh$ from the center, so
$S_m$ grows as $m^3$. Averaging the $n$ rows contributes the remaining
$n^{-1/2}$.

The table compares the formula with a Monte Carlo simulation of 4000
random draws per window and
with the Q4 element's $1.155\,\sigma / h$. [Figure](#fig-sw-noise)
plots the same comparison for $n$ from 3 to 19:

<!-- cmdrun python3 strain_window_noise.py -->

<figure id="fig-sw-noise">
    <img src="strain_window_noise.png" alt="log-scale plot of the standard deviation of du/dX, in units of sigma over h, against window points per side n from 3 to 19. A black formula curve falls from 0.41 at n = 3 to 0.0096 at n = 19. Blue Monte Carlo dots sit on the curve. A dashed red horizontal line marks the Q4 element at 1.155" />
    <figcaption>Standard deviation of $\partial u / \partial X$ for independent errors, in units of $\sigma / h$, against $n$. The black curve is the formula. The blue dots are a Monte Carlo simulation of 4000 random draws per window. The dashed red line is a Q4 element of side $h$, from <a href="#q4-baseline">Q4 Baseline</a>.</figcaption>
</figure>

If the tracking errors were independent, the $75\times$ reduction at
$n = 15$ would cut Kernel Warping's 1161 microstrain to 15.5 microstrain. That $75\times$
compares the window with a Q4 element on the same grid.
[Window versus Q4](#window-versus-q4) splits it into a $14\times$ gain from the larger
footprint and a $5.35\times$ gain from the least-squares fit.
Matching resolution instead of footprint moves that split to
$11.3\times$ and $6.6\times$. The exploratory test measured 39 microstrain, 2.5 times more. The tracking error is
not independent. [Kernel Warping](./kernel_warping.md) found a wave
with a 51 px period. Points 5 px apart sit 35° apart on that wave's
cycle, so their errors correlate at $\cos 35° = 0.82$.
[Frequency Response](#frequency-response) computes the fraction of a
wave's slope that a window passes.

### Uniform Weights

Every point here gets the same weight in the sum of squared residuals.
For independent errors with equal variance, uniform weights give the
lowest variance of any linear unbiased estimator. A tent or Gaussian
weight would reduce the influence of each window's outer points. Both
are candidate refinements for a later stage. Neither appears here.

## Window versus Q4

[Q4 Baseline](#q4-baseline) derived a Q4 element's noise,
$1.155\,\sigma / L$. [Noise in a General Window](#noise-in-a-general-window)
derived the window's. This section compares the two at any window
size. Two points frame the comparison.

* **Q4 shows where the gain comes from.** A Q4 element fits 4
  coefficients to 4 displacements. The fit is exact, so it averages
  nothing. A 15x15 window fits 3 coefficients to 225 displacements.
  That redundancy does the averaging.
* **A fair comparison controls for footprint.** On a grid with
  spacing $h$, a Q4 element spans $h$. A 15x15 window spans $14h$
  between its outer points. That larger footprint alone accounts for
  $14\times$ of the window's $74.8\times$ lead. It also blurs the
  strain field. [Equal Footprint](#equal-footprint) holds the
  footprint fixed. [Q4 at Equal Resolution](#q4-at-equal-resolution)
  holds the resolution fixed, which is the fairer test.

### Equal Spacing

A Q4 element at $L = h$ gives 2309 microstrain. The 3x3 window gives
816 microstrain, 2.8 times less, at the same $\sigma = 0.01$ px and
$h = 5$ px. Dividing the Q4 standard deviation by the general window's
standard deviation gives the ratio for any window size:

$$
\frac{\operatorname{std}_{\text{Q4}}}{\operatorname{std}_{\text{window}}}
= \frac{2\, n \sqrt{m(m+1)}}{3}.
\label{eq-sw-q4-spacing-ratio}
$$

The ratio is 2.8 at $m = 1$ and 74.8 at $m = 7$. It gives the gain
`dictk` would see by replacing its Q4 elements with windows on the same
grid. It does not split that gain by source.

### Equal Footprint

A 15x15 window at $h = 5$ px spans 70 px between its outer points. A
Q4 element at $L = h$ spans 5 px. To remove the footprint gain, give the
Q4 element the window's footprint. Its corners then sit on the window's
4 corner points, and $L = 2mh$. [Figure](#fig-sw-q4-footprint) shows
the three choices on one grid.

<!-- cmdrun python3 strain_window_q4_footprint.py -->

<figure id="fig-sw-q4-footprint">
    <img src="strain_window_q4_footprint.png" alt="three panels, each a 15 by 15 grid of points with columns and rows from -7 to 7. Left: all 225 points orange inside a blue square, titled 15x15 window, std 0.0154 sigma over h. Middle: 4 orange points at the corners of one small red square cell near the center, the other points light gray, titled Q4 equal spacing, std 1.1547. Right: 4 orange points at the grid corners joined by a large red square, the other points light gray, titled Q4 equal footprint, std 0.0825" />
    <figcaption>The tracked points each method uses on one 15x15 grid. Left: the window uses all 225. Middle: a Q4 element at equal spacing uses 4 neighbors, 1 cell wide. Right: a Q4 element at equal footprint uses the 4 corner points, 14 cells wide. Each title gives the standard deviation of $\partial u / \partial X$ in units of $\sigma / h$.</figcaption>
</figure>

With $L = 2mh$, the ratio becomes

$$
\frac{\operatorname{std}_{\text{Q4}}}{\operatorname{std}_{\text{window}}}
= \frac{n \sqrt{m(m+1)}}{3m}.
\label{eq-sw-q4-footprint-ratio}
$$

The ratio is 1.41 at $m = 1$ and 5.35 at $m = 7$, and it approaches
$n / 3$ as $m$ grows. The two ratios differ by exactly $2m$, the ratio
of the footprints. At $n = 15$, $74.8 = 14 \times 5.35$. The 14 comes
from the footprint. The 5.35 comes from the fit. The window fits 225
displacements by least squares. The Q4 element interpolates 4 exactly.

Counting points alone suggests $\sqrt{225/4} = 7.5\times$. Two
effects turn that into $5.35\times$. First, the window's interior
points sit closer to its center. A change in slope moves a point in
column $c$ by an amount proportional to $c$. So each point adds
information about the slope in proportion to $c^2$. A point at
$c = 1$ adds 1/49 as much as a point at $c = 7$. The 15 points at
$c = 0$ add none. Over one row, $\sum c^2 = 0.381\, n m^2$, so the 225 points carry
as much as 85.7 points in the outer columns would. That costs the
window a factor $\sqrt{0.381} = 0.617$. Second, the Q4 element weights
its corners unequally, with $g_1 = 0.211$ and $g_2 = 0.789$. Equal
weights of 0.5 would give $1.0\,\sigma / L$ instead of
$1.155\,\sigma / L$. That costs the Q4 element a factor 1.155.
Together, $7.5 \times 0.617 \times 1.155 = 5.35$.

<!-- cmdrun python3 strain_window_q4_noise.py -->

[Figure](#fig-sw-q4-noise) plots all three for $n$ from 3 to 19.

<figure id="fig-sw-q4-noise">
    <img src="strain_window_q4_noise.png" alt="log-scale plot of the standard deviation of du/dX, in units of sigma over h, against window points per side n from 3 to 19. A dashed red line holds at 1.155 for the equal-spacing Q4 element. A solid red line with hollow squares falls from 0.58 at n = 3 to 0.064 at n = 19 for the equal-footprint Q4 element. A solid blue line with dots falls faster, from 0.41 to 0.0096, for the window. At n = 15, labels give the values 1.1547, 0.0825, and 0.0154, and gray double arrows split the gap into 14× footprint, between the two red lines, and 5.35× fit, between the lower red line and the blue line" />
    <figcaption>Standard deviation of $\partial u / \partial X$ against $n$ for the window and for Q4 elements at equal spacing and at equal footprint. At $n = 15$, the gray arrows split the $74.8\times$ equal-spacing ratio into a $14\times$ footprint gain and a $5.35\times$ least-squares fit gain. The labels give each series' value at $n = 15$, in units of $\sigma / h$.</figcaption>
</figure>

A larger footprint lowers noise and blurs the field. Two methods with
the same footprint can still blur by different amounts. [Q4 at Equal
Resolution](#q4-at-equal-resolution) checks whether the $5.35\times$ favors
the window.

## From Gradient to Strain

Fitting $u$ and $v$ gives the four components of the displacement
gradient at the window center:

$$
\boldsymbol{\nabla}_0\,\boldsymbol{u} =
\begin{bmatrix}
\partial u / \partial X & \partial u / \partial Y \\
\partial v / \partial X & \partial v / \partial Y
\end{bmatrix}.
\label{eq-sw-gradient}
$$

The fit uses reference positions $ch$ and $rh$, so this is the
Lagrangian gradient. The rest follows
[Continuum Mechanics](./continuum_mechanics.md):

$$
\begin{aligned}
\boldsymbol{F} &= \boldsymbol{I} + \boldsymbol{\nabla}_0\,\boldsymbol{u}, \\[1em]
\boldsymbol{U} &= \sqrt{\boldsymbol{F}^\top \boldsymbol{F}}, \\[1em]
\boldsymbol{E}^{(0)} &= \ln \boldsymbol{U}.
\end{aligned}
\label{eq-sw-strain}
$$

This page reports the log strain $\boldsymbol{E}^{(0)}$, to match the
figures on the pages before it. The fit is linear in the
displacements. The strain is not, because $\boldsymbol{U}$ and
$\ln$ are nonlinear. So the noise formulas above hold exactly for
$\boldsymbol{\nabla}_0\,\boldsymbol{u}$. For strain they hold to
first order. The 1D Example's [Noise](#noise) showed that log strain
noise runs 2% below slope noise at the 2% stretch on these pages.

Fitting the current positions $\boldsymbol{x}$ instead of $u$ and $v$
gives $\boldsymbol{F}$ directly as the slope. Both routes agree,
because the reference positions $ch$ and $rh$ are exactly linear in
$c$ and $r$.

## Bias and Resolution

A window reduces variance and adds bias. Two results size the bias.

**Cubic term.** Let the true field be
$u_{c,r} = \tfrac{1}{6}\, u'''\, (ch)^3$, with
$u''' = \partial^3 u / \partial X^3$. The true gradient at the center
is 0. The fitted slope is

$$
\frac{\partial u}{\partial X}\bigg|_{\text{fit}}
= \frac{h \sum c\, u_{c,r}}{h^2 \sum c^2}
= \frac{u'''}{6}\, h^2\, \frac{\sum c^4}{\sum c^2}
= \frac{u'''\, h^2\, (3m^2 + 3m - 1)}{30}.
\label{eq-sw-cubic-bias}
$$

At $m = 1$, that is $u''' h^2 / 6$. The standard deviation falls as
$n^{-2}$, and this bias grows as $n^2$. So the mean squared error,
variance plus squared bias, has a minimum. The window size at that
minimum depends on $u'''$ and on $\sigma$.

A quadratic fit gives the same center slope as the affine fit. A
quadratic term is even about the center, and the slope weight $c$ is
odd. In a symmetric window, the two are orthogonal. Only a cubic fit
removes the bias above, and it raises the variance.

### Frequency Response

Take $u = b \sin(kX)$, with wavenumber $k = 2\pi / \text{period}$.
The window's half-width is $a = nh/2$, half its extent. In the
continuum limit, the ratio of the fitted slope to the true slope at
the window center is

$$
\begin{aligned}
T(k) &= \frac{3\left( \sin z - z \cos z \right)}{z^3}
\;\approx\; 1 - \frac{z^2}{10}
\quad \text{for } z \ll 1, \\[1em]
z &= ka = \frac{knh}{2}.
\end{aligned}
\label{eq-sw-frequency}
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
    <img src="strain_window_frequency.png" alt="plot of T, fitted slope over true slope, against wave period from 20 to 400 px for a 15 by 15 window at 5 px spacing. A wide light gray continuum band and a thin dark navy discrete line overlap, with the line running down the middle of the band. Both oscillate near zero below 60 px, cross zero near 52 px, and rise toward 1, reaching 0.9 near 230 px. A red dot marks the 51 px wave at T = -0.017. A dotted vertical line marks the 75 px window extent" />
    <figcaption>Frequency response of a 15x15 window at $h = 5$ px. The wide gray band is the continuum formula with $a = nh/2$. The thin navy line is the discrete least-squares fit. The two differ by at most 0.004 in $T$, at an 81 px period, so the line stays inside the band. The red dot marks Kernel Warping's 51 px bias wave. The dotted line marks the 75 px window extent.</figcaption>
</figure>

### Q4 at Equal Resolution

For the same wave $u = b \sin(kX)$, a Q4 element of side $L$ reads
the same edge difference on both of its edges. For a field that varies
along $X$ only, all four Gauss points return the same gradient. Its
ratio to the true slope at the element center is

$$
T_{\text{Q4}}(k) = \frac{\sin z}{z} \;\approx\; 1 - \frac{z^2}{6}
\quad \text{for } z \ll 1,
\qquad z = \frac{kL}{2}.
\label{eq-sw-q4-frequency}
$$

The window's $T$ falls as $1 - z^2/10$. At equal footprint, the Q4
element blurs more:

<!-- cmdrun python3 strain_window_q4_frequency.py -->

So matching resolution instead of footprint raises the window's lead
from $5.35\times$ to $6.6\times$. Equal resolution holds the
half-power period fixed at 94 px, so it is the fairer comparison. At
equal resolution, the $74.8\times$ equal-spacing lead splits into
$11.3\times$ from the footprint and $6.6\times$ from the fit.

Both Q4 elements also pass more of a short wave with its sign
reversed. Each one's $T$ bottoms out at $-0.217$, the minimum of
$\sin z / z$. The 70 px element reaches it at a 49 px period, and the
56.7 px element at 40 px. The window's $T$ bottoms out at $-0.088$,
at a 41 px period.
[Figure](#fig-sw-q4-frequency) plots all three responses.

<figure id="fig-sw-q4-frequency">
    <img src="strain_window_q4_frequency.png" alt="plot of T, fitted slope over true slope, against wave period from 20 to 400 px. A blue curve for the 15 by 15 window crosses T = 0.5 at 94 px, marked by a blue dot. A solid red curve for a Q4 element with a 70 px side crosses T = 0.5 later, at 116 px, marked by a red dot. A dashed red curve for a Q4 element with a 56.7 px side nearly overlaps the blue curve above T = 0. Below T = 0, both red curves dip to -0.217, the solid one at a 49 px period and the dashed one at 40 px. The blue curve dips only to -0.088, at 41 px. A dotted gray line marks T = 0.5" />
    <figcaption>Frequency response of a 15x15 window at $h = 5$ px against two Q4 elements. The solid red curve has the window's 70 px footprint. The dashed red curve has the side that matches the window's 94 px half-power period. The legend gives each one's standard deviation of $\partial u / \partial X$. The dots mark where each solid curve keeps half the slope.</figcaption>
</figure>

## Window Edges

Near the grid boundary, the window truncates. Every tracked point
still gets a strain. A truncated window loses the cancellations, so
$\sum c$ and $\sum r$ no longer vanish. The matrix is no longer
diagonal, and the fit solves the full $3 \times 3$ normal equations.
[Figure](#fig-sw-edges) shows interior, edge, and corner windows for
$m = 3$.

<!-- cmdrun python3 strain_window_edges.py -->

<figure id="fig-sw-edges">
    <img src="strain_window_edges.png" alt="three panels showing a 7 by 7 window near the top-left corner of a grid of gray dots, with the area outside the grid shaded. Interior: 49 filled orange points, the window center and centroid coincide, std factor 1.00. Edge: the window centers on a point in the left column, 21 points fall outside the grid as hollow circles, 28 remain, the red centroid cross sits 1.5 columns right of the center, std factor 2.37. Corner: 33 points fall outside, 16 remain, the centroid sits 1.5 columns right and 1.5 rows down, std factor 3.13" />
    <figcaption>Interior, edge, and corner windows for $m = 3$. Filled points enter the fit. Hollow points fall outside the grid. The square marks the window center, where the strain is reported. The red cross marks the centroid of the kept points, where the fit measures the gradient. Each title gives the standard deviation of $\partial u / \partial X$ relative to the interior window.</figcaption>
</figure>

Truncation costs precision in two ways. Take the $X$ gradient of a
window that lost its $-X$ half, with $m + 1$ columns left.

**Variance.** The slope variance is $\sigma^2$ divided by
$h^2 \sum (c - \bar{c})^2$, where $\bar{c}$ is the mean column of the
kept points. That sum falls from $h^2 n\, S_m$ to
$h^2 n\, m(m+1)(m+2)/12$. The standard deviation rises by the factor

$$
\sqrt{\frac{4(2m + 1)}{m + 2}} .
\label{eq-sw-edge-factor}
$$

At $m = 7$, the factor is 2.58. At a corner, the window also keeps only
$m + 1$ rows. The factor becomes

$$
\sqrt{\frac{4(2m + 1)^2}{(m + 1)(m + 2)}},
\label{eq-sw-corner-factor}
$$

which is 3.54 at $m = 7$. At $m = 3$, the factors are 2.37 and 3.13,
as [Figure](#fig-sw-edges) shows.

In units of $\sigma/h$, a 15x15 window's standard deviation is 0.0154
in the interior, 0.0398 on an edge, and 0.0545 at a corner. The Q4
element gives 1.155. The edge value is 29 times lower than that. The
corner value is 21 times lower.

**Location.** Take a quadratic field, $u_{c,r} = \tfrac{1}{2}\, u''\, (ch)^2$,
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

## Measured Result

[`dictk.strain_window.log_strains`](../api/dictk/strain_window.html#log_strains)
runs the window on [Kernel Warping](./kernel_warping.md)'s tracked
positions. The grid has 53x54 points at 5 px spacing. The current image
stretches the reference 2% in $x$, so the true $E_{11}$ is
$\ln 1.02 = 19803$ microstrain. The window has $m = 7$, so $n = 15$. It
steps by 1 point. The Q4 row repeats Kernel Warping's baseline on the
same positions.

<!-- cmdrun python3 strain_window_measured.py -->

The interior row reproduces the exploratory test. Each of its 1560
points has a full 15x15 window. Their $E_{11}$ standard deviation is 39
microstrain. Q4 gives 1161 microstrain on the same positions, so the
window cuts the spread $30\times$. The interior mean matches
$\ln 1.02$ to within 1 microstrain. The Q4 mean sits 48 microstrain
above it.

The 39 microstrain leaves out 45.5% of the grid. Those 1302 points sit
within 7 points of an edge, so their windows truncate. Their standard
deviation is 117 microstrain, 3.0 times the interior value. Their mean
sits 73 microstrain below $\ln 1.02$. Over all 2862 points, the
standard deviation is 91 microstrain. A full strain field includes its
edges, so 91 microstrain is the spread a reader of that field sees.

### Edges and Corners

[Window Edges](#window-edges) predicts how truncation raises the spread
for independent errors. The table tests that prediction on the measured
field. It groups the 2862 points by distance to the grid boundary.
$d_X$ counts columns to the nearest left or right edge. $d_Y$ counts
rows to the nearest top or bottom edge. Both stop at $m = 7$, where the
window no longer truncates. The table reports the root-mean-square
(RMS) error of $E_{11}$ against $\ln 1.02$. The RMS includes bias, and
the standard deviation does not. The independent prediction comes from
[`std_factors`](../api/dictk/strain_window.html#std_factors). The last
column gives the largest fraction of a 51 px wave's slope that each
window passes, over all phases of the wave.

<!-- cmdrun python3 strain_window_edges_measured.py -->

The independent-error model underpredicts every $X$ edge group. At the
edge column, $d_X = 0$, the RMS error is 158 microstrain, 4.03 times the
interior's 39. The model predicts 2.58. The worst group sits 3 columns
in. Its RMS error is 237 microstrain, 6.04 times the interior. The model
predicts 1.60 there.

$Y$ edges add 17% to the interior RMS. The top and bottom rows give 46
microstrain, 1.17 times the interior, below the predicted 1.37. The 4
corner points give 187 microstrain, 4.76 times the interior, against a
predicted 3.54. The corners also sit at $d_X = 0$. Their 187
microstrain sits within 29 microstrain of the $X$ edge's 158.

The tracking error accounts for the gap. [Kernel
Warping](./kernel_warping.md) found that the error follows a wave in
$X$ with a 51 px period. Panel (a) of [Figure](#fig-sw-edges-measured)
shows the strain error as vertical stripes. It depends on $X$, not on
$Y$. Panel (b) averages each column over the 40 rows with a full $Y$
window. The column-mean displacement error has an RMS of 0.0076 px. A
window fit of that error predicts the column-mean $E_{11}$ error with
correlation 0.9997.

<figure id="fig-sw-edges-measured">
    <img src="strain_window_edges_measured.png" alt="two panels. Left: a map of E11 minus ln 1.02 over the 53 by 54 grid, on a red-blue scale from -338 to +338 microstrain. The error forms vertical stripes. The leftmost column is dark red, the next six columns are blue, and the rightmost seven columns are dark blue. A dashed rectangle encloses the interior points with a full window, where every point stays within 105 microstrain. Right: column-mean E11 error against grid column 0 to 52. Blue dots follow a black line closely. The curve starts at +174 at column 0, dips to -210 at column 3, oscillates between -70 and +58 between the dashed lines at columns 6.5 and 45.5, then falls to -287 at column 50" />
    <figcaption>(a) The $E_{11}$ error of a 15x15 window at each tracked point. The dashed rectangle encloses the 1560 points with a full window. (b) The column-mean $E_{11}$ error over the 40 rows with a full $Y$ window. The blue dots are measured. The black line is a window fit of the column-mean displacement error. The dashed lines separate truncated columns from full ones.</figcaption>
</figure>

A full window passes 1.7% of the wave's slope. The 51 px period sits
1.4 px from the window's zero crossing at 52.4 px. A truncated window
loses that cancellation. At the $X$ edge, it passes up to 52.3%. Three
columns in, it passes up to 24.1%. These are upper bounds over the
wave's phase. Each $d_X$ group holds only 2 columns, one per side. Its
RMS depends on where those 2 columns fall on the wave, so it need not
peak at the edge. Here it peaks at $d_X = 3$.

The truncated points' 73 microstrain mean offset has the same cause.
Their columns sample the wave at phases that do not cancel. Within 5
columns of an $X$ edge, the RMS error runs 2.9 to 6.0 times the
interior's. So a field-wide spread from this tracker should report
interior and edge points separately.

Continue to [Discontinuities](./discontinuities.md).
