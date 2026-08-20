# High Point Density

[Simple Stretch Revisited](./simple_stretch.html#simple-stretch-revisited)
capped out at 250 points — the most `x` values that stay integer-safe
at `factor_x = 1.02`, within the image's own margins. [Subpixel
Accuracy](./subpixel_accuracy.md) removed that ceiling: once tracking
doesn't need its answer to be a whole pixel, `x` doesn't need to be a
multiple of 50 either. This page pushes all the way to VIC-2D's own
density — 5 pixels apart, the same 53x54, 2862-point grid [Verification
Against VIC-2D](./simple_stretch.html#verification-against-vic-2d) and
Subpixel Accuracy both already used.

## Tracking at Full Density

```python
from dictk.grid import generate, locate_subpixel

points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)
found = locate_subpixel(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=20,
    kernel_margin_height=20,
    search_margin_width=48,
    search_margin_height=52,
    upsample_factor=10,
)
```

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch; from dictk.grid import generate, locate_subpixel; reference_image = read(path='astronaut0.png'); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); points = generate(origin=PixelCoordinate(x=18, y=16), count_x=53, count_y=54, spacing_x=5, spacing_y=5); found = locate_subpixel(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52, upsample_factor=10); print(f'{len(points)} points tracked')" -->

## Strain at Full Density

Same recipe as Simple Stretch Revisited: [`dictk.grid.elements`](../api/dictk/grid.html#elements)
for connectivity (2756 elements this time, not 196), then
[`gauss_point_log_strains`](../api/dictk/element.html#gauss_point_log_strains)/[`gauss_point_coordinates`](../api/dictk/element.html#gauss_point_coordinates)
at each of the resulting 11024 Gauss points. Node numbers stay off —
2862 of them would be unreadable:

```python
from dictk.element import gauss_point_coordinates, gauss_point_log_strains
from dictk.grid import elements
from dictk.image import element_strain_plot

element_indices = elements(count_x=53, count_y=54)
values = []
coordinates = []
for element in element_indices:
    reference_corners = [points[i] for i in element]
    current_corners = [found[i] for i in element]
    strains = gauss_point_log_strains(
        reference_points=reference_corners, current_points=current_corners
    )
    values.extend(strain[0, 0] for strain in strains)
    coordinates.extend(gauss_point_coordinates(points=current_corners))

element_strain_plot(
    points=found,
    elements=element_indices,
    coordinates=coordinates,
    values=values,
    label=r"Log Strain, $E_{11}$",
    path="high_point_density_strain_gauss_points.png",
)
element_strain_plot(
    points=found,
    elements=element_indices,
    coordinates=coordinates,
    values=values,
    label=r"Log Strain, $E_{11}$",
    image=current_image,
    path="high_point_density_strain_on_current.png",
)
```

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch, element_strain_plot; from dictk.grid import generate, locate_subpixel, elements; from dictk.element import gauss_point_coordinates, gauss_point_log_strains; reference_image = read(path='astronaut0.png'); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); points = generate(origin=PixelCoordinate(x=18, y=16), count_x=53, count_y=54, spacing_x=5, spacing_y=5); found = locate_subpixel(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52, upsample_factor=10); element_indices = elements(count_x=53, count_y=54); values, coordinates = [], []; [ (values.extend(strain[0, 0] for strain in gauss_point_log_strains(reference_points=[points[i] for i in element], current_points=[found[i] for i in element])), coordinates.extend(gauss_point_coordinates(points=[found[i] for i in element]))) for element in element_indices ]; element_strain_plot(points=found, elements=element_indices, coordinates=coordinates, values=values, label=r'Log Strain, \$E_{11}\$', path='high_point_density_strain_gauss_points.png'); element_strain_plot(points=found, elements=element_indices, coordinates=coordinates, values=values, label=r'Log Strain, \$E_{11}\$', image=current_image, path='high_point_density_strain_on_current.png')" -->

<figure>
    <img src="high_point_density_strain_gauss_points.png" alt="a dense 53x54 mesh with 4 Gauss points per element, colored by log strain E11, no node numbers, no background image" />
    <figcaption>The full 2862-point mesh, colored by log strain $E_{11}$.</figcaption>
</figure>

<figure>
    <img src="high_point_density_strain_on_current.png" alt="the same dense mesh and colored Gauss points overlaid on current_image, the stretched astronaut photo" />
    <figcaption>The same dense mesh, overlaid on <code>current_image</code>.</figcaption>
</figure>

## A Real Trade-Off, Not a Bug

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch; from dictk.grid import generate, locate_subpixel, elements; from dictk.element import gauss_point_log_strains; import numpy as np; reference_image = read(path='astronaut0.png'); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); points = generate(origin=PixelCoordinate(x=18, y=16), count_x=53, count_y=54, spacing_x=5, spacing_y=5); found = locate_subpixel(reference_image=reference_image, current_image=current_image, reference_points=points, kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52, upsample_factor=10); element_indices = elements(count_x=53, count_y=54); values = []; [values.extend(strain[0, 0] for strain in gauss_point_log_strains(reference_points=[points[i] for i in element], current_points=[found[i] for i in element])) for element in element_indices]; values = np.array(values); print(f'2862-point, 5px-spacing mesh: mean \$E_{{11}}\$ = {values.mean():.4f} (true value {np.log(factor_x):.4f}), but std = {values.std():.4f}, range [{values.min():.4f}, {values.max():.4f}]')" -->

