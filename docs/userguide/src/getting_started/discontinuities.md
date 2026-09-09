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

Crack Dislocation | Image
--- | ---
Original | ![original](astronaut_crack_plain_original.png)
offset=4 pixels | ![crack dislocation](astronaut_crack_plain_dislocation.png)

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
