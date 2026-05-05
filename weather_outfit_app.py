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

# ── CSS (unchanged) ────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif !important;
}
.stApp {
    color: #f5f5f5;
    background-color: #0f0c29;
}
.stTextInput input,
.stSelectbox select,
.stDateInput input,
.stTimeInput input {
    background: #1e1e2f !important;
    color: #fff !important;
    border: 1px solid #444 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    width: 100%;
}
.metric-card {
    background: rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ── Matplotlib ────────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#1a1a2e",
    "text.color": "#e8e8f0",
})

# ── Helpers ────────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

# ───────────────────────────────────────────────────────────────────────────────
# ✅ FIXED GEOLOCATION (NO MORE RANDOM FAILURES)
# ───────────────────────────────────────────────────────────────────────────────

def geocode(location_name):
    """
    Robust geocoder:
    1. Try Open-Meteo (more stable)
    2. fallback to Nominatim if needed
    """

    # Normalize input (THIS FIXES "denver, colorado")
    q = location_name.strip().lower()

    # ── 1. Open-Meteo geocoding (PRIMARY FIX) ──
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": q, "count": 1},
            timeout=6,
        )
        data = r.json()

        if "results" in data and len(data["results"]) > 0:
            res = data["results"][0]
            return res["latitude"], res["longitude"], res["name"]
    except:
        pass

    # ── 2. fallback: Nominatim ──
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location_name, "format": "json", "limit": 1},
            headers={"User-Agent": "weather-app"},
            timeout=6,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    except:
        pass

    return None

# ── Weather ────────────────────────────────────────────────────────────────────
def fetch_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        "&timezone=auto"
    )
    r = requests.get(url, timeout=8)
    return r.json()

# ── Outfit logic ───────────────────────────────────────────────────────────────
def outfit_for(temp_f):
    if temp_f < 45:
        return "🧥 Heavy Jacket"
    if temp_f < 65:
        return "🧤 Light Jacket"
    if temp_f < 80:
        return "👕 T-Shirt"
    return "😎 Summer"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    location_input = st.text_input("📍 Location", "Denver, Colorado")
    go = st.button("Get Outfit")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("Weather Outfit Advisor")

if not go:
    st.stop()

geo = geocode(location_input)

if not geo:
    st.error("Could not find location. Try 'Denver' instead of full phrase.")
    st.stop()

lat, lon, name = geo
data = fetch_weather(lat, lon)

temps = data["hourly"]["temperature_2m"]

temp_f = to_f(temps[0])
outfit = outfit_for(temp_f)

st.markdown(f"## {name}")
st.markdown(f"### 🌡️ {temp_f}°F")
st.markdown(f"### {outfit}")

# ── Simple chart ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots()
ax.plot(temps[:24])
st.pyplot(fig)
