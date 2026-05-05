import streamlit as st
import requests
import datetime
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

# ── Geocode (fixed + stable API) ───────────────────────────────────────────────
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

# ── Weather API ────────────────────────────────────────────────────────────────
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

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather · Outfit Advisor")

if not go:
    st.stop()

# ── Location ───────────────────────────────────────────────────────────────────
geo = geocode(location)

if "error" in geo:
    st.error("❌ Location API failed or not found.")
    st.stop()

lat, lon, city_name, tz = geo["lat"], geo["lon"], geo["name"], geo["tz"]

# ── Weather ────────────────────────────────────────────────────────────────────
data = fetch_weather(lat, lon, tz)

if "error" in data:
    st.error("❌ Weather API failed.")
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

st.metric("Location", city_name)
st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

# ── 7-DAY CHART (FIXED + LEGEND INCLUDED) ──────────────────────────────────────
if show_7day:
    st.markdown("### 7-Day Forecast")

    daily = data["daily"]
    d_dates = daily["time"]
    d_tmin = [to_f(t) for t in daily["temperature_2m_min"]]
    d_tmax = [to_f(t) for t in daily["temperature_2m_max"]]
    d_prec = daily["precipitation_probability_max"]
    d_wind = [to_mph(w) for w in daily["wind_speed_10m_max"]]

    days = [datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%b %d") for d in d_dates]

    fig, ax1 = plt.subplots(figsize=CHART_SIZE)

    l1 = ax1.plot(days, d_tmin, color=ACCENT1, marker="o", linewidth=2, label=f"Min ({units})")
    l2 = ax1.plot(days, d_tmax, color=ACCENT2, marker="o", linewidth=2, label=f"Max ({units})")
    l3 = ax1.plot(days, d_wind, color=ACCENT3, marker="x", linestyle="--", label="Wind (mph)")

    ax1.fill_between(days, d_tmin, d_tmax, alpha=0.12, color=ACCENT1)

    ax1.set_ylabel("Temp / Wind")
    ax1.grid(True, alpha=0.4)

    ax2 = ax1.twinx()
    bars = ax2.bar(days, d_prec, color=ACCENT1, alpha=0.25, label="Rain %")
    ax2.set_ylim(0, 130)
    ax2.set_ylabel("Precipitation %")

    # ── FIXED LEGEND (includes rain) ──
    rain_patch = mpatches.Patch(color=ACCENT1, alpha=0.25, label="Rain %")
    ax1.legend(handles=[l1[0], l2[0], l3[0], rain_patch],
               loc="upper center",
               bbox_to_anchor=(0.5, -0.15),
               ncol=4)

    plt.title(f"7-Day Forecast — {city_name}")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# ── 24-HOUR CHART (FIXED + LEGEND INCLUDED) ────────────────────────────────────
if show_24h:
    st.markdown(f"### Next {forecast_hrs} Hours")

    now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)

    ft, fp, fw = [], [], []

    for i, t in enumerate(times):
        if t >= now and len(ft) < forecast_hrs:
            ft.append(t.strftime("%-I %p"))
            fp.append(prec[i])
            fw.append(wind[i])

    fig2, ax3 = plt.subplots(figsize=CHART_SIZE)

    t_line = ax3.plot(ft, temps[:len(ft)], color=ACCENT2, label=f"Temp ({units})")
    w_line = ax3.plot(ft, fw, color=ACCENT3, linestyle="--", label="Wind (mph)")

    ax3.fill_between(ft, temps[:len(ft)], alpha=0.1, color=ACCENT2)

    ax3.set_ylabel("Temp / Wind")
    ax3.grid(True, alpha=0.4)

    ax4 = ax3.twinx()
    ax4.bar(ft, fp, color=ACCENT1, alpha=0.25, label="Rain %")
    ax4.set_ylim(0, 130)
    ax4.set_ylabel("Precipitation %")

    # ── FIXED LEGEND (includes rain) ──
    rain_patch2 = mpatches.Patch(color=ACCENT1, alpha=0.25, label="Rain %")
    ax3.legend(handles=[t_line[0], w_line[0], rain_patch2],
               loc="upper center",
               bbox_to_anchor=(0.5, -0.2),
               ncol=3)

    plt.title(f"Next {forecast_hrs} Hours — {city_name}")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

st.success("Done ✔")
