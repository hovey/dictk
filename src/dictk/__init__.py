"""dictk: Digital Image Correlation Toolkit."""

from importlib.metadata import PackageNotFoundError, version

from dictk.core import zero_normalized_cross_correlation

try:
    __version__ = version("dictk")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["zero_normalized_cross_correlation", "__version__"]
