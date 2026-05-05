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

# ── Styling ────────────────────────────────────────────────────────────────────
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
CHART_SIZE = (13, 4)

# ── Helpers ────────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ── Geocode ────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    try:
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
            "tz": "UTC"
        }

    except:
        return {"error": "API_LIMITED"}

# ── Weather ────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&timezone={tz}"
        "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        "&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
    )

    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return {"error": "API_LIMITED"}

    return r.json()

# ── Outfit logic ───────────────────────────────────────────────────────────────
def outfit_for(temp_f, precip, wind):
    if temp_f < 32:
        return "🧥", "Heavy Coat", "Freezing cold"
    if temp_f < 50:
        return "🧣", "Jacket", "Cold weather"
    if precip > 60:
        return "☂️", "Umbrella Needed", "Rain expected"
    if wind > 20:
        return "💨", "Windbreaker", "Windy day"
    if temp_f < 75:
        return "👕", "T-Shirt Weather", "Mild day"
    return "😎", "Summer Vibes", "Hot and sunny"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌤️ Outfit Planner")

    location = st.text_input("Location", "New York City")

    date = st.date_input("Date", datetime.date.today() + datetime.timedelta(days=1))

    times = [
        datetime.datetime.strptime(f"{h}:{m:02d}", "%H:%M").strftime("%-I:%M %p")
        for h in range(24) for m in [0, 30]
    ]
    time_str = st.selectbox("Time", times, index=26)
    time_obj = datetime.datetime.strptime(time_str, "%I:%M %p").time()

    units = st.radio("Units", ["°F", "°C"])

    show_7 = st.checkbox("7-Day Chart", True)
    show_24 = st.checkbox("24-Hour Chart", True)
    hours = st.slider("Hours", 6, 48, 24)

    go = st.button("Get Outfit")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor")

if not go:
    st.stop()

# ── Location ───────────────────────────────────────────────────────────────────
geo = geocode(location)

if "error" in geo:
    if geo["error"] == "API_LIMITED":
        st.error("❌ Location API limited. Try again shortly.")
    else:
        st.error("❌ Location not found.")
    st.stop()

lat, lon, city, tz = geo["lat"], geo["lon"], geo["name"], geo["tz"]

# ── Weather ────────────────────────────────────────────────────────────────────
data = fetch_weather(lat, lon, tz)

if "error" in data:
    st.error("❌ Weather API limited. Try again later.")
    st.stop()

hourly = data["hourly"]

times = [datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in hourly["time"]]
temps = [to_f(v) for v in hourly["temperature_2m"]]
prec = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

# ── Match time ────────────────────────────────────────────────────────────────
target = datetime.datetime.combine(date, time_obj)

idx = min(
    range(len(times)),
    key=lambda i: abs((times[i] - target).total_seconds())
)

tf, pr, wd = temps[idx], prec[idx], wind[idx]

emoji, title, desc = outfit_for(tf, pr, wd)

st.subheader(f"{emoji} {title}")
st.write(desc)

st.metric("Location", city)
st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

# ── 7 DAY CHART ───────────────────────────────────────────────────────────────
if show_7:
    daily = data["daily"]

    days = [
        datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a")
        for d in daily["time"]
    ]

    tmin = [to_f(v) for v in daily["temperature_2m_min"]]
    tmax = [to_f(v) for v in daily["temperature_2m_max"]]
    rain = daily["precipitation_probability_max"]
    w = [to_mph(v) for v in daily["wind_speed_10m_max"]]

    fig, ax = plt.subplots(figsize=CHART_SIZE)

    ax.plot(days, tmin, label="Min Temp", color=ACCENT1, marker="o")
    ax.plot(days, tmax, label="Max Temp", color=ACCENT2, marker="o")
    ax.plot(days, w, label="Wind", color=ACCENT3, linestyle="--")

    ax2 = ax.twinx()
    ax2.bar(days, rain, alpha=0.2, color=ACCENT1, label="Rain %")

    ax.set_title("7-Day Forecast")
    ax.legend()
    st.pyplot(fig)

# ── 24 HOUR CHART ──────────────────────────────────────────────────────────────
if show_24:
    now = datetime.datetime.now()

    f_t, f_tmp, f_r, f_w = [], [], [], []

    for i, t in enumerate(times):
        if t >= now and len(f_t) < hours:
            f_t.append(t.strftime("%I %p"))
            f_tmp.append(temps[i])
            f_r.append(prec[i])
            f_w.append(wind[i])

    fig2, ax = plt.subplots(figsize=CHART_SIZE)

    ax.plot(f_t, f_tmp, label="Temp", color=ACCENT2, marker="o")
    ax.plot(f_t, f_w, label="Wind", color=ACCENT3, linestyle="--")

    ax2 = ax.twinx()
    ax2.bar(f_t, f_r, alpha=0.2, color=ACCENT1)

    ax.set_title(f"Next {hours} Hours")
    ax.legend()
    st.pyplot(fig2)

st.success("Done ✔️")
