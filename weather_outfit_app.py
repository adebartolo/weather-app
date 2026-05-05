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
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    color: #e8e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04) !important;
}

/* Inputs */
.stTextInput input, .stSelectbox, .stDateInput input, .stTimeInput input {
    background: rgba(255,255,255,0.08) !important;
    color: white !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border-radius: 10px !important;
    width: 100%;
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.06);
    padding: 1rem;
    border-radius: 12px;
    text-align: center;
}
.metric-card .value {
    font-size: 1.6rem;
    font-weight: 700;
}

/* Outfit */
.outfit-banner {
    padding: 1.2rem;
    border-radius: 16px;
    background: rgba(102,126,234,0.2);
    margin-bottom: 1rem;
}
.outfit-banner .title {
    font-size: 1.2rem;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

# ── Matplotlib theme ───────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#1a1a2e",
    "text.color": "#e8e8f0",
    "axes.labelcolor": "#aaaacc",
    "xtick.color": "#aaaacc",
    "ytick.color": "#aaaacc",
})

ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 4)

# ── Helpers ────────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ── GEOCODE (FIXED + FAIL SAFE) ────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location_name, "format": "json", "limit": 1},
            headers={"User-Agent": "weather-app"},
            timeout=8
        )
        data = r.json()

        if not data:
            return None

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        name = data[0]["display_name"].split(",")[0]

        return lat, lon, name, "UTC"

    except:
        return None

# ── WEATHER API (FIXED ERROR HANDLING) ─────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
            f"&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
            f"&timezone=auto"
        )
        r = requests.get(url, timeout=8)

        if r.status_code != 200:
            return "LIMITED"

        return r.json()

    except:
        return "LIMITED"

# ── Outfit logic ───────────────────────────────────────────────────────────────
def outfit_for(temp_f, rain, wind):
    if temp_f < 40:
        return "🧥", "Heavy Coat", "Very cold — bundle up."
    if temp_f < 55:
        return "🧥", "Light Jacket", "Cool weather."
    if rain > 60:
        return "☂️", "Rain Gear", "Bring umbrella."
    if wind > 20:
        return "💨", "Windy Outfit", "Layer lightly."
    return "👕", "T-Shirt Weather", "Comfortable day."

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌤️ Outfit Planner")

    location = st.text_input("Location", "New York City")

    date = st.date_input("Date", datetime.date.today())
    time = st.time_input("Time", datetime.datetime.now().time())

    units = st.radio("Units", ["°F", "°C"])

    run = st.button("Get Outfit")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather Outfit Advisor")

if not run:
    st.stop()

geo = geocode(location)

if not geo:
    st.error("Could not find location. Try 'New York, USA'")
    st.stop()

lat, lon, name, tz = geo

weather = fetch_weather(lat, lon)

if weather == "LIMITED":
    st.error("API call limited or failed. Try again later.")
    st.stop()

# ── Parse ──────────────────────────────────────────────────────────────────────
hourly = weather["hourly"]
times = hourly["time"]

temps = [to_f(t) for t in hourly["temperature_2m"]]
rain = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

idx = 0

temp = temps[idx]
rain_v = rain[idx]
wind_v = wind[idx]

emoji, outfit, desc = outfit_for(temp, rain_v, wind_v)

# ── Output ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="outfit-banner">
<div class="title">{emoji} {outfit}</div>
<p>{desc}</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("Location", name)
col2.metric("Temp", f"{temp}°F")
col3.metric("Rain", f"{rain_v}%")

# ── 7 DAY CHART ────────────────────────────────────────────────────────────────
daily = weather["daily"]

days = daily["time"]
tmin = [to_f(x) for x in daily["temperature_2m_min"]]
tmax = [to_f(x) for x in daily["temperature_2m_max"]]
rain_d = daily["precipitation_probability_max"]

fig, ax = plt.subplots(figsize=CHART_SIZE)

ax.fill_between(days, tmin, tmax, alpha=0.2, color=ACCENT1)
ax.plot(days, tmin, marker="o", label="Min")
ax.plot(days, tmax, marker="o", label="Max")

ax2 = ax.twinx()
ax2.bar(days, rain_d, alpha=0.2, color=ACCENT2)

ax.set_title("7 Day Forecast")
ax.legend()

st.pyplot(fig)

# ── 24 HOUR CHART ──────────────────────────────────────────────────────────────
fig2, ax = plt.subplots(figsize=CHART_SIZE)

ax.plot(temps[:24], label="Temp", color=ACCENT2)
ax.plot(wind[:24], label="Wind", color=ACCENT3)

ax2 = ax.twinx()
ax2.bar(range(24), rain[:24], alpha=0.2, color=ACCENT1)

ax.set_title("24 Hour Forecast")
ax.legend()

st.pyplot(fig2)
