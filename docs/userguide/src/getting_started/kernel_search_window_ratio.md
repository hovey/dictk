# Recoverable Displacement Range

[Simple Stretch](./simple_stretch.md) raised a natural follow-up
question: how far can `astronaut0` be stretched, or compressed, before
`locate` stops finding the exact expected position? The investigation
that followed didn't answer that question directly. It found something
more fundamental first — a real, silent bug in `locate` itself, now
fixed. This page chronicles how.

## The First Sweep

Reuse [Point Grid](./multi_point_motion.md#point-grid)'s 12 points and
sweep `factor_x` upward, sizing `search_margin_width` per factor so it
always comfortably contains the largest point's displacement — wide
enough that "the window was too small" can't explain a failure:

```python
from dictk.image import read, stretch, PixelCoordinate
from dictk.grid import generate, locate

reference_image = read(path="astronaut0.png")
points = generate(
    origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55
)
kernel_margin = 20

for p in [2, 4, 6, 8, 18, 20, 40, 80]:
    factor_x = 1 + p / 100
    current_image = stretch(arr=reference_image, factor_x=factor_x)
    max_disp = max(abs(pt.x * (factor_x - 1)) for pt in points)
    search_margin_width = max(int(max_disp) + 15, kernel_margin + 10)
    found = locate(
        reference_image=reference_image, current_image=current_image, reference_points=points,
        kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin,
        search_margin_width=search_margin_width, search_margin_height=52,
    )
    expected = [PixelCoordinate(x=int(pt.x * factor_x), y=pt.y) for pt in points]
    n_match = sum(1 for f, e in zip(found, expected) if f == e)
    print(f"{p:3d}%  search_margin_width={search_margin_width:4d}  matched={n_match:2d}/12")
```

<!-- cmdrun python3 -c "from dictk.image import read, stretch, PixelCoordinate; from dictk.grid import generate, locate; reference_image = read(path='astronaut0.png'); points = generate(origin=PixelCoordinate(x=50, y=50), count_x=3, count_y=4, spacing_x=50, spacing_y=55); kernel_margin = 20; print('| Stretch | factor_x | search_margin_width | Matched |'); print('|---|---|---|---|'); [print(f'| {p}% | {1+p/100:.2f} | {max(int(max(abs(pt.x * ((1+p/100) - 1)) for pt in points)) + 15, kernel_margin + 10)} | {sum(1 for f, e in zip(locate(reference_image=reference_image, current_image=stretch(arr=reference_image, factor_x=1+p/100), reference_points=points, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=max(int(max(abs(pt.x * ((1+p/100) - 1)) for pt in points)) + 15, kernel_margin + 10), search_margin_height=52), [PixelCoordinate(x=int(pt.x * (1+p/100)), y=pt.y) for pt in points]) if f == e)}/12 |') for p in [2, 4, 6, 8, 18, 20, 40, 80]]" -->

Matching collapses almost immediately — well before 20% stretch. That's
surprising: at this book's own 40-pixel kernel scale, a real
degradation-driven failure shouldn't set in this early.

## Two Hypotheses, Both Ruled Out

Two mechanisms seemed likely going in.

### Hypothesis 1: Blur

`stretch` uses bilinear interpolation, sampling an increasingly small
crop of the original image to fill the same canvas. Whole-image
contrast does drop as `factor_x` grows — but only mildly, from a
standard deviation of 63.8 at `factor_x=1.0` to 58.1 even at
`factor_x=3.0`. Not a collapse.

That claim is a whole-image statistic. Seeing it directly, side by
side with the image it's measuring, makes it concrete rather than
just asserted:

```python
import matplotlib.pyplot as plt
from dictk.image import read, stretch

reference_image = read(path="astronaut0.png")
factors = [1.0, 1.5, 2.0, 3.0]

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, axes = plt.subplots(2, len(factors), figsize=(11, 5.8), constrained_layout=True)
for col, factor_x in enumerate(factors):
    img = stretch(arr=reference_image, factor_x=factor_x)
    mean, std = img.mean(), img.std()

    axes[0, col].imshow(img, cmap="gray", vmin=0, vmax=255)
    axes[0, col].set_title(f"factor_x={factor_x:.1f}\nstd={std:.1f}", fontsize=10)
    axes[0, col].set_xticks([])
    axes[0, col].set_yticks([])

    ax_hist = axes[1, col]
    counts, _, _ = ax_hist.hist(img.ravel(), bins=50, range=(0, 255), color="black", alpha=0.7)
    y_bracket = counts.max() * 1.12
    ax_hist.axvline(mean - std, color="tab:red", linestyle="--", linewidth=1)
    ax_hist.axvline(mean + std, color="tab:red", linestyle="--", linewidth=1)
    ax_hist.annotate(
        "",
        xy=(mean - std, y_bracket),
        xytext=(mean + std, y_bracket),
        arrowprops=dict(arrowstyle="<->", color="tab:red"),
    )
    ax_hist.text(mean, y_bracket * 1.06, f"±1 std = {std:.1f}", ha="center", va="bottom", fontsize=8, color="tab:red")
    ax_hist.set_ylim(0, y_bracket * 1.35)
    ax_hist.set_xlim(0, 255)
    ax_hist.set_xlabel("pixel value", fontsize=8)
fig.savefig("kernel_search_window_ratio_blur.png", dpi=300)
```

<!-- cmdrun python3 -c "import matplotlib.pyplot as plt; from dictk.image import read, stretch; plt.rcParams.update({'font.family': 'serif', 'mathtext.fontset': 'cm'}); reference_image = read(path='astronaut0.png'); factors = [1.0, 1.5, 2.0, 3.0]; fig, axes = plt.subplots(2, len(factors), figsize=(11, 5.8), constrained_layout=True); [ (lambda img, mean, std, col=col, factor_x=factor_x: (axes[0, col].imshow(img, cmap='gray', vmin=0, vmax=255), axes[0, col].set_title(f'factor_x={factor_x:.1f}\nstd={std:.1f}', fontsize=10), axes[0, col].set_xticks([]), axes[0, col].set_yticks([]), (lambda counts: (lambda y_bracket: (axes[1, col].axvline(mean - std, color='tab:red', linestyle='--', linewidth=1), axes[1, col].axvline(mean + std, color='tab:red', linestyle='--', linewidth=1), axes[1, col].annotate('', xy=(mean - std, y_bracket), xytext=(mean + std, y_bracket), arrowprops=dict(arrowstyle='<->', color='tab:red')), axes[1, col].text(mean, y_bracket * 1.06, f'±1 std = {std:.1f}', ha='center', va='bottom', fontsize=8, color='tab:red'), axes[1, col].set_ylim(0, y_bracket * 1.35)))(counts.max() * 1.12))(axes[1, col].hist(img.ravel(), bins=50, range=(0, 255), color='black', alpha=0.7)[0]), axes[1, col].set_xlim(0, 255), axes[1, col].set_xlabel('pixel value', fontsize=8)))(stretch(arr=reference_image, factor_x=factor_x), stretch(arr=reference_image, factor_x=factor_x).mean(), stretch(arr=reference_image, factor_x=factor_x).std()) for col, factor_x in enumerate(factors) ]; fig.savefig('kernel_search_window_ratio_blur.png', dpi=300); print('Saved: kernel_search_window_ratio_blur.png')" -->

<figure>
    <img src="kernel_search_window_ratio_blur.png" alt="astronaut0 stretched at factor_x 1.0, 1.5, 2.0, and 3.0, with each image's pixel-value histogram below it, each histogram marked with a red bracket showing the ±1 standard deviation span narrowing from 63.8 to 58.2" />
    <figcaption>Top: <code>astronaut0</code> stretched at four factors. Bottom: each one's own pixel-value histogram, with a red bracket marking the ±1 standard deviation span. The images show <em>where</em> the blur comes from — horizontal streaking, since <code>stretch</code> only resamples along $x$ — but the bracket confirms it's mild: the span narrows only slightly as standard deviation drops from 63.8 to 58.2, nowhere near the collapse the first sweep showed at just 6-8%.</figcaption>
</figure>

There's also a theoretical reason this mild blur shouldn't move the peak
at all. `locate`'s [phase normalization](./correlation_criteria.md#fourier-domain)
divides out signal strength at every frequency and keeps only direction.
Blurring changes strength, not direction — the same property that already
makes `locate` insensitive to contrast. Only heavy blur eventually breaks
that guarantee in practice, since real images pad and round at their
edges instead of matching the idealized math exactly. `stretch` never
reaches that regime at these factors.

### Hypothesis 2: Canvas Exit

`stretch` pivots at the origin, so a point far enough from it can be
pushed past the image's fixed 300-pixel edge. For $x=150$ (this grid's
maximum $x$ dimension) that doesn't happen until `factor_x=2.0` — 100%
stretch, long after the matching collapse above.

