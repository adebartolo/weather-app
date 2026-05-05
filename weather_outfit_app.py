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

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

@st.cache_data(show_spinner=False)
def geocode(location_name):
    """More robust geocoder with fallback queries"""
    try:
        queries = [
            location_name,
            f"{location_name}, USA",
            location_name.replace("City", "").strip()
        ]

        for q in queries:
            try:
                r = requests.get(
                    GEOCODE_URL,
                    params={"q": q, "format": "json", "limit": 1},
                    headers={
                        "User-Agent": "WeatherOutfitApp/1.0",
                        "Accept-Language": "en"
                    },
                    timeout=8,
                )

                if r.status_code != 200:
                    continue

                results = r.json()
                if results:
                    lat = float(results[0]["lat"])
                    lon = float(results[0]["lon"])
                    display = results[0]["display_name"].split(",")[0]

                    # timezone fallback (safe)
                    try:
                        from timezonefinder import TimezoneFinder
                        tf = TimezoneFinder()
                        tz = tf.timezone_at(lat=lat, lng=lon) or "UTC"
                    except:
                        tz = "UTC"

                    return lat, lon, display, tz
            except:
                continue

        return None

    except Exception:
        return None


@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz, daily_vars=None, hourly_vars=None):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&timezone={tz}"
    )
    if daily_vars:
        url += "&daily=" + ",".join(daily_vars)
    if hourly_vars:
        url += "&hourly=" + ",".join(hourly_vars)

    r = requests.get(url, timeout=10)
    return r.json() if r.status_code == 200 else None


def outfit_for(temp_f, precip_pct, wind_mph):
    if temp_f < 32:
        return "🧥", "Heavy Parka + Layers", "Extreme cold — insulated coat."
    if temp_f < 45:
        return "🧣", "Heavy Jacket + Scarf", "Very cold."
    if temp_f < 55:
        return "🧥", "Jacket", "Cool weather."
    if temp_f < 65:
        return "🧤", "Light Jacket", "Mild weather."
    if precip_pct > 60:
        return "☂️", "Umbrella Needed", "Rain expected."
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

    show_7day = st.checkbox("7-Day Forecast", True)
    show_24h = st.checkbox("24-Hour Forecast", True)
    forecast_hrs = st.slider("Hours", 6, 48, 24, 6)

    go = st.button("Get Outfit")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor")

if not go:
    st.stop()

# ── Geocode ────────────────────────────────────────────────────────────────────
geo = geocode(location_input)
if not geo:
    st.error("Could not find location. Try 'New York, USA' or another city.")
    st.stop()

lat, lon, city_name, tz_str = geo

# ── Weather ────────────────────────────────────────────────────────────────────
data = fetch_weather(
    lat, lon, tz_str,
    hourly_vars=["temperature_2m", "precipitation_probability", "wind_speed_10m"],
    daily_vars=["temperature_2m_min", "temperature_2m_max",
                "precipitation_probability_max", "wind_speed_10m_max"]
)

if not data:
    st.error("Weather API failed")
    st.stop()

hourly = data["hourly"]

times = [
    datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M")
    for t in hourly["time"]
]

temps_f = [to_f(v) for v in hourly["temperature_2m"]]
temps_c = hourly["temperature_2m"]
precips = hourly["precipitation_probability"]
winds = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── Match time ────────────────────────────────────────────────────────────────
target_dt = datetime.datetime.combine(target_date, target_time)

best_idx = min(
    (i for i, t in enumerate(times) if t.date() == target_date),
    key=lambda i: abs((times[i] - target_dt).total_seconds()),
    default=0,
)

tf, pr, wd = temps_f[best_idx], precips[best_idx], winds[best_idx]

emoji, title, desc = outfit_for(tf, pr, wd)

st.markdown(f"""
### {emoji} {title}
{desc}
""")

st.metric("Location", city_name)
st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

st.success("App running ✔️")
