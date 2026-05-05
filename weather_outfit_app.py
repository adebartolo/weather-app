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

# ── CSS (your original) ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Sans:wght@300;400&display=swap');

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

.stTextInput input, .stSelectbox, .stDateInput, .stTimeInput {
    background: rgba(255,255,255,0.06) !important;
    color: #fff !important;
}

.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border-radius: 10px !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ── Matplotlib theme ──────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#1a1a2e",
    "axes.edgecolor": "#333355",
    "axes.labelcolor": "#aaaacc",
    "text.color": "#e8e8f0",
    "xtick.color": "#888899",
    "ytick.color": "#888899",
    "grid.color": "#2a2a4a",
})

ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 3.8)

# ── Helpers ────────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ── FIXED GEOCODER ────────────────────────────────────────────────────────────
GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

@st.cache_data(show_spinner=False)
def geocode(location_name):
    try:
        if not location_name:
            return None

        r = requests.get(
            GEOCODE_URL,
            params={
                "q": location_name,
                "format": "json",
                "limit": 1
            },
            headers={"User-Agent": "weather-app/1.0"},
            timeout=8
        )

        if r.status_code != 200:
            return "RATE_LIMIT"

        data = r.json()
        if not data:
            return None

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        name = data[0]["display_name"].split(",")[0]

        return lat, lon, name, "UTC"

    except Exception:
        return "ERROR"


# ── Weather API ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        f"&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
        f"&timezone={tz}"
    )

    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        return None, "API_ERROR"

    return r.json(), None


# ── Outfit logic ──────────────────────────────────────────────────────────────
def outfit_for(temp_f, precip, wind):
    if temp_f < 40:
        return "🧥", "Heavy Jacket", "Very cold — bundle up."
    if temp_f < 60:
        return "🧥", "Light Jacket", "Cool weather."
    if precip > 60:
        return "☂️", "Rain Gear", "Bring umbrella."
    if wind > 20:
        return "💨", "Wind Layer", "Windy conditions."
    return "👕", "T-Shirt Weather", "Comfortable day."


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌤️ Outfit App")

    location = st.text_input("Location", "New York City")

    date = st.date_input(
        "Date",
        value=datetime.date.today() + datetime.timedelta(days=1)
    )

    time = st.time_input("Time", datetime.time(13, 0))

    units = st.radio("Units", ["°F", "°C"])

    go = st.button("Get Outfit")


# ── MAIN ──────────────────────────────────────────────────────────────────────
st.title("Weather Outfit Advisor")

if not go:
    st.stop()

# ── GEOCODE ───────────────────────────────────────────────────────────────────
geo = geocode(location)

if geo == "RATE_LIMIT":
    st.error("⚠️ Location service rate-limited. Try again in a few seconds.")
    st.stop()

if geo == "ERROR":
    st.error("⚠️ Location API error.")
    st.stop()

if not geo:
    st.error("Could not find location. Try 'New York, USA'.")
    st.stop()

lat, lon, city, tz = geo

# ── WEATHER ────────────────────────────────────────────────────────────────────
data, err = fetch_weather(lat, lon, tz)

if err == "API_ERROR":
    st.error("⚠️ Weather API limited or unavailable.")
    st.stop()

if not data:
    st.error("Weather fetch failed.")
    st.stop()


# ── Parse ─────────────────────────────────────────────────────────────────────
hourly = data["hourly"]

times = [
    datetime.datetime.fromisoformat(t)
    for t in hourly["time"]
]

temps = hourly["temperature_2m"]
prec = hourly["precipitation_probability"]
wind = hourly["wind_speed_10m"]

# pick closest time
target_dt = datetime.datetime.combine(date, time)

idx = min(
    range(len(times)),
    key=lambda i: abs((times[i] - target_dt).total_seconds())
)

temp_f = to_f(temps[idx])
precip = prec[idx]
wind_mph = to_mph(wind[idx])

emoji, outfit, desc = outfit_for(temp_f, precip, wind_mph)

# ── OUTPUT ─────────────────────────────────────────────────────────────────────
st.subheader(f"{emoji} {outfit}")
st.write(desc)

st.metric("Location", city)
st.metric("Temp", f"{temp_f}°F")
st.metric("Rain", f"{precip}%")
st.metric("Wind", f"{wind_mph} mph")


# ── CHARTS (FIXED + CLEAN) ────────────────────────────────────────────────────
st.subheader("Hourly Forecast")

fig, ax = plt.subplots(figsize=CHART_SIZE)

ax.plot(temps[:24], color=ACCENT2, label="Temp")
ax.plot(wind[:24], color=ACCENT3, label="Wind")

ax2 = ax.twinx()
ax2.bar(range(24), prec[:24], alpha=0.2, color=ACCENT1, label="Rain")

ax.set_title("Next 24 Hours")
ax.legend(loc="upper left")

st.pyplot(fig)
plt.close(fig)


# ── DAILY ──────────────────────────────────────────────────────────────────────
st.subheader("7-Day Forecast")

daily = data["daily"]

days = daily["time"]
tmin = daily["temperature_2m_min"]
tmax = daily["temperature_2m_max"]

fig2, ax = plt.subplots(figsize=CHART_SIZE)

ax.plot(tmin, marker="o", color=ACCENT1)
ax.plot(tmax, marker="o", color=ACCENT2)

ax.set_xticks(range(len(days)))
ax.set_xticklabels(days, rotation=45)

st.pyplot(fig2)
plt.close(fig2)