Plotting that point's *expected* position directly on each stretched
image makes the exit itself visible, not just computed:

```python
import matplotlib.pyplot as plt
from dictk.image import read, stretch

reference_image = read(path="astronaut0.png")
height, width = reference_image.shape
p_x, p_y = 150, 50  # the grid's farthest point from the origin
factors = [1.0, 1.5, 2.0, 2.5]

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, axes = plt.subplots(1, len(factors), figsize=(11, 3.4), constrained_layout=True)
for ax, factor_x in zip(axes, factors):
    img = stretch(arr=reference_image, factor_x=factor_x)
    x_expected = p_x * factor_x
    on_canvas = x_expected < width

    ax.imshow(img, cmap="gray", vmin=0, vmax=255, extent=[0, width, height, 0])
    ax.axvline(width, color="tab:red", linestyle="--", linewidth=1)
    ax.plot(x_expected, p_y, marker="+", color="tab:orange", markersize=10, markeredgewidth=2.5)
    ax.set_xlim(-20, 400)
    ax.set_ylim(height + 20, -20)
    status = "on canvas" if on_canvas else "OFF CANVAS"
    ax.set_title(f"factor_x={factor_x:.1f}\nx={x_expected:.0f}  ({status})", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
fig.savefig("kernel_search_window_ratio_canvas_exit.png", dpi=300)
```

