"""Interactive prompt-based wrapper for non-coders.

Usage:
    from spotmap import run_interactive
    run_interactive()
"""

import os
from pathlib import Path

import pandas as pd

from .exceptions import NoCasePointsError, ColumnNotFoundError
from .map_builder import SpotMap


# =========================================================
# PRETTY OUTPUT HELPERS
# =========================================================

def _line(char="═", length=55):
    print(char * length)


def _header(text):
    _line()
    print(f"   {text}")
    _line()


def _ok(text):
    print(f"✓ {text}")


def _err(text):
    print(f"❌ {text}")


def _warn(text):
    print(f"⚠️  {text}")


def _info(text):
    print(f"ℹ️  {text}")


# =========================================================
# SAFE INPUT WITH RETRY
# =========================================================

def _ask(prompt: str, default: str = None, allow_blank: bool = False) -> str:
    """Ask user a question.  Allows a default value (press Enter to accept)."""
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            value = input(f"{prompt}{suffix}: ").strip().strip('"').strip("'")
        except (KeyboardInterrupt, EOFError):
            print("\n\nCancelled by user.")
            raise SystemExit(0)

        if value:
            return value
        if default is not None:
            return default
        if allow_blank:
            return ""
        _err("Please type a value (cannot be empty).")


def _ask_choice(prompt: str, options: list, default_index: int = 0) -> str:
    """Ask user to pick one of the listed options by number or by typing it."""
    for i, opt in enumerate(options, 1):
        marker = " (default)" if i - 1 == default_index else ""
        print(f"  {i}. {opt}{marker}")
    while True:
        raw = _ask(prompt, default=str(default_index + 1))
        # By number
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
            _err(f"Pick a number between 1 and {len(options)}.")
            continue
        # By name
        if raw in options:
            return raw
        # Case-insensitive match
        matches = [o for o in options if o.lower() == raw.lower()]
        if matches:
            return matches[0]
        _err(f"'{raw}' is not in the list. Pick a number or type one of the names exactly.")


# =========================================================
# SMART GUESSING
# =========================================================

_LAT_NAMES  = ["lat", "latitude", "y"]
_LONG_NAMES = ["lon", "long", "lng", "longitude", "x"]
_OUT_NAMES  = ["outcome", "status", "case_control", "class", "result"]


def _guess(columns: list, candidates: list) -> int:
    """Return index of best-matching column name, or 0 if none found."""
    for i, c in enumerate(columns):
        lc = c.lower()
        if any(name in lc for name in candidates):
            return i
    return 0


# =========================================================
# STEP HANDLERS — each catches its own errors and retries
# =========================================================

