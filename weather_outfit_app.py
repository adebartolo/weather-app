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

# ── Simple styling (safe + stable) ─────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif;
}
.stApp {
    background: #0f0c29;
    color: #e8e8f0;
}
</style>
""", unsafe_allow_html=True)

# ── Matplotlib theme ───────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#1a1a2e",
    "axes.edgecolor": "#333355",
    "axes.labelcolor": "#aaaacc",
    "text.color": "#e8e8f0",
    "xtick.color": "#888899",
    "ytick.color": "#888899",
    "grid.color": "#2a2a4a",
    "grid.linewidth": 0.7,
    "font.family": "DejaVu Sans",
    "font.size": 9,
})

ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 3.8)

# ── Helpers ────────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ── GEOCODER (FIXED + RELIABLE) ────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):
    """
    Stable geocoder using Open-Meteo.
    Returns structured error messages for API failure vs no results.
    """
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"

        r = requests.get(
            url,
            params={
                "name": location_name,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=8
        )

        # 🔴 API failure / rate limit
        if r.status_code != 200:
            return {"error": "API_LIMITED"}

        data = r.json()

        if "results" not in data or len(data["results"]) == 0:
            return {"error": "NOT_FOUND"}

        place = data["results"][0]

        lat = place["latitude"]
        lon = place["longitude"]

        name = place.get("name", location_name)
        country = place.get("country", "")
        display = f"{name}, {country}" if country else name

        # timezone fallback
        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        except:
            tz = "UTC"

        return {
            "lat": lat,
            "lon": lon,
            "name": display,
            "tz": tz
        }

    except Exception:
        return {"error": "API_LIMITED"}

# ── Weather API ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz):
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&timezone={tz}"
            "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
            "&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
        )

        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return {"error": "API_LIMITED"}

        return r.json()

    except Exception:
        return {"error": "API_LIMITED"}

# ── Outfit logic ───────────────────────────────────────────────────────────────
def outfit_for(temp_f, precip_pct, wind_mph):
    if temp_f < 32:
        return "🧥", "Heavy Parka", "Extreme cold — bundle up."
    if temp_f < 45:
        return "🧣", "Heavy Jacket", "Very cold."
    if temp_f < 55:
        return "🧥", "Jacket", "Cool weather."
    if precip_pct > 60:
        return "☂️", "Umbrella Needed", "Rain likely."
    if wind_mph > 20:
        return "💨", "Wind Breaker", "Windy conditions."
    if temp_f < 75:
        return "👕", "T-Shirt Weather", "Comfortable."
    return "😎", "Summer Vibes", "Hot and sunny."

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌤️ What to Wear")

    location_input = st.text_input("📍 Location", "New York City")

    target_date = st.date_input(
        "Date",
        value=datetime.date.today() + datetime.timedelta(days=1)
    )

    time_options = [
        datetime.datetime.strptime(f"{h}:{m:02d}", "%H:%M").strftime("%-I:%M %p")
        for h in range(24) for m in [0, 30]
    ]
    selected_time_str = st.selectbox("Time", time_options, index=26)
    target_time = datetime.datetime.strptime(selected_time_str, "%I:%M %p").time()

    units = st.radio("Units", ["°F", "°C"])

    go = st.button("Get Outfit")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor")

if not go:
    st.stop()

# ── Geocode ────────────────────────────────────────────────────────────────────
geo = geocode(location_input)

if "error" in geo:
    if geo["error"] == "API_LIMITED":
        st.error("❌ Location API is currently rate-limited. Try again in a few seconds.")
    else:
        st.error("❌ Location not found. Try a different city (e.g., 'New York, USA').")
    st.stop()

lat, lon, city_name, tz_str = geo["lat"], geo["lon"], geo["name"], geo["tz"]

# ── Weather ────────────────────────────────────────────────────────────────────
data = fetch_weather(lat, lon, tz_str)

if "error" in data:
    st.error("❌ Weather API is currently limited. Try again shortly.")
    st.stop()

hourly = data["hourly"]

times = [
    datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M")
    for t in hourly["time"]
]

temps_f = [to_f(v) for v in hourly["temperature_2m"]]
precips = hourly["precipitation_probability"]
winds = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── Pick current match ────────────────────────────────────────────────────────
target_dt = datetime.datetime.combine(target_date, target_time)

best_idx = min(
    range(len(times)),
    key=lambda i: abs((times[i] - target_dt).total_seconds())
)

tf = temps_f[best_idx]
pr = precips[best_idx]
wd = winds[best_idx]

emoji, title, desc = outfit_for(tf, pr, wd)

# ── Output ─────────────────────────────────────────────────────────────────────
st.subheader(f"{emoji} {title}")
st.write(desc)

st.metric("Location", city_name)
st.metric("Temperature", f"{tf}°F")
st.metric("Rain Chance", f"{pr}%")
st.metric("Wind", f"{wd} mph")

st.success("App loaded successfully ✔️")
