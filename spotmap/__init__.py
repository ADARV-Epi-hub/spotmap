"""spotmap — Interactive epidemiological spot maps for India."""

from .exceptions import ColumnNotFoundError, NoCasePointsError, SpotMapError
from .interactive import run_interactive, spotmap_run
from .map_builder import SpotMap

__version__ = "0.1.15"
__all__ = [
    "SpotMap",
    "spotmap_run",
    "run_interactive",  # deprecated alias, kept for backward compat
    "SpotMapError",
    "ColumnNotFoundError",
    "NoCasePointsError",
]
