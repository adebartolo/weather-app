import streamlit as st
import requests
import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches

# ── TIMEZONE ────────────────────────────────────────────────────────────────
ET = pytz.timezone("America/New_York")

# ── PAGE ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon="🌤️",
    layout="wide",
)

st.info("🕒 All times are shown in Eastern Time (ET).")

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
})

ACCENT1, ACCENT2, ACCENT3 = "#667eea", "#f093fb", "#43e97b"
CHART_SIZE = (13, 4)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ── SESSION STATE ────────────────────────────────────────────────────────────
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

# ── WEATHER (KEEP ET OUTPUT FROM API) ────────────────────────────────────────
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

# ── OUTFIT LOGIC ─────────────────────────────────────────────────────────────
def outfit(temp_f, precip, wind):
    if temp_f < 32:
        return "🥶", "Heavy Coat"
    if temp_f < 45:
        return "🧣", "Winter Jacket"
    if temp_f < 60:
        return "🧥", "Light Jacket"
    if precip > 60:
        return "☂️", "Umbrella Needed"
    if wind > 20:
        return "💨", "Windbreaker"
    if temp_f < 80:
        return "👕", "T-Shirt Weather"
    return "😎", "Summer"

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    location = st.text_input("Location", "New York City")

    # NOW FIX (updates BOTH properly)
    if st.button("⚡ Use NOW (ET)"):
        st.session_state.date = now_et.date()
        st.session_state.time = now_et.replace(minute=0, second=0, microsecond=0).time()
        st.rerun()

    date = st.date_input("Date (ET)", key="date")

    times = [datetime.time(h, m) for h in range(24) for m in [0, 30]]

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

# ── CRITICAL FIX #1: convert ALL times to ET safely ─────────────────────────
times = [
    datetime.datetime.fromisoformat(t).replace(tzinfo=pytz.utc).astimezone(ET)
    for t in hourly["time"]
]

temps = [to_f(v) for v in hourly["temperature_2m"]]
prec = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── FIX #2: correct matching logic ───────────────────────────────────────────
target = ET.localize(datetime.datetime.combine(date, time_obj))

idx = min(
    range(len(times)),
    key=lambda i: abs((times[i] - target).total_seconds())
)

tf, pr, wd = temps[idx], prec[idx], wind[idx]

emoji, title = outfit(tf, pr, wd)

st.subheader(f"{emoji} {title}")
st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

# ── 7 DAY (UNCHANGED FUNCTIONALITY) ─────────────────────────────────────────
st.markdown("### 7-Day Forecast")

daily = data["daily"]

d_tmin = [to_f(x) for x in daily["temperature_2m_min"]]
d_tmax = [to_f(x) for x in daily["temperature_2m_max"]]
d_prec = daily["precipitation_probability_max"]
d_wind = [to_mph(x) for x in daily["wind_speed_10m_max"]]

days = [
    datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%b %d")
    for d in daily["time"]
]

fig, ax1 = plt.subplots(figsize=CHART_SIZE)

ax1.plot(days, d_tmin, color=ACCENT1, label="Min")
ax1.plot(days, d_tmax, color=ACCENT2, label="Max")
ax1.plot(days, d_wind, color=ACCENT3, linestyle="--", label="Wind")
ax1.fill_between(days, d_tmin, d_tmax, alpha=0.12, color=ACCENT1)

ax2 = ax1.twinx()
ax2.bar(days, d_prec, color=ACCENT1, alpha=0.35)
ax2.set_ylabel("Rain %")

rain_patch = mpatches.Patch(color=ACCENT1, alpha=0.35, label="Rain %")

ax1.legend(handles=[ax1.lines[0], ax1.lines[1], ax1.lines[2], rain_patch])

st.pyplot(fig)
plt.close(fig)

# ── 24 HOUR (FIXED TYPE ERROR + CORRECT ALIGNMENT) ───────────────────────────
st.markdown("### Next 24 Hours (ET, fixed)")

now = now_et

ft, fp, fw, ftmp = [], [], [], []

for i, t in enumerate(times):
    # FIX: both are ET-aware → safe comparison
    if t >= now and len(ft) < forecast_hrs:
        ft.append(t.strftime("%-I %p"))
        fp.append(prec[i])
        fw.append(wind[i])
        ftmp.append(temps[i])

fig2, ax3 = plt.subplots(figsize=CHART_SIZE)

ax3.plot(ft, ftmp, color=ACCENT2, label="Temp")
ax3.plot(ft, fw, color=ACCENT3, linestyle="--", label="Wind")
ax3.fill_between(ft, ftmp, alpha=0.1, color=ACCENT2)

ax2 = ax3.twinx()
ax2.bar(ft, fp, color=ACCENT1, alpha=0.4)
ax2.set_ylabel("Rain %")

rain_patch2 = mpatches.Patch(color=ACCENT1, alpha=0.4, label="Rain %")

ax3.legend(handles=[ax3.lines[0], ax3.lines[1], rain_patch2])

st.pyplot(fig2)
plt.close(fig2)

st.success("Done ✔")
