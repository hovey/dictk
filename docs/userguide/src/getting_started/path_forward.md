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
* **Subpixel accuracy (upsampling).** Every worked example in this book
  is deliberately built around a known, exact-integer-pixel ground
  truth (see [Single Point
  Motion](./single_point_motion.md#current-configuration-and-displacement)),
  so `dictk`'s correlation results have never needed anything past
  whole-pixel accuracy. `skimage.registration.phase_cross_correlation`
  already supports an `upsample_factor` parameter for sub-pixel
  registration; `dictk` doesn't expose it yet. Real, non-synthetic
  displacements won't land on exact pixels, so this becomes necessary
  once the book moves past known-integer test cases.

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
