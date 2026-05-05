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

# ── STATE → DEFAULT CITY MAP (IMPORTANT FIX) ────────────────────────────────
STATE_CITY_MAP = {
    "florida": ("Miami", "Florida"),
    "fl": ("Miami", "Florida"),

    "new york": ("New York City", "New York"),
    "ny": ("New York City", "New York"),

    "california": ("Los Angeles", "California"),
    "ca": ("Los Angeles", "California"),

    "texas": ("Houston", "Texas"),
    "tx": ("Houston", "Texas"),

    "illinois": ("Chicago", "Illinois"),
    "il": ("Chicago", "Illinois"),

    "washington": ("Seattle", "Washington"),
    "wa": ("Seattle", "Washington"),

    "colorado": ("Denver", "Colorado"),
    "co": ("Denver", "Colorado"),

    "georgia": ("Atlanta", "Georgia"),
    "ga": ("Atlanta", "Georgia"),

    "nevada": ("Las Vegas", "Nevada"),
    "nv": ("Las Vegas", "Nevada"),

    "arizona": ("Phoenix", "Arizona"),
    "az": ("Phoenix", "Arizona"),
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

# ── HELPERS ─────────────────────────────────────────────────────────────────
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

# ── GEOCODE ──────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    raw = location_name.strip().lower()

    # ── STATE SHORTCUT HANDLING ─────────────────────────────
    if raw in STATE_CITY_MAP:
        city, state = STATE_CITY_MAP[raw]
        query = f"{city}, {state}, United States"
    else:
        query = f"{location_name}, United States"

    r = requests.get(
        url,
        params={"name": query, "count": 10, "language": "en"},
        timeout=8
    )

    if r.status_code != 200:
        return {"error": "API_LIMITED"}

    results = r.json().get("results", [])
    if not results:
        return {"error": "NOT_FOUND"}

    us = [r for r in results if r.get("country") == "United States"]
    p = us[0] if us else results[0]

    country = p.get("country", "United States")
    state = p.get("admin1")

    name_parts = [p["name"]]
    if state:
        name_parts.append(state)
    name_parts.append(country)

    return {
        "lat": p["latitude"],
        "lon": p["longitude"],
        "name": ", ".join(name_parts),
        "state": state
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

# ── OUTFIT LOGIC ────────────────────────────────────────────────────────────
def outfit_for(temp_f, precip, wind):
    if temp_f < 32:
        return "🥶", "Heavy Coat", "Freezing cold"
    if temp_f < 45:
        return "🧣", "Winter Jacket", "Very cold"
    if temp_f < 60:
        return "🧥", "Light Jacket", "Cool weather"
    if precip > 60:
        return "☂️", "Umbrella Needed", "Rain expected"
    if wind > 20:
        return "💨", "Windbreaker", "Windy day"
    if temp_f < 80:
        return "👕", "T-Shirt Weather", "Warm day"
    return "😎", "Summer Vibes", "Hot and sunny"

# ── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌤️ Outfit Planner")

    location = st.text_input(
        "Location",
        value="New York City",
        placeholder="Enter city or state"
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

# ── AUTO RUN ────────────────────────────────────────────────────────────────
if st.session_state.auto_run:
    st.session_state.auto_run = False
    go = True

# ── MAIN ────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor (ET Standardized)")

if not go:
    st.stop()

geo = geocode(location)

if "error" in geo:
    st.error("❌ Location not found.")
    st.stop()

lat, lon, city_name = geo["lat"], geo["lon"], geo["name"]
state_name = geo.get("state")

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

selected = datetime.datetime.combine(date, time_obj).replace(tzinfo=ET)

idx = min(
    range(len(times)),
    key=lambda i: abs((times[i] - selected).total_seconds())
)

tf, pr, wd = temps[idx], prec[idx], wind[idx]

emoji, title, desc = outfit_for(tf, pr, wd)

st.subheader(f"{emoji} {title}")
st.write(desc)

st.metric("Location", city_name)
if state_name:
    st.caption(f"State: {state_name}")

st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

# ── 7 DAY ───────────────────────────────────────────────────────────────────
if show_7day:
    st.markdown("### 7-Day Forecast")

    dmin = [to_f(x) for x in daily["temperature_2m_min"]]
    dmax = [to_f(x) for x in daily["temperature_2m_max"]]
    rain = daily["precipitation_probability_max"]
    wind_d = [to_mph(x) for x in daily["wind_speed_10m_max"]]

    days = [
        datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%b %d")
        for d in daily["time"]
    ]

    fig, ax1 = plt.subplots(figsize=CHART_SIZE)

    ax1.plot(days, dmin, label="Min Temp", color=ACCENT1)
    ax1.plot(days, dmax, label="Max Temp", color=ACCENT2)
    ax1.plot(days, wind_d, label="Wind", color=ACCENT3, linestyle="--")
    ax1.fill_between(days, dmin, dmax, alpha=0.15)

    ax2 = ax1.twinx()
    ax2.bar(days, rain, alpha=0.3, color=ACCENT1, label="Rain %")

    ax1.set_title(f"7-Day Forecast — {city_name}")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    st.pyplot(fig)
    plt.close(fig)

# ── 24 HOUR ────────────────────────────────────────────────────────────────
if show_24h:
    st.markdown("### Next 24 Hours")

    now = datetime.datetime.now(ET)

    ft, fp, fw, ftmp = [], [], [], []

    for i, t in enumerate(times):
        if t < now:
            continue
        if len(ft) >= forecast_hrs:
            break

        ft.append(t.strftime("%-I %p"))
        fp.append(prec[i])
        fw.append(wind[i])
        ftmp.append(temps[i])

    fmin = [min(ftmp[max(0,i-2):i+1]) for i in range(len(ftmp))]
    fmax = [max(ftmp[max(0,i-2):i+1]) for i in range(len(ftmp))]

    fig2, ax = plt.subplots(figsize=CHART_SIZE)

    ax.plot(ft, fmin, label="Min Temp", color=ACCENT1)
    ax.plot(ft, fmax, label="Max Temp", color=ACCENT2)
    ax.fill_between(ft, fmin, fmax, alpha=0.15)

    ax.plot(ft, fw, label="Wind", color=ACCENT3, linestyle="--")

    ax2 = ax.twinx()
    ax2.bar(ft, fp, alpha=0.3, color=ACCENT1, label="Rain %")

    ax.set_title(f"Next 24 Hours — {city_name}")
    ax.legend(loc="upper left")
    ax2.legend(loc="upper right")

    st.pyplot(fig2)
    plt.close(fig2)

st.success("Done ✔")
