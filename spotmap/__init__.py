"""spotmap — Interactive epidemiological spot maps for India."""

from .exceptions import ColumnNotFoundError, NoCasePointsError, SpotMapError
from .interactive import run_interactive, spotmap_run
from .map_builder import SpotMap

# Short, friendly alias so non-coders can simply do:  import spotmap; spotmap.run()
run = spotmap_run

__version__ = "0.1.32"
__all__ = [
    "SpotMap",
    "run",  # friendly alias for spotmap_run
    "spotmap_run",
    "run_interactive",  # deprecated alias, kept for backward compat
    "SpotMapError",
    "ColumnNotFoundError",
    "NoCasePointsError",
]

# Friendly welcome shown when the package is imported, to help first-time
# (non-coder) users know how to launch the tool.  At this point `import spotmap`
# has already run, so we only need to tell them the one next line.
print(
    f"\n"
    f"Interactive SpotMap for India  -  created by ADARV\n"
    f"\n"
    f"  No code required! To build your map, just run:\n"
    f"\n"
    f"      spotmap.run()\n"
    f"\n"
    f"  You'll be asked to choose your data file, then your map appears.\n"
)
