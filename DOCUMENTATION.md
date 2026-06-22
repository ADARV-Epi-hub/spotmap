# SpotMap — Developer Documentation

Internal/architecture guide for the **spotmap** package. For installation and
end-user usage, see [README.md](README.md). This document explains how the code
is organised, how data flows through the pipeline, and the conventions a
contributor needs to know.

---

## 1. What SpotMap does

SpotMap turns a table of case/control coordinates into a self-contained
interactive HTML map for India. Each row becomes a point; points are spatially
joined to bundled state and district boundaries, split into cases vs. controls,
and rendered with [Folium](https://python-visualization.github.io/folium/)
(Leaflet under the hood). The output HTML embeds a sidebar (mode toggle, colour
pickers, pin-size slider, PNG/PDF export) and needs no server to view.

Two presentation modes share the same data:

- **Dot density** — a `MarkerCluster` of cases whose bubble colour deepens with
  local case count.
- **Spot pins** — individual teardrop pins for cases and (optionally) controls.

---

## 2. Project layout

```
spotmap/
├── spotmap/                  # the installable package
│   ├── __init__.py           # public exports + __version__
│   ├── map_builder.py        # SpotMap class — orchestrates the pipeline
│   ├── loader.py             # file reading + column/case auto-detection
│   ├── spatial.py            # boundary loading, spatial join, mode/zoom logic
│   ├── layers.py             # Folium cluster + pin layer builders
│   ├── sidebar.py            # generated HTML/CSS/JS control panel
│   ├── interactive.py        # spotmap_run() terminal wizard for non-coders
│   ├── cli.py                # `spotmap` console-script entry point
│   ├── exceptions.py         # SpotMapError hierarchy
│   └── data/                 # bundled India boundaries (FlatGeobuf)
│       ├── state_boundary_lite.fgb
│       └── district_boundary_lite.fgb
├── app.py                    # Streamlit web front-end (uses the package)
├── tests/                    # (currently empty — see §8)
├── pyproject.toml            # build metadata + dependencies
├── requirements.txt          # deps for running app.py / the Streamlit deploy
├── README.md                 # user-facing docs
└── DOCUMENTATION.md          # this file
```

There are three independent entry points, all of which converge on the
`SpotMap` class:

| Entry point | Audience | Lives in |
|---|---|---|
| `SpotMap(...).build().save(...)` | Python developers | `map_builder.py` |
| `spotmap <csv> -o out.html` | command-line users | `cli.py` |
| `spotmap_run()` / `streamlit run app.py` | non-coders | `interactive.py` / `app.py` |

---

## 3. The build pipeline

`SpotMap.build()` ([spotmap/map_builder.py](spotmap/map_builder.py)) runs the
whole pipeline and stores the Folium map on `self._map`. It returns `self` so
calls chain: `SpotMap(data).build().save("map.html")`.

```
data (path or DataFrame)
        │
        ▼
┌───────────────────────────────────────────────┐
│ 1. load_csv()                loader.py         │
│    • read CSV / Excel / TSV                     │
│    • auto-detect lat / lon columns             │
│    • coerce coords to numeric, drop bad rows   │
│    • auto-detect outcome column + case value   │
│    → df, lat_col, long_col, outcome_col,       │
│      case_value                                │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ 2. load_boundaries()         spatial.py        │
│    • read bundled / custom state & district    │
│      polygons, reproject to WGS84, make valid  │
│    → states, districts, name columns           │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ 3. spatial_join()            spatial.py        │
│    • point-in-polygon: attach state & district │
│      name to every point                       │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ 4. split cases / controls    map_builder.py    │
│    mask = _spotmap_outcome_norm == case_value  │
│    (raises NoCasePointsError if no cases)       │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ 5. determine_mode() + crop   spatial.py        │
│    • pick districts / states / india zoom      │
│    • crop boundary layers to data bbox+margin  │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ 6–9. render                  layers/sidebar.py │
│    • init folium.Map, fit_bounds to target     │
│    • add boundary GeoJson layers               │
│    • add cluster + case/control pin layers     │
│    • inject sidebar HTML/CSS/JS                 │
└───────────────────────────────────────────────┘
        │
        ▼
   self._map  →  .save(path)
```

---

## 4. Module reference

### `loader.py` — reading & auto-detection
- **`load_csv(data, lat_col, long_col, outcome_col, case_value)`** is the entry.
  Accepts a path (`.csv`, `.xlsx/.xls/.xlsm/.xlsb/.ods`, `.tsv/.txt`) **or** a
  `pandas.DataFrame`. Strips column-name whitespace, coerces coordinates to
  numeric, and **drops rows** with missing / out-of-range coordinates (with a
  `UserWarning`). Raises `ValueError` if the data is empty or every row is
  invalid.
- **Coordinate detection** (`detect_lat_lon`): if the user supplies both column
  names they are validated; otherwise it looks for a combined `"lat,lon"` column
  (`_is_pair_col` / `_detect_from_combined`), then for separately named numeric
  columns (matching `_LAT_NAMES` / `_LON_NAMES`), then falls back to "the only
  two numeric columns". A combined column is split into hidden
  `_spotmap_auto_lat` / `_spotmap_auto_lon` columns, disambiguating lat vs. lon
  by magnitude (anything with |value| > 90 must be longitude).
- **Outcome detection** (`detect_outcome`): searches column names against
  `_OUTCOME_CANDIDATES`; picks the case value from `_CASE_VALUES`
  (`case`, `1`, `yes`, `true`, `positive`, …) or defaults to the first value.
  The returned `case_value` is normalised to lowercase.
- A **sanity check** warns (does not fail) if fewer than half the points fall
  inside India's bounding box (lat 6–38, lon 67–98) — usually a sign of swapped
  lat/lon columns.

> **Note on naming:** the canonical Python keyword for longitude is
> **`long_col`** everywhere in the package API. The CLI flag is spelled
> `--lon-col` and is mapped to `long_col` inside `cli.py`. See §7.

### `spatial.py` — geometry
- **`load_boundaries`** reads the bundled FlatGeobuf files (or custom paths),
  ensures WGS84 (EPSG:4326) and valid geometries, and resolves the name column
  from a list of candidates (`ST_NM`, `STATE`, `dtname`, …) so it tolerates
  different shapefile schemas.
- **`spatial_join`** builds `shapely` points from the coordinates and does two
  left `sjoin`s (district, then state) with `predicate="within"`, de-duplicating
  on index. `_get_col_safe` handles the `_shp`-suffixed column names that
  GeoPandas produces on join collisions.
- **`determine_mode`** chooses the zoom target: ≤ `count_cutoff` affected
  districts → `"districts"`; many states → `"india"`; otherwise `"states"`. It
  also returns the case-point bounding box used for cropping and `fit_bounds`.
- **`crop_geodataframe`** trims boundary layers to the data bbox plus
  `margin_deg`, keeping the file small; it returns the original frame if the crop
  would be empty.

### `layers.py` — Folium rendering
- **`add_boundary_layers`** adds three non-interactive `GeoJson` overlays: India
  outline, affected states, affected districts.
- **`add_marker_layers`** builds the `MarkerCluster` (dot density) plus two
  `FeatureGroup`s for case and control pins, and returns the three layers so the
  sidebar JS can reference them by Leaflet variable name. `_cluster_icon_fn`
  emits the JavaScript that colours each cluster bubble by case fraction.

### `sidebar.py` — the control panel
A single function, **`build_sidebar_html`**, returns an f-string of
HTML + CSS + JS that is injected into the map root. It wires up the
dots/pins toggle, live colour pickers, pin-size slider, legend, and the
PNG/print export (via `leaflet-simple-map-screenshoter`). It references the
Leaflet objects by the names returned from `add_marker_layers` and
`map.get_name()`.

### `map_builder.py` — orchestration
The **`SpotMap`** class holds configuration and runs the pipeline. Key options:
`state_shp` / `district_shp` (custom boundaries), `lat_col` / `long_col` /
`outcome_col` / `case_value` (override auto-detection), `count_cutoff` (zoom
threshold), `margin_deg` (crop padding), and the three colour overrides.
`.save()` raises `RuntimeError` if called before `.build()`.

### `cli.py` — console script
Argparse front-end registered as the `spotmap` entry point in
`pyproject.toml`. Every error is caught and printed to stderr with exit code 1.

### `interactive.py` — terminal wizard
**`spotmap_run(output_path)`** is a friendly, retry-on-error prompt flow for
non-coders: load file → pick columns → pick the case value (with value-count
bars) → build. `run_interactive` is a **deprecated alias** kept for backward
compatibility (emits `DeprecationWarning`).

### `exceptions.py`
```
SpotMapError
├── ColumnNotFoundError   # lat/lon/outcome column can't be found or is invalid
└── NoCasePointsError     # no rows match the chosen case value
```

---

## 5. Public API surface

Exported from `spotmap/__init__.py`:

| Name | Kind | Notes |
|---|---|---|
| `SpotMap` | class | main entry point |
| `spotmap_run` | function | interactive terminal wizard |
| `run_interactive` | function | **deprecated** alias of `spotmap_run` |
| `SpotMapError` | exception | base class |
| `ColumnNotFoundError` | exception | |
| `NoCasePointsError` | exception | |

---

## 6. Dependencies & data

Runtime deps (`pyproject.toml`): `folium`, `geopandas`, `numpy`, `pandas`,
`shapely`, `openpyxl` (Excel support). `app.py` additionally needs `streamlit`.
Python ≥ 3.9.

Boundary data ships inside the wheel under `spotmap/data/` as FlatGeobuf
(`.fgb`) files, so no shapefile setup is required by the user. `load_boundaries`
sets `SHAPE_RESTORE_SHX=YES` for resilience when custom shapefiles are passed.

---

## 7. Bug fixed in this pass

**CLI was completely broken — keyword-argument mismatch.**

`cli.py` constructed `SpotMap(..., lon_col=args.lon_col, ...)`, but the
`SpotMap.__init__` keyword is `long_col` (keyword-only). Every CLI invocation
therefore crashed before producing a map:

```
Error: SpotMap.__init__() got an unexpected keyword argument 'lon_col'.
Did you mean 'long_col'?
```

**Fix:** map the `--lon-col` argument to the correct keyword in
[spotmap/cli.py](spotmap/cli.py):

```diff
-            lon_col=args.lon_col,
+            long_col=args.lon_col,
```

The `README.md` Python-API reference was also updated from `lon_col=None` to
`long_col=None` to match the real signature. The Python API, Streamlit app, and
interactive wizard were already passing `long_col` correctly and were
unaffected.

Verified after the fix: `spotmap data.csv -o map.html` and the explicit
`--lat-col/--lon-col/--case-value` form both produce maps; combined-column and
`y`/`x` auto-detection paths also build successfully.

---

## 8. Gaps / good next steps

- **No automated tests.** `tests/` contains only an empty `__init__.py`. The
  CLI regression above would have been caught by one end-to-end test. Worth
  adding `pytest` cases for: CLI smoke test, combined-column detection,
  lat/lon swap warning, and `NoCasePointsError`.
- **Naming consistency.** Consider accepting `lon_col` as an alias for
  `long_col` in `SpotMap.__init__` so the public kwarg matches the common
  ecosystem spelling and the `--lon-col` flag.
- **`dist/` artifacts** for old versions (0.1.10–0.1.12) are checked into the
  working tree; consider `.gitignore`-ing `dist/`.
