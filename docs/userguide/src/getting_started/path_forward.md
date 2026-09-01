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

## 2026-08-26

[High Point Density](../getting_started/high_point_density.html)'s own
closing gap — how `dictk`'s tracking time scales as point count grows,
across sequential, threaded, and multi-process execution — is answered
by a new page, [Timing at
Scale](../getting_started/timing_at_scale.html) (Parallelization's new
`9.3` child). It set out looking for this M1 Pro machine's genuine RAM
ceiling: grow a pure-`rosta` reference image (no `astronaut`, avoiding
any bicubic-upsampling artifact) along a geometric ladder, tracking the
real `grid.locate_subpixel` pipeline at each size until 32GB of RAM ran
out.

It never did. `sysctl vm.swapusage` was checked directly throughout the
entire multi-hour run and never once reported nonzero swap use, even as
peak RSS climbed to 11.5GB at the largest tier reached (10204px,
3,229,209 points). What actually stopped the ladder was this script's
own 1800-second (30-minute) per-tier timeout — a genuine compute-time wall, found
by raising that timeout once (240s → 1800s, after the first pass showed
processes and sequential both dying to it well before any memory
pressure) and hitting it again anyway. `threads` reached the furthest
(996,004 points, 861.5s) before also timing out at the next tier.
`processes` died earliest (1750px) for an unrelated, real reason: its
own `ProcessPoolExecutor.map()` re-pickles `dictk.grid.locate`'s bound
`reference_image`/`current_image` once per task, not once per worker —
confirmed directly in source, and directly observed as ~50% single-core
utilization on a retry, not eight processes computing in parallel.

This documents, with real numbers, the "documented CPU bottleneck" this
page's own GPU direction (below) has been gated on since it was first
written: reaching a million tracked points took `threads` 14.4 minutes
on 10 cores; a real problem at this page's own north-star scale (a
billion correlations) extrapolates to weeks on this same hardware. 348
tests (unchanged — docs-only, plus a new standalone benchmark script,
same precedent as `parallelization_bench.py`).

## 2026-09-01

**9.4 Parallelism with PyTorch, shipped.** New page,
[Parallelism with PyTorch](./parallelism_pytorch.md), Parallelization's
fourth child. It reruns [Timing at Scale](./timing_at_scale.md)'s own
ladder — same image sizes, same point grids, same 26x26 kernel, same
per-size search areas, same machine — on a batched PyTorch correlation
instead of one `grid.locate_subpixel` call per point. Docs-only plus a
standalone benchmark script, matching 9.3's own precedent. 348 tests
unchanged. `pyproject.toml` deliberately untouched: CI runs
`uv sync --all-extras`, so a `torch` extra would install PyTorch on
every CI run for a script CI never executes.

This continues work Andrew Polonsky and Chad Hovey started in the
private `hdic` codebase in 2025, and the page attributes it directly.
That work established the grouped-`conv2d` batching trick (stack N
search areas as channels, N kernels as N groups, `groups=N` so kernel
`i` sees window `i` only), measured it on a Windows CUDA machine, and
recorded the decision "torch implementation, then CUDA implementation"
on 2025-09-23. It left three gaps. 9.4 closes two: it runs on Apple
silicon, which `hdic`'s own correlation module refused to do via a hard
`RuntimeError("...does not run on macOS")` that was simply false; and it
refines peaks to subpixel, which that implementation never did. The FFT
gap stays open, and is now the named next step.

