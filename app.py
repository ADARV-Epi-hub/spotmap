"""Streamlit web app for SpotMap — no coding required.

Run locally:
    streamlit run app.py

Or deploy free at: https://share.streamlit.io
"""

import io
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from spotmap import SpotMap


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="SpotMap — Epidemiological Spot Maps",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ SpotMap")
st.caption("Interactive epidemiological spot maps for India — no coding required")

st.markdown("---")


# =========================================================
# STEP 1 — UPLOAD CSV
# =========================================================
st.header("Step 1 — Upload your CSV file")

uploaded = st.file_uploader(
    "Drag and drop your CSV file here, or click to browse",
    type=["csv"],
    help="Your CSV must contain latitude, longitude, and outcome columns.",
)

if uploaded is None:
    st.info("👆 Upload a CSV file to begin.")
    st.stop()

# Read the CSV
try:
    df = pd.read_csv(uploaded)
    df.columns = df.columns.str.strip()  # clean whitespace
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

st.success(f"✓ Loaded {len(df)} rows and {len(df.columns)} columns")

with st.expander("Preview data (first 5 rows)"):
    st.dataframe(df.head())


# =========================================================
# STEP 2 — SELECT COLUMNS
# =========================================================
st.header("Step 2 — Choose your columns")

cols = list(df.columns)

col1, col2, col3 = st.columns(3)

# Smart defaults
def _guess(candidates):
    for c in cols:
        if any(name in c.lower() for name in candidates):
            return c
    return cols[0]

with col1:
    lat_col = st.selectbox(
        "Latitude column",
        cols,
        index=cols.index(_guess(["lat", "latitude", "y"])),
    )

with col2:
    long_col = st.selectbox(
        "Longitude column",
        cols,
        index=cols.index(_guess(["lon", "long", "lng", "x"])),
    )

with col3:
    outcome_col = st.selectbox(
        "Outcome column",
        cols,
        index=cols.index(_guess(["outcome", "status", "case_control", "class"])),
    )

# Case value selector — pull unique values from the outcome column
unique_values = df[outcome_col].dropna().astype(str).str.strip().unique().tolist()

if not unique_values:
    st.error(f"Column '{outcome_col}' has no values.")
    st.stop()

case_value = st.selectbox(
    f"Which value in '{outcome_col}' represents a CASE?",
    unique_values,
)


# =========================================================
# STEP 3 — CUSTOMISE COLOURS (optional)
# =========================================================
st.header("Step 3 — Customise colours (optional)")

c1, c2, c3 = st.columns(3)

with c1:
    cluster_color = st.color_picker("Dot density (clusters)", "#E85252")
with c2:
    case_color = st.color_picker("Case pin colour", "#D55757")
with c3:
    control_color = st.color_picker("Control pin colour", "#7676E7")

count_cutoff = st.slider(
    "District count cutoff (lower = more zoomed in)",
    min_value=1, max_value=10, value=2,
)


# =========================================================
# STEP 4 — GENERATE MAP
# =========================================================
st.header("Step 4 — Generate the map")

if st.button("🚀 Generate Map", type="primary", use_container_width=True):

    with st.spinner("Building map... this takes a few seconds"):
        try:
            # Build map to a temp file
            tmp_path = Path(tempfile.gettempdir()) / "spotmap_output.html"

            SpotMap(
                df,
                lat_col=lat_col,
                long_col=long_col,
                outcome_col=outcome_col,
                case_value=case_value,
                count_cutoff=count_cutoff,
                cluster_color=cluster_color,
                case_color=case_color,
                control_color=control_color,
            ).build().save(str(tmp_path))

            html_bytes = tmp_path.read_bytes()

            st.success("✓ Map generated!")

            # Show it inline
            st.components.v1.html(
                html_bytes.decode("utf-8"),
                height=700,
                scrolling=False,
            )

            # Download button
            st.download_button(
                label="📥 Download HTML map",
                data=html_bytes,
                file_name="spotmap_output.html",
                mime="text/html",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.exception(e)


# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    "Built with [SpotMap](https://pypi.org/project/spotmap/) · "
    "[GitHub](https://github.com/ADARV-Epi-hub/spotmap)"
)