def _step_load_csv() -> pd.DataFrame:
    """Step 1 — load the CSV, with retry on file errors."""
    while True:
        path = _ask("\n📁 Enter the path to your CSV file")
        if not os.path.exists(path):
            _err(f"File not found: {path}")
            _info("Tip: paste the full path, or drag the file into the terminal.")
            continue
        if not path.lower().endswith(".csv"):
            _warn("That doesn't look like a .csv file — trying anyway.")
        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            if len(df) == 0:
                _err("The file is empty. Try a different file.")
                continue
            _ok(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            return df
        except pd.errors.EmptyDataError:
            _err("The CSV file is empty.")
        except pd.errors.ParserError as e:
            _err(f"Could not parse CSV: {e}")
        except PermissionError:
            _err("Permission denied reading the file.")
        except UnicodeDecodeError:
            _err("Encoding error. Try saving the CSV as UTF-8 and retry.")
        except Exception as e:  # noqa: BLE001
            _err(f"Could not read file: {e}")


def _step_pick_columns(df: pd.DataFrame):
    """Step 2 — let user pick lat/long/outcome columns."""
    cols = list(df.columns)

    print("\nColumns available in your file:")

    print("\n📍 Pick your LATITUDE column:")
    lat_col = _ask_choice("Latitude column", cols, _guess(cols, _LAT_NAMES))

    print("\n📍 Pick your LONGITUDE column:")
    long_col = _ask_choice("Longitude column", cols, _guess(cols, _LONG_NAMES))

    print("\n🏥 Pick your OUTCOME (case/control) column:")
    outcome_col = _ask_choice("Outcome column", cols, _guess(cols, _OUT_NAMES))

    if lat_col == long_col:
        _warn("Latitude and Longitude are the same column — that's probably wrong.")

    return lat_col, long_col, outcome_col


def _step_pick_case_value(df: pd.DataFrame, outcome_col: str) -> str:
    """Step 3 — pick which value represents a case."""
    values = (
        df[outcome_col]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    if not values:
        _err(f"Column '{outcome_col}' has no values. Cannot continue.")
        raise SystemExit(1)

    if len(values) == 1:
        _warn(f"Only one value found in '{outcome_col}': {values[0]}")
        _info("Using it as the case value.")
        return values[0]

    print(f"\n🎯 Pick which value represents a CASE:")
    default_idx = 0
    for i, v in enumerate(values):
        if v.lower() in ("case", "cases", "1", "yes", "true", "positive"):
            default_idx = i
            break
    return _ask_choice("Case value", values, default_idx)


def _step_output_path() -> str:
    """Step 4 — where to save the HTML."""
    while True:
        path = _ask(
            "\n💾 Where to save the map (HTML file)",
            default="spotmap_output.html",
        )
        if not path.lower().endswith(".html"):
            path += ".html"
            _info(f"Added .html → {path}")
        out = Path(path)
        if out.parent and not out.parent.exists():
            create = _ask(
                f"📂 Folder '{out.parent}' doesn't exist. Create it? (y/n)",
                default="y",
            )
            if create.lower().startswith("y"):
                try:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    _ok(f"Created folder: {out.parent}")
                except Exception as e:  # noqa: BLE001
                    _err(f"Could not create folder: {e}")
                    continue
            else:
                continue
        # Test write permission
        try:
            with open(path, "a"):
                pass
            os.remove(path) if os.path.getsize(path) == 0 else None
        except PermissionError:
            _err(f"No write permission for: {path}")
            continue
        except Exception:
            pass
        return path


def _step_build_map(df, lat_col, long_col, outcome_col, case_value, output_path):
    """Step 5 — actually build the map."""
    print("\n⚙️  Building the map...")
    try:
        SpotMap(
            df,
            lat_col=lat_col,
            long_col=long_col,
            outcome_col=outcome_col,
            case_value=case_value,
        ).build().save(output_path)
        _ok(f"Map saved to: {output_path}")
        return True
    except NoCasePointsError:
        _err(f"No rows found with outcome = '{case_value}'.")
        values = (
            df[outcome_col].dropna().astype(str).str.strip().str.lower().unique().tolist()
        )
        _info(f"Available values in '{outcome_col}': {values}")
        _info("Tip: case_value comparison is case-insensitive. Check spelling.")
    except ColumnNotFoundError as e:
        _err(str(e))
    except ValueError as e:
        msg = str(e)
        if "name column" in msg.lower():
            _err("Boundary file has unexpected columns. Are you using a custom shapefile?")
        else:
            _err(f"Invalid data: {msg}")
            _info("Tip: check that your latitude/longitude columns contain valid numbers.")
    except FileNotFoundError as e:
        _err(f"File not found: {e}")
    except Exception as e:  # noqa: BLE001
        _err(f"Something went wrong: {e}")
        _info("If this keeps happening, report it at:")
        _info("  https://github.com/TharunMallesan/spotmap/issues")
    return False


# =========================================================
# MAIN ENTRY POINT
# =========================================================

def run_interactive() -> None:
    """Run an interactive prompt-based wizard to build a SpotMap.

    Designed for users who don't want to write Python code.  Each step
    catches errors and lets the user retry instead of crashing.
    """
    _header("SpotMap — Interactive Setup")
    print("Press Enter to accept the default shown in [brackets].\n")

    # Step 1 — load CSV
    df = _step_load_csv()

    # Step 2 — pick columns
    lat_col, long_col, outcome_col = _step_pick_columns(df)

    # Step 3 — pick case value
    case_value = _step_pick_case_value(df, outcome_col)

    # Step 4 — output path
    output_path = _step_output_path()

    # Step 5 — build with retry
    while True:
        success = _step_build_map(
            df, lat_col, long_col, outcome_col, case_value, output_path
        )
        if success:
            break
        retry = _ask("\nTry again with different settings? (y/n)", default="n")
        if not retry.lower().startswith("y"):
            print("\nExiting. No map was created.")
            return
        # Re-prompt for whatever they want to fix
        print("\nLet's redo the setup:")
        lat_col, long_col, outcome_col = _step_pick_columns(df)
        case_value = _step_pick_case_value(df, outcome_col)

    _line()
    print(f"\n🗺️  Open this file in your browser:\n   {output_path}\n")
    _line()
