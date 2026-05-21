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


def _ask_choice(prompt: str, options: list, default_index: int = 0, previews: list = None) -> str:
    """Ask user to pick one of the listed options by number or by typing it.

    If *previews* is given (same length as *options*), shows sample values next
    to each option to help the user choose.
    """
    # Compute column widths for alignment
    col_w = max(len(str(o)) for o in options) + 2
    for i, opt in enumerate(options, 1):
        marker = " (default)" if i - 1 == default_index else ""
        if previews:
            print(f"  {i}. {str(opt).ljust(col_w)} →  {previews[i-1]}{marker}")
        else:
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


def _preview_dataframe(df: pd.DataFrame, n_rows: int = 3) -> None:
    """Show a clean preview of the dataframe — columns and first few rows."""
    print()
    print("─" * 55)
    print(f"📋 Here's what's in your file ({len(df)} rows × {len(df.columns)} columns):")
    print("─" * 55)
    print()
    print("Columns found:")
    for i, c in enumerate(df.columns, 1):
        sample = df[c].dropna().astype(str).str.strip()
        if len(sample) > 0:
            preview_val = sample.iloc[0]
            if len(preview_val) > 30:
                preview_val = preview_val[:30] + "…"
        else:
            preview_val = "(empty)"
        print(f"  {i:>2}. {c:<25} →  e.g.  {preview_val}")
    print()
    print(f"First {min(n_rows, len(df))} rows:")
    try:
        # Use a compact representation that doesn't blow up the terminal width
        with pd.option_context("display.max_columns", None,
                               "display.width", 120,
                               "display.max_colwidth", 20):
            print(df.head(n_rows).to_string(index=False))
    except Exception:
        print(df.head(n_rows))
    print()


# =========================================================
# STEP HANDLERS — each catches its own errors and retries
# =========================================================

_SUPPORTED_EXT = (".csv", ".xlsx", ".xls", ".xlsm", ".xlsb", ".ods", ".tsv", ".txt")


