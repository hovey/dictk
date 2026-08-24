from pathlib import Path

import numpy as np
import pytest

from dictk.correlation import WindowingMethod, _kernel_pad, cc, phase_correlation, zncc
from dictk.grid import elements as grid_elements
from dictk.grid import generate as grid_generate
from dictk.rosta import rosta
from dictk.image import (
    PixelCoordinate,
    SubpixelCoordinate,
    astronaut,
    checkerboard,
    combine,
    subimage,
    translate,
)
from dictk.plot import (
    ArrowAnnotation,
    BoxAnnotation,
    PointAnnotation,
    element_strain_plot,
    phase_correlation_quadrant_plot,
    point_grid_boxes_plot,
    point_grid_plot,
    point_plot,
    reference_frame_plot,
    spatial_correlation_quadrant_plot,
    subimage_bounds_plot,
    subimage_comparison_plot,
    subimage_plot,
)


def test_subimage_bounds_plot_writes_file(tmp_path: Path):
    arr = checkerboard(width=40, height=40)
    path = tmp_path / "bounds.png"
    subimage_bounds_plot(
        image=arr, origin=PixelCoordinate(x=-5, y=10), width=20, height=15, path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize("width,height", [(0, 5), (5, 0)])
def test_subimage_bounds_plot_invalid_size_raises(tmp_path: Path, width, height):
    arr = checkerboard(width=40, height=40)
    with pytest.raises(ValueError):
        subimage_bounds_plot(
            image=arr,
            origin=PixelCoordinate(x=0, y=0),
            width=width,
            height=height,
            path=tmp_path / "out.png",
        )


def test_subimage_plot_writes_file(tmp_path: Path):
    arr = checkerboard(width=40, height=40)
    path = tmp_path / "region.png"
    subimage_plot(
        image=arr, origin=PixelCoordinate(x=-5, y=10), width=20, height=15, path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize("width,height", [(0, 5), (5, 0)])
def test_subimage_plot_invalid_size_raises(tmp_path: Path, width, height):
    arr = checkerboard(width=40, height=40)
    with pytest.raises(ValueError):
        subimage_plot(
            image=arr,
            origin=PixelCoordinate(x=0, y=0),
            width=width,
            height=height,
            path=tmp_path / "out.png",
        )


def test_subimage_comparison_plot_writes_file(tmp_path: Path):
    # Larger than the 40x40 used elsewhere in this file: subimage_comparison_plot
    # renders two side-by-side panels with constrained_layout, which warns
    # ("axes sizes collapsed to zero") on very small figures.
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "comparison.png"
    subimage_comparison_plot(
        image=arr, origin=PixelCoordinate(x=-20, y=40), width=80, height=60, path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_subimage_comparison_plot_with_point_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "comparison_with_point.png"
    subimage_comparison_plot(
        image=arr,
        origin=PixelCoordinate(x=20, y=40),
        width=80,
        height=60,
        point=PixelCoordinate(x=50, y=60),
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_subimage_comparison_plot_with_point_color_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "comparison_with_point_color.png"
    subimage_comparison_plot(
        image=arr,
        origin=PixelCoordinate(x=20, y=40),
        width=80,
        height=60,
        point=PixelCoordinate(x=50, y=60),
        point_color="orange",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_subimage_comparison_plot_with_point_and_origin_labels_writes_file(
    tmp_path: Path,
):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "comparison_with_labels.png"
    subimage_comparison_plot(
        image=arr,
        origin=PixelCoordinate(x=20, y=40),
        width=80,
        height=60,
        point=PixelCoordinate(x=50, y=60),
        point_label="P",
        origin_label="K",
        source_origin_label="O",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_subimage_comparison_plot_with_subimage_label_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "comparison_with_label.png"
    subimage_comparison_plot(
        image=arr,
        origin=PixelCoordinate(x=20, y=40),
        width=80,
        height=60,
        subimage_label="kernel",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_subimage_comparison_plot_with_color_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "comparison_with_color.png"
    subimage_comparison_plot(
        image=arr,
        origin=PixelCoordinate(x=20, y=40),
        width=80,
        height=60,
        color="orange",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_subimage_comparison_plot_with_figsize_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "comparison_with_figsize.png"
    subimage_comparison_plot(
        image=arr,
        origin=PixelCoordinate(x=20, y=40),
        width=80,
        height=60,
        figsize=(6.4, 4.8),
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize("width,height", [(0, 5), (5, 0)])
def test_subimage_comparison_plot_invalid_size_raises(tmp_path: Path, width, height):
    arr = checkerboard(width=40, height=40)
    with pytest.raises(ValueError):
        subimage_comparison_plot(
            image=arr,
            origin=PixelCoordinate(x=0, y=0),
            width=width,
            height=height,
            path=tmp_path / "out.png",
        )


def test_point_plot_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "points.png"
    point_plot(
        image=arr,
        arrows=[
            ArrowAnnotation(
                tail=PixelCoordinate(x=0, y=0),
                head=PixelCoordinate(x=100, y=75),
                color="gold",
                label="p0",
            ),
            ArrowAnnotation(
                tail=PixelCoordinate(x=100, y=75),
                head=PixelCoordinate(x=94, y=83),
                color="magenta",
                label="displacement",
            ),
        ],
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_plot_arrow_outside_image_bounds(tmp_path: Path):
    arr = checkerboard(width=40, height=40)
    path = tmp_path / "points.png"
    point_plot(
        image=arr,
        arrows=[
            ArrowAnnotation(
                tail=PixelCoordinate(x=0, y=0),
                head=PixelCoordinate(x=-10, y=60),
                color="cyan",
                label="p1",
            )
        ],
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_plot_empty_arrows_raises(tmp_path: Path):
    arr = checkerboard(width=40, height=40)
    with pytest.raises(ValueError):
        point_plot(image=arr, arrows=[], path=tmp_path / "out.png")


def test_point_plot_with_boxes_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "points_with_boxes.png"
    point_plot(
        image=arr,
        arrows=[
            ArrowAnnotation(
                tail=PixelCoordinate(x=0, y=0),
                head=PixelCoordinate(x=100, y=75),
                color="blue",
                label="arrow",
            )
        ],
        boxes=[
            BoxAnnotation(
                origin=PixelCoordinate(x=20, y=30),
                width=40,
                height=50,
                color="green",
                label="box",
            )
        ],
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_plot_with_points_writes_file(tmp_path: Path):
    arr = checkerboard(width=200, height=200)
    path = tmp_path / "points_with_labels.png"
    point_plot(
        image=arr,
        arrows=[
            ArrowAnnotation(
                tail=PixelCoordinate(x=0, y=0),
                head=PixelCoordinate(x=100, y=75),
                color="blue",
                label="arrow",
            )
        ],
        points=[
            PointAnnotation(
                position=PixelCoordinate(x=0, y=0), label="$O$", color="blue"
            ),
            PointAnnotation(
                position=PixelCoordinate(x=100, y=75), label="$P$", color="black"
            ),
        ],
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_plot_without_legend_writes_file(tmp_path: Path):
    arr = checkerboard(width=40, height=40)
    path = tmp_path / "points_no_legend.png"
    point_plot(
        image=arr,
        arrows=[
            ArrowAnnotation(
                tail=PixelCoordinate(x=0, y=0),
                head=PixelCoordinate(x=20, y=20),
                color="blue",
                label="arrow",
            )
        ],
        legend=False,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_plot_with_figsize_writes_file(tmp_path: Path):
    arr = checkerboard(width=40, height=40)
    path = tmp_path / "points_figsize.png"
    point_plot(
        image=arr,
        arrows=[
            ArrowAnnotation(
                tail=PixelCoordinate(x=0, y=0),
                head=PixelCoordinate(x=20, y=20),
                color="blue",
                label="arrow",
            )
        ],
        legend=False,
        figsize=(6.4, 4.8),
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_reference_frame_plot_writes_file(tmp_path: Path):
    arr = checkerboard(width=300, height=300)
    path = tmp_path / "reference_frame.png"
    reference_frame_plot(image=arr, path=path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_reference_frame_plot_non_square_image(tmp_path: Path):
    arr = checkerboard(width=200, height=100)
    path = tmp_path / "reference_frame.png"
    reference_frame_plot(image=arr, path=path)
    assert path.exists()
    assert path.stat().st_size > 0


def _astronaut0_kernel_and_search(
    *, dx: float, dy: float, kernel_margin: int, search_margin: int
):
    """`astronaut0` (rosta speckle combined atop the astronaut photo),
    reconstructed from dictk's own public API rather than reading the
    bundled PNG -- bit-for-bit identical thanks to rosta()'s deterministic
    default `random_seed=42`, matching image_generation.md's own
    construction exactly. Unlike checkerboard() (perfectly periodic, no
    unambiguous peak) or plain astronaut() (large flat regions bias
    un-normalized CC toward the wrong window), astronaut0's speckle
    texture gives even plain CC a single, reliable peak -- the same reason
    the rest of the book uses astronaut0, not plain astronaut, for
    correlation examples."""
    reference_image = combine(
        a=rosta(width=300, height=300, density=0.5), b=astronaut(width=300, height=300)
    )
    current_image = translate(arr=reference_image, dx=dx, dy=dy)
    point = PixelCoordinate(x=100, y=100)
    kernel = subimage(
        image=reference_image,
        origin=PixelCoordinate(x=point.x - kernel_margin, y=point.y - kernel_margin),
        width=2 * kernel_margin,
        height=2 * kernel_margin,
    )
    search = subimage(
        image=current_image,
        origin=PixelCoordinate(x=point.x - search_margin, y=point.y - search_margin),
        width=2 * search_margin,
        height=2 * search_margin,
    )
    return kernel, search


def test_spatial_correlation_quadrant_plot_writes_file(tmp_path: Path):
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )

    path = tmp_path / "correlation_quadrant.png"
    spatial_correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        correlation_surface=cc(kernel=kernel, search=search),
        title="Cross-Correlation (CC)",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_spatial_correlation_quadrant_plot_long_title_writes_file(tmp_path: Path):
    """Regression test: the full criterion name used to overflow the
    correlation-surface panel's own title and collide with its colorbar --
    now rendered as a figure-level suptitle instead, so it should never
    raise regardless of length."""
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )

    path = tmp_path / "correlation_quadrant_zncc.png"
    spatial_correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        correlation_surface=zncc(kernel=kernel, search=search),
        title="Zero-mean Normalized Cross-Correlation (ZNCC)",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_spatial_correlation_quadrant_plot_search_smaller_than_kernel_raises(
    tmp_path: Path,
):
    kernel = np.zeros((20, 20), dtype=np.uint8)
    search = np.zeros((10, 10), dtype=np.uint8)
    path = tmp_path / "correlation_quadrant.png"
    with pytest.raises(ValueError):
        spatial_correlation_quadrant_plot(
            kernel=kernel,
            search=search,
            correlation_surface=np.zeros((1, 1)),
            title="Cross-Correlation (CC)",
            path=path,
        )


def test_spatial_correlation_quadrant_plot_peak_matches_known_displacement(
    tmp_path: Path,
):
    """The found position drawn on the Fixed Image panel (and used to
    center the Solution Vicinity zoom) must come from correlation_surface's
    own argmax -- verified here against a known ground-truth displacement,
    not just that a file got written."""
    dx, dy = -6, 8
    kernel_margin, search_margin = 25, 50
    kernel, search = _astronaut0_kernel_and_search(
        dx=dx, dy=dy, kernel_margin=kernel_margin, search_margin=search_margin
    )
    surface = cc(kernel=kernel, search=search)
    expected_x = search_margin + dx - kernel_margin
    expected_y = search_margin + dy - kernel_margin
    found_y, found_x = np.unravel_index(np.argmax(surface), surface.shape)
    assert (found_x, found_y) == (expected_x, expected_y)

    path = tmp_path / "correlation_quadrant.png"
    spatial_correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        correlation_surface=surface,
        title="Cross-Correlation (CC)",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_phase_correlation_quadrant_plot_writes_file(tmp_path: Path):
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )

    path = tmp_path / "phase_correlation_quadrant.png"
    phase_correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_phase_correlation_quadrant_plot_default_title(tmp_path: Path):
    # No method choice to make for the Fourier domain (unlike spatial's
    # cc/ncc/zcc/zncc), so title has a sensible default and is optional --
    # verify that omitting it doesn't raise, matching the sibling function's
    # required title.
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    path = tmp_path / "phase_correlation_quadrant.png"
    phase_correlation_quadrant_plot(kernel=kernel, search=search, path=path)
    assert path.exists()


def test_phase_correlation_quadrant_plot_search_smaller_than_kernel_raises(
    tmp_path: Path,
):
    kernel = np.zeros((20, 20), dtype=np.uint8)
    search = np.zeros((10, 10), dtype=np.uint8)
    path = tmp_path / "phase_correlation_quadrant.png"
    with pytest.raises(ValueError):
        phase_correlation_quadrant_plot(kernel=kernel, search=search, path=path)


def test_phase_correlation_quadrant_plot_peak_matches_known_displacement(
    tmp_path: Path,
):
    """Same correctness bar as
    test_spatial_correlation_quadrant_plot_peak_matches_known_displacement:
    verify the found position against a known ground-truth displacement,
    not just that a file got written."""
    dx, dy = -6, 8
    kernel_margin, search_margin = 25, 50
    kernel, search = _astronaut0_kernel_and_search(
        dx=dx, dy=dy, kernel_margin=kernel_margin, search_margin=search_margin
    )
    surface = phase_correlation(kernel=kernel, search=search)
    expected_x = search_margin + dx - kernel_margin
    expected_y = search_margin + dy - kernel_margin
    found_y, found_x = np.unravel_index(np.argmax(surface), surface.shape)
    assert (found_x, found_y) == (expected_x, expected_y)

    path = tmp_path / "phase_correlation_quadrant.png"
    phase_correlation_quadrant_plot(kernel=kernel, search=search, path=path)
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize("method", [WindowingMethod.HANN, WindowingMethod.HAMMING])
def test_phase_correlation_quadrant_plot_windowing_writes_file(tmp_path: Path, method):
    """windowing is accepted and still writes a valid figure."""
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    path = tmp_path / "phase_correlation_quadrant.png"
    phase_correlation_quadrant_plot(
        kernel=kernel, search=search, windowing=method, path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize("method", [WindowingMethod.HANN, WindowingMethod.HAMMING])
def test_phase_correlation_quadrant_plot_windowing_peak_matches_known_displacement(
    tmp_path: Path, method
):
    """The peak still matches a known displacement with windowing applied."""
    dx, dy = -6, 8
    kernel_margin, search_margin = 25, 50
    kernel, search = _astronaut0_kernel_and_search(
        dx=dx, dy=dy, kernel_margin=kernel_margin, search_margin=search_margin
    )
    surface = phase_correlation(kernel=kernel, search=search, windowing=method)
    expected_x = search_margin + dx - kernel_margin
    expected_y = search_margin + dy - kernel_margin
    found_y, found_x = np.unravel_index(np.argmax(surface), surface.shape)
    assert (found_x, found_y) == (expected_x, expected_y)

    path = tmp_path / "phase_correlation_quadrant.png"
    phase_correlation_quadrant_plot(
        kernel=kernel, search=search, windowing=method, path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize("method", [WindowingMethod.HANN, WindowingMethod.HAMMING])
def test_phase_correlation_quadrant_plot_windowing_changes_display(
    tmp_path: Path, method
):
    """The Fixed Image/Moving Image panels change too, not just the
    surface -- regression guard for a real bug: windowing used to reach
    the correlation surface but silently leave the displayed
    kernel/search untapered, showing panels that no longer matched what
    was actually correlated. A byte-difference check doesn't prove which
    panel changed (the surface panels already differed before this fix),
    but it does prove the windowed and unwindowed renders aren't
    identical -- see the visual check in the commit history for
    confirmation the correct panels taper toward black."""
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    path_none = tmp_path / "phase_correlation_quadrant_none.png"
    path_windowed = tmp_path / "phase_correlation_quadrant_windowed.png"
    phase_correlation_quadrant_plot(kernel=kernel, search=search, path=path_none)
    phase_correlation_quadrant_plot(
        kernel=kernel, search=search, windowing=method, path=path_windowed
    )
    assert path_none.read_bytes() != path_windowed.read_bytes()


def test_phase_correlation_quadrant_plot_reported_position_writes_file(
    tmp_path: Path,
):
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    path = tmp_path / "phase_correlation_quadrant_reported.png"
    phase_correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        reported_position=PixelCoordinate(x=10, y=10),
        reported_position_label="locate_uncentered",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_phase_correlation_quadrant_plot_reported_position_changes_display(
    tmp_path: Path,
):
    """Regression guard, same shape as the windowing test above: passing
    reported_position must actually draw the second box (and legend),
    not silently do nothing."""
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    path_without = tmp_path / "phase_correlation_quadrant_without.png"
    path_with = tmp_path / "phase_correlation_quadrant_with.png"
    phase_correlation_quadrant_plot(kernel=kernel, search=search, path=path_without)
    phase_correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        reported_position=PixelCoordinate(x=10, y=10),
        path=path_with,
    )
    assert path_without.read_bytes() != path_with.read_bytes()


def test_phase_correlation_quadrant_plot_centered_writes_file(tmp_path: Path):
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    path = tmp_path / "phase_correlation_quadrant_centered.png"
    phase_correlation_quadrant_plot(
        kernel=kernel, search=search, centered=True, path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_phase_correlation_quadrant_plot_centered_changes_display(tmp_path: Path):
    """centered=True must actually change the render (different Moving
    Image padding, different Fixed Image box position for the same
    kernel/search), not silently do nothing."""
    kernel, search = _astronaut0_kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    path_uncentered = tmp_path / "phase_correlation_quadrant_uncentered.png"
    path_centered = tmp_path / "phase_correlation_quadrant_centered.png"
    phase_correlation_quadrant_plot(kernel=kernel, search=search, path=path_uncentered)
    phase_correlation_quadrant_plot(
        kernel=kernel, search=search, centered=True, path=path_centered
    )
    assert path_uncentered.read_bytes() != path_centered.read_bytes()


def test_phase_correlation_quadrant_plot_centered_box_matches_known_displacement(
    tmp_path: Path,
):
    """Same correctness bar as the uncentered peak_matches_known_displacement
    test: independently compute the centered surface's own content-adjusted
    box position (raw argmax + _kernel_pad's own pad_before, wrapped) and
    verify it lands on the same true geometric position the uncentered
    surface's raw argmax already does -- despite the differently-shifted
    raw peak underneath, since centering only moves where kernel's content
    sits inside the padded array, not the true match position itself.
    dictk.correlation.phase_correlation itself has the equivalent, more
    thorough test against a real locate() call --
    test_phase_correlation_centered_matches_locate; this one stays focused
    on phase_correlation_quadrant_plot's own box-placement math."""
    dx, dy = -6, 8
    kernel_margin, search_margin = 25, 50
    kernel, search = _astronaut0_kernel_and_search(
        dx=dx, dy=dy, kernel_margin=kernel_margin, search_margin=search_margin
    )
    expected_x = search_margin + dx - kernel_margin
    expected_y = search_margin + dy - kernel_margin

    surface = phase_correlation(kernel=kernel, search=search, centered=True)
    _, pad_before_height, pad_before_width = _kernel_pad(
        kernel=kernel, shape=search.shape, centered=True
    )
    raw_peak_y, raw_peak_x = np.unravel_index(np.argmax(surface), surface.shape)
    box_x = (int(raw_peak_x) + pad_before_width) % search.shape[1]
    box_y = (int(raw_peak_y) + pad_before_height) % search.shape[0]
    assert (box_x, box_y) == (expected_x, expected_y)

    path = tmp_path / "phase_correlation_quadrant_centered.png"
    phase_correlation_quadrant_plot(
        kernel=kernel, search=search, centered=True, path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_writes_file(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=5,
        count_y=4,
        spacing_x=45,
        spacing_y=55,
    )
    path = tmp_path / "point_grid.png"
    point_grid_plot(image=photo, points=points, path=path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_empty_points_writes_file(tmp_path: Path):
    arr = checkerboard(width=100, height=100)
    path = tmp_path / "point_grid_empty.png"
    point_grid_plot(image=arr, points=[], path=path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_without_node_numbers_writes_file(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=5,
        count_y=4,
        spacing_x=45,
        spacing_y=55,
    )
    path = tmp_path / "point_grid_unlabeled.png"
    point_grid_plot(image=photo, points=points, show_node_numbers=False, path=path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_dot_size_writes_file(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=5,
        count_y=4,
        spacing_x=45,
        spacing_y=55,
    )
    path = tmp_path / "point_grid_dot_size.png"
    point_grid_plot(
        image=photo,
        points=points,
        show_node_numbers=False,
        dot_size=3,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_custom_labels_writes_file(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=2,
        count_y=2,
        spacing_x=60,
        spacing_y=60,
    )
    path = tmp_path / "point_grid_custom_labels.png"
    point_grid_plot(
        image=photo, points=points, labels=["05", "12", "31", "48"], path=path
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_labels_length_mismatch_raises(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=2,
        count_y=2,
        spacing_x=60,
        spacing_y=60,
    )
    with pytest.raises(ValueError):
        point_grid_plot(
            image=photo, points=points, labels=["only one"], path=tmp_path / "out.png"
        )


def test_point_grid_plot_origin_writes_file(tmp_path: Path):
    # A crop of `photo`, with `points` left in `photo`'s own global frame
    # (not translated to the crop's local 0-based coordinates) -- origin
    # tells point_grid_plot where that crop sits, so the saved figure's
    # own axes read in photo's global numbers, matching a full-image
    # figure of the same points exactly.
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=5,
        count_y=4,
        spacing_x=45,
        spacing_y=55,
    )
    crop_origin = PixelCoordinate(x=40, y=40)
    cropped = subimage(image=photo, origin=crop_origin, width=60, height=60)
    path = tmp_path / "point_grid_origin.png"
    point_grid_plot(
        image=cropped,
        points=points,
        origin=crop_origin,
        show_node_numbers=False,
        dot_size=3,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_circle_writes_file(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=5,
        count_y=4,
        spacing_x=45,
        spacing_y=55,
    )
    path = tmp_path / "point_grid_circle.png"
    point_grid_plot(
        image=photo,
        points=points,
        show_node_numbers=False,
        circle_center=PixelCoordinate(x=150, y=150),
        circle_radius=40,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_plot_circle_center_without_radius_raises(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    with pytest.raises(ValueError):
        point_grid_plot(
            image=photo,
            points=[],
            circle_center=PixelCoordinate(x=150, y=150),
            path=tmp_path / "out.png",
        )


def test_point_grid_plot_circle_radius_without_center_raises(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    with pytest.raises(ValueError):
        point_grid_plot(
            image=photo, points=[], circle_radius=40, path=tmp_path / "out.png"
        )


def test_point_grid_plot_circle_linewidth_writes_file(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    path = tmp_path / "point_grid_circle_linewidth.png"
    point_grid_plot(
        image=photo,
        points=[],
        circle_center=PixelCoordinate(x=150, y=150),
        circle_radius=40,
        circle_linewidth=0.8,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def _element_strain_plot_inputs():
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=3,
        count_y=4,
        spacing_x=50,
        spacing_y=55,
    )
    element_indices = grid_elements(count_x=3, count_y=4)
    # Fabricated coordinates/values -- element_strain_plot only draws what
    # it's given, so a real strain computation isn't needed to test it.
    coordinates = [(float(p.x) + 5, float(p.y) + 5) for p in points for _ in range(2)][
        : len(element_indices) * 4
    ]
    values = [float(i) for i in range(len(coordinates))]
    return points, element_indices, coordinates, values


def test_element_strain_plot_requires_keyword_arguments():
    points, element_indices, coordinates, values = _element_strain_plot_inputs()
    with pytest.raises(TypeError):
        element_strain_plot(points, element_indices, coordinates, values, "label")


def test_element_strain_plot_without_image_writes_file(tmp_path: Path):
    points, element_indices, coordinates, values = _element_strain_plot_inputs()
    path = tmp_path / "element_strain.png"
    element_strain_plot(
        points=points,
        elements=element_indices,
        coordinates=coordinates,
        values=values,
        label="Log Strain, E11",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_element_strain_plot_with_image_writes_file(tmp_path: Path):
    points, element_indices, coordinates, values = _element_strain_plot_inputs()
    photo = astronaut(width=300, height=300)
    path = tmp_path / "element_strain_on_image.png"
    element_strain_plot(
        points=points,
        elements=element_indices,
        coordinates=coordinates,
        values=values,
        label="Log Strain, E11",
        image=photo,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_element_strain_plot_show_node_numbers_writes_file(tmp_path: Path):
    points, element_indices, coordinates, values = _element_strain_plot_inputs()
    path = tmp_path / "element_strain_numbered.png"
    element_strain_plot(
        points=points,
        elements=element_indices,
        coordinates=coordinates,
        values=values,
        label="Log Strain, E11",
        show_node_numbers=True,
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_element_strain_plot_accepts_subpixel_coordinate_points(tmp_path: Path):
    _, element_indices, coordinates, values = _element_strain_plot_inputs()
    points = [SubpixelCoordinate(x=50.3, y=50.7)] * 12  # only .x/.y are used
    path = tmp_path / "element_strain_subpixel.png"
    element_strain_plot(
        points=points,
        elements=element_indices,
        coordinates=coordinates,
        values=values,
        label="Log Strain, E11",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_boxes_plot_writes_file(tmp_path: Path):
    photo = astronaut(width=300, height=300)
    points = grid_generate(
        origin=PixelCoordinate(x=50, y=50),
        count_x=3,
        count_y=4,
        spacing_x=50,
        spacing_y=55,
    )
    path = tmp_path / "point_grid_boxes.png"
    point_grid_boxes_plot(
        image=photo,
        points=points,
        margin_width=25,
        margin_height=25,
        label_prefix="kernel",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_point_grid_boxes_plot_empty_points_writes_file(tmp_path: Path):
    arr = checkerboard(width=100, height=100)
    path = tmp_path / "point_grid_boxes_empty.png"
    point_grid_boxes_plot(
        image=arr,
        points=[],
        margin_width=10,
        margin_height=10,
        label_prefix="kernel",
        path=path,
    )
    assert path.exists()
    assert path.stat().st_size > 0
