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

# ── GEOCODE ──────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    r = requests.get(
        url,
        params={"name": location_name, "count": 1, "language": "en"},
        timeout=8
    )

    if r.status_code != 200:
        return {"error": "API_LIMITED"}

    data = r.json()
    if "results" not in data:
        return {"error": "NOT_FOUND"}

    p = data["results"][0]

    return {
        "lat": p["latitude"],
        "lon": p["longitude"],
        "name": f'{p["name"]}, {p.get("country","")}',
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

    # ✅ placeholder + default
    location = st.text_input(
        "Location",
        value="New York City",
        placeholder="Enter city or state"
    )

    if not location.strip():
        location = "New York City"

    if st.button("⚡ Use NOW (ET)"):
        st.session_state.date = now_et.date()
        st.session_state.time = now_et.replace(minute=0, second=0, microsecond=0).time()
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

# ── AUTO RUN ON LOAD ─────────────────────────────────────────────────────────
if st.session_state.auto_run:
    st.session_state.auto_run = False
    go = True

# ── MAIN ─────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor (ET Standardized)")

if not go:
    st.stop()

# ── LOCATION ────────────────────────────────────────────────────────────────
geo = geocode(location)

if "error" in geo:
    st.error("❌ Location API failed or not found.")
    st.stop()

lat, lon, city_name = geo["lat"], geo["lon"], geo["name"]

# ── WEATHER ─────────────────────────────────────────────────────────────────
data = fetch_weather(lat, lon)

if "error" in data:
    st.error("❌ Weather API failed.")
    st.stop()

hourly = data["hourly"]

times = [
    datetime.datetime.fromisoformat(t).replace(tzinfo=UTC).astimezone(ET)
    for t in hourly["time"]
]

temps = [to_f(v) for v in hourly["temperature_2m"]]
prec = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── MATCH USER TIME ─────────────────────────────────────────────────────────
target = datetime.datetime.combine(date, time_obj).replace(tzinfo=ET)

idx = min(
    range(len(times)),
    key=lambda i: abs((times[i] - target).total_seconds())
)

tf, pr, wd = temps[idx], prec[idx], wind[idx]

emoji, title, desc = outfit_for(tf, pr, wd)

st.subheader(f"{emoji} {title}")
st.write(desc)

st.metric("Location", city_name)
st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

# ── 7-DAY ───────────────────────────────────────────────────────────────────
if show_7day:
    st.markdown("### 7-Day Forecast")

    daily = data["daily"]

    d_tmin = [to_f(t) for t in daily["temperature_2m_min"]]
    d_tmax = [to_f(t) for t in daily["temperature_2m_max"]]
    d_prec = daily["precipitation_probability_max"]
    d_wind = [to_mph(w) for w in daily["wind_speed_10m_max"]]

    days = [
        datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%b %d")
        for d in daily["time"]
    ]

    fig, ax1 = plt.subplots(figsize=CHART_SIZE)

    ax1.plot(days, d_tmin, color=ACCENT1, marker="o")
    ax1.plot(days, d_tmax, color=ACCENT2, marker="o")
    ax1.plot(days, d_wind, color=ACCENT3, linestyle="--")
    ax1.fill_between(days, d_tmin, d_tmax, alpha=0.12)

    ax2 = ax1.twinx()
    ax2.bar(days, d_prec, color=ACCENT1, alpha=0.35)

    ax1.set_title(f"7-Day Forecast — {city_name}")
    st.pyplot(fig)
    plt.close(fig)

# ── 24 HOUR ─────────────────────────────────────────────────────────────────
if show_24h:
    st.markdown("### Next 24 Hours (Always ET)")

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

    fig2, ax3 = plt.subplots(figsize=CHART_SIZE)

    ax3.plot(ft, ftmp, color=ACCENT2)
    ax3.plot(ft, fw, color=ACCENT3, linestyle="--")
    ax3.fill_between(ft, ftmp, alpha=0.1, color=ACCENT2)

    ax4 = ax3.twinx()
    ax4.bar(ft, fp, color=ACCENT1, alpha=0.4)

    ax3.set_title(f"Next 24 Hours — {city_name} (ET)")
    st.pyplot(fig2)
    plt.close(fig2)

st.success("Done ✔")
