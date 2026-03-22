# Brandrisico Monitor — Uitbreidingshandleiding

## Architectuur

Het systeem bestaat uit twee losse onderdelen:

```
monitor.py          → Backend: haalt data op, berekent risicoscore, slaat state op
fire-monitor-map/   → Frontend: haalt zelf live data op, toont kaart + sidebar
```

Beide zijn onafhankelijk uitbreidbaar. De backend draait als cron (1x per dag), de frontend haalt bij elke pageload realtime data op uit de API's.

---

## 1. Nieuwe databron toevoegen aan de BACKEND (monitor.py)

### Stap 1: Data-ophaalfunctie schrijven

Voeg een nieuwe functie toe in het `# ── Data Collection` blok (rond regel 102):

```python
def get_mijn_databron():
    """Omschrijving van wat deze bron levert."""
    url = "https://api.example.com/data?param=value"
    # Voor API's met key: voeg header toe
    # headers = {"Authorization": "Bearer JOUW_API_KEY"}
    data = fetch_json(url)
    if not data:
        return None
    # Verwerk en return wat je nodig hebt
    return data
```

**Voor API's met authenticatie**, pas `fetch_json` aan of maak een variant:

```python
def fetch_json_auth(url, api_key, timeout=15):
    """Fetch met API key in header."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "FireMonitor/1.0",
            "Authorization": f"Bearer {api_key}",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return None
```

**API keys** kun je opslaan in een apart configuratiebestand:

```python
# Bovenaan monitor.py
CONFIG_FILE = os.path.join(TRACKING_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

# config.json voorbeeld:
# {
#   "nasa_firms_key": "jouw-key-hier",
#   "openweather_key": "...",
#   "sentinel_hub_key": "..."
# }
```

### Stap 2: Integreren in de risicoscore

In `calculate_risk_score()` (regel 227), voeg een nieuw scoreblok toe:

```python
# ── Jouw nieuwe factor (0-X punten) ──
if mijn_nieuwe_data:
    waarde = mijn_nieuwe_data.get("relevant_veld", 0)
    if waarde > drempel_hoog:
        score += 1.0; details.append(f"Hoog risico via [bronnaam]: {waarde}")
    elif waarde > drempel_middel:
        score += 0.5; details.append(f"Matig risico via [bronnaam]: {waarde}")
```

**Let op:** de maximale theoretische score is nu ~7 punten, genormaliseerd naar 1-5 op regel 325. Als je veel factoren toevoegt, pas de normalisatie aan:

```python
# Huidige normalisatie (regel 325):
risk_level = min(5, max(1, round(score * 5 / 6)))

# Na toevoegen van bijv. 3 extra punten:
risk_level = min(5, max(1, round(score * 5 / 9)))
```

### Stap 3: Doorvoeren in run_monitor()

Roep je nieuwe functie aan in `run_monitor()` (rond regel 338):

```python
# Collect data
forecasts, agg_forecasts = get_ipma_forecasts()
warnings = get_ipma_warnings()
fires = get_active_fires()
mijn_data = get_mijn_databron()          # ← Nieuw

# En geef het mee aan calculate_risk_score:
risk_level, details = calculate_risk_score(
    region_name, forecast_today, forecast_tomorrow,
    warnings, region_fires,
    mijn_data=mijn_data                   # ← Nieuw argument
)
```

### Stap 4: Toevoegen aan het rapport

In `build_report()` (regel 470), voeg een nieuwe sectie toe:

```python
# Na de bestaande secties
if mijn_data:
    lines.append("\n### Mijn Nieuwe Indicator")
    lines.append(f"- Waarde: {mijn_data['veld']}")
    lines.append(f"- Trend: {mijn_data['trend']}")
```

---

## 2. Nieuwe databron toevoegen aan de FRONTEND (kaart)

### Stap 1: Data ophalen in loadData()

In `index.html`, in de `loadData()` functie (zoek naar `Promise.all`):

```javascript
const [forecastDay0, forecastCovilha, warningsData, firesData, mijnData] = await Promise.all([
  fetchJSON('https://api.ipma.pt/...'),
  fetchJSON('https://api.ipma.pt/...'),
  fetchJSON('https://api.ipma.pt/...'),
  fetchJSON('https://api-dev.fogos.pt/new/fires'),
  fetchJSON('https://api.example.com/data'),     // ← Nieuw
]);
```

### Stap 2: Nieuwe kaartlaag toevoegen

