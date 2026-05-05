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

# ── 50 STATE → DEFAULT CITY MAP ─────────────────────────────────────────────
STATE_CITY_MAP = {
    "alabama": ("Birmingham", "Alabama"),
    "alaska": ("Anchorage", "Alaska"),
    "arizona": ("Phoenix", "Arizona"),
    "arkansas": ("Little Rock", "Arkansas"),
    "california": ("Los Angeles", "California"),
    "colorado": ("Denver", "Colorado"),
    "connecticut": ("Hartford", "Connecticut"),
    "delaware": ("Wilmington", "Delaware"),
    "florida": ("Miami", "Florida"),
    "georgia": ("Atlanta", "Georgia"),
    "hawaii": ("Honolulu", "Hawaii"),
    "idaho": ("Boise", "Idaho"),
    "illinois": ("Chicago", "Illinois"),
    "indiana": ("Indianapolis", "Indiana"),
    "iowa": ("Des Moines", "Iowa"),
    "kansas": ("Wichita", "Kansas"),
    "kentucky": ("Louisville", "Kentucky"),
    "louisiana": ("New Orleans", "Louisiana"),
    "maine": ("Portland", "Maine"),
    "maryland": ("Baltimore", "Maryland"),
    "massachusetts": ("Boston", "Massachusetts"),
    "michigan": ("Detroit", "Michigan"),
    "minnesota": ("Minneapolis", "Minnesota"),
    "mississippi": ("Jackson", "Mississippi"),
    "missouri": ("Kansas City", "Missouri"),
    "montana": ("Billings", "Montana"),
    "nebraska": ("Omaha", "Nebraska"),
    "nevada": ("Las Vegas", "Nevada"),
    "new hampshire": ("Manchester", "New Hampshire"),
    "new jersey": ("Newark", "New Jersey"),
    "new mexico": ("Albuquerque", "New Mexico"),
    "new york": ("New York City", "New York"),
    "north carolina": ("Charlotte", "North Carolina"),
    "north dakota": ("Fargo", "North Dakota"),
    "ohio": ("Columbus", "Ohio"),
    "oklahoma": ("Oklahoma City", "Oklahoma"),
    "oregon": ("Portland", "Oregon"),
    "pennsylvania": ("Philadelphia", "Pennsylvania"),
    "rhode island": ("Providence", "Rhode Island"),
    "south carolina": ("Charleston", "South Carolina"),
    "south dakota": ("Sioux Falls", "South Dakota"),
    "tennessee": ("Nashville", "Tennessee"),
    "texas": ("Houston", "Texas"),
    "utah": ("Salt Lake City", "Utah"),
    "vermont": ("Burlington", "Vermont"),
    "virginia": ("Virginia Beach", "Virginia"),
    "washington": ("Seattle", "Washington"),
    "west virginia": ("Charleston", "West Virginia"),
    "wisconsin": ("Milwaukee", "Wisconsin"),
    "wyoming": ("Cheyenne", "Wyoming"),
}

# abbreviations
STATE_ABBR = {
    "ny":"new york","ca":"california","fl":"florida","tx":"texas","nj":"new jersey",
    "pa":"pennsylvania","ga":"georgia","nc":"north carolina","sc":"south carolina",
    "va":"virginia","ma":"massachusetts","oh":"ohio","mi":"michigan","wa":"washington",
    "or":"oregon","az":"arizona","nv":"nevada","co":"colorado","ut":"utah","il":"illinois"
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

# ── GEOCODE (FIXED STATE LOGIC) ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    raw = location_name.strip().lower()

    # --- STATE DETECTION ---
    if raw in STATE_ABBR:
        raw = STATE_ABBR[raw]

    if raw in STATE_CITY_MAP:
        city, state = STATE_CITY_MAP[raw]
        query = f"{city}, {state}, United States"
    elif len(raw.split()) == 1:
        # treat single word as possible state OR city
        if raw in STATE_CITY_MAP:
            city, state = STATE_CITY_MAP[raw]
            query = f"{city}, {state}, United States"
        else:
            query = f"{raw}, United States"
    else:
        query = location_name

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

# ── WEATHER ─────────────────────────────────────────────────────────────────
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

data = fetch_weather(lat, lon)

hourly = data["hourly"]
daily = data["daily"]

times = [
    datetime.datetime.fromisoformat(t).replace(tzinfo=UTC).astimezone(ET)
    for t in hourly["time"]
]

temps = [to_f(v) for v in hourly["temperature_2m"]]
prec = hourly["precipitation_probability"]
wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

target = datetime.datetime.combine(date, time_obj).replace(tzinfo=ET)

idx = min(range(len(times)), key=lambda i: abs((times[i]-target).total_seconds()))

tf, pr, wd = temps[idx], prec[idx], wind[idx]

emoji, title, desc = outfit_for(tf, pr, wd)

st.subheader(f"{emoji} {title}")
st.write(desc)

st.metric("Location", city_name)
st.metric("Temp", f"{tf}°F")
st.metric("Rain", f"{pr}%")
st.metric("Wind", f"{wd} mph")

st.success("Done ✔")
