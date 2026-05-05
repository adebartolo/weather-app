import streamlit as st
import requests
import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>

/* Font consistency */
html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif !important;
}

/* Keep your dark gradient */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
}

/* Ensure readable default text */
html, body, .stApp {
    color: #e8e8f0 !important;
}

/* Sidebar */
[data-testid="stSidebar"] * {
    color: #e8e8f0 !important;
}

/* FIX: Inputs always visible */
.stTextInput input,
.stSelectbox select,
.stDateInput input,
.stTimeInput input {
    background: rgba(255,255,255,0.08) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}

/* Placeholder text */
::placeholder {
    color: rgba(255,255,255,0.6) !important;
}

/* Buttons */
.stButton > button {
    font-family: Arial, Helvetica, sans-serif !important;
    color: #ffffff !important;
}

/* Prevent invisible text anywhere */
.stMarkdown, p, span, div, label {
    color: inherit !important;
}

/* Metric cards safety */
.metric-card .label,
.metric-card .value,
.metric-card .unit {
    color: #ffffff !important;
}

</style>
""", unsafe_allow_html=True)

# ── Matplotlib dark theme ──────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor":  "#1a1a2e",
    "axes.facecolor":    "#1a1a2e",
    "axes.edgecolor":    "#333355",
    "axes.labelcolor":   "#aaaacc",
    "text.color":        "#e8e8f0",
    "xtick.color":       "#888899",
    "ytick.color":       "#888899",
    "grid.color":        "#2a2a4a",
    "grid.linewidth":    0.7,
    "font.family":       "DejaVu Sans",
    "font.size":         9,
})
ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 3.8)

# ── Utility helpers ────────────────────────────────────────────────────────────
def to_f(c):  return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

@st.cache_data(show_spinner=False)
def geocode(location_name):
    """Return (lat, lon, display_name, timezone_str) or None."""
    try:
        r = requests.get(
            GEOCODE_URL,
            params={"q": location_name, "format": "json", "limit": 1},
            headers={"User-Agent": "WeatherOutfitApp/1.0"},
            timeout=6,
        )
        results = r.json()
        if not results:
            return None
        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        display = results[0]["display_name"].split(",")[0]

        # Timezone via timezonefinder (fallback: UTC)
        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        except Exception:
            tz = "UTC"

        return lat, lon, display, tz
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz, daily_vars=None, hourly_vars=None):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&timezone={tz}"
    )
    if daily_vars:  url += "&daily="  + ",".join(daily_vars)
    if hourly_vars: url += "&hourly=" + ",".join(hourly_vars)
    r = requests.get(url, timeout=8)
    return r.json() if r.status_code == 200 else None

def outfit_for(temp_f, precip_pct, wind_mph):
    if temp_f < 32:
        return "🧥", "Heavy Parka + Layers", "Extreme cold — insulated coat, thermal base, gloves, hat, scarf."
    if temp_f < 45:
        return "🧣", "Heavy Jacket + Scarf", "Very cold — puffy or wool coat with warm accessories."
    if temp_f < 55:
        return "🧥", "Jacket", "Cool out — a mid-weight jacket should do it."
    if temp_f < 65:
        return "🧤", "Light Jacket / Sweater", "Mild — a light layer over a shirt works great."
    if precip_pct > 60:
        return "☂️", "Bring an Umbrella!", "Rain likely — waterproof layer and grab that umbrella."
    if temp_f < 75:
        if wind_mph > 20:
            return "💨", "T-Shirt + Wind Breaker", "Comfortable temp but windy — a light shell helps."
        return "👕", "T-Shirt Weather", "Comfortable — light clothing, maybe a tee and jeans."
    if precip_pct > 40:
        return "🌦️", "Light Clothes + Umbrella", "Warm but some rain chance — stay light and be ready."
    return "😎", "Summer Vibes", "Hot and sunny — shorts, sunscreen, and shades!"

# ── Sidebar inputs ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:0.2rem">🌤️ What to Wear</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:rgba(255,255,255,0.4);font-size:0.82rem;margin-bottom:1.5rem">Dress smarter, not harder.</div>', unsafe_allow_html=True)

    location_input = st.text_input("📍 Location", value="New York City", placeholder="City, Country…")

    st.markdown('<div class="section-title">Outfit Check</div>', unsafe_allow_html=True)
    col_d, col_t = st.columns(2)
    with col_d:
        target_date = st.date_input("Date", value=datetime.date.today() + datetime.timedelta(days=1))
    with col_t:
        time_options = [
            (datetime.datetime.strptime(f"{h}:{m:02d}", "%H:%M")).strftime("%-I:%M %p")
            for h in range(24)
            for m in [0, 30]  # every 30 min (change to [0,15,30,45] if needed)
        ]
    
        selected_time_str = st.selectbox("Time", time_options, index=26)  # ~1:00 PM default
    
        # Convert back to datetime.time object for your logic
        target_time = datetime.datetime.strptime(selected_time_str, "%I:%M %p").time()

    units = st.radio("Temperature Units", ["°F", "°C"], horizontal=True)
    
    st.markdown('<div class="section-title">Charts</div>', unsafe_allow_html=True)
    show_7day    = st.checkbox("7-Day Forecast",   value=True)
    show_24h     = st.checkbox("24-Hour Forecast", value=True)
    forecast_hrs = st.slider("Hours to show (24h chart)", 6, 48, 24, step=6)

    go = st.button("🔍  Get My Outfit", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown('<h1 style="font-family:Syne,sans-serif;font-weight:800;font-size:2.4rem;margin-bottom:0.1rem">Weather · Outfit Advisor</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:rgba(255,255,255,0.45);margin-bottom:1.5rem">Enter your location and time, then see exactly what to wear.</p>', unsafe_allow_html=True)

if not go:
    st.info("👈  Set your location and preferences in the sidebar, then hit **Get My Outfit**.")
    st.stop()

# ── Geocode ────────────────────────────────────────────────────────────────────
with st.spinner(f"Looking up **{location_input}**…"):
    geo = geocode(location_input)

if not geo:
    st.error("❌ Couldn't find that location. Try a different city name.")
    st.stop()

lat, lon, city_name, tz_str = geo

# ── Fetch hourly data ──────────────────────────────────────────────────────────
with st.spinner("Fetching weather data…"):
    data = fetch_weather(
        lat, lon, tz_str,
        hourly_vars=["temperature_2m", "precipitation_probability", "wind_speed_10m"],
        daily_vars=["temperature_2m_min", "temperature_2m_max",
                    "precipitation_probability_max", "wind_speed_10m_max"],
    )

if not data:
    st.error("❌ Failed to fetch weather data. Try again later.")
    st.stop()

# ── Parse hourly ───────────────────────────────────────────────────────────────
hourly = data["hourly"]
times  = [datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in hourly["time"]]
temps_f  = [to_f(v) for v in hourly["temperature_2m"]]
temps_c  = [round(v, 1) for v in hourly["temperature_2m"]]
precips  = hourly["precipitation_probability"]
winds    = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── Match target datetime ──────────────────────────────────────────────────────
target_dt = datetime.datetime.combine(target_date, target_time).replace(minute=0, second=0, microsecond=0)
available_dates = {t.date() for t in times}

if target_date not in available_dates:
    st.error("📅 That date is outside the 7-day forecast window. Pick a closer date.")
    st.stop()

best_idx = min(
    (i for i, t in enumerate(times) if t.date() == target_date),
    key=lambda i: abs((times[i] - target_dt).total_seconds()),
    default=None,
)

if best_idx is None:
    st.error("No data for that time.")
    st.stop()

tf  = temps_f[best_idx]
tc  = temps_c[best_idx]
pr  = precips[best_idx]
wd  = winds[best_idx]
display_temp = f"{tf}°F" if units == "°F" else f"{tc}°C"

# ── Outfit result ──────────────────────────────────────────────────────────────
emoji, outfit_name, outfit_desc = outfit_for(tf, pr, wd)

st.markdown(f"""
<div class="outfit-banner">
  <div class="emoji">{emoji}</div>
  <div class="title">{outfit_name}</div>
  <div class="desc">{outfit_desc}</div>