```javascript
// Na de fire markers sectie
if (mijnData) {
  mijnData.features.forEach(feature => {
    const [lon, lat] = feature.geometry.coordinates;
    L.circleMarker([lat, lon], {
      radius: 6,
      color: '#60a5fa',
      fillColor: '#60a5fa',
      fillOpacity: 0.5,
    }).addTo(map).bindPopup(`
      <div class="popup-title">${feature.properties.naam}</div>
      <div class="popup-detail">${feature.properties.waarde}</div>
    `);
  });
}
```

### Stap 3: Sidebar-sectie toevoegen

Voeg een nieuwe `<div class="sidebar-section">` toe in de HTML:

```html
<div class="sidebar-section">
  <h2>Mijn Indicator</h2>
  <div id="mijn-indicator-list"></div>
</div>
```

En vul het in JavaScript:

```javascript
const mijnEl = document.getElementById('mijn-indicator-list');
mijnEl.innerHTML = mijnData
  ? `<p style="font-size:12px;">Waarde: ${mijnData.value}</p>`
  : '<p style="font-size:12px;color:var(--text-muted);">Geen data</p>';
```

---

## 3. Concrete API's die je direct kunt toevoegen

### A. NASA FIRMS — Satelliet-hotspots (gratis, API key nodig)

Registreer op https://firms.modaps.eosdis.nasa.gov/api/area/ voor een gratis key.

```python
def get_nasa_firms(api_key):
    """VIIRS satelliet-hotspots binnen bounding box Centro Portugal."""
    # bbox: west,south,east,north
    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{api_key}/VIIRS_SNPP_NRT/-8.5,39.5,-6.5,41.5/1"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FireMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            import csv, io
            text = resp.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            hotspots = []
            for row in reader:
                lat, lon = float(row["latitude"]), float(row["longitude"])
                dist = haversine_km(COVILHA_LAT, COVILHA_LON, lat, lon)
                if dist <= 50:  # 50km filter
                    hotspots.append({
                        "lat": lat, "lon": lon,
                        "brightness": float(row.get("bright_ti4", 0)),
                        "confidence": row.get("confidence", ""),
                        "frp": float(row.get("frp", 0)),  # Fire Radiative Power
                        "acq_time": row.get("acq_time", ""),
                        "distance_km": round(dist, 1),
                    })
            return hotspots
    except Exception as e:
        print(f"  [WARN] FIRMS failed: {e}", file=sys.stderr)
        return []
```

**Risicoscore-integratie:**
```python
# In calculate_risk_score():
if firms_hotspots:
    high_confidence = [h for h in firms_hotspots if h["confidence"] in ("high", "h")]
    if len(high_confidence) >= 3:
        score += 1.0; details.append(f"🛰️ {len(high_confidence)} satelliet-hotspots")
    elif len(high_confidence) >= 1:
        score += 0.5; details.append(f"🛰️ {len(high_confidence)} satelliet-hotspot(s)")
```

### B. Sentinel-2 NDVI via Copernicus Data Space (gratis)

Vereist OAuth2-token van https://dataspace.copernicus.eu/

```python
def get_sentinel_ndvi(access_token, bbox="-8.0,40.0,-7.0,40.6"):
    """Haal NDVI-statistieken op via Sentinel Hub Statistical API."""
    url = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
    payload = json.dumps({
        "input": {
            "bounds": {"bbox": [float(x) for x in bbox.split(",")]},
            "data": [{"type": "sentinel-2-l2a", "dataFilter": {"maxCloudCoverage": 30}}]
        },
        "aggregation": {
            "timeRange": {"from": "2026-03-10T00:00:00Z", "to": "2026-03-17T23:59:59Z"},
            "aggregationInterval": {"of": "P7D"}
        },
        "calculations": {"ndvi": {"histograms": {"bins": {"nbins": 10}}}}
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    })
    # ... parse response voor gemiddelde NDVI
```

### C. OpenWeatherMap — Uurlijkse data + UV-index (gratis tier)

```python
def get_openweather_detail(api_key, lat, lon):
    """Gedetailleerde weerdata inclusief UV, dauwpunt, luchtvochtigheid."""
    url = (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        f"&exclude=minutely"
    )
    data = fetch_json(url)
    if not data:
        return None
    current = data.get("current", {})
    return {
        "humidity": current.get("humidity"),       # Luchtvochtigheid %
        "dew_point": current.get("dew_point"),     # Dauwpunt °C
        "uvi": current.get("uvi"),                 # UV-index
        "wind_gust": current.get("wind_gust"),     # Windstoten m/s
        "hourly_precip": sum(                      # Neerslag komende 12u
            h.get("pop", 0) for h in data.get("hourly", [])[:12]
        ) / 12,
    }
```

