# Detection

[Synthetic Dislocation](./synthetic_dislocation.md) and [Experimental
Dislocation](./experimental_dislocation.md) both found the same
signature. A kernel that straddles a crack shows two comparably tall
correlation peaks, not one. On both pages, a person placed the kernel
on the crack first. This page finds the crack without that step.

It tracks a full grid of points with
[`grid.locate_warp_propagated`](../api/dictk/grid.html#locate_warp_propagated)
from [Seed Propagation](./seed_propagation.md), then maps each point's
ZNSSD. An affine warp can't represent a jump in displacement. No single
warp matches both sides of a straddling kernel, so its ZNSSD can rise
above the `znssd_limit` gate of 0.3.

## A Synthetic Crack

The test reuses Synthetic Dislocation's 300x300 image, `rosta` speckle
combined with the astronaut. `crack_dislocation` splits it between
pixel columns 149 and 150. The left half moves down, and the right half
moves up. The grid holds 1849 points, 43 by 43 at 5 px spacing. It uses
Seed Propagation's margins, `kernel_margin=13` and `search_margin=25`.
Each kernel is 27 px wide, so a point straddles the crack when its x
lies between 137 and 162.

Two cases test the method. The on-grid case uses Synthetic
Dislocation's 4 px offset and puts a grid column at x = 150. The
off-grid case uses a 4.3 px offset and shifts the grid 2 px right, so
no column lines up with the crack. A subpixel offset forces
interpolation, so ZNSSD away from the crack no longer comes out exactly
zero. As a baseline, `locate_warp` from [Kernel
Warping](./kernel_warping.md) tracks the same grid without a gate:

<!-- cmdrun python3 discontinuity_detection_synthetic.py -->

Away from the crack, every point passes the gate. The largest ZNSSD
there is 0.020, and the largest error is 0.029 px. The gate rejects 162
of the 215 straddling points on-grid, and 165 of 258 off-grid.

The gate keeps the crack from spreading a bad fit. No accepted point
lands more than 1 px from its true position. Without the gate,
`locate_warp` puts 48 points more than 1 px off on-grid, and 44
off-grid. A point that no accepted fit can reach gets its own start
search, as Seed Propagation describes. No fit has to cross the crack.

Accepted straddling points pay in accuracy. They land up to 0.300 px
off, 10 times the 0.029 px largest error away from the crack. An affine
warp has no term for the jump, so it settles on a compromise between
the two sides.

The ZNSSD map finds the crack without a line chosen in advance.
[Figure](#fig-dd-synthetic) shows the off-grid case. The rejected points
form one vertical band. The column with the highest median ZNSSD sits
at x = 147, 2.5 px from the crack at x = 149.5. On-grid, it sits at
x = 150, 0.5 px away. The off-grid crack sits midway between columns
147 and 152, 2.5 px from each. No column could land closer.

<figure id="fig-dd-synthetic">
    <img src="discontinuity_detection_synthetic.png" alt="two panels over the synthetic speckle image: left, each grid point's ZNSSD as a colored square, dark purple everywhere except a vertical band of green, yellow, and red squares around x = 150; right, v at accepted points only, red on the left half and blue on the right half, with a gap where the band was" />
    <figcaption>The off-grid case: a 4.3 px offset, with no grid column on the crack. The dashed line marks the crack at x = 149.5. Left: each point's ZNSSD at its reference position, clipped at 1. Red points were never fitted. Right: v at accepted points only. The left half reads +4.3 px and the right half reads −4.3 px. The gap between them holds the points the gate rejected.</figcaption>
</figure>

## A Real Crack

The real test uses Experimental Dislocation's 512x512 micrograph pair.
No ground truth exists. The crack can't be seen in the reference image.
It shows as a diagonal band in the current image. Points also move far:
u runs from 18 to 37 px and v from 9 to 13 px. Seed Propagation's 25 px
search margin can't cover a 37 px motion. This test pairs a 27 px
kernel with a 50 px search margin, and a 51 px kernel with
Experimental Dislocation's 65 px. Both grids use 5 px spacing.

Two checks stand in for ground truth. A line fit tests whether the
rejected points form one straight band. Each row's band center is the
mean x of its rejected points, ignoring any more than 40 px from the
row's median. A neighbor check compares each accepted point with the
accepted points within 10 px on the same side of that line. A point
fails when its u or v differs from their median by more than 1 px. The
second table measures displacement across a fainter streak, described
below:

<!-- cmdrun python3 discontinuity_detection_experimental.py -->

The rejected points form one straight band. With the 27 px kernel,
573 of the 580 rejected points lie within 36 px of the fitted line.
That line runs 30.8° from vertical. Across 81 rows, the band centers
scatter 1.83 px RMS about it. The 51 px kernel gives a line at 30.7°,
and all 913 of its rejected points lie within 60 px of it.

The kernel sets the band's width. The median width is 35 px with the
27 px kernel and 60 px with the 51 px kernel. The smaller kernel leaves
580 of 6561 points without a trusted position, 8.8%. The larger one
leaves 913 of 5625, 16.2%. The smaller kernel also rejects 7 isolated
points away from the band. The larger kernel rejects none.

The gate holds on real texture. No accepted point differs from its
same-side neighbors by more than 1 px. The largest difference is
0.51 px with the 27 px kernel and 0.27 px with the 51 px kernel. With
the 27 px kernel, the lower-left side moves a median u of 19.94 px and
the upper-right side 32.33 px. The crack opens 12.39 px in u and
0.86 px in v.

[Figure](#fig-dd-experimental) also shows a fainter streak, parallel to
the crack and 155 to 185 px to its lower left. Its median ZNSSD reaches
0.130, below the 0.3 gate, so the gate rejects no point there. The
second table measures u and v across it, over a 100 px stretch along
the crack near the streak's middle. From the band 185 to 200 px from
the crack to the band 140 to 155 px from it, u rises 2.06 px and v
rises 1.62 px. Between the other adjacent bands, u changes by at most
0.39 px and v by at most 0.36 px. The streak carries a jump in u one
sixth the size of the crack's. This test can't tell a second, smaller
crack from a narrow band of concentrated strain. Either way, the 0.3
gate misses it.

<figure id="fig-dd-experimental">
    <img src="discontinuity_detection_experimental.png" alt="four panels of the real micrograph pair in a 2 by 2 grid: top left, the current image with a bright diagonal crack from upper left to lower right; top right, each grid point's ZNSSD as a colored square over the reference image, dark purple except a diagonal band of red and yellow squares along the crack, a dashed white fitted line through it, and a faint lighter streak parallel to it in the lower left; bottom left, u at accepted points only, blue on the lower-left side and red on the upper-right side, with a gap along the crack; bottom right, v at accepted points only, with the same gap along the crack and a sharp step along the streak in the lower left" />
    <figcaption>The real crack, with the 27 px kernel. Top left: the current image. Top right: each point's ZNSSD at its reference position, clipped at 1. Red points were never fitted. The dashed line is the fit to the band, x = 0.596 y + 104.6. The faint streak 155 to 185 px to its lower left stays below the 0.3 gate. Bottom left: u at accepted points only. The lower-left side moves a median 19.94 px and the upper-right side 32.33 px. Bottom right: v at accepted points only. The lower-left side moves a median 10.65 px and the upper-right side 11.51 px. v also steps along the streak, where the table above measures a 1.62 px rise.</figcaption>
</figure>

## What This Doesn't Do

Points inside the band get no trusted displacement. The band leaves a
strip 35 to 60 px wide along the crack with no data. A straight-line
fit also assumes one straight crack. A curved or branching crack would
need a different fit. Both tests here use one crack each, and the real
test has no ground truth.

Continue to [Localization](./discontinuity_localization.md).

### `discontinuity_detection_synthetic.py`

<details>
<summary>Show the code</summary>

```python
<!-- cmdrun cat discontinuity_detection_synthetic.py -->
```

</details>

### `discontinuity_detection_experimental.py`

<details>
<summary>Show the code</summary>

```python
<!-- cmdrun cat discontinuity_detection_experimental.py -->
```

</details>
