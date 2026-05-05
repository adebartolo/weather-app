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

# ── Custom CSS (UPDATED ONLY THIS SECTION) ─────────────────────────────────────
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
    st.markdown('<div style="font-size:1.6rem;font-weight:800;margin-bottom:0.2rem">🌤️ What to Wear</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:inherit;font-size:0.82rem;margin-bottom:1.5rem">Dress smarter, not harder.</div>', unsafe_allow_html=True)

    location_input = st.text_input("📍 Location", value="New York City")

    st.markdown('<div class="section-title">Outfit Check</div>', unsafe_allow_html=True)
    col_d, col_t = st.columns(2)
    with col_d:
        target_date = st.date_input("Date", value=datetime.date.today() + datetime.timedelta(days=1))
    with col_t:
        time_options = [
            (datetime.datetime.strptime(f"{h}:{m:02d}", "%H:%M")).strftime("%-I:%M %p")
            for h in range(24)
            for m in [0, 30]
        ]
        selected_time_str = st.selectbox("Time", time_options, index=26)
        target_time = datetime.datetime.strptime(selected_time_str, "%I:%M %p").time()

    units = st.radio("Temperature Units", ["°F", "°C"], horizontal=True)

    go = st.button("🔍  Get My Outfit", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown('<h1 style="font-weight:800;font-size:2.4rem;">Weather · Outfit Advisor</h1>', unsafe_allow_html=True)

if not go:
    st.info("👈 Set inputs and click Get My Outfit.")
    st.stop()

geo = geocode(location_input)
if not geo:
    st.error("Location not found.")
    st.stop()

lat, lon, city_name, tz_str = geo
data = fetch_weather(lat, lon, tz_str,
    hourly_vars=["temperature_2m", "precipitation_probability", "wind_speed_10m"]
)

hourly = data["hourly"]
temps_f = [to_f(v) for v in hourly["temperature_2m"]]
precips = hourly["precipitation_probability"]
winds = [to_mph(w) for w in hourly["wind_speed_10m"]]

tf, pr, wd = temps_f[0], precips[0], winds[0]

emoji, outfit_name, outfit_desc = outfit_for(tf, pr, wd)

st.markdown(f"<div class='outfit-banner'><div>{emoji}</div><div>{outfit_name}</div><div>{outfit_desc}</div></div>", unsafe_allow_html=True)