**Risicoscore-integratie:**
```python
if ow_data:
    # Lage luchtvochtigheid = hoger risico
    if ow_data["humidity"] and ow_data["humidity"] < 20:
        score += 0.8; details.append(f"Zeer droge lucht: {ow_data['humidity']}% RV")
    elif ow_data["humidity"] and ow_data["humidity"] < 35:
        score += 0.4; details.append(f"Droge lucht: {ow_data['humidity']}% RV")
    # UV > 8 = extra uitdrogingsrisico
    if ow_data["uvi"] and ow_data["uvi"] >= 8:
        score += 0.3; details.append(f"Hoge UV: {ow_data['uvi']}")
```

### D. EFFIS FWI via WMS (gratis, geen key)

```python
def get_effis_fwi(lat, lon):
    """Fire Weather Index van EFFIS via GetFeatureInfo."""
    # EFFIS WMS endpoint
    url = (
        "https://ies-ows.jrc.ec.europa.eu/effis"
        f"?service=WMS&version=1.1.1&request=GetFeatureInfo"
        f"&layers=ecmwf007.fwi&query_layers=ecmwf007.fwi"
        f"&info_format=application/json"
        f"&srs=EPSG:4326&width=1&height=1"
        f"&bbox={lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}"
        f"&x=0&y=0"
    )
    data = fetch_json(url)
    if data and "features" in data and data["features"]:
        props = data["features"][0].get("properties", {})
        return {
            "fwi": props.get("fwi"),
            "isi": props.get("isi"),    # Initial Spread Index
            "bui": props.get("bui"),    # Build Up Index
            "ffmc": props.get("ffmc"),  # Fine Fuel Moisture Code
            "dc": props.get("dc"),      # Drought Code
        }
    return None
```

### E. ICNF — Áreas ardidas shapefile (gratis)

Via https://geocatalogo.icnf.pt/ kun je shapefiles downloaden van historische brandgebieden. Integratie met `shapely`/`geopandas` voor overlap-analyse.

### F. SoilGrids — Bodemvocht (gratis)

```python
def get_soil_moisture(lat, lon):
    """Bodemvocht via ISRIC SoilGrids API."""
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=bdod&depth=0-5cm&value=mean"
    return fetch_json(url)
```

---

## 4. Notificatie-triggers uitbreiden

In `detect_changes()` (regel 416), voeg nieuwe triggers toe:

```python
# Voorbeeld: notificeer als FWI boven extreme drempel komt
prev_fwi = prev_state.get("fwi_scores", {})
curr_fwi = current_state.get("fwi_scores", {})
for region, curr_val in curr_fwi.items():
    prev_val = prev_fwi.get(region, 0)
    if curr_val >= 50 and prev_val < 50:  # Extreme drempel
        changes.append({
            "type": "fwi_extreme",
            "region": region,
            "message": f"🌡️ {region}: FWI naar EXTREEM ({curr_val})"
        })

# Vergeet niet dit type toe te voegen aan should_notify (regel 559):
should_notify = any(
    c["type"] in ("risk_increase", "new_fire", "warning_upgrade", "fwi_extreme")
    for c in changes
)
```

---

## 5. Configuratiebestand (config.json)

Maak `/home/user/workspace/cron_tracking/fire_monitor/config.json`:

```json
{
  "nasa_firms_key": null,
  "openweather_key": null,
  "sentinel_hub_client_id": null,
  "sentinel_hub_client_secret": null,
  "custom_apis": [
    {
      "name": "Mijn sensor netwerk",
      "url": "https://mijn-api.example.com/data",
      "auth_header": "X-API-Key",
      "auth_value": "...",
      "field_mapping": {
        "risk_field": "fire_risk_index",
        "lat_field": "latitude",
        "lon_field": "longitude"
      },
      "risk_weight": 0.5,
      "risk_thresholds": {"low": 0, "medium": 30, "high": 60, "extreme": 80}
    }
  ]
}
```

---

## 6. Samenvatting: wat je kunt doen

| Wat                        | Waar                          | Moeite   |
|---------------------------|-------------------------------|----------|
| Gratis API toevoegen       | `monitor.py` + `index.html`   | 30 min   |
| Betaalde API met key       | + `config.json` voor keys     | 45 min   |
| Nieuwe kaartlaag           | `index.html` in `loadData()`  | 20 min   |
| Extra risicofactor         | `calculate_risk_score()`      | 15 min   |
| Nieuwe notificatie-trigger | `detect_changes()`            | 10 min   |
| Eigen sensor/IoT data      | Nieuwe `get_*()` functie      | 1-2 uur  |
| Sentinel-2 satellietdata   | OAuth2 + Statistical API      | 2-3 uur  |
