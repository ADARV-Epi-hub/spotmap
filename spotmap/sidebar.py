"""Sidebar HTML/JS/CSS generation."""


def build_sidebar_html(
    map_id: str,
    dots_name: str,
    pins_cases_name: str,
    pins_controls_name: str,
    labels_name: str,
    mode: str,
    n_cases: int,
    n_controls: int,
    cluster_color: str,
    case_color: str,
    control_color: str,
) -> str:
    return f"""
<style>
:root {{
    --sm-primary: #1b2a5e;
    --sm-primary-2: #2a3d7a;
    --sm-accent: #2563eb;
    --sm-ink: #0f172a;
    --sm-muted: #64748b;
    --sm-border: #e2e8f0;
    --sm-surface: #ffffff;
    --sm-tint: #f8fafc;
}}
#sidebar-toggle-btn {{
    position: fixed; top: 16px; right: 16px; z-index: 10000;
    width: 44px; height: 44px; background: var(--sm-primary); border-radius: 10px;
    box-shadow: 0 4px 14px rgba(27,42,94,0.35); display: flex;
    align-items: center; justify-content: center; cursor: pointer;
    user-select: none; transition: all 0.18s ease;
}}
#sidebar-toggle-btn:hover {{ background: var(--sm-primary-2); transform: translateY(-1px); box-shadow: 0 6px 18px rgba(27,42,94,0.45); }}
#sidebar-toggle-btn span {{
    display: block; width: 20px; height: 2.5px;
    background: #ffffff; margin: 2.5px 0; border-radius: 2px;
}}
#map-sidebar {{
    position: fixed; top: 16px; right: 16px; bottom: 16px; width: 318px;
    z-index: 9999; background: var(--sm-surface); border-radius: 16px;
    box-shadow: 0 10px 40px rgba(15,23,42,0.18);
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px; color: var(--sm-ink); overflow-y: auto;
    transform: translateX(118%);
    transition: transform 0.32s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(15,23,42,0.05);
}}
#map-sidebar.open {{ transform: translateX(0); }}
#map-sidebar::-webkit-scrollbar {{ width: 7px; }}
#map-sidebar::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
.sidebar-header {{
    padding: 20px 20px 18px; position: relative; overflow: hidden;
    background: linear-gradient(135deg, var(--sm-primary) 0%, var(--sm-primary-2) 100%);
    border-radius: 16px 16px 0 0; color: #fff;
}}
.sidebar-header::after {{
    content: ""; position: absolute; top: -40px; right: -40px;
    width: 130px; height: 130px; border-radius: 50%;
    background: rgba(255,255,255,0.08);
}}
.sidebar-header h2 {{ margin: 0; font-size: 18px; font-weight: 700; letter-spacing: 0.2px; }}
.stat-row {{
    margin-top: 16px; display: flex; gap: 8px; position: relative; z-index: 1;
}}
.stat-card {{
    flex: 1; background: rgba(255,255,255,0.14); border-radius: 10px;
    padding: 9px 8px; text-align: center;
    border: 1px solid rgba(255,255,255,0.18);
}}
.stat-card b {{ font-size: 18px; font-weight: 700; display: block; line-height: 1.1; }}
.stat-card span {{ font-size: 9.5px; font-weight: 600; letter-spacing: 0.5px;
    text-transform: uppercase; opacity: 0.85; display: block; margin-top: 3px; }}
.sidebar-section {{ padding: 16px 20px; border-bottom: 1px solid var(--sm-border); }}
.sidebar-section h4 {{
    margin: 0 0 11px 0; font-size: 10.5px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.9px; color: var(--sm-muted);
    display: flex; align-items: center; gap: 7px;
}}
.sidebar-section h4::before {{
    content: ""; width: 3px; height: 12px; border-radius: 2px;
    background: var(--sm-accent); display: inline-block;
}}
.seg-control {{
    display: flex; background: var(--sm-tint); border-radius: 10px; padding: 4px; gap: 4px;
    border: 1px solid var(--sm-border);
}}
.seg-control label {{
    flex: 1; text-align: center; border-radius: 7px;
    cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.15s ease;
}}
.seg-control input {{ display: none; }}
.seg-control input:checked + span {{
    background: var(--sm-primary); box-shadow: 0 2px 6px rgba(27,42,94,0.28);
    color: #fff; font-weight: 600;
}}
.seg-control span {{
    display: block; padding: 8px 8px; border-radius: 7px;
    color: var(--sm-muted); transition: all 0.15s ease;
}}
.seg-control label:hover span {{ color: var(--sm-ink); }}
.swatch-row {{
    display: flex; gap: 10px; align-items: center; margin: 8px 0;
    padding: 8px 10px; background: var(--sm-tint); border-radius: 9px;
    border: 1px solid var(--sm-border);
}}
.swatch-row label {{ flex: 1; font-size: 12.5px; font-weight: 500; color: #334155; }}
.swatch-row input[type="color"] {{
    width: 42px; height: 30px; border: 1px solid var(--sm-border); border-radius: 7px;
    cursor: pointer; padding: 2px; background: #fff;
}}
input[type="range"] {{ width: 100%; accent-color: var(--sm-accent); height: 5px; }}
.slider-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 6px 10px; background: var(--sm-tint); border-radius: 9px;
    border: 1px solid var(--sm-border);
}}
.slider-value {{
    min-width: 38px; font-size: 12.5px; font-weight: 700; color: var(--sm-accent);
    text-align: right;
}}
.btn {{
    display: block; width: 100%; padding: 11px 12px; margin: 8px 0 0;
    background: var(--sm-primary); color: #fff; border: none; border-radius: 9px;
    cursor: pointer; font-size: 12.5px; font-weight: 600; text-align: center;
    text-decoration: none; transition: all 0.16s ease; letter-spacing: 0.2px;
}}
.btn:hover {{ background: var(--sm-primary-2); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(27,42,94,0.25); }}
.btn.secondary {{ background: #fff; color: var(--sm-primary); border: 1.5px solid var(--sm-border); }}
.btn.secondary:hover {{ background: var(--sm-tint); border-color: var(--sm-accent); color: var(--sm-accent); }}
.sidebar-foot {{
    padding: 13px 20px; text-align: center; font-size: 10px; color: #94a3b8;
    letter-spacing: 0.3px; background: var(--sm-tint); border-radius: 0 0 16px 16px;
}}
.spot-filter {{ display: none; margin-top: 12px; }}
.spot-filter.show {{ display: block; }}
#map-legend {{
    position: absolute; top: 16px; left: 60px; z-index: 1000; background: #fff;
    padding: 12px 16px; border-radius: 12px; box-shadow: 0 6px 24px rgba(15,23,42,0.15);
    font-size: 12px; font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    min-width: 120px; display: none; border: 1px solid var(--sm-border);
}}
#map-legend h4 {{
    margin: 0 0 9px 0; font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.7px; color: var(--sm-muted); text-align: center;
}}
.legend-item {{
    display: flex; align-items: center; margin-bottom: 6px;
    font-size: 12.5px; font-weight: 500; color: var(--sm-ink);
}}
.legend-icon {{
    width: 15px; height: 15px; border-radius: 50%;
    margin-right: 10px; border: 1px solid rgba(0,0,0,0.12);
}}
.toggle-row {{
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    padding: 10px 12px; margin: 6px 0;
    background: var(--sm-tint); border-radius: 9px; border: 1px solid var(--sm-border);
    font-size: 12.5px; font-weight: 500; color: #334155;
}}
.toggle-state {{
    font-size: 11px; font-weight: 700; color: var(--sm-muted);
    text-transform: uppercase; letter-spacing: 0.5px; min-width: 22px; text-align: right;
}}
.switch {{ position: relative; display: inline-block; width: 42px; height: 22px; flex: 0 0 auto; }}
.switch input {{ opacity: 0; width: 0; height: 0; margin: 0; }}
.slider-toggle {{
    position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
    background: #cbd5e1; border-radius: 22px; transition: 0.2s;
}}
.slider-toggle::before {{
    content: ""; position: absolute; height: 16px; width: 16px; left: 3px; bottom: 3px;
    background: #fff; border-radius: 50%; transition: 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}}
.switch input:checked + .slider-toggle {{ background: var(--sm-primary); }}
.switch input:checked + .slider-toggle::before {{ transform: translateX(20px); }}
#map-credit {{
    position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
    z-index: 1000; background: rgba(255,255,255,0.92); color: var(--sm-primary);
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 11px; font-weight: 600; letter-spacing: 0.2px;
    padding: 5px 13px; border-radius: 8px; border: 1px solid var(--sm-border);
    box-shadow: 0 2px 8px rgba(15,23,42,0.12); pointer-events: none; white-space: nowrap;
}}
@media print {{
    * {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
    }}
    html, body {{ background: #fff !important; }}
    #map-sidebar, #sidebar-toggle-btn {{ display: none !important; }}
    #map-legend {{
        display: block !important; position: absolute; top: 10px; left: 10px;
        background: #fff !important; border: 1px solid #ccc;
    }}
    .legend-icon {{ border: 1px solid #333 !important; }}
    .leaflet-control-zoom, .leaflet-control-attribution {{ display: none !important; }}
    .cluster-icon > div, .marker-cluster div {{ box-shadow: none !important; }}
}}
</style>

<div id="sidebar-toggle-btn" title="Map options">
  <div><span></span><span></span><span></span></div>
</div>

<div id="map-credit">Interactive spot maps for India &middot; created by ADARV</div>

<div id="map-legend">
    <h4>Legend</h4>
    <div class="legend-item" id="legend-case-item">
        <span class="legend-icon" id="legend-icon-case" style="background-color:{case_color};"></span>
        <span>Case</span>
    </div>
    <div class="legend-item" id="legend-control-item" style="display:none;">
        <span class="legend-icon" id="legend-icon-control" style="background-color:{control_color};"></span>
        <span>Control</span>
    </div>
</div>

<div id="map-sidebar">
  <div class="sidebar-header">
    <h2>SpotMap</h2>
    <div class="stat-row">
      <div class="stat-card"><b>{n_cases}</b><span>Cases</span></div>
      <div class="stat-card"><b>{n_controls}</b><span>Controls</span></div>
      <div class="stat-card"><b>{mode}</b><span>Zoom</span></div>
    </div>
  </div>

  <div class="sidebar-section">
    <h4>Display Mode</h4>
    <div class="seg-control">
      <label>
        <input type="radio" name="markerMode" value="dots" checked>
        <span>Dot Density</span>
      </label>
      <label>
        <input type="radio" name="markerMode" value="pins">
        <span>Spot Pins</span>
      </label>
    </div>
    <div class="spot-filter" id="spotFilterBox">
      <h4 style="margin-top:12px;">Show</h4>
      <div class="seg-control">
        <label>
          <input type="radio" name="spotFilterMode" value="cases" checked>
          <span>Cases Only</span>
        </label>
        <label>
          <input type="radio" name="spotFilterMode" value="both">
          <span>Cases &amp; Controls</span>
        </label>
      </div>
    </div>
  </div>

  <div class="sidebar-section" id="clusterColorSection">
    <h4>Cluster Colour</h4>
    <div class="swatch-row">
      <label>Pick a colour</label>
      <input type="color" id="clusterCustomColor" value="{cluster_color}">
    </div>
  </div>

  <div class="sidebar-section" id="pinColorSection" style="display:none;">
    <h4>Pin Colours</h4>
    <div class="swatch-row">
      <label>Cases</label>
      <input type="color" id="caseColorPicker" value="{case_color}">
    </div>
    <div class="swatch-row">
      <label>Controls</label>
      <input type="color" id="controlColorPicker" value="{control_color}">
    </div>
    <h4 style="margin-top:14px;">Pin Size</h4>
    <div class="slider-row">
      <input type="range" id="pinSizeSlider" min="0.5" max="2.0" step="0.1" value="1.0">
      <span class="slider-value" id="pinSizeValue">1.0x</span>
    </div>
  </div>

  <div class="sidebar-section">
    <h4>Map Labels</h4>
    <div class="toggle-row">
      <span>Place names</span>
      <span style="display:flex; align-items:center; gap:9px;">
        <span class="toggle-state" id="labelsState">Off</span>
        <label class="switch">
          <input type="checkbox" id="toggleLabels">
          <span class="slider-toggle"></span>
        </label>
      </span>
    </div>
  </div>

  <div class="sidebar-section">
    <h4>Export Map</h4>
    <a class="btn" id="downloadPngLink">Download PNG</a>
    <a class="btn secondary" id="downloadPrintLink">Print / Save PDF</a>
  </div>

  <div class="sidebar-foot">Generated with SpotMap &middot; spotmap</div>
</div>

<script src="https://unpkg.com/leaflet-simple-map-screenshoter"></script>
<script>
window.addEventListener('load', function() {{
  var mapObj            = {map_id};
  var dotsLayer         = {dots_name};
  var pinsCasesLayer    = {pins_cases_name};
  var pinsControlsLayer = {pins_controls_name};
  var labelsLayer = {labels_name};

  // Move legend inside map container so screenshoter captures it
  var legendDiv = document.getElementById('map-legend');
  mapObj.getContainer().appendChild(legendDiv);

  // Move the ADARV credit caption inside the map container too
  var creditDiv = document.getElementById('map-credit');
  if (creditDiv) mapObj.getContainer().appendChild(creditDiv);

  var simpleMapScreenshoter = L.simpleMapScreenshoter({{
      hidden: true,
      mimeType: 'image/png'
  }}).addTo(mapObj);

  var sidebar = document.getElementById('map-sidebar');
  var toggleBtn = document.getElementById('sidebar-toggle-btn');
  var sidebarOpen = true;
  sidebar.classList.add('open');

  toggleBtn.addEventListener('click', function() {{
    sidebarOpen = !sidebarOpen;
    sidebar.classList.toggle('open', sidebarOpen);
  }});

  window.caseColor    = '{case_color}';
  window.controlColor = '{control_color}';
  window.clusterBaseColor = '{cluster_color}';
  window.pinScale = 1.0;

  function updateLegend() {{
    var legendBox = document.getElementById('map-legend');
    var isPins = document.querySelector('input[name="markerMode"]:checked').value === 'pins';
    legendBox.style.display = isPins ? 'block' : 'none';
    if (!isPins) return;
    document.getElementById('legend-icon-case').style.backgroundColor = window.caseColor;
    document.getElementById('legend-icon-control').style.backgroundColor = window.controlColor;
    var isBoth = document.querySelector('input[name="spotFilterMode"]:checked').value === 'both';
    document.getElementById('legend-control-item').style.display = isBoth ? 'flex' : 'none';
  }}

  function makePinIcon(colorHex) {{
    var scale = window.pinScale || 1.0;
    var baseW = 18, baseH = 24;
    var html =
      '<div style="position:relative;width:'+baseW+'px;height:'+baseH+'px;transform:scale('+scale+');transform-origin:50% 100%;">' +
        '<div style="position:absolute;left:3px;top:6px;width:12px;height:12px;border-radius:50% 50% 50% 0;background:'+colorHex+';transform:rotate(-45deg);box-shadow:0 0 2px rgba(0,0,0,0.5);"></div>' +
        '<div style="position:absolute;left:6.5px;top:9.5px;width:5px;height:5px;border-radius:50%;background:white;opacity:0.9;"></div>' +
      '</div>';
    return new L.DivIcon({{ html: html, className: '', iconSize: [baseW, baseH], iconAnchor: [baseW/2, baseH] }});
  }}

  function redrawPins() {{
    if (pinsCasesLayer) {{
      pinsCasesLayer.eachLayer(function(marker) {{
        if (marker.setIcon) marker.setIcon(makePinIcon(window.caseColor));
      }});
    }}
    if (pinsControlsLayer) {{
      pinsControlsLayer.eachLayer(function(marker) {{
        if (marker.setIcon) marker.setIcon(makePinIcon(window.controlColor));
      }});
    }}
    updateLegend();
  }}

  function refreshClusters() {{
    // Use the proper Leaflet.markercluster API to force redraw
    if (dotsLayer && typeof dotsLayer.refreshClusters === 'function') {{
      dotsLayer.refreshClusters();
    }} else if (mapObj.hasLayer(dotsLayer)) {{
      // Fallback for older versions: full remove + re-add
      mapObj.removeLayer(dotsLayer);
      mapObj.addLayer(dotsLayer);
    }}
  }}

  function applyLayerLogic() {{
    var mode = document.querySelector('input[name="markerMode"]:checked').value;
    var filter = document.querySelector('input[name="spotFilterMode"]:checked').value;

    // Show/hide UI sections based on mode
    document.getElementById('spotFilterBox').classList.toggle('show', mode === 'pins');
    document.getElementById('clusterColorSection').style.display = mode === 'dots' ? 'block' : 'none';
    document.getElementById('pinColorSection').style.display = mode === 'pins' ? 'block' : 'none';

    if (mode === 'dots') {{
      if (!mapObj.hasLayer(dotsLayer)) mapObj.addLayer(dotsLayer);
      if (mapObj.hasLayer(pinsCasesLayer)) mapObj.removeLayer(pinsCasesLayer);
      if (mapObj.hasLayer(pinsControlsLayer)) mapObj.removeLayer(pinsControlsLayer);
    }} else {{
      if (mapObj.hasLayer(dotsLayer)) mapObj.removeLayer(dotsLayer);
      if (!mapObj.hasLayer(pinsCasesLayer)) mapObj.addLayer(pinsCasesLayer);
      if (filter === 'both') {{
        if (!mapObj.hasLayer(pinsControlsLayer)) mapObj.addLayer(pinsControlsLayer);
      }} else {{
        if (mapObj.hasLayer(pinsControlsLayer)) mapObj.removeLayer(pinsControlsLayer);
      }}
      redrawPins();
    }}
    updateLegend();
  }}

  document.querySelectorAll('input[type=radio]').forEach(function(r) {{
    r.addEventListener('change', applyLayerLogic);
  }});

  // === Cluster colour — live update on every change ===
  var custClust = document.getElementById('clusterCustomColor');
  if (custClust) {{
    custClust.addEventListener('input', function() {{
      window.clusterBaseColor = custClust.value;
      refreshClusters();
    }});
  }}

  // === Pin colours — live update (no Apply button needed) ===
  document.getElementById('caseColorPicker').addEventListener('input', function(e) {{
    window.caseColor = e.target.value;
    redrawPins();
  }});
  document.getElementById('controlColorPicker').addEventListener('input', function(e) {{
    window.controlColor = e.target.value;
    redrawPins();
  }});

  // === Pin size ===
  var sizeSlider = document.getElementById('pinSizeSlider');
  var sizeValue = document.getElementById('pinSizeValue');
  sizeSlider.addEventListener('input', function(e) {{
    window.pinScale = parseFloat(e.target.value);
    sizeValue.textContent = window.pinScale.toFixed(1) + 'x';
    redrawPins();
  }});

  // === Export ===
  document.getElementById('downloadPrintLink').addEventListener('click', function() {{ window.print(); }});
  document.getElementById('downloadPngLink').addEventListener('click', function() {{
    sidebar.classList.remove('open');
    sidebarOpen = false;
    setTimeout(function() {{
      simpleMapScreenshoter.takeScreen('blob', {{ caption: function() {{ return ''; }} }})
        .then(function(blob) {{
          var link = document.createElement('a');
          link.download = 'spotmap.png';
          link.href = URL.createObjectURL(blob);
          link.click();
        }})
        .catch(function(e) {{ alert(e); }})
        .finally(function() {{
          sidebar.classList.add('open');
          sidebarOpen = true;
        }});
    }}, 500);
  }});

  // === OpenStreetMap place labels — default off ===
  function applyLabelLogic() {{
    var show = document.getElementById('toggleLabels').checked;
    if (show) {{ if (!mapObj.hasLayer(labelsLayer)) mapObj.addLayer(labelsLayer); }}
    else {{ if (mapObj.hasLayer(labelsLayer)) mapObj.removeLayer(labelsLayer); }}
    document.getElementById('labelsState').textContent = show ? 'On' : 'Off';
  }}
  document.getElementById('toggleLabels').addEventListener('change', applyLabelLogic);
  applyLabelLogic();

  applyLayerLogic();
  redrawPins();
}});
</script>
"""