<!-- cmdrun python3 -c "import matplotlib.pyplot as plt; from dictk.image import read, stretch; plt.rcParams.update({'font.family': 'serif', 'mathtext.fontset': 'cm'}); reference_image = read(path='astronaut0.png'); height, width = reference_image.shape; p_x, p_y = 150, 50; factors = [1.0, 1.5, 2.0, 2.5]; fig, axes = plt.subplots(1, len(factors), figsize=(11, 3.4), constrained_layout=True); [ (lambda img, x_expected, on_canvas, ax=ax, factor_x=factor_x: (ax.imshow(img, cmap='gray', vmin=0, vmax=255, extent=[0, width, height, 0]), ax.axvline(width, color='tab:red', linestyle='--', linewidth=1), ax.plot(x_expected, p_y, marker='+', color='tab:orange', markersize=10, markeredgewidth=2.5), ax.set_xlim(-20, 400), ax.set_ylim(height + 20, -20), ax.set_title(f'factor_x={factor_x:.1f}\nx={x_expected:.0f}  ({\"on canvas\" if on_canvas else \"OFF CANVAS\"})', fontsize=10), ax.set_xticks([]), ax.set_yticks([])))(stretch(arr=reference_image, factor_x=factor_x), p_x * factor_x, p_x * factor_x < width) for ax, factor_x in zip(axes, factors) ]; fig.savefig('kernel_search_window_ratio_canvas_exit.png', dpi=300); print('Saved: kernel_search_window_ratio_canvas_exit.png')" -->

<figure>
    <img src="kernel_search_window_ratio_canvas_exit.png" alt="astronaut0 stretched at factor_x 1.0, 1.5, 2.0, and 2.5, with an orange marker showing where the x=150 point is expected to land; the marker moves right with each stretch, sits exactly on the canvas edge at factor_x=2.0, and floats clearly outside the image at factor_x=2.5" />
    <figcaption>The $x=150$ point's expected position (orange marker), plotted directly on each stretched image. The dashed red line marks the canvas's own right edge. The marker sits exactly on that edge at <code>factor_x=2.0</code> — the threshold the text above states — and floats clearly outside the image by <code>factor_x=2.5</code>. That threshold sits far past the collapse the first sweep showed at just 6-8%, ruling canvas exit out too.</figcaption>
