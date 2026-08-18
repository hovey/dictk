# Pure Rotation

How large a rigid-body rotation angle can
`dictk`'s correlation-based tracking actually recover before it breaks
down? [Rigid Body Motion](./rigid_body_motion.md) and the polar
decomposition ($\boldsymbol{F} = \boldsymbol{R}\boldsymbol{U}$, see
[Continuum Mechanics](./continuum_mechanics.md#polar-decomposition))
already separate rotation from stretch in theory — a pure rotation
carries zero strain by construction. This page starts checking that
against real tracking, not just the closed-form math.

## The First Sweep

Reuse [Point Grid](./multi_point_motion.md#point-grid)'s 12 points and
sweep `rotate`'s `angle` upward. `rotate` pivots on the image's
top-left corner (0, 0), so each point's expected position after
rotation comes from the standard rotation matrix applied to its own
$(X, Y)$ coordinate — not a fixed displacement, since points farther
from the pivot sweep a wider arc for the same angle. Size
`search_margin_width`/`search_margin_height` per angle so they always
comfortably contain the farthest point's displacement, the same
generous-margin approach [Recoverable Displacement
Range](./recoverable_displacement_range.md#the-first-sweep) used:

```python
from dictk.image import read, rotate, PixelCoordinate
from dictk.grid import generate, locate
import numpy as np

reference_image = read(path="astronaut0.png")
points = generate(
    origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55
)
kernel_margin = 20

def expected_position(pt, angle_deg):
    theta = np.deg2rad(angle_deg)
    c, s = np.cos(theta), np.sin(theta)
    x = c * pt.x - s * pt.y
    y = s * pt.x + c * pt.y
    return PixelCoordinate(x=int(round(x)), y=int(round(y)))

for angle in [0.5, 1, 1.5, 2, 3, 5, 8, 15]:
    current_image = rotate(arr=reference_image, angle=angle)
    expected = [expected_position(pt, angle) for pt in points]
    max_disp = max(max(abs(e.x - pt.x), abs(e.y - pt.y)) for pt, e in zip(points, expected))
    search_margin = max(int(max_disp) + 15, kernel_margin + 10)
    found = locate(
        reference_image=reference_image, current_image=current_image, reference_points=points,
        kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin,
        search_margin_width=search_margin, search_margin_height=search_margin,
    )
    n_match = sum(1 for f, e in zip(found, expected) if f == e)
    print(f"{angle}deg  search_margin={search_margin}  matched={n_match}/12")
```

<!-- cmdrun python3 -c "from dictk.image import read, rotate, PixelCoordinate; from dictk.grid import generate, locate; import numpy as np; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; expected_position = lambda pt, a: PixelCoordinate(x=int(round(np.cos(np.deg2rad(a))*pt.x - np.sin(np.deg2rad(a))*pt.y)), y=int(round(np.sin(np.deg2rad(a))*pt.x + np.cos(np.deg2rad(a))*pt.y))); print('| Angle (deg) | search_margin | Matched |'); print('|---|---|---|'); [print(f'| {angle} | {sm} | {nm}/12 |') for angle in [0.5, 1, 1.5, 2, 3, 5, 8, 15] for expected in [[expected_position(pt, angle) for pt in points]] for max_disp in [max(max(abs(e.x-pt.x), abs(e.y-pt.y)) for pt,e in zip(points, expected))] for sm in [max(int(max_disp)+15, kernel_margin+10)] for found in [locate(reference_image=reference_image, current_image=rotate(arr=reference_image, angle=angle), reference_points=points, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=sm, search_margin_height=sm)] for nm in [sum(1 for f,e in zip(found,expected) if f==e)]]" -->

Matching collapses even faster than [Recoverable Displacement
Range](./recoverable_displacement_range.md#the-first-sweep)'s stretch
sweep did — well under half the points still match by 2 degrees, and
none do by 8 degrees. `search_margin` is generous at every angle here,
so window size isn't the constraint. 
A likely reason: a large enough rotation doesn't just move a
point, it turns the kernel's own content around that point, and a
translation-only search can't follow content that's rotating, not just
sliding. The next two sections test that directly.

## Confirming the Content-Rotation Hypothesis

### Removing the Search Itself

The First Sweep's `search_margin` is generous, but it's still a guess —
`locate` still has to search for the right answer within that margin.
Remove that variable entirely: pass `search_centers` the true expected
position directly, so `locate` doesn't have to search at all, and shrink
the margin down to a fixed, minimal size:

<!-- cmdrun python3 -c "from dictk.image import read, rotate, PixelCoordinate; from dictk.grid import generate, locate; import numpy as np; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; tiny_margin = kernel_margin + 10; expected_position = lambda pt, a: PixelCoordinate(x=int(round(np.cos(np.deg2rad(a))*pt.x - np.sin(np.deg2rad(a))*pt.y)), y=int(round(np.sin(np.deg2rad(a))*pt.x + np.cos(np.deg2rad(a))*pt.y))); print('| Angle (deg) | Matched |'); print('|---|---|'); [print(f'| {angle} | {nm}/12 |') for angle in [0.5, 1, 1.5, 2, 3, 5, 8, 15] for expected in [[expected_position(pt, angle) for pt in points]] for found in [locate(reference_image=reference_image, current_image=rotate(arr=reference_image, angle=angle), reference_points=points, search_centers=expected, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=tiny_margin, search_margin_height=tiny_margin)] for nm in [sum(1 for f,e in zip(found,expected) if f==e)]]" -->

Nearly the same collapse, at nearly the same angles, as the First
Sweep's generous-margin version. Handing `locate` the exact right
answer barely helps. Search mechanics — margin size, centering guesses
— were never the constraint.

### Measuring Content Similarity Directly

If the search itself isn't the problem, the content being matched is.
Set that up as a direct measurement, with no search or `locate` call at
all: extract the kernel from `reference_image` at each point, extract
the same-sized patch from the rotated `current_image` at that point's
*exact* true position, and score their similarity with
[`dictk.correlation.zncc`](./correlation_criteria.md), which is exactly
1.0 for identical content and falls toward 0 (or negative) as content
diverges:

<!-- cmdrun python3 -c "from dictk.image import read, rotate, PixelCoordinate, subimage; from dictk.grid import generate; from dictk.correlation import zncc; import numpy as np; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; expected_position = lambda pt, a: PixelCoordinate(x=int(round(np.cos(np.deg2rad(a))*pt.x - np.sin(np.deg2rad(a))*pt.y)), y=int(round(np.sin(np.deg2rad(a))*pt.x + np.cos(np.deg2rad(a))*pt.y))); patch = lambda img, c, m: subimage(image=img, origin=PixelCoordinate(x=c.x-m, y=c.y-m), width=2*m, height=2*m); print('| Angle (deg) | Mean ZNCC | Min ZNCC |'); print('|---|---|---|'); [print(f'| {angle} | {scores.mean():.3f} | {scores.min():.3f} |') for angle in [0, 0.5, 1, 1.5, 2, 3, 5, 8, 15] for current_image in [rotate(arr=reference_image, angle=angle)] for scores in [np.array([zncc(kernel=patch(reference_image, pt, kernel_margin), search=patch(current_image, expected_position(pt, angle), kernel_margin))[0,0] for pt in points])]]" -->

Similarity falls off steeply and smoothly with angle, with zero search
involved at all — this is the exact correct alignment, every time. By 8
degrees, mean similarity has already dropped to about half; by 15, some
points score negative, meaning the rotated patch is anti-correlated
with the original, not just a weaker match. That confirms the
hypothesis directly: a rotated kernel's content genuinely stops
resembling itself, at exactly the position where it should match
perfectly. This isn't a search, margin, or centering-guess problem —
it's that the content itself has changed shape.

One thing this doesn't separate out: `rotate` uses the same bilinear
interpolation as `stretch`, and [Recoverable Displacement
Range](./recoverable_displacement_range.md#an-interpolation-confound-set-aside)
already found interpolation blur alone can cause a similar-looking
near-miss failure. A genuinely rotated feature (say, a straight edge
tilted a few degrees) looks different from the original even with
perfect, blur-free resampling — so both effects are likely compounding
here, not just one. Telling those two contributions apart is a
reasonable next step, not done yet.