The mean is accurate. The spread is not small. Unlike Simple Stretch
Revisited's perfectly uniform result, individual elements here scatter
well beyond the true $\ln(1.02) \approx 0.0198$ value — some report
negative strain, some report nearly 4 times the true value.

This isn't a tracking bug. Log strain is, in effect, a finite
difference: $E_{11} \approx \Delta u / L$, a displacement difference
divided by element size $L$. [Subpixel Accuracy](./subpixel_accuracy.md)'s
own measurement found `locate_subpixel`'s residual error is small in
absolute terms — a few hundredths of a pixel, on average — but at 5
pixels of element spacing, that same absolute error is a much larger
*fraction* of $L$ than it was at Simple Stretch Revisited's 50-pixel
spacing. The smaller the element, the more a fixed amount of tracking
noise gets amplified into strain noise. Checked directly, not just
argued:

<!-- cmdrun python3 -c "from dictk.image import read, PixelCoordinate, stretch; from dictk.grid import generate, locate_subpixel, elements; from dictk.element import gauss_point_log_strains; import numpy as np; reference_image = read(path='astronaut0.png'); factor_x = 1.02; current_image = stretch(arr=reference_image, factor_x=factor_x); print('| Element spacing | Mean E11 | Std E11 |'); print('|---|---|---|'); [ (lambda points, found: (lambda element_indices: (lambda values: print(f'| {spacing}px | {values.mean():.5f} | {values.std():.5f} |'))(np.array([s[0,0] for element in element_indices for s in gauss_point_log_strains(reference_points=[points[i] for i in element], current_points=[found[i] for i in element])])))(elements(count_x=260 // spacing, count_y=260 // spacing)))(generate(origin=PixelCoordinate(x=20, y=20), count_x=260 // spacing, count_y=260 // spacing, spacing_x=spacing, spacing_y=spacing), locate_subpixel(reference_image=reference_image, current_image=current_image, reference_points=generate(origin=PixelCoordinate(x=20, y=20), count_x=260 // spacing, count_y=260 // spacing, spacing_x=spacing, spacing_y=spacing), kernel_margin_width=20, kernel_margin_height=20, search_margin_width=48, search_margin_height=52, upsample_factor=10)) for spacing in [5, 10, 20, 40] ]" -->

Standard deviation falls as element spacing grows — the same tracking
noise, spread over a larger $L$, moves less of the resulting strain.
This is exactly why VIC-2D and other commercial DIC packages offer a
**strain window** — averaging displacement over several subsets before
computing strain, trading spatial resolution for strain precision.
`dictk` doesn't implement that averaging yet. This page's own dense
mesh is accurate on average and honestly noisy point to point, not
silently smoothed into looking better than the underlying tracking
supports.

Point count, tracking accuracy, and now strain precision have all been
free variables throughout Simple Stretch, Subpixel Accuracy, and this
page. How `dictk`'s own tracking time scales as point count grows —
across sequential, threaded, and multi-process execution — is
[Parallelization](./parallelization.md)'s own question, still not
attempted here either.
