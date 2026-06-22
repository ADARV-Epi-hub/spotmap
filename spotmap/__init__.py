"""spotmap — Interactive epidemiological spot maps for India."""

from .exceptions import ColumnNotFoundError, NoCasePointsError, SpotMapError
from .interactive import run_interactive, spotmap_run
from .map_builder import SpotMap

__version__ = "0.1.20"
__all__ = [
    "SpotMap",
    "spotmap_run",
    "run_interactive",  # deprecated alias, kept for backward compat
    "SpotMapError",
    "ColumnNotFoundError",
    "NoCasePointsError",
]

# Friendly welcome shown when the package is imported, to help first-time
# (non-coder) users know how to launch the tool.
print(
    f"\n"
    f"SpotMap v{__version__} - interactive spot maps for India (created by ADARV)\n"
    f"\n"
    f"  To build your map, run these two lines:\n"
    f"      from spotmap import spotmap_run\n"
    f"      spotmap_run()\n"
)
