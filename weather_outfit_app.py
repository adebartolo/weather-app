import streamlit as st
import requests
import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches

# ── Page config ─────────────────────────────────────────
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Sans:wght@300;400&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', Arial, sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', Arial, sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e);
    color: #e8e8f0;
}

.stTextInput input,
.stSelectbox select,
.stDateInput input,
.stTimeInput input {
    background: rgba(255,255,255,0.08) !important;
    color: #fff !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}

::placeholder {
    color: rgba(255,255,255,0.6);
}
</style>
""", unsafe_allow_html=True)

# ── Matplotlib theme ───────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#1a1a2e",
    "text.color": "#e8e8f0",
})

# ── Helpers ────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

# ✅ FIXED GEOCODE
@st.cache_data(show_spinner=False)
def geocode(location_name):
    try:
        query = location_name.strip()

        r = requests.get(
            GEOCODE_URL,
            params={
                "q": query,
                "format": "json",
                "limit": 1
            },
            headers={
                "User-Agent": "weather-app (test@example.com)"
            },
            timeout=10
        )

        if r.status_code != 200:
            return None

        results = r.json()

        # fallback for "denver, colorado"
        if not results and "," in query:
            query = query.split(",")[0]
            r = requests.get(
                GEOCODE_URL,
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "weather-app (test@example.com)"},
                timeout=10
            )
            results = r.json()

        if not results:
            return None

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        display = results[0]["display_name"].split(",")[0]

        return lat, lon, display, "UTC"

    except:
        return None


@st.cache_data(show_spinner=False)
def fetch_weather(lat, lon, tz):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,wind_speed_10m&timezone={tz}"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None


def outfit_for(temp_f, precip, wind):
    if temp_f < 45:
        return "🧥 Jacket", "Cold — layer up"
    if precip > 60:
        return "☂️ Umbrella", "Rain likely"
    if temp_f < 75:
        return "👕 T-Shirt", "Nice weather"
    return "😎 Summer", "Hot & sunny"


# ── Sidebar ────────────────────────────────────────────
with st.sidebar:
    location_input = st.text_input("📍 Location", "New York City")
    go = st.button("Get Outfit")

# ── Main ───────────────────────────────────────────────
st.title("Weather Outfit Advisor")

if not go:
    st.stop()

geo = geocode(location_input)

if not geo:
    st.error("❌ Location not found")
    st.stop()

lat, lon, city, tz = geo
data = fetch_weather(lat, lon, tz)

hourly = data["hourly"]
temp = to_f(hourly["temperature_2m"][0])
precip = hourly["precipitation_probability"][0]
wind = to_mph(hourly["wind_speed_10m"][0])

outfit, desc = outfit_for(temp, precip, wind)

st.markdown(f"""
### {outfit}
{desc}

📍 {city}  
🌡️ {temp}°F  
🌧️ {precip}%  
💨 {wind} mph
""")
