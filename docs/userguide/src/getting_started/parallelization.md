# Parallelization

[Multi-Point Motion](./multi_point_motion.md#tracking-the-grid) just ran 12
independent calls to
[`dictk.translation.locate`](../api/dictk/translation.html#locate) -- one
per point, each doing its own FFT-based phase correlation -- to verify
every point's displacement. We anticipate the need to process a very
large number of point-to-point correspondences to support large-scale
DIC work -- a real finite element mesh (see [Finite Element
Method](./finite_element_method.md)) can easily have thousands-to-millions
of nodes, not the 12 points in the simple grid above. Each point
correspondence is independent of every other: locating point $i$ never
reads or writes anything locating point $j$ touches. That independence
isn't just a convenient property to point out --
[`dictk.grid.locate`](../api/dictk/grid.html#locate) is already written to
exploit it. Its entire body is a single map over `reference_points`, one
call to [`dictk.translation.locate`](../api/dictk/translation.html#locate)
per point, accumulating no shared state between iterations:

```python
return [
    translation.locate(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=reference_point,
        search_center=search_center,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
    )
    for reference_point, search_center in zip(reference_points, search_centers)
]
```

Because every iteration is already independent, parallelizing it is a
matter of swapping this list comprehension for a parallel map over the same
per-point calls -- not a redesign. The standard library's
`concurrent.futures.ProcessPoolExecutor` can drive that map today, calling
only dictk's existing public API:

```python
from concurrent.futures import ProcessPoolExecutor
from functools import partial

def _locate_one(
    args, *, reference_image, current_image,
    kernel_margin_width, kernel_margin_height,
    search_margin_width, search_margin_height,
):
    reference_point, search_center = args
    return translation.locate(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=reference_point,
        search_center=search_center,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
    )

def locate_grid_parallel(
    *,
    reference_image,
    current_image,
    reference_points,
    search_centers,
    kernel_margin_width,
    kernel_margin_height,
    search_margin_width,
    search_margin_height,
):
    worker = partial(
        _locate_one,
        reference_image=reference_image,
        current_image=current_image,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
    )
    with ProcessPoolExecutor() as executor:
        return list(executor.map(worker, zip(reference_points, search_centers)))
```

`_locate_one` takes its point pair as a single positional argument, not
dictk's usual keyword-only style: `ProcessPoolExecutor.map` (like the
built-in `map`) always calls its target positionally, one item per
iterable, so a keyword-only signature isn't an option for the function
being mapped over. This actual snippet runs correctly against `astronaut0`
and recovers the same displacements as the sequential version [Multi-Point
Motion](./multi_point_motion.md#tracking-the-grid) already ran -- it just
isn't wired up as a real `dictk.grid` function, and can't be run live on
this page as a `cmdrun` figure the way the others are: `ProcessPoolExecutor`
spawns worker processes that each re-import the target callable by module
path, which rules out a worker function defined inline in a one-off
script.

Two practical caveats before reaching for this:

- **Threads won't help.** The obvious first instinct is a
  `ThreadPoolExecutor` instead, since it avoids process-spawn and
  pickling overhead entirely -- but `translation.locate`'s search-area
  correlation is dominated by NumPy/SciPy array operations that mostly
  hold the GIL for the small kernel and search-area sizes this guide uses,
  so threads mostly just add scheduling overhead without real concurrency.
  A process pool sidesteps the GIL entirely, at the cost of that
  spawn/pickling overhead per task.
- **Overhead has to be worth it.** Spawning a worker pool and pickling
  image arrays across process boundaries isn't free, and for a handful of
  points (like the 12-point grid above), that overhead can easily exceed
  the time saved. It starts paying off once the point count is large
  enough. But, what is *large enough*?  That question will be answered in turn
  in the analysis that follows.
