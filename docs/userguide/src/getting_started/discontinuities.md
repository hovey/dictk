# Discontinuities

Every correlation criterion since [Correlation
Criteria](./correlation_criteria.md), and every worked example through
[Parallelism with PyTorch](./parallelism_pytorch.md), depends on one
tacit assumption: the true displacement field is smooth.
A kernel window moves as a rigid or gently stretching patch. The search
for its match assumes one answer exists.

Real specimens may not always have a continuous displacement field.
A crack, a slip band, or a material
interface can produce a genuine jump in displacement instead of a
continuous displacement. [Image Transformation](./transformation.md#crack-dislocation)
already built exactly that jump:

<figure id="fig-crack-dislocation-repeat">
    <div class="figure-row">
        <div>
            <img src="astronaut_crack_plain_original.png" alt="original" />
            <span>(a)</span>
        </div>
        <div>
            <img src="astronaut_crack_plain_dislocation.png" alt="crack dislocation" />
            <span>(b)</span>
        </div>
    </div>
    <figcaption>Crack Dislocation, the same image pair as <a href="./transformation.html#fig-crack-dislocation">Figure</a>. (a) Original. (b) offset=4 pixels.</figcaption>
</figure>

A vertical crack splits the image at its vertical midline. The left half
shifts down 4 pixels. The right half shifts up 4 pixels. Standard DIC
can't represent that jump.

This chapter seeks to identify characteristics of the correlation map in the presence
of a discontinuous displacement field. Specifically,
what does a correlation surface look like when
a kernel window straddles a real discontinuity instead of sitting
cleanly on one side of it?

[Synthetic Dislocation](./synthetic_dislocation.md) answers that with a
known, exact ground truth: the same 4-pixel offset above, now carrying a
speckle pattern a correlation can actually track. [Experimental
Dislocation](./experimental_dislocation.md) then repeats the same
straddling window on a real experimental crack image pair. There the
ground truth isn't known in advance, so it checks whether the same
signature shows up outside a synthetic setup.

Neither section proposes a discontinuity-aware correlation algorithm on
its own. [Discontinuity
Localization](./discontinuity_localization.md) addresses that challenge.

## Relation to Heaviside-DIC

Heaviside-DIC (H-DIC)[^Bourdin_2018] can represent a displacement jump
like the crack dislocation above. For the continuous part of its
displacement, it uses the same affine kernel warp that [Kernel
Warping](./kernel_warping.md) introduced. The paper calls each kernel
a subset. Its Eq. (1) writes each kernel point's deformed position as
the sum of three terms: the reference position, a rigid-body
translation, and a first-gradient term. The paper labels those terms
"Conventional DIC method." They are the six parameters
$\boldsymbol{p}$ of Kernel Warping's warp, $\boldsymbol{W}$.
$(u, v)$ is the translation, and
$(u_x, u_y, v_x, v_y)$ is the first gradient. The paper's Fig. 2 draws
the same two steps as Kernel Warping's [rigid versus warped kernel
figure](./kernel_warping.md#inverse-compositional-gauss-newton): a
rigid-body displacement, then a first-gradient warp.

H-DIC then adds one term, a jump $\boldsymbol{u}'$ times a Heaviside
function $H$:

$$
\boldsymbol{x} = \boldsymbol{X} + \boldsymbol{u}
+ \nabla\boldsymbol{u} \, (\boldsymbol{X} - \boldsymbol{X}_0)
+ \boldsymbol{u}' \, H(r - r^*),
\qquad
r = \Delta x \cos\theta^* + \Delta y \sin\theta^*.
$$

$H$ is 0 on one side of a line and 1 on the other. The line sits a
distance $r^*$ from the kernel center, at angle $\theta^*$. Pixels on
the far side of the line shift by an extra $\boldsymbol{u}'$. When the
optimized jump is zero, H-DIC reduces to the conventional (continuous)
affine warp. The paper optimizes all parameters together with a
Newton-based method. It doesn't say whether that method uses the inverse
compositional form.

So [`dictk.warp`](../api/dictk/warp.html) covers H-DIC's continuous
half. The missing half is the jump and its line: $\boldsymbol{u}'$,
$r^*$, and $\theta^*$. [Discontinuity
Localization](./discontinuity_localization.md) finds where such a line
crosses a chosen path.

[^Bourdin_2018]: Bourdin F, Stinville JC, Echlin MP, Callahan PG, Lenthe WC, Torbet CJ, Texier D, Bridier F, Cormier J, Villechaise P, Pollock TM. Measurements of plastic localization by heaviside-digital image correlation. Acta Materialia. 2018 Sep 15;157:307-25. [link](https://doi.org/10.1016/j.actamat.2018.07.013)
