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

**Two avenues toward that**, in the order we'll likely explore them:

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
