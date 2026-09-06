# Discontinuities

Every correlation criterion from [Correlation
Criteria](./correlation_criteria.md) onward, and every worked example
through [Parallelism with PyTorch](./parallelism_pytorch.md), tracks one
assumption without saying so: the true displacement field is smooth. A
kernel window moves as a rigid or gently stretching patch, and the search
for its match assumes a single answer exists.

Real specimens don't always cooperate. A crack, a slip band, or a material
interface can produce a genuine jump in displacement rather than a
gradient. [Image Transformation](./transformation.md#crack-dislocation)
already built exactly that jump:

Crack Dislocation | Image
--- | ---
Original | ![original](astronaut_crack_plain_original.png)
offset=4 pixels | ![crack dislocation](astronaut_crack_plain_dislocation.png)

A vertical crack splits the image at its vertical midline. The left half
shifts down 4 pixels. The right half shifts up 4 pixels. Standard DIC has
no way to represent that jump. Every criterion this book covers fits one
displacement per kernel, not two.

This chapter asks a narrower question than "how do you fix that." It asks
what happens first. What does a correlation surface actually look like
when a kernel window straddles a real discontinuity, rather than sitting
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
Localization](./discontinuity_localization.md) takes that on next:
comparing a few candidate algorithms and settling on one that finds
this signature by itself, without a person centering the window first.
