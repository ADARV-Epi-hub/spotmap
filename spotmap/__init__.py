"""spotmap — Interactive epidemiological spot maps for India."""

from .exceptions import ColumnNotFoundError, NoCasePointsError, SpotMapError
from .interactive import run_interactive, spotmap_run
from .map_builder import SpotMap

__version__ = "0.1.28"
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
    f"SpotMap by ADARV  -  turn your case data into an interactive map of India (no coding needed).\n"
    f"\n"
    f"  Get started - copy these two lines and run them:\n"
    f"\n"
    f"      from spotmap import spotmap_run\n"
    f"      spotmap_run()\n"
    f"\n"
    f"  You'll be asked to choose your data file, then your map appears right away.\n"
)
