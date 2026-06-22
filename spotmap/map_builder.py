"""Main SpotMap class — orchestrates loading, spatial join, and map building."""

import folium
import pandas as pd

from .exceptions import NoCasePointsError
from .layers import add_boundary_layers, add_marker_layers, add_label_layers
from .loader import load_csv
from .sidebar import build_sidebar_html
from .spatial import (
    build_india_outline,
    crop_geodataframe,
    determine_mode,
    load_boundaries,
    spatial_join,
)

_DEFAULT_CLUSTER_COLOR = "#E85252"
_DEFAULT_CASE_COLOR = "#D55757"
_DEFAULT_CONTROL_COLOR = "#7676E7"


class SpotMap:
    """Build an interactive epidemiological spot map for India.

    Parameters
    ----------
    data:
        Path to a CSV file **or** a pandas DataFrame containing point data.
    state_shp:
        Optional path to a custom state boundary file (shapefile / GeoPackage /
        FlatGeobuf).  Defaults to the bundled India state boundaries.
    district_shp:
        Optional path to a custom district boundary file.  Defaults to the
        bundled India district boundaries.
    lat_col:
        Column name for latitude.  Auto-detected when omitted.
    long_col:
        Column name for longitude.  Auto-detected when omitted.
    outcome_col:
        Column name for the case/control outcome.  Auto-detected when omitted.
    case_value:
        Value in *outcome_col* that represents a **case**.  Auto-detected when
        omitted.
    all_cases:
        If ``True``, skip outcome detection and treat every row as a case (no
        controls on the map).  Useful for outbreak surveillance or case-only
        datasets that have no control group.  Defaults to ``False``.
    count_cutoff:
        If the number of affected districts is ≤ this value, the map zooms to
        district level; otherwise to state or national level.
    margin_deg:
        Padding (degrees) added around the data bounding box when cropping
        boundary layers.
    cluster_color:
        Hex colour for the dot-density cluster bubbles.
    case_color:
        Hex colour for case pins in spot-map mode.
    control_color:
        Hex colour for control pins in spot-map mode.
    """

    def __init__(
        self,
        data,
        *,
        state_shp: str = None,
        district_shp: str = None,
        lat_col: str = None,
        long_col: str = None,
        outcome_col: str = None,
        case_value: str = None,
        all_cases: bool = False,
        count_cutoff: int = 2,
        margin_deg: float = 1.0,
        cluster_color: str = _DEFAULT_CLUSTER_COLOR,
        case_color: str = _DEFAULT_CASE_COLOR,
        control_color: str = _DEFAULT_CONTROL_COLOR,
    ):
        if not isinstance(data, (str, pd.DataFrame)):
            raise TypeError("data must be a file path (str) or a pandas DataFrame.")
        self.data = data
        self.state_shp = state_shp
        self.district_shp = district_shp
        self.lat_col = lat_col
        self.long_col = long_col
        self.outcome_col = outcome_col
        self.case_value = case_value
        self.all_cases = all_cases
        self.count_cutoff = count_cutoff
        self.margin_deg = margin_deg
        self.cluster_color = cluster_color
        self.case_color = case_color
        self.control_color = control_color

        self._map: folium.Map = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> "SpotMap":
        """Run the full pipeline and store the Folium map internally.

        Returns *self* so calls can be chained: ``SpotMap(...).build().save(...)``.
        """
        # 1. Load data (path or DataFrame)
        df, lat_col, long_col, outcome_col, case_value = load_csv(
            self.data,
            lat_col=self.lat_col,
            long_col=self.long_col,
            outcome_col=self.outcome_col,
            case_value=self.case_value,
            all_cases=self.all_cases,
        )

        # 2. Load boundaries
        states, districts, state_name_col, district_name_col = load_boundaries(
            state_shp=self.state_shp,
            district_shp=self.district_shp,
        )

        # 3. Spatial join
        points_joined = spatial_join(
            df, lat_col, long_col, states, districts, state_name_col, district_name_col
        )

        # 4. Split cases / controls
        mask = points_joined["_spotmap_outcome_norm"] == case_value
        points_cases = points_joined[mask].copy()
        points_controls = points_joined[~mask].copy()

        if points_cases.empty:
            raise NoCasePointsError(
                f"No case points found with outcome value '{case_value}'."
            )

        # 5. Determine mode + crop boundaries
        mode, affected_dist_names, unique_state_names, bounds = determine_mode(
            points_cases, district_name_col, state_name_col, self.count_cutoff
        )

        india_outline = build_india_outline(states)
        affected_states = states[states[state_name_col].isin(unique_state_names)].copy()
        affected_districts = districts[
            districts[district_name_col].isin(affected_dist_names)
        ].copy()

        india_sub = crop_geodataframe(india_outline, bounds, self.margin_deg)
        states_sub = crop_geodataframe(affected_states, bounds, self.margin_deg)
        districts_sub = crop_geodataframe(affected_districts, bounds, self.margin_deg)

        # 6. Init map
        m = folium.Map(
            location=[points_cases.geometry.y.mean(), points_cases.geometry.x.mean()],
            zoom_start=5,
            tiles="CartoDB positron",
            zoom_snap=0.1,
            zoom_delta=0.1,
            max_zoom=25,
            scroll_wheel_zoom=True,
        )

        # 7. Boundary layers
        add_boundary_layers(m, india_sub, states_sub, districts_sub)

        # 7a. Label layers (toggled from the sidebar)
        state_labels, district_labels = add_label_layers(
            m, states_sub, districts_sub, state_name_col, district_name_col
        )

        # 7b. Auto-zoom to the most relevant view
        import numpy as np
        n_states_uniq = len(unique_state_names)
        n_dist_uniq = len(affected_dist_names)

        target_bounds = None
        if n_states_uniq > 1:
            target_bounds = affected_states.total_bounds if not affected_states.empty else bounds
        elif n_states_uniq == 1:
            if n_dist_uniq > 1:
                target_bounds = affected_states.total_bounds if not affected_states.empty else bounds
            else:
                target_bounds = affected_districts.total_bounds if not affected_districts.empty else bounds
        else:
            target_bounds = bounds

        if target_bounds is not None and np.isfinite(target_bounds).all():
            min_x, min_y, max_x, max_y = target_bounds
            span_x = max_x - min_x
            span_y = max_y - min_y
            buffer_ratio = 0.05
            fit_box = [
                [min_y - span_y * buffer_ratio, min_x - span_x * buffer_ratio],
                [max_y + span_y * buffer_ratio, max_x + span_x * buffer_ratio],
            ]
            m.fit_bounds(fit_box)

        # 8. Marker layers
        cluster, pins_cases, pins_controls = add_marker_layers(
            m,
            points_cases,
            points_controls,
            state_name_col,
            district_name_col,
            cluster_color=self.cluster_color,
            case_color=self.case_color,
            control_color=self.control_color,
        )

        # 9. Sidebar
        sidebar_html = build_sidebar_html(
            map_id=m.get_name(),
            dots_name=cluster.get_name(),
            pins_cases_name=pins_cases.get_name(),
            pins_controls_name=pins_controls.get_name(),
            state_labels_name=state_labels.get_name(),
            district_labels_name=district_labels.get_name(),
            mode=mode,
            n_cases=len(points_cases),
            n_controls=len(points_controls),
            cluster_color=self.cluster_color,
            case_color=self.case_color,
            control_color=self.control_color,
        )
        m.get_root().html.add_child(folium.Element(sidebar_html))

        self._map = m
        return self

    def save(self, output_path: str) -> "SpotMap":
        """Save the built map to an HTML file."""
        if self._map is None:
            raise RuntimeError("Call .build() before .save().")
        self._map.save(output_path)
        return self

    @property
    def map(self) -> folium.Map:
        """The underlying Folium map object (after build)."""
        if self._map is None:
            raise RuntimeError("Call .build() first.")
        return self._map
