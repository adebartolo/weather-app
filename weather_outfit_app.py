import streamlit as st
import requests
import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches

# ── TIMEZONE ────────────────────────────────────────────────────────────────
ET = pytz.timezone("America/New_York")
UTC = pytz.UTC

# ── STATE → DEFAULT CITY MAP ────────────────────────────────────────────────
STATE_TO_CITY = {
    "florida": "Miami",
    "fl": "Miami",
    "new york": "New York City",
    "ny": "New York City",
    "california": "Los Angeles",
    "ca": "Los Angeles",
    "texas": "Houston",
    "tx": "Houston",
    "colorado": "Denver",
    "co": "Denver",
    "illinois": "Chicago",
    "il": "Chicago",
    "washington": "Seattle",
    "wa": "Seattle",
}

# ── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

st.info("🕒 All times are standardized to **Eastern Time (ET)**.")

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
CHART_SIZE = (13, 4)

def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

now_et = datetime.datetime.now(ET)

# ── GEOCODE ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):

    raw = location_name.strip().lower()

    if raw in STATE_TO_CITY:
        location_name = STATE_TO_CITY[raw]

    url = "https://geocoding-api.open-meteo.com/v1/search"

    r = requests.get(
        url,
        params={"name": f"{location_name}, United States", "count": 10},
        timeout=8
    )

    results = r.json().get("results", [])
    if not results:
        return {"error": "NOT_FOUND"}

    us = [r for r in results if r.get("country") == "United States"]
    p = us[0] if us else results[0]

    state = p.get("admin1")

    name_parts = [p["name"]]
    if state:
        name_parts.append(state)
    name_parts.append("United States")

    return {
        "lat": p["latitude"],
        "lon": p["longitude"],
        "name": ", ".join(name_parts),
    }

# ── WEATHER ────────────────────────────────────────────────────────────────
def fetch_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&timezone=America/New_York"
        "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        "&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
    )
    return requests.get(url).json()

# ── OUTFIT ──────────────────────────────────────────────────────────────────
def outfit_for(temp, precip, wind):
    if temp < 32: return "🥶", "Heavy Coat", "Freezing cold"
    if temp < 45: return "🧣", "Winter Jacket", "Very cold"
    if temp < 60: return "🧥", "Light Jacket", "Cool weather"
    if precip > 60: return "☂️", "Umbrella Needed"
    if wind > 20: return "💨", "Windbreaker", "Windy day"
    if temp < 80: return "👕", "T-Shirt Weather", "Warm day"
    return "😎", "Summer Vibes"

# ── INPUT ───────────────────────────────────────────────────────────────────
location = st.text_input("Enter city or state", "New York City")

if st.button("Get Outfit"):

    geo = geocode(location)

    if "error" in geo:
        st.error("Location not found")
        st.stop()

    st.success(geo["name"])

    data = fetch_weather(geo["lat"], geo["lon"])

    hourly = data["hourly"]
    daily = data["daily"]

    temps = [to_f(t) for t in hourly["temperature_2m"]]
    rain = hourly["precipitation_probability"]
    wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

    date = st.session_state.get("date", now_et.date())
    time = st.session_state.get("time", now_et.time())

    target = datetime.datetime.combine(date, time).replace(tzinfo=ET)

    # ─────────────────────────────────────────────
    # 🔥 KEY FIX: FUTURE DATE RANGE LOGIC
    # ─────────────────────────────────────────────
    is_future = date > now_et.date()

    if is_future:
        idx = (date - now_et.date()).days

        tmin = to_f(daily["temperature_2m_min"][idx])
        tmax = to_f(daily["temperature_2m_max"][idx])

        tf = (tmin + tmax) / 2
        pr = daily["precipitation_probability_max"][idx]
        wd = to_mph(daily["wind_speed_10m_max"][idx])

        temp_display = f"{tmin}°F – {tmax}°F"

    else:
        times = [
            datetime.datetime.fromisoformat(t).replace(tzinfo=UTC).astimezone(ET)
            for t in hourly["time"]
        ]

        idx = min(range(len(times)),
                  key=lambda i: abs((times[i] - target).total_seconds()))

        tf = temps[idx]
        pr = rain[idx]
        wd = wind[idx]

        temp_display = f"{tf}°F"

    emoji, title, desc = outfit_for(tf, pr, wd)

    st.subheader(f"{emoji} {title}")
    st.write(desc)

    st.metric("Location", geo["name"])
    st.metric("Temp", temp_display)
    st.metric("Rain", f"{pr}%")
    st.metric("Wind", f"{wd} mph")

st.success("Done ✔")
