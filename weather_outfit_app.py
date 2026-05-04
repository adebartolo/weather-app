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

# ── GLOBAL ARIAL FONT (FOR EVERYTHING) ─────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"], .stApp, .stMarkdown, .stText, .stButton,
input, textarea, select, div {
    font-family: Arial, Helvetica, sans-serif !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: bold;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* Inputs */
.stTextInput input,
.stSelectbox,
.stDateInput input,
.stTimeInput input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    color: white !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: bold !important;
    width: 100%;
}

/* Cards */
.metric-card, .outfit-banner {
    font-family: Arial, Helvetica, sans-serif !important;
}

</style>
""", unsafe_allow_html=True)

# ── Matplotlib (FORCED ARIAL) ──────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#1a1a2e",
    "axes.edgecolor": "#333355",
    "axes.labelcolor": "#ffffff",
    "text.color": "#ffffff",
    "xtick.color": "#aaaaaa",
    "ytick.color": "#aaaaaa",
    "grid.color": "#2a2a4a",
    "grid.linewidth": 0.7,
    "font.family": ["Arial", "Helvetica", "sans-serif"],
    "font.size": 10,
})

ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 3.8)

# ── Helpers ────────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

@st.cache_data(show_spinner=False)
def geocode(location_name):
    try:
        r = requests.get(
            GEOCODE_URL,
            params={"q": location_name, "format": "json", "limit": 1},
            headers={"User-Agent": "WeatherApp/1.0"},
            timeout=6,
        )
        results = r.json()
        if not results:
            return None

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        name = results[0]["display_name"].split(",")[0]

        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            tz = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        except:
            tz = "UTC"

        return lat, lon, name, tz
    except:
        return None

@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&timezone={tz}"
        f"&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        f"&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
    )
    r = requests.get(url, timeout=8)
    return r.json() if r.status_code == 200 else None

def outfit(temp, rain, wind):
    if temp < 32:
        return "🧥 Heavy Winter Coat", "Freezing cold"
    if temp < 45:
        return "🧣 Heavy Jacket", "Very cold"
    if temp < 55:
        return "🧥 Jacket", "Cold"
    if rain > 60:
        return "☂️ Umbrella Needed", "Rain likely"
    if wind > 20:
        return "💨 Light Jacket", "Windy"
    if temp < 75:
        return "👕 T-shirt", "Mild weather"
    return "😎 Summer Outfit", "Hot weather"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌤️ Outfit App")

    location = st.text_input("Location", "New York City")

    date = st.date_input("Date", datetime.date.today())
    time = st.time_input("Time", datetime.time(13, 0))  # ⬅️ NOT military

    units = st.radio("Units", ["°F", "°C"])
    run = st.button("Get Outfit")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather Outfit Advisor")

if not run:
    st.stop()

geo = geocode(location)
if not geo:
    st.error("Location not found")
    st.stop()

lat, lon, city, tz = geo
data = fetch_weather(lat, lon, tz)

hourly = data["hourly"]
times = [datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in hourly["time"]]
temps = [to_f(t) for t in hourly["temperature_2m"]]
rain = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

target = datetime.datetime.combine(date, time)

idx = min(range(len(times)), key=lambda i: abs((times[i] - target).total_seconds()))

temp, pr, wd = temps[idx], rain[idx], wind[idx]

fit, desc = outfit(temp, pr, wd)

st.subheader(f"{city}")
st.metric("Temperature", f"{temp}°F" if units == "°F" else f"{round((temp-32)*5/9,1)}°C")
st.metric("Rain Chance", f"{pr}%")
st.metric("Wind", f"{wd} mph")

st.success(f"{fit} — {desc}")

# ── Simple chart ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=CHART_SIZE)
ax.plot(temps[:24], label="Temp (°F)")
ax.plot(wind[:24], label="Wind")
ax.set_title("Next 24 Hours")
ax.legend()
st.pyplot(fig)