</div>
""", unsafe_allow_html=True)

# ── Metric row ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
metrics = [
    ("📍 Location", city_name, ""),
    ("🌡️ Temperature", display_temp, ""),
    ("🌧️ Rain Chance", f"{pr}%", "precipitation"),
    ("💨 Wind", f"{wd} mph", ""),
]
for col, (lbl, val, _) in zip([c1,c2,c3,c4], metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div class="label">{lbl}</div>
          <div class="value">{val}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("")

# ── 7-Day chart ────────────────────────────────────────────────────────────────
if show_7day:
    st.markdown('<div class="section-title">7-Day Forecast</div>', unsafe_allow_html=True)
    daily = data["daily"]
    d_dates = daily["time"]
    d_tmin  = [to_f(t) for t in daily["temperature_2m_min"]]
    d_tmax  = [to_f(t) for t in daily["temperature_2m_max"]]
    d_prec  = daily["precipitation_probability_max"]
    d_wind  = [to_mph(w) for w in daily["wind_speed_10m_max"]]

    if units == "°C":
        d_tmin = [round((v - 32)*5/9, 1) for v in d_tmin]
        d_tmax = [round((v - 32)*5/9, 1) for v in d_tmax]

    days = [datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%b %d") for d in d_dates]

    fig, ax1 = plt.subplots(figsize=CHART_SIZE)
    ax1.fill_between(days, d_tmin, d_tmax, alpha=0.12, color=ACCENT1)
    ax1.plot(days, d_tmin, color=ACCENT1, marker="o", linewidth=2, label=f"Min ({units})")
    ax1.plot(days, d_tmax, color=ACCENT2, marker="o", linewidth=2, label=f"Max ({units})")
    ax1.plot(days, d_wind, color=ACCENT3, marker="x", linestyle="--", linewidth=1.5, label="Wind (mph)")
    ax1.set_ylabel(f"Temp ({units}) / Wind (mph)", color="#aaaacc")
    ax1.grid(True, alpha=0.4)

    ax2 = ax1.twinx()
    ax2.bar(days, d_prec, color=ACCENT1, alpha=0.22, label="Rain %", zorder=0)
    ax2.set_ylim(0, 130)
    ax2.set_ylabel("Precipitation (%)", color="#aaaacc")
    ax2.tick_params(colors="#888899")

    lines, labels = ax1.get_legend_handles_labels()
    bar_patch = mpatches.Patch(color=ACCENT1, alpha=0.4, label="Rain %")
    ax1.legend(handles=lines + [bar_patch], loc="upper center",
               bbox_to_anchor=(0.5, -0.18), ncol=4,
               facecolor="#1a1a2e", edgecolor="#333355")

    plt.title(f"7-Day Forecast — {city_name}", pad=12)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# ── 24-Hour chart ──────────────────────────────────────────────────────────────
if show_24h:
    st.markdown(f'<div class="section-title">Next {forecast_hrs}-Hour Forecast</div>', unsafe_allow_html=True)

    now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    filt_t, filt_tmp, filt_pr, filt_wd = [], [], [], []
    for i, t in enumerate(times):
        if t >= now and len(filt_t) < forecast_hrs:
            filt_t.append(t.strftime("%-I %p"))
            tmp = temps_f[i] if units == "°F" else temps_c[i]
            filt_tmp.append(tmp)
            filt_pr.append(precips[i])
            filt_wd.append(winds[i])

    fig2, ax3 = plt.subplots(figsize=CHART_SIZE)
    ax3.fill_between(filt_t, filt_tmp, alpha=0.1, color=ACCENT2)
    ax3.plot(filt_t, filt_tmp, color=ACCENT2, marker="o", markersize=4, linewidth=2, label=f"Temp ({units})")
    ax3.plot(filt_t, filt_wd,  color=ACCENT3, marker="x", linestyle="--", linewidth=1.5, label="Wind (mph)")
    ax3.set_ylabel(f"Temp ({units}) / Wind (mph)", color="#aaaacc")
    ax3.grid(True, alpha=0.4)

    # x-tick thinning
    step = max(1, len(filt_t) // 12)
    ax3.set_xticks(range(0, len(filt_t), step))
    ax3.set_xticklabels(filt_t[::step], rotation=30, ha="right")

    ax4 = ax3.twinx()
    ax4.bar(filt_t, filt_pr, color=ACCENT1, alpha=0.22, label="Rain %", zorder=0)
    ax4.set_ylim(0, 130)
    ax4.set_ylabel("Precipitation (%)", color="#aaaacc")
    ax4.tick_params(colors="#888899")

    lines3, labels3 = ax3.get_legend_handles_labels()
    bar_patch2 = mpatches.Patch(color=ACCENT1, alpha=0.4, label="Rain %")
    ax3.legend(handles=lines3 + [bar_patch2], loc="upper center",
               bbox_to_anchor=(0.5, -0.22), ncol=3,
               facecolor="#1a1a2e", edgecolor="#333355")

    plt.title(f"Next {forecast_hrs}h Forecast — {city_name}", pad=12)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""<hr style="border-color:rgba(255,255,255,0.08);margin-top:2rem">
<div style="text-align:center;color:rgba(255,255,255,0.25);font-size:0.8rem">
Weather data via Open-Meteo · Geocoding via Nominatim
</div>""", unsafe_allow_html=True)
