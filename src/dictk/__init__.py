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
    "astronaut",
    "checkerboard",
    "rosta",
    "__version__",
]
