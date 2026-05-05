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
html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif !important;
}
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
}
html, body, .stApp { color: #e8e8f0 !important; }
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }

.stTextInput input,
.stSelectbox select,
.stDateInput input,
.stTimeInput input {
    background: rgba(255,255,255,0.08) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}

::placeholder { color: rgba(255,255,255,0.6) !important; }

.stMarkdown, p, span, div, label { color: inherit !important; }

.metric-card .label,
.metric-card .value,
.metric-card .unit { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ── Matplotlib theme ───────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor":  "#1a1a2e",
    "axes.facecolor":    "#1a1a2e",
    "text.color":        "#e8e8f0",
})
ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 3.8)

# ── Helpers ────────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

# ✅ FIXED GEOCODE FUNCTION
@st.cache_data(show_spinner=False)
def geocode(location_name):
    try:
        query = location_name.strip()

        r = requests.get(
            GEOCODE_URL,
            params={
                "q": query,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
            },
            headers={
                "User-Agent": "weather-outfit-app (test@example.com)"
            },
            timeout=10,
        )

        if r.status_code != 200:
            return None

        results = r.json()

        # fallback if "denver, colorado" fails
        if not results and "," in query:
            query_simple = query.split(",")[0]
            r = requests.get(
                GEOCODE_URL,
                params={"q": query_simple, "format": "json", "limit": 1},
                headers={"User-Agent": "weather-outfit-app (test@example.com)"},
                timeout=10,
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
        except:
            tz = "UTC"

        return lat, lon, display, tz

    except:
        return None


@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz, daily_vars=None, hourly_vars=None):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&timezone={tz}"
    if daily_vars: url += "&daily=" + ",".join(daily_vars)
    if hourly_vars: url += "&hourly=" + ",".join(hourly_vars)
    r = requests.get(url, timeout=8)
    return r.json() if r.status_code == 200 else None


def outfit_for(temp_f, precip_pct, wind_mph):
    if temp_f < 45: return "🧥", "Jacket", "Cold — wear layers."
    if precip_pct > 60: return "☂️", "Umbrella", "Rain likely."
    if temp_f < 75: return "👕", "T-Shirt", "Nice weather."
    return "😎", "Summer Vibes", "Hot and sunny."

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    location_input = st.text_input("📍 Location", value="New York City")
    go = st.button("🔍 Get My Outfit")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather Outfit Advisor")

if not go:
    st.stop()

geo = geocode(location_input)

if not geo:
    st.error("❌ Couldn't find that location.")
    st.stop()

lat, lon, city_name, tz = geo

data = fetch_weather(
    lat, lon, tz,
    hourly_vars=["temperature_2m", "precipitation_probability", "wind_speed_10m"]
)

hourly = data["hourly"]
tf = to_f(hourly["temperature_2m"][0])
pr = hourly["precipitation_probability"][0]
wd = to_mph(hourly["wind_speed_10m"][0])

emoji, outfit, desc = outfit_for(tf, pr, wd)

st.markdown(f"""
### {emoji} {outfit}
{desc}

📍 {city_name}  
🌡️ {tf}°F  
🌧️ {pr}% rain  
💨 {wd} mph wind
""")
