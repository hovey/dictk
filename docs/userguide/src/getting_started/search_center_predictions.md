# Search Center Predictions

[`dictk.grid.locate`](../api/dictk/grid.html#locate)'s `search_centers`
parameter defaults to `None`, which means each point's own
`reference_points` entry doubles as its search center — a "zero
displacement" guess. Every worked example in this book relies on that
default. It works well here because every displacement used so far is
small relative to the search margin chosen to contain it.

[Recoverable Displacement Range](./kernel_search_window_ratio.md)
establishes that the searchable range is bounded by `search_margin`
itself now, not by `kernel_margin`. That's good news — it's a real,
symmetric bound to design around — but it doesn't remove the underlying
tension: a bigger unknown displacement still needs a bigger
`search_margin` to contain it, and a bigger `search_margin` costs more
compute (a larger FFT, at every point). The zero-displacement guess is
the worst case for this: it forces `search_margin` to cover the *entire*
possible displacement, with no help from anything already known about
how the specimen is actually deforming.

## A Better Guess

If some estimate of the deformation already exists — a coarse global DIC
pass, a prior loading step in a finite element analysis, or just a
reasonable assumption about how the specimen is expected to move — that
estimate can predict roughly where each point ended up, instead of
guessing zero displacement. A smaller `search_margin` then suffices,
since it only needs to cover how *wrong* that prediction might be, not
the full displacement itself.

The natural way to express such an estimate is a **deformation
gradient**, the same $\boldsymbol{F}$ [Continuum
Mechanics](./continuum_mechanics.md#deformation-gradient)
already defines — extended here to an affine map in homogeneous
coordinates, so a single matrix carries both the linear part (stretch,
rotation, shear) and a translation:

$$
\boldsymbol{F} = \begin{bmatrix} F_{11} & F_{12} & t_x \\ F_{21} & F_{22} & t_y \\ 0 & 0 & 1 \end{bmatrix}, \qquad
\hat{\boldsymbol{x}} = \boldsymbol{F}\,\boldsymbol{X}, \qquad
\boldsymbol{X} = \begin{bmatrix} X \\ Y \\ 1 \end{bmatrix}
$$

where $\boldsymbol{X}$ is a point's reference position (in homogeneous
form) and $\hat{\boldsymbol{x}}$ is its *predicted* current position —
the search center to use, not the answer itself. This is not quite
Continuum Mechanics' own $\boldsymbol{F}$: that one is purely linear (no
translation, $2\times 2$ in 2D); this extends it to $3\times 3$
specifically so one matrix can express a rigid translation too, the same
kind of motion [Multi-Point Motion](./multi_point_motion.md) tracks.

**The default should be $\boldsymbol{F} = \boldsymbol{I}$** — the
identity:

$$
\boldsymbol{I} = \begin{bmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{bmatrix}
$$

Because $\boldsymbol{I}\,\boldsymbol{X} = \boldsymbol{X}$, an identity
$\boldsymbol{F}$ predicts zero displacement — exactly today's existing
default (`search_centers=None` ⟹ each point's own reference position).
Introducing $\boldsymbol{F}$ this way changes nothing for every example
already in this book; it only adds a way to do better when a better
guess is available.

## Not Implemented Yet

This is a real API change, not a small one, and it touches design
questions this page doesn't resolve on its own:

- Where does $\boldsymbol{F}$ apply — `grid.locate` only (a natural
  fit, since it already computes a `search_centers` list per call), or
  does `translation.locate`'s single-point API need an equivalent?
- If a caller supplies both `F` and `search_centers` explicitly, which
  wins, or is that combination an error?
- Applying an affine $\boldsymbol{F}$ to a `PixelCoordinate` is itself a
  small, independently testable piece — likely a new function in
  `dictk.image`, alongside `translate`/`stretch`, before `grid.locate`
  ever calls it.
- A worked example needs a *source* for $\boldsymbol{F}$ that isn't
  circular (an estimate close enough to be useful, but not so close it
  trivializes what `locate` is finding). Where that estimate comes from
  in practice is its own open question.

None of this is scoped or scheduled — this page records that the
direction exists and sketches its math, not a commitment to build it on
any timeline. Build it in pieces, each with its own tests, rather than
landing the whole API change at once: the small affine-transform helper
first, then wiring it into `grid.locate` behind the identity default,
then a worked example once both exist. See [Path
Forward](./path_forward.md#2026-08-11) for the related "dynamic
search-window sizing" direction this connects to — a better
$\boldsymbol{F}$-based guess and a smaller `search_margin` are two sides
of the same idea.

Twelve points, twelve independent correlations, each one still
sequential so far: [Parallelization](./parallelization.md) picks up
from here.
