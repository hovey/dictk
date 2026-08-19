"""dictk: Digital Image Correlation Toolkit.

CLI vs. API: the `dictk` command-line entry points (`dictk rosta`,
`dictk checkerboard`, `dictk astronaut`, ...) write image files to disk —
that's their whole job. The corresponding Python API functions
(`dictk.rosta`, `dictk.checkerboard`, `dictk.astronaut`, ...) do not
perform any file I/O; they return NumPy arrays only. This keeps the API
composable in a functional style — arrays
can be piped through further functions (e.g. `dictk.image.combine`)
before anything touches disk — and callers who do want a file call
`dictk.image.write` explicitly as a separate, deliberate step.
"""

from importlib.metadata import PackageNotFoundError, version

from dictk.image import astronaut, checkerboard
from dictk.rosta import rosta

try:
    __version__ = version("dictk")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    # Top-level re-exports: the array-returning API functions this
    # docstring describes above.
    "astronaut",
    "checkerboard",
    "rosta",
    "__version__",
    # Submodule names, not re-exports: without these, `from dictk import
    # *` only binds the four names above, and pdoc's own package walk
    # (both what it documents and what it links under "Submodules" on
    # the dictk.html landing page) only discovers dictk.rosta -- by
    # coincidence, since "rosta" already appears above as a re-export
    # and happens to share its module's name. Listing every submodule
    # here explicitly, not by that accident, is what makes both
    # `from dictk import *` and pdoc's discovery complete and uniform.
    # Add any new top-level submodule here too, or it silently drops out
    # of both.
    "cli",
    "correlation",
    "element",
    "grid",
    "image",
    "translation",
]
