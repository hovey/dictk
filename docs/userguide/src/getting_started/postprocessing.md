# Postprocessing

[Prediction Improvement](./prediction_improvement.md) improved where
each tracked point lands. On the 2% stretch,
[Kernel Warping](./kernel_warping.md)'s `locate_warp` cut the $E_{11}$
standard deviation from 16531 to 1161 microstrain, against VIC-2D's
1385.

This chapter keeps those tracked positions fixed. It changes what the
book computes from them. Every strain so far came from Q4 elements.
Each element differentiates the displacements of its own four corner
points, so each strain value carries the tracking error of four
points.

* [Strain Window](./strain_window.md) fits displacement over a
  neighborhood of points before computing strain. It adds
  `dictk.strain_window`. A 15x15 window cuts the $E_{11}$ standard
  deviation from 1161 to 39 microstrain at the 1560 points with a full
  window, and to 91 microstrain across all 2862 points.
