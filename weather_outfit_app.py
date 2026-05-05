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

# ── STATE ABBREVIATION MAP ──────────────────────────────────────────────────
STATE_MAP = {
    "ny": "New York",
    "nj": "New Jersey",
    "ca": "California",
    "fl": "Florida",
    "tx": "Texas",
    "il": "Illinois",
    "pa": "Pennsylvania",
    "ga": "Georgia",
    "nc": "North Carolina",
    "sc": "South Carolina",
    "va": "Virginia",
    "ma": "Massachusetts",
    "oh": "Ohio",
    "mi": "Michigan",
    "wa": "Washington",
    "or": "Oregon",
    "az": "Arizona",
    "nv": "Nevada",
    "co": "Colorado",
    "ut": "Utah",
}

# ── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── STYLE ───────────────────────────────────────────────────────────────────
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

# ── MATPLOTLIB THEME ─────────────────────────────────────────────────────────
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

# ── HELPERS ──────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ── SESSION DEFAULTS ─────────────────────────────────────────────────────────
now_et = datetime.datetime.now(ET)

if "date" not in st.session_state:
    st.session_state.date = now_et.date()

if "time" not in st.session_state:
    st.session_state.time = now_et.replace(minute=0, second=0, microsecond=0).time()

if "auto_run" not in st.session_state:
    st.session_state.auto_run = True

# ── SMART GEOCODER (FIXED + STATE INTELLIGENCE) ─────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    raw = location_name.strip().lower()

    # ── detect state abbreviations ──
    if raw in STATE_MAP:
        raw = STATE_MAP[raw]

    # ── detect single word input ──
    is_single = len(raw.split()) == 1

    query = raw
    if is_single:
        query = f"{raw}, United States"

    r = requests.get(
        url,
        params={"name": query, "count": 10, "language": "en"},
        timeout=8
    )

    if r.status_code != 200:
        return {"error": "API_LIMITED"}

    data = r.json()
    results = data.get("results", [])

    if not results:
        return {"error": "NOT_FOUND"}

    # ── US PRIORITY FILTER ──
    us = [r for r in results if r.get("country") == "United States"]

    if is_single:
        p = us[0] if us else results[0]
    else:
        p = us[0] if us else results[0]

    country = p.get("country") or "United States"
    state = p.get("admin1")

    parts = [p["name"]]
    if state:
        parts.append(state)
    parts.append(country)

    return {
        "lat": p["latitude"],
        "lon": p["longitude"],
        "name": ", ".join(parts),
    }

# ── WEATHER ──────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&timezone=America/New_York"
        "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        "&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
    )

    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return {"error": "API_LIMITED"}

    return r.json()

# ── OUTFIT LOGIC ─────────────────────────────────────────────────────────────
def outfit_for(temp_f, precip, wind):
    if temp_f < 32:
        return "🥶", "Heavy Coat", "Freezing cold"
    if temp_f < 45:
        return "🧣", "Winter Jacket", "Very cold"
    if temp_f < 60:
        return "🧥", "Light Jacket / Hoodie", "Cool weather"
    if precip > 60:
        return "☂️", "Umbrella Needed", "Rain expected"
    if wind > 20:
        return "💨", "Windbreaker", "Windy day"
    if temp_f < 80:
        return "👕", "T-Shirt Weather", "Warm day"
    return "😎", "Summer Vibes", "Hot and sunny"

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌤️ Outfit Planner")

    location = st.text_input(
        "Location",
        value="New York City",
        placeholder="Enter city or state (e.g. NY, Florida)"
    )

    if not location.strip():
        location = "New York City"

    if st.button("⚡ Use NOW (ET)"):
        st.session_state.date = now_et.date()
        st.session_state.time = now_et.replace(minute=0).time()
        st.rerun()

    date = st.date_input("Date (ET)", key="date")

    times = [
        datetime.datetime.strptime(f"{h}:{m:02d}", "%H:%M").time()
        for h in range(24) for m in [0, 30]
    ]

    time_obj = st.selectbox(
        "Time (ET)",
        times,
        format_func=lambda t: t.strftime("%-I:%M %p"),
        key="time"
    )

    show_7day = st.checkbox("7-Day Chart", True)
    show_24h = st.checkbox("24-Hour Chart", True)

    forecast_hrs = st.slider("Hours (max 24)", 6, 24, 24)

    go = st.button("Get Outfit")

# ── AUTO RUN ─────────────────────────────────────────────────────────────────
if st.session_state.auto_run:
    st.session_state.auto_run = False
    go = True

# ── MAIN ─────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor (ET Standardized)")

if not go:
    st.stop()

geo = geocode(location)

if "error" in geo:
    st.error("❌ Location API failed or not found.")
    st.stop()

lat, lon, city_name = geo["lat"], geo["lon"], geo["name"]

data = fetch_weather(lat, lon)

if "error" in data:
    st.error("❌ Weather API failed.")
    st.stop()

hourly = data["hourly"]
daily = data["daily"]

times = [
    datetime.datetime.fromisoformat(t).replace(tzinfo=UTC).astimezone(ET)
    for t in hourly["time"]
]

temps = [to_f(v) for v in hourly["temperature_2m"]]
prec = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── SMART TEMP LOGIC ────────────────────────────────────────────────────────
selected_dt = datetime.datetime.combine(date, time_obj).replace(tzinfo=ET)
is_today = date == now_et.date()

if is_today:
    idx = min(
        range(len(times)),
        key=lambda i: abs((times[i] - selected_dt).total_seconds())
    )

    tf = temps[idx]
    pr = prec[idx]
    wd = wind[idx]

    temp_label = f"{tf}°F"

else:
    day_idx = (selected_dt.date() - now_et.date()).days
    day_idx = max(0, min(day_idx, len(daily["temperature_2m_min"]) - 1))

    tmin = to_f(daily["temperature_2m_min"][day_idx])
    tmax = to_f(daily["temperature_2m_max"][day_idx])

    pr = daily["precipitation_probability_max"][day_idx]
    wd = to_mph(daily["wind_speed_10m_max"][day_idx])

    tf = (tmin + tmax) / 2
    temp_label = f"{tmin}°F – {tmax}°F"

emoji, title, desc = outfit_for(tf, pr, wd)

st.subheader(f"{emoji} {title}")
st.write(desc)

st.metric("Location", city_name)
st.metric("Temp", temp_label)
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

st.success("Done ✔")