**A real prerequisite fix to 9.3.** [Timing at
Scale](./timing_at_scale.md#finding-the-ceiling) stated `kernel_margin=13`
and said `search_margin` varies per tier, but never gave pixel
dimensions. Adding them surfaced something that page never said: the
kernel is fixed at 26x26 at every tier, but the search area grows from
48x48 to 420x420, because `factor_x=1.02` displaces a far edge further
in a bigger image. Search pixels therefore grow 76x across the ladder,
so 9.3's cost curve is not a pure point-count curve — it measures point
count and per-correlation size growing together. Doesn't invalidate any
9.3 finding (all three executors saw identical geometry), but it
explains part of the slope, and 9.4 could not describe its own tensor
shapes without it.

**The headline result, and the caveat under it.** The Apple GPU (MPS,
Metal Performance Shaders) wins at every size. It completed 10204px —
3,229,209 points in 2,334.7s — which 9.3's `threads` attempted and could
not finish. At the largest size both pages measured (5669px, 996,004
points) it runs 3.4x faster than `threads`: 3,884 points/s against
1,156, which turns 9.3's own "roughly 1.4 weeks for a billion
correlations" into roughly 3 days. Real, and not enough — a billion is
Path Forward's entry-level target, not its ceiling.

The speedup is not constant, and the shape of it is the finding. It
climbs to 15.7x at 29,584 points, then falls to 3.4x at 996,004. Point
count only ever increased, so batching can't explain the decline. The
growing search area can, and the CPU column proves it directly.

**Polonsky's cusp, located.** His 2025-04-15 email said the team was
"right on the cusp of whether or not doing the FFT for cross-correlation
will be faster than brute force sliding dot product," and never resolved
it. 9.4 resolves it, because `torch` CPU and 9.3's `threads` run on the
same ten cores and differ only in algorithm. At a 74x74 search area,
`torch` CPU wins 7.8s to 16.9s. At 102x102 they tie, 53.4s to 58.6s. At
156x156 the FFT wins 215.2s to 512.7s. On this machine, at a 26x26
kernel, **the cusp sits near a 100x100 pixel search area.** Below it,
brute force wins; above it, the FFT does.

Which reframes 9.4's own GPU result: the GPU is running the *losing*
algorithm at these search areas and still beats ten CPU cores. Nobody
has yet combined the better hardware with the better algorithm. That
combination — a batched `torch.fft` phase correlation, the same
algorithm 9.1-9.3 already use, on the devices 9.4 already measures — is
the obvious next step and is not started.

**Subpixel came out better than expected.** A three-point parabolic fit
on the correlation surface `conv2d` already returns gives 0.0369px mean
absolute error against analytical truth, against
`grid.locate_subpixel`'s own 0.0925px at `upsample_factor=100` on the
same 2,809 points. 2.5x more accurate, for a small fraction of the
correlation's cost. Peak locking is present but mild (fractional-part
bins 330/338/258/219/280/265/210/257/313/339 against a flat 280).
Integer positions agree with `grid.locate` on 98.7% of points, and every
one of the 37 disagreements has a true fractional part between 0.460 and
0.560 — the half-pixel boundary where rounding is genuinely ambiguous,
not an error. MPS matched CPU digit for digit; float32 cost nothing
measurable.

**A prediction the measurement contradicted.** 9.4 retired 9.3's
1800-second wall clock and replaced it with a caught out-of-memory error
as the primary stop, reasoning that search areas are chunkable but the
two resident images are not, so the unchunkable part would eventually
fail. It never did. Both devices stopped on the secondary rule instead —
a predicted-cost gate, extrapolating each size from the previous size's
measured rate. At the largest size attempted, the two images occupied
0.83GB of Metal's 26.8GB budget, about 3%; peak host RSS reached 13.9GB
of 32GB. Same conclusion 9.3 reached, for the same reason: compute time
is the wall, memory is not. The OOM arithmetic still holds at around
59508px; this ladder just never gets there, because that size's
arithmetic outruns any reasonable wait.

**Two bugs found by testing rather than assuming.** Forcing an
out-of-memory on purpose revealed that Metal reports it two different
ways, and only one says "out of memory" — a single tensor past Metal's
per-buffer ceiling raises `Invalid buffer size: 3013.73 GiB` instead.
Trusting the first message would have turned a real memory finding into
an unexplained crash. Separately, a first version of the benchmark
re-uploaded both full images to the device once per chunk rather than
once per size (26 redundant 40MB uploads at 3149px), which inflated
measured extraction cost; partial results were discarded and the ladder
re-run after the fix. Both are recorded in the script's own docstrings.
