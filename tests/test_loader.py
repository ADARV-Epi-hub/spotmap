"""Unit tests for column/value detection in spotmap.loader.

Mirrors the R package's tests/testthat/test-loader.R so the two
implementations stay in sync.
"""

import numpy as np
import pandas as pd
import pytest

from spotmap.exceptions import ColumnNotFoundError
from spotmap.loader import detect_lat_lon, detect_outcome, load_csv


# ---------------------------------------------------------------------------
# detect_lat_lon
# ---------------------------------------------------------------------------

def test_detect_lat_lon_finds_named_columns():
    df = pd.DataFrame(
        {"latitude": [28.6, 19.0], "longitude": [77.2, 72.8],
         "outcome": ["case", "control"]}
    )
    lat, lon = detect_lat_lon(df)
    assert lat == "latitude"
    assert lon == "longitude"


def test_detect_lat_lon_with_explicit_columns():
    df = pd.DataFrame({"y": [28.6, 19.0], "x": [77.2, 72.8]})
    lat, lon = detect_lat_lon(df, lat_col="y", long_col="x")
    assert lat == "y"
    assert lon == "x"


def test_detect_lat_lon_errors_on_missing_explicit_columns():
    df = pd.DataFrame({"a": [1], "b": [2]})
    with pytest.raises(ColumnNotFoundError, match="not found"):
        detect_lat_lon(df, lat_col="lat", long_col="lon")


def test_detect_lat_lon_splits_combined_column():
    df = pd.DataFrame({"coords": ["28.6, 77.2", "19.0, 72.8"]})
    lat, lon = detect_lat_lon(df)
    assert lat == "_spotmap_auto_lat"
    assert lon == "_spotmap_auto_lon"
    assert "_spotmap_auto_lat" in df.columns
    assert "_spotmap_auto_lon" in df.columns
    np.testing.assert_allclose(df["_spotmap_auto_lat"].tolist(), [28.6, 19.0])
    np.testing.assert_allclose(df["_spotmap_auto_lon"].tolist(), [77.2, 72.8])


def test_detect_lat_lon_accepts_scientific_notation():
    df = pd.DataFrame(
        {"lat": ["1.1e1", "1.11e1", "1.12e1"],
         "lon": ["7.69e1", "7.70e1", "7.71e1"]}
    )
    lat, lon = detect_lat_lon(df)
    assert lat == "lat"
    assert lon == "lon"


def test_detect_lat_lon_errors_when_undetectable():
    df = pd.DataFrame({"name": ["a", "b"], "note": ["x", "y"]})
    with pytest.raises(ColumnNotFoundError, match="auto-detect"):
        detect_lat_lon(df)


# ---------------------------------------------------------------------------
# detect_outcome
# ---------------------------------------------------------------------------

def test_detect_outcome_finds_standard_column_names():
    df = pd.DataFrame({"lat": [1, 1, 1], "lon": [2, 2, 2],
                       "outcome": ["case", "control", "case"]})
    outcome_col, case_value = detect_outcome(df)
    assert outcome_col == "outcome"
    assert case_value == "case"


def test_detect_outcome_uses_explicit_values():
    df = pd.DataFrame({"status": ["pos", "neg", "pos"]})
    outcome_col, case_value = detect_outcome(df, outcome_col="status",
                                             case_value="pos")
    assert outcome_col == "status"
    assert case_value == "pos"


def test_detect_outcome_case_value_is_normalised_lowercase():
    df = pd.DataFrame({"status": ["POS", "NEG"]})
    _, case_value = detect_outcome(df, outcome_col="status", case_value="POS")
    assert case_value == "pos"


def test_detect_outcome_errors_when_case_value_absent():
    df = pd.DataFrame({"status": ["pos", "neg"]})
    with pytest.raises(ColumnNotFoundError, match="not found in outcome column"):
        detect_outcome(df, outcome_col="status", case_value="missing")


def test_detect_outcome_errors_on_missing_column():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ColumnNotFoundError, match="not found"):
        detect_outcome(df, outcome_col="missing")


def test_detect_outcome_errors_when_no_outcome_column():
    df = pd.DataFrame({"fever": ["yes", "no"], "lat": [1, 2], "lon": [3, 4]})
    with pytest.raises(ColumnNotFoundError, match="Could not find outcome column"):
        detect_outcome(df)


# ---------------------------------------------------------------------------
# load_csv (DataFrame input path)
# ---------------------------------------------------------------------------

def test_load_csv_empty_dataframe_errors():
    df = pd.DataFrame({"lat": [], "lon": [], "case_control": []})
    with pytest.raises(ValueError, match="empty"):
        load_csv(df)


def test_load_csv_drops_bad_coordinates_with_warning():
    df = pd.DataFrame({
        "lat": [11.0, np.nan, 11.2],
        "lon": [76.9, 77.0, 77.1],
        "case_control": ["case", "case", "control"],
    })
    with pytest.warns(UserWarning, match="missing or out-of-range"):
        out_df, lat_col, lon_col, outcome_col, case_value = load_csv(df)
    assert len(out_df) == 2
    assert case_value == "case"


def test_load_csv_all_bad_coordinates_errors():
    df = pd.DataFrame({
        "lat": [np.nan, 999.0],
        "lon": [77.0, 77.1],
        "case_control": ["case", "control"],
    })
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError, match="All rows"):
            load_csv(df)


def test_load_csv_all_cases_skips_outcome_detection():
    df = pd.DataFrame({
        "fever": ["yes", "no"],
        "lat": [11.0, 11.1],
        "lon": [76.9, 77.0],
    })
    out_df, lat_col, lon_col, outcome_col, case_value = load_csv(
        df, all_cases=True
    )
    assert case_value == "case"
    assert (out_df["_spotmap_outcome_norm"] == "case").all()
