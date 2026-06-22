"""Integration tests for the full SpotMap build pipeline.

Mirrors the R package's tests/testthat/test-spot-map.R. These exercise the
spatial join against the bundled boundary files, so they require the optional
geo stack (geopandas / shapely / folium). They skip cleanly if it's missing.
"""

import pandas as pd
import pytest

pytest.importorskip("geopandas")
pytest.importorskip("folium")

from spotmap import SpotMap  # noqa: E402
from spotmap.exceptions import ColumnNotFoundError  # noqa: E402


def test_all_cases_builds_a_map(tmp_path):
    df = pd.DataFrame({
        "fever": ["yes", "yes", "no", "yes"],
        "diarrhea": ["no", "yes", "yes", "no"],
        "lat": [11.0, 11.1, 11.2, 11.3],
        "lon": [76.9, 77.0, 77.1, 77.05],
    })
    out = tmp_path / "map.html"
    SpotMap(df, all_cases=True).build().save(str(out))
    assert out.exists()


def test_missing_outcome_column_errors_clearly():
    df = pd.DataFrame({
        "fever": ["yes", "no"],
        "lat": [11.0, 11.1],
        "lon": [76.9, 77.0],
    })
    with pytest.raises(ColumnNotFoundError, match="Could not find outcome column"):
        SpotMap(df).build()


def test_empty_dataframe_errors_clearly():
    df = pd.DataFrame({"lat": [], "lon": [], "case_control": []})
    with pytest.raises(ValueError, match="empty"):
        SpotMap(df).build()


def test_na_coordinates_dropped_with_warning(tmp_path):
    df = pd.DataFrame({
        "lat": [11.0, None, 11.2],
        "lon": [76.9, 77.0, 77.1],
        "case_control": ["case", "case", "control"],
    })
    out = tmp_path / "map.html"
    with pytest.warns(UserWarning, match="missing or out-of-range"):
        SpotMap(df).build().save(str(out))
    assert out.exists()


def test_normal_case_control_builds(tmp_path):
    df = pd.DataFrame({
        "lat": [11.0, 11.1, 11.2],
        "lon": [76.9, 77.0, 77.1],
        "case_control": ["case", "control", "case"],
    })
    out = tmp_path / "map.html"
    SpotMap(df).build().save(str(out))
    assert out.exists()


def test_map_has_label_toggles():
    df = pd.DataFrame({
        "lat": [11.0, 11.1, 28.6, 28.7],
        "lon": [76.9, 77.0, 77.2, 77.3],
        "case_control": ["case", "control", "case", "control"],
    })
    html = SpotMap(df).build().map.get_root().render()
    # Sidebar controls + JS wiring for the state/district label toggles
    assert "toggleStateLabels" in html
    assert "toggleDistrictLabels" in html
    assert "applyLabelLogic" in html
    assert "var stateLabelsLayer" in html
    assert "var districtLabelsLayer" in html
    # Actual label markers were rendered (more than just the CSS rule)
    assert html.count("spotmap-state-label") > 1
    assert html.count("spotmap-district-label") > 1


def test_save_before_build_raises():
    df = pd.DataFrame({
        "lat": [11.0], "lon": [76.9], "case_control": ["case"],
    })
    with pytest.raises(RuntimeError, match="build"):
        SpotMap(df).save("nope.html")
