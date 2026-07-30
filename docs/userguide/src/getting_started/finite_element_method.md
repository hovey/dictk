# Finite Element Method

A finite element mesh is a collection of **nodes** (points) connected into
**elements** — small regions used to interpolate a quantity of interest
(e.g. displacement) across the whole domain. The point grid built in
[Multi-Point Motion](./multi_point_motion.md#point-grid) is exactly the
kind of nodal point collection a mesh needs, and [Tracking the
Grid](./multi_point_motion.md#tracking-the-grid) already found every one
of its 12 points' current positions — exactly the per-node displacement
data a mesh needs to represent how an object deformed.

[Tracking the Grid](./multi_point_motion.md#tracking-the-grid) already
covers the kernel-size-versus-point-spacing tradeoff involved in getting
that per-node data reliably — the same considerations apply whether the
points come from a toy grid or a real mesh.

Once every node's current position is known, an actual finite element
mesh still needs one more thing this page doesn't provide: **element
connectivity** — which nodes join together into which elements. Building
that connectivity, and the element formulation it enables (shape
functions, strain, stress), is future work, not implemented here.
