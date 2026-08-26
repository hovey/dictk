# Path Forward

This page is a running log, not a tutorial. It records forward-looking
notes as they come up — open questions, scale targets, directions worth
exploring — dated as they're written. Nothing here is implemented yet
unless the note says so.

## 2026-08-11

**North star.** DIC at real finite-element-mesh scale eventually means
at least a billion correlations. Realistically, tens of billions. The
working assumption is that this stays under a trillion — that's the
ceiling to design for, not a target to reach.

**Four directions worth exploring**, in the order we'll likely take
them:

1. **GPU implementations.** [Parallelization](./parallelization.md)
   only covers CPU-bound threads and processes so far. GPU work is
   still explicitly deferred until a documented CPU bottleneck exists
   (see the parallelism roadmap referenced there) — this note doesn't
   change that. It's on the list for when that bottleneck shows up.
2. **Dynamic search-window sizing.** Every worked example so far uses a
   fixed, generously-sized search area per point.
   [Parallelization](./parallelization.md#measuring-the-trade-space)'s
   own measurements found that per-correlation size, not point count
   alone, is the dominant cost lever. A search window only as large as
   it needs to be — sized from a prior displacement estimate rather
   than a fixed worst-case margin — shrinks that per-correlation cost
   directly, for every point in a mesh, not just the parallelizable
   part of the problem.
3. **Pure rotation.** [Rigid Body Motion](./rigid_body_motion.md) and
   the polar decomposition ($\boldsymbol{F} = \boldsymbol{R}\boldsymbol{U}$,
   see [Continuum Mechanics](./continuum_mechanics.md#polar-decomposition))
   already separate rotation from stretch: a pure rotation carries zero
   strain by construction. Two things worth testing empirically, not
   just assuming from the closed-form math: how large a rigid-body
   rotation angle `dictk`'s own correlation-based tracking can actually
   recover before it breaks down — a large enough rotation distorts a
   kernel's own content beyond what a translation-only search can still
   match — and confirming a correctly-tracked pure rotation reports
   zero strain end to end, not just in theory.
4. **Synthetic dataset comparison to XCorrel and VIC-2D.** Run the same
   synthetic datasets this book already uses through both tools, and
   compare their reported displacements and strain against `dictk`'s
   own. A synthetic dataset has a known, exact ground truth — the same
   trick every worked example in this book already relies on — so this
   is a direct, numeric check against established DIC software, not
   just a qualitative one.

**A practical constraint to design around**: real DIC data typically
uses kernel sizes from about 35x35 pixels on the small end up to about
50x50 pixels on the large end. Every benchmark or worked example aimed
at "realistic" DIC scale should stay inside that range, not the
40-pixel figure this book's own teaching examples happen to use.

**Heaviside DIC and XFEM.** Every correlation technique this book
covers assumes a smooth displacement field. Real specimens don't
always deform smoothly — a crack or a material interface can produce a
genuine discontinuity, a jump rather than a gradient. [Image
Transformation](./transformation.md#crack-dislocation) already
generates a synthetic example of exactly that jump, and names the
reason: standard DIC can't capture it, and cases like it motivate the
Heaviside finite-element formulation. XFEM handles this on the finite
element side by enriching the basis with Heaviside step functions, so
the mesh doesn't need to conform to the crack. The DIC-side analogue —
enriching the correlation itself to detect and locate a discontinuity,
not just generating test images that contain one — is worth exploring.
Not scoped yet.

## 2026-08-14

**Re-running The First Sweep after the centered-padding fix: checked,
not automatically fixed.** [Recoverable Displacement
Range](./recoverable_displacement_range.md#the-first-sweep)'s own
opening sweep sizes `search_margin_width` generously for every
percentage tested — always larger than the true displacement — so it
was never hitting the asymmetric-padding bug that page's fix
addresses. Re-ran it against the fixed `locate()` to check directly,
rather than assume: the collapse is identical to before the fix —
12/12, 12/12, 10/12, 6/12, 1/12, 1/12, 0/12, 0/12 for
$p = 2, 4, 6, 8, 18, 20, 40, 80$. The real cause is still [the
interpolation confound that page already
names](./recoverable_displacement_range.md#an-interpolation-confound-set-aside):
`stretch`'s own bilinear interpolation subtly blurs kernel-surrounding
texture even where a point's center pixel lands on an exact integer,
producing near-miss failures — not the wraparound cliff the fix
resolved. Confirms the Postponed subpixel-accuracy item below is still
the right next step here, not something this fix already covered.

### Postponed

Noted, not being pursued right now:

* **Heaviside DIC and XFEM** — enriching the correlation itself to
  detect and locate a discontinuity, not just generating test images
  that contain one (see above).
* **`grid.locate()` windowing demo.** `windowing` has only ever been
  demonstrated directly on
  [`dictk.correlation.phase_correlation`](../api/dictk/correlation.html#phase_correlation)
  (see [Correlation
  Visualization](./correlation_visualization.md#phase-correlation)).
  Every
  `grid.locate()` call across the book so far (Multi-Point Motion,
  Simple Stretch, Recoverable Displacement Range, Pure Rotation,
  Parallelization) leaves `windowing` at its default `None` — the one
  parameter of `grid.locate`'s own signature with no live worked
  example yet.

## 2026-08-18

**Pure Rotation: The First Sweep.** New page, [Pure
Rotation](./pure_rotation.md), starts checking direction 3 above
empirically. Its First Sweep reuses [Point
Grid](./multi_point_motion.md#point-grid)'s 12-point grid and sweeps
`rotate`'s angle, sizing `search_margin` generously at every step so
window size can't be the limiting factor — the same approach
[Recoverable Displacement
Range](./recoverable_displacement_range.md#the-first-sweep) used.
Matching collapses even faster than that page's stretch sweep did: well
under half the points still match by 2 degrees, none by 8 degrees. The
likely cause, already named in this page's own direction-3 note above,
isn't confirmed yet — a large enough rotation turns a kernel's own
content around a point, not just moves it, and a translation-only
search can't follow that. Checking that hypothesis directly is the next
step here, not started yet.

**Pure Rotation: hypothesis confirmed.** Same page, new [Confirming the
Content-Rotation
Hypothesis](./pure_rotation.md#confirming-the-content-rotation-hypothesis)
section. Two direct checks: handing `locate` the exact true search
center instead of a generous margin barely changes the collapse,
ruling out search mechanics; and a plain `zncc` similarity score
between the reference kernel and the true-aligned current-image patch
(no search at all) falls off steeply with angle, confirming the real
cause is content, not search. One thing this doesn't separate out yet:
`rotate` shares `stretch`'s bilinear interpolation, and [Recoverable
Displacement
Range](./recoverable_displacement_range.md#an-interpolation-confound-set-aside)
already found interpolation blur alone can look similar — genuine
geometric content rotation and interpolation blur are likely both
compounding here. Telling them apart is the next open step, not
started.

## 2026-08-20

**Postponed subpixel accuracy item, resolved.** [Simple Stretch
Revisited](./simple_stretch.md#simple-stretch-revisited) found the
concrete trigger this Postponed item's own wording anticipated: at
`factor_x = 1.02`, only points whose `x` is a multiple of 50 land on
an integer pixel in the deformed configuration. A denser grid mostly
doesn't. New [Subpixel
Accuracy](./subpixel_accuracy.md) page: `dictk.translation.locate_subpixel`
and `dictk.grid.locate_subpixel`, exposing
`phase_cross_correlation`'s own `upsample_factor` — separate functions
from `locate`/`grid.locate`, not a parameter added to them, returning
a new `dictk.image.SubpixelCoordinate` (float `x`/`y`) instead of
`PixelCoordinate`. Measured directly against VIC-2D's own 2862-point
grid: `upsample_factor` doesn't make `locate`'s truncated integer
answer more often correct (the true target usually isn't an integer at
that density, so no refinement changes that) — but it substantially
improves how close the tracked position lands to the true, generally
fractional, target (mean absolute error 0.26px at `upsample_factor=1`,
down to 0.09px at `10`). Parallelization (9) gains this as its first
child, 9.1; a second child, 9.2 High Point Density, picking the same
subpixel tooling up at real density, is the planned next step, not
started yet.

## 2026-08-24

**9.2 High Point Density, shipped.** New page, [High Point
Density](./high_point_density.md), closes the 9.1/9.2 pair under
[Parallelization](./parallelization.md). It pushes `grid.locate_subpixel`
to VIC-2D's own point density: 2862 points, 5px spacing, 2756 elements.
No new library code — it composes entirely from already-shipped
functions, the same way [Simple Stretch
Revisited](./simple_stretch.md#simple-stretch-revisited) did.

A real finding came out of it, verified before writing anything up.
The strain field isn't clean at this density. Mean E11 still tracks
the true value closely (0.0199 vs. 0.0198), but individual elements
scatter widely (std 0.0155, range -0.016 to 0.077). A live 4-point
spacing sweep (5/10/20/40px) confirmed the mechanism directly: strain
noise scales with displacement-noise divided by element size, so the
same small subpixel tracking residual gets amplified more at smaller
spacing. Std shrinks monotonically across the sweep
(0.0154/0.0125/0.0099/0.0032). The page names VIC-2D's own
strain-window averaging as the standard remedy but doesn't implement
it — that stays open.

## 2026-08-25

**High Point Density retuned to VIC-2D's real geometry, plus a
quantization finding.** [High Point Density](./high_point_density.md)'s
tracking call used a much larger kernel/search area than VIC-2D's own
`25 x 25` px subset — leftover from earlier pages, never tuned to
match. `kernel_margin = 12` (the closest whole-pixel match) was tried
first and rejected: checked directly against known true positions, it
produced real multi-pixel mismatches at a handful of points, not just
subpixel noise. `kernel_margin = 13` (`26 x 26` px) tracks cleanly,
zero mismatches across all 2862 points; `search_margin = 25` gives
generous headroom.

A second, unplanned finding came out of building the page's new
strain histogram (the `dictk`-side counterpart to [Verification
Against VIC-2D](./simple_stretch.md#verification-against-vic-2d)'s
own VIC-2D histogram). At `upsample_factor = 10` — Subpixel Accuracy's
own choice — the histogram wasn't a smooth spread; it separated into
sharp spikes exactly 20000 microstrain apart. Checked directly: `0.1`px
(the displacement quantization step at `upsample_factor = 10`) divided
by this mesh's own 5px element spacing is exactly `0.02`, i.e. 20000
microstrain — the artifact was `upsample_factor` itself, invisible in
Subpixel Accuracy's own raw-displacement measurement but amplified into
visible banding once divided by a small element size to get strain.
`upsample_factor = 100` removes the banding; mean and std barely move
(std 17776 → 16531 microstrain), confirming the real spread was already
there and only its blocky shape was artificial.

With both fixed, the real numbers: mean $E_{11}$ = 20464.3 microstrain
vs. the analytical 19802.6 (3.3% off, worse than VIC-2D's own 0.4%);
std 16531 microstrain; range -16446 to 106134 microstrain, over 21x
VIC-2D's own roughly 5800-microstrain-wide spread. The page's own
closing analysis ties this to kernel size directly: matching VIC-2D's
small subset, instead of earlier pages' generously oversized kernels,
trades away some of the noise-averaging a bigger kernel provides — part
of `dictk`'s own extra spread here is the expected cost of matching
VIC-2D's geometry, not a `dictk`-specific shortcoming.

A new figure places the two fields side by side, both forced onto
VIC-2D's own fixed colorbar (`17560`-`22360` microstrain) — not an
approximate rainbow,
but VIC-2D's own particular 16-band palette, sampled pixel-by-pixel
from its own legend image and rebuilt as a `matplotlib` `ListedColormap`.
Forced onto that same narrow range, only 9.5% of `dictk`'s own 11024
Gauss points land inside it; 52.9% clip to the floor, 37.7% to the
ceiling — visual, not just numeric, confirmation of how much wider
`dictk`'s own spread is. The figure's own `figsize` is tuned
(`(6.9, 6.0)`) to match VIC-2D's screenshot's own aspect ratio, so the
two panels align in height in the page's side-by-side flex layout.

[`element_strain_plot`](../api/dictk/plot.html#element_strain_plot)
gained four new keyword-only parameters this session, each
default-preserving for every existing caller: `dot_size` (default
`150`), `vmin`/`vmax` (fixed color-scale bounds, for the VIC-2D
comparison above), `show_mesh_lines` (default `True`), and `marker`
(default `"o"`) — `cmap` also widened to accept a `Colormap` instance,
not just a name, for the extracted VIC-2D palette. All three of this
page's dense figures now use `dot_size=6`, `marker="s"`, and
`show_mesh_lines=False`: square markers tile a regular grid edge to
edge with no gaps, where circles — even sized to just touch — leave
small diamond-shaped gaps at their own tangent points; mesh lines add
clutter without information at this density. 348 tests (343 + 5 new).