def _step_load_csv() -> pd.DataFrame:
    """Step 1 — load the data file (CSV / Excel / TSV), with retry on errors."""
    print("─" * 55)
    print("📁 Step 1 — Where is your data file?")
    print("   Supported: CSV (.csv), Excel (.xlsx, .xls), TSV")
    print("   Tip: you can paste the full path, or drag-drop the file here.")
    print("─" * 55)
    while True:
        path = _ask("Path to your file")
        if not os.path.exists(path):
            _err(f"File not found: {path}")
            _info("Tip: paste the full path, or drag the file into the terminal.")
            continue
        lower = path.lower()
        if not lower.endswith(_SUPPORTED_EXT):
            _warn(f"Unrecognised file type. Supported: {', '.join(_SUPPORTED_EXT)}")
            _info("Trying anyway as CSV.")
        try:
            if lower.endswith((".xlsx", ".xls", ".xlsm", ".xlsb", ".ods")):
                df = pd.read_excel(path)
                _ok("Detected Excel file.")
            elif lower.endswith((".tsv", ".txt")):
                df = pd.read_csv(path, sep="\t")
                _ok("Detected TSV file.")
            else:
                df = pd.read_csv(path)
            # Clean column names: strip whitespace and remove fully unnamed columns
            df.columns = df.columns.astype(str).str.strip()
            unnamed_cols = [c for c in df.columns if c.startswith("Unnamed:") or c == ""]
            if unnamed_cols:
                # Drop fully empty unnamed columns (common Excel artifact)
                for c in unnamed_cols:
                    if df[c].isna().all():
                        df = df.drop(columns=[c])
            if len(df) == 0:
                _err("The file is empty. Try a different file.")
                continue
            _ok(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            _preview_dataframe(df)
            return df
        except ImportError as e:
            _err(f"Missing reader for this file type: {e}")
            _info("For Excel files, run:  pip install openpyxl")
        except pd.errors.EmptyDataError:
            _err("The file is empty.")
        except pd.errors.ParserError as e:
            _err(f"Could not parse file: {e}")
        except PermissionError:
            _err("Permission denied — close the file in Excel and retry.")
        except UnicodeDecodeError:
            _err("Encoding error. Try saving the file as UTF-8 and retry.")
        except Exception as e:  # noqa: BLE001
            _err(f"Could not read file: {e}")


def _build_previews(df: pd.DataFrame, max_samples: int = 3, max_chars: int = 40) -> list:
    """Build a short string showing sample values for each column."""
    previews = []
    for c in df.columns:
        # Take up to N unique non-null values
        samples = (
            df[c]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()[:max_samples]
        )
        joined = ", ".join(samples) if samples else "(empty)"
        if len(joined) > max_chars:
            joined = joined[: max_chars - 1] + "…"
        previews.append(joined)
    return previews


def _step_pick_columns(df: pd.DataFrame):
    """Step 2 — let user pick lat/long/outcome columns."""
    cols = list(df.columns)
    previews = _build_previews(df)

    print("\n" + "─" * 55)
    print("📍 Step 2 — Which column holds the LATITUDE?")
    print("   (Latitude is the North-South number, e.g. 28.61 for Delhi)")
    print("─" * 55)
    lat_col = _ask_choice("Your latitude column", cols, _guess(cols, _LAT_NAMES), previews)

    print("\n" + "─" * 55)
    print("📍 Step 3 — Which column holds the LONGITUDE?")
    print("   (Longitude is the East-West number, e.g. 77.20 for Delhi)")
    print("─" * 55)
    long_col = _ask_choice("Your longitude column", cols, _guess(cols, _LONG_NAMES), previews)

    print("\n" + "─" * 55)
    print("🏥 Step 4 — Which column tells us CASE vs CONTROL?")
    print("   (e.g. a column with values like 'case'/'control' or '1'/'0')")
    print("─" * 55)
    outcome_col = _ask_choice("Your outcome column", cols, _guess(cols, _OUT_NAMES), previews)

    if lat_col == long_col:
        _warn("You picked the same column for latitude and longitude. That's probably wrong.")

    # Validate lat/long are numeric and in valid range
    _validate_coordinates(df, lat_col, long_col)

    return lat_col, long_col, outcome_col


def _validate_coordinates(df: pd.DataFrame, lat_col: str, long_col: str) -> None:
    """Warn if lat/long values look wrong."""
    try:
        lat_num = pd.to_numeric(df[lat_col], errors="coerce")
        lon_num = pd.to_numeric(df[long_col], errors="coerce")
    except Exception:
        _warn(f"Columns '{lat_col}' / '{long_col}' don't look numeric.")
        return

    n_missing_lat = lat_num.isna().sum()
    n_missing_lon = lon_num.isna().sum()
    if n_missing_lat or n_missing_lon:
        _warn(f"{n_missing_lat} rows have missing latitude, {n_missing_lon} have missing longitude — these will be skipped.")

    # India bounds: roughly lat 6-37, lon 68-98
    valid_lat = lat_num.between(-90, 90).sum()
    valid_lon = lon_num.between(-180, 180).sum()
    total = lat_num.notna().sum()

    if valid_lat < total or valid_lon < total:
        _warn("Some coordinates are outside valid Earth ranges (lat ±90, lon ±180).")
        _info("Tip: are lat/long columns swapped in your CSV?")

    in_india_lat = lat_num.between(6, 38).sum()
    in_india_lon = lon_num.between(67, 98).sum()
    if total > 0 and (in_india_lat / total < 0.5 or in_india_lon / total < 0.5):
        _warn("Most coordinates don't fall inside India.")
        _info(f"  Lat range in your data: {lat_num.min():.2f} to {lat_num.max():.2f} (India: 6 to 38)")
        _info(f"  Lon range in your data: {lon_num.min():.2f} to {lon_num.max():.2f} (India: 67 to 98)")
        _info("Tip: lat/long columns may be swapped. Boundaries won't show correctly.")


def _step_pick_case_value(df: pd.DataFrame, outcome_col: str) -> str:
    """Step 3 — pick which value represents a case.  Shows counts for each value."""
    # Build a value-count table
    norm = df[outcome_col].dropna().astype(str).str.strip()
    counts = norm.value_counts()
    values = counts.index.tolist()

    if not values:
        _err(f"Column '{outcome_col}' has no non-empty values. Cannot continue.")
        raise SystemExit(1)

    if len(values) == 1:
        _warn(f"Only one value found in '{outcome_col}': {values[0]} ({counts.iloc[0]} rows)")
        _info("Treating all rows as cases — no controls will appear on the map.")
        return values[0]

    # Show values WITH counts
    print("\n" + "─" * 55)
    print(f"🎯 Step 5 — Which value in '{outcome_col}' means a CASE?")
    print("   (We treat that value as cases, everything else as controls)")
    print("─" * 55)
    print(f"\nHere's what we found in '{outcome_col}':\n")
    for i, v in enumerate(values, 1):
        bar = "█" * min(int(counts.iloc[i-1] / counts.max() * 12), 12)
        print(f"  {i}. {v:<15} {bar}  ({counts.iloc[i-1]} rows)")
    print()

    # Smart default
    default_idx = 0
    for i, v in enumerate(values):
        if v.lower() in ("case", "cases", "1", "yes", "true", "positive", "present"):
            default_idx = i
            break

    print("Which value should be treated as CASE? (everything else becomes CONTROL)")
    case_value = _ask_choice("Case value", values, default_idx)

    # Show the user EXACTLY what will happen
    n_cases = counts[case_value]
    n_controls = counts.sum() - n_cases
    print()
    _info(f"Plotting {n_cases} cases and {n_controls} controls.")

    if n_cases == 0:
        _err("No case rows — cannot build map.")
        return _step_pick_case_value(df, outcome_col)

    return case_value


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

_DEFAULT_OUTPUT = "spotmap.html"


def run_interactive(output_path: str = _DEFAULT_OUTPUT) -> None:
    """Run an interactive prompt-based wizard to build a SpotMap.

    Designed for users who don't want to write Python code.  Each step
    catches errors and lets the user retry instead of crashing.

    Parameters
    ----------
    output_path:
        Where to save the HTML map.  Defaults to ``spotmap.html`` in the
        current directory.
    """
    print()
    _line("═")
    print("   🗺️  Welcome to SpotMap")
    print("   We'll guide you through 5 quick steps to build your map.")
    _line("═")
    print("Tip: press Enter to accept the suggested answer in [brackets].\n")

    # Step 1 — load file
    df = _step_load_csv()

    # Step 2 — pick columns
    lat_col, long_col, outcome_col = _step_pick_columns(df)

    # Step 3 — pick case value
    case_value = _step_pick_case_value(df, outcome_col)

    # Step 4 — build immediately (no confirmation needed)
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
    print(f"\n🗺️  Open this file in your browser:\n   {os.path.abspath(output_path)}\n")
    _line()
