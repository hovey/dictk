# Prediction Improvement

[Search Center Predictions](./search_center_predictions.md) improved
where each search starts. This chapter improves what each search
returns: the point's predicted position in the current image.

Chapter 8 never had to report a position between pixels. It avoided
that in two ways. [Simple Stretch](./simple_stretch.md) stretched the
image by $\text{factor}_x = 1.02$ and placed every point at an $x$ that is a
multiple of 50. Only those $x$ values stretch onto whole pixels. That
kept [`dictk.translation.locate`](../api/dictk/translation.html#locate)
exact, because `locate` returns whole pixels only. It also capped the
grid, at 12 points and then 250 in [Simple Stretch
Revisited](./simple_stretch.html#simple-stretch-revisited). [Pure
Rotation](./pure_rotation.md) took the other way. It rounded each
rotated point's true position to the nearest pixel before scoring
`locate` against it.

VIC-2D measured the same stretch on a 53x54 grid, 5 px apart, starting
at $x = 18$. No $x$ on that grid is a multiple of 50. So every one of
its 2862 true positions falls between pixels. `locate` can only report
a whole pixel, so it misses every one of them. A real specimen poses the same problem.
Its displacements don't land on whole pixels either.

The four pages of this chapter take that on in order:

* [Subpixel Accuracy](./subpixel_accuracy.md) adds `locate_subpixel`,
  which returns a fractional position. On the 2862-point grid, it cuts
  `locate`'s mean position error by about a third.
* [High Point Density](./high_point_density.md) computes strain from
  all 2862 tracked points. That strain spreads far wider than VIC-2D's:
  `dictk`'s $E_{11}$ ranges from about -16400 to 106100 microstrain, more than 21
  times VIC-2D's own range of about 17300 to 23100.
* [Kernel Warping](./kernel_warping.md) traces that spread to an error
  in `locate_subpixel` tied to where each true position falls within
  its pixel. It adds `locate_warp`, which lets the kernel stretch and
  shear along with the material. The $E_{11}$ standard deviation falls
  from 16531 to 1161 microstrain, against VIC-2D's 1385.
* [Strain Window](./strain_window.md) is a placeholder for fitting
  displacement over a neighborhood of points before computing strain.