</figure>

Neither blur nor canvas exit explains a collapse at 6-8%. Something else
is going on, and it isn't image degradation.

## An Interpolation Confound, Set Aside

Chasing the real cause directly through `stretch` turned out to be the
wrong tool: even at a percentage chosen so a point's *center* pixel
lands on an exact integer, bilinear interpolation still resamples
every *other* pixel in that point's kernel from a fractional source
coordinate. The center matches; the kernel's surrounding texture is
subtly blurred anyway, in a way that grows with `factor_x`. That's a
real phenomenon — related to [Path Forward's Postponed subpixel-accuracy
item](./path_forward.md#2026-08-11) — but a second, separate one from
whatever is causing the sharp, early collapse above. Isolating the real
cause means removing this confound entirely: pure integer-pixel
[`translate`](../api/dictk/image.html#translate) instead of `stretch`,
where every pixel maps from an exact integer source coordinate and
bilinear interpolation never activates at all.

## Isolating the Real Variable

The first guess was the kernel-to-search-window size *ratio*. It's
wrong — a small, fixed, well-within-bounds displacement succeeds at
every ratio tested, from a comfortable 0.67 down to a razor-thin 0.10:

```python
from dictk.image import read, translate, PixelCoordinate
from dictk.translation import locate

reference_image = read(path="astronaut0.png")
p0 = PixelCoordinate(x=150, y=150)
dx = 10
current_image = translate(arr=reference_image, dx=dx, dy=0)
expected = PixelCoordinate(x=p0.x + dx, y=p0.y)

for kernel_margin in [15, 20, 25, 30]:
    for search_margin in [kernel_margin + 15, kernel_margin + 80]:
        found = locate(
            reference_image=reference_image, current_image=current_image,
            reference_point=p0, search_center=p0,
            kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin,
            search_margin_width=search_margin, search_margin_height=search_margin,
        )
        ratio = kernel_margin / search_margin
        print(f"kernel_margin={kernel_margin:2d}  search_margin={search_margin:3d}  ratio={ratio:.2f}  match={found == expected}")
```

<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.translation import locate; reference_image = read(path='astronaut0.png'); p0 = PixelCoordinate(x=150, y=150); dx = 10; current_image = translate(arr=reference_image, dx=dx, dy=0); expected = PixelCoordinate(x=p0.x + dx, y=p0.y); print('| kernel_margin | search_margin | ratio | match |'); print('|---|---|---|---|'); [print(f'| {km} | {sm} | {km/sm:.2f} | {locate(reference_image=reference_image, current_image=current_image, reference_point=p0, search_center=p0, kernel_margin_width=km, kernel_margin_height=km, search_margin_width=sm, search_margin_height=sm) == expected} |') for km in [15, 20, 25, 30] for sm in [km+15, km+80]]" -->

Ratio genuinely doesn't matter. What does: the *raw displacement*,
compared against `kernel_margin` alone — not `search_margin`, no matter
how generously it's sized. Demonstrating this needs `locate`'s *pre-fix*
behavior explicitly (`centered=False`, the padding placement this page
is about to change) — the real, shipped `locate` no longer reproduces
the bug it's meant to illustrate. A `def`-based helper like this doesn't fit
a single-line `cmdrun` invocation, so
[`kernel_search_window_ratio_uncentered_demo.py`](#kernel_search_window_ratio_uncentered_demopy)
(full source at the bottom of this page) holds it instead, matching
[`parallelization_bench.py`](./parallelization.md#parallelization_benchpy)'s
precedent for logic too complex for a one-liner — cheap enough here to
still run live, though, not a committed snapshot:

<!-- cmdrun python3 kernel_search_window_ratio_uncentered_demo.py -->

A sharp cliff, exactly at `dx == kernel_margin`. `search_margin=180` —
six times larger than `kernel_margin` — makes no difference at all.

## Root Cause

[`dictk.translation.locate`](../api/dictk/translation.html#locate)
zero-pads the kernel up to the search area's own size before the FFT
(see [Correlation Criteria](./correlation_criteria.md#fourier-domain)).
Until this page, that padding placed the kernel's real content at the
padded array's top-left corner — everything else, zero. FFT-based phase
correlation is circular: the shift it reports is only meaningful modulo
the array's own size, wrapping silently past that. With the kernel
anchored at the corner instead of centered, the *safe* half of that
circle landed almost entirely on the negative side. The positive side
had almost none of it to spare — capped at exactly `kernel_margin`,
regardless of how large `search_margin` was set. Past that cap, `locate`
didn't fail visibly. It returned a confidently wrong `PixelCoordinate`,
offset from the true one by exactly the padded array's own width.

## The Fix

Center the kernel's content within the padded array instead — split the
padding before/after rather than putting it all after. The recoverable
range becomes symmetric, bounded by `search_margin` in *both*
directions, exactly as the parameter's own name implies it always
should have been:

<!-- cmdrun python3 -c "from dictk.image import read, translate, PixelCoordinate; from dictk.translation import locate; reference_image = read(path='astronaut0.png'); p0 = PixelCoordinate(x=150, y=150); kernel_margin = 30; search_margin = 45; print('| dx | found | expected | match |'); print('|---|---|---|---|'); [print(f'| {dx} | ({locate(reference_image=reference_image, current_image=translate(arr=reference_image, dx=dx, dy=0), reference_point=p0, search_center=p0, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=search_margin, search_margin_height=search_margin).x},{p0.y}) | ({p0.x+dx},{p0.y}) | {locate(reference_image=reference_image, current_image=translate(arr=reference_image, dx=dx, dy=0), reference_point=p0, search_center=p0, kernel_margin_width=kernel_margin, kernel_margin_height=kernel_margin, search_margin_width=search_margin, search_margin_height=search_margin) == PixelCoordinate(x=p0.x+dx, y=p0.y)} |') for dx in [30, 40, 44, 45, -44, -45]]" -->

`dx=45` (exactly `search_margin`) now succeeds in both directions —
`dx=44` positive, `dx=-44` negative, both fine too, with `dx=45`/`-45`
sitting at the single aliased boundary point every circular system has
(where $+45$ and $-45$ are indistinguishable modulo the array's own
90-pixel width). That one-pixel edge case is an inherent property of
representing a circle with discrete arithmetic, not a bug — a world away
from the old, severely lopsided range this page started with.

## Scope of the Fix

The old, single `_window_and_pad` helper did two separable jobs at
once: taper `kernel`/`search` toward zero (if `windowing` was given),
then zero-pad `kernel` up to `search`'s own shape. Only the first job
ever needed the full `search` array; the second only ever read its
*shape*. Splitting them makes that honest: `_window` tapers both arrays
(unchanged from before), and `_kernel_pad` grows `kernel` up to a given
`(height, width)` — never `search` itself — gaining the `centered`
parameter this page is about. `locate` calls `_kernel_pad` with
`centered=True`.
[`phase_correlation`](../api/dictk/correlation.html#phase_correlation) —
the surface-visualization function behind every figure in [Correlation
Visualization](./correlation_visualization.md) — keeps the old,
uncentered default. Every peak position already published there, all
well within the old safe range regardless of which convention computed
it, stays exactly as documented; nothing needed regenerating.
[Correlation Criteria](./correlation_criteria.md#fourier-domain) notes
the difference where its own teaching example reimplements this same
padding step.

## What This Means in Practice

`search_margin` now means what it always should have: the full range a
true displacement can fall within, safely, in every direction. That's
progress, but it doesn't remove the underlying cost — a bigger unknown
displacement still needs a bigger `search_margin`, and a bigger
`search_margin` still means a bigger FFT at every point. [Search Center
Predictions](./search_center_predictions.md) picks up exactly here: a
better initial guess than "zero displacement" shrinks how much
`search_margin` has to cover in the first place.

The original question — how far `astronaut0` can actually be stretched
or compressed before `locate` breaks — is still open. This page didn't
answer it; it found and fixed something that had to be fixed first. The
interpolation confound flagged above is still there too. Both are
follow-up work, not resolved here.

### `kernel_search_window_ratio_uncentered_demo.py`

```python
<!-- cmdrun cat kernel_search_window_ratio_uncentered_demo.py -->
```
