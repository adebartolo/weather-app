import streamlit as st
import requests
import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches

# ── TIMEZONE ────────────────────────────────────────────────────────────────
ET = pytz.timezone("America/New_York")
UTC = pytz.utc

# ── PAGE ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon="🌤️",
    layout="wide",
)

st.info("🕒 All times are standardized to Eastern Time (ET).")

# ── STYLE ─────────────────────────────────────────────────────────────────────
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
    "font.size": 9,
})

ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 4)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ── SESSION DEFAULTS ─────────────────────────────────────────────────────────
now_et = datetime.datetime.now(ET)

if "date" not in st.session_state:
    st.session_state.date = now_et.date()

if "time" not in st.session_state:
    st.session_state.time = now_et.replace(minute=0, second=0, microsecond=0).time()

# ── GEOCODE ───────────────────────────────────────────────────────────────────
@st.cache_data
def geocode(location):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},
        timeout=8
    )
    data = r.json()
    if "results" not in data:
        return {"error": "NOT_FOUND"}

    p = data["results"][0]

    return {
        "lat": p["latitude"],
        "lon": p["longitude"],
        "name": f'{p["name"]}, {p.get("country","")}',
    }

# ── WEATHER (IMPORTANT FIX: force ET timezone output) ───────────────────────
@st.cache_data
def fetch_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&timezone=America/New_York"
        "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        "&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
    )

    return requests.get(url).json()

# ── OUTFIT ───────────────────────────────────────────────────────────────────
def outfit(temp_f, precip, wind):
    if temp_f < 32:
        return "🥶", "Heavy Coat"
    if temp_f < 45:
        return "🧣", "Winter Jacket"
    if temp_f < 60:
        return "🧥", "Light Jacket"
    if precip > 60:
        return "☂️", "Umbrella"
    if wind > 20:
        return "💨", "Windbreaker"
    if temp_f < 80:
        return "👕", "T-Shirt Weather"
    return "😎", "Summer"

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    location = st.text_input("Location", "New York City")

    if st.button("⚡ Use NOW (ET)"):
        st.session_state.date = now_et.date()
        st.session_state.time = now_et.replace(minute=0, second=0, microsecond=0).time()
        st.rerun()

    date = st.date_input("Date (ET)", key="date")

    times = [
        datetime.time(h, m)
        for h in range(24) for m in [0, 30]
    ]

    time_obj = st.selectbox(
        "Time (ET)",
        times,
        format_func=lambda t: t.strftime("%-I:%M %p"),
        key="time"
    )

    forecast_hrs = st.slider("Hours (max 24)", 6, 24, 24)

    go = st.button("Get Outfit")

# ── MAIN ─────────────────────────────────────────────────────────────────────
if not go:
    st.stop()

geo = geocode(location)
if "error" in geo:
    st.error("Location not found")
    st.stop()

data = fetch_weather(geo["lat"], geo["lon"])

hourly = data["hourly"]

# ── FIX: parse as UTC then convert to ET ─────────────────────────────────────
raw_times = [
    datetime.datetime.fromisoformat(t).replace(tzinfo=UTC).astimezone(ET)
    for t in hourly["time"]
]

temps = [to_f(v) for v in hourly["temperature_2m"]]
prec = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── FIX MATCHING ─────────────────────────────────────────────────────────────
target = ET.localize(datetime.datetime.combine(date, time_obj))

idx = min(
    range(len(raw_times)),
    key=lambda i: abs((raw_times[i] - target).total_seconds())
)

tf, pr, wd = temps[idx], prec[idx], wind[idx]

emoji, title = outfit(tf, pr, wd)

st.subheader(f"{emoji} {title}")

st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

# ── 24H ALWAYS FROM NOW (FIXED TYPE ERROR) ───────────────────────────────────
st.markdown("### Next 24 Hours (ET)")

now = now_et  # already ET-aware

ft, fp, fw, ftmp = [], [], [], []

for i, t in enumerate(raw_times):
    if t >= now and len(ft) < forecast_hrs:
        ft.append(t.strftime("%-I %p"))
        fp.append(prec[i])
        fw.append(wind[i])
        ftmp.append(temps[i])

fig, ax1 = plt.subplots(figsize=CHART_SIZE)

ax1.plot(ft, ftmp, color=ACCENT2, label="Temp")
ax1.plot(ft, fw, color=ACCENT3, linestyle="--", label="Wind")
ax1.fill_between(ft, ftmp, alpha=0.1, color=ACCENT2)

ax2 = ax1.twinx()
ax2.bar(ft, fp, color=ACCENT1, alpha=0.4)
ax2.set_ylabel("Rain %")

ax1.legend()
plt.title(f"Next 24 Hours — {geo['name']} (ET)")
st.pyplot(fig)

st.success("Done ✔")
