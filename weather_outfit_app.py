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
    show_7day = st.checkbox("7-Day Chart", True)
    show_24h = st.checkbox("24-Hour Chart", True)
    forecast_hrs = st.slider("Hours", 6, 48, 24)

    go = st.button("Get Outfit")

# ── MAIN ───────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor")

if not go:
    st.stop()

# ── Location ───────────────────────────────────────────────────────────────────
geo = geocode(location)

if "error" in geo:
    st.error("❌ Location API issue or not found.")
    st.stop()

lat, lon, city, tz = geo["lat"], geo["lon"], geo["name"], geo["tz"]

# ── Weather ────────────────────────────────────────────────────────────────────
data = fetch_weather(lat, lon, tz)

if "error" in data:
    st.error("❌ Weather API limited.")
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

# ── 7-DAY CHART (FIXED) ───────────────────────────────────────────────────────
if show_7day:
    st.subheader("7-Day Forecast")

    daily = data["daily"]

    d_tmin = [to_f(v) for v in daily["temperature_2m_min"]]
    d_tmax = [to_f(v) for v in daily["temperature_2m_max"]]
    d_prec = daily["precipitation_probability_max"]
    d_wind = [to_mph(v) for v in daily["wind_speed_10m_max"]]

    days = daily["time"]

    fig, ax1 = plt.subplots(figsize=CHART_SIZE)

    ax1.fill_between(days, d_tmin, d_tmax, alpha=0.12, color=ACCENT1)
    ax1.plot(days, d_tmin, color=ACCENT1, marker="o", label="Min")
    ax1.plot(days, d_tmax, color=ACCENT2, marker="o", label="Max")
    ax1.plot(days, d_wind, color=ACCENT3, linestyle="--", label="Wind")

    ax1.set_xticks(range(len(days)))
    ax1.set_xticklabels(days, rotation=45)

    ax2 = ax1.twinx()
    ax2.bar(range(len(days)), d_prec, alpha=0.2, color=ACCENT1)

    ax1.legend()
    st.pyplot(fig)
    plt.close(fig)

# ── 24-HOUR CHART (FIXED) ─────────────────────────────────────────────────────
if show_24h:
    st.subheader(f"Next {forecast_hrs} Hours")

    now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)

    f_t, f_temp, f_prec, f_wind = [], [], [], []

    for i, t in enumerate(times):
        if t >= now and len(f_t) < forecast_hrs:
            f_t.append(t.strftime("%-I %p"))
            f_temp.append(temps[i])
            f_prec.append(prec[i])
            f_wind.append(wind[i])

    fig2, ax = plt.subplots(figsize=CHART_SIZE)

    ax.plot(f_t, f_temp, color=ACCENT2, marker="o")
    ax.plot(f_t, f_wind, color=ACCENT3, linestyle="--")

    ax2 = ax.twinx()
    ax2.bar(f_t, f_prec, alpha=0.2, color=ACCENT1)

    step = max(1, len(f_t)//10)
    ax.set_xticks(range(0, len(f_t), step))
    ax.set_xticklabels(f_t[::step], rotation=30)

    st.pyplot(fig2)
    plt.close(fig2)

st.success("Loaded successfully")
