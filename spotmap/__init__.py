"""spotmap — Interactive epidemiological spot maps for India."""

from .exceptions import ColumnNotFoundError, NoCasePointsError, SpotMapError
from .interactive import run_interactive
from .map_builder import SpotMap

__version__ = "0.1.3"
__all__ = [
    "SpotMap",
    "run_interactive",
    "SpotMapError",
    "ColumnNotFoundError",
    "NoCasePointsError",
]
