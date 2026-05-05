import streamlit as st
import requests
import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib

# ── TIMEZONE ────────────────────────────────────────────────────────────────
ET = pytz.timezone("America/New_York")
UTC = pytz.UTC

# ── STATE → DEFAULT CITY MAP ────────────────────────────────────────────────
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

STATE_ABBR = {
    "fl":"florida","ca":"california","tx":"texas","ny":"new york",
    "co":"colorado","il":"illinois","wa":"washington","nv":"nevada",
    "az":"arizona","ga":"georgia","ma":"massachusetts","pa":"pennsylvania",
    "nj":"new jersey","nc":"north carolina","sc":"south carolina",
    "va":"virginia","oh":"ohio","mi":"michigan","or":"oregon","ut":"utah"
}

# ── PAGE ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon="🌤️",
    layout="wide",
)

st.title("Weather Outfit Advisor")

# ── HELPERS ─────────────────────────────────────────────────────────────────
def to_f(c): return round(c * 9/5 + 32, 1)
def to_mph(k): return round(k * 0.621371, 1)

now_et = datetime.datetime.now(ET)

# ── GEOCODE (STATE-SAFE + GUARANTEED FIX) ───────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(location):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    raw = location.strip().lower()

    # normalize abbreviations
    if raw in STATE_ABBR:
        raw = STATE_ABBR[raw]

    # STATE OVERRIDE (NO API GUESSING)
    if raw in STATE_CITY_MAP:
        city, state = STATE_CITY_MAP[raw]
        return {
            "lat": None,
            "lon": None,
            "name": f"{city}, {state}, United States",
            "preset": True
        }

    query = f"{location}, United States"

    r = requests.get(url, params={"name": query, "count": 5})
    data = r.json().get("results", [])

    if not data:
        return {"error": "NOT_FOUND"}

    p = data[0]

    state = p.get("admin1")

    name = [p["name"]]
    if state:
        name.append(state)
    name.append("United States")

    return {
        "lat": p["latitude"],
        "lon": p["longitude"],
        "name": ", ".join(name),
        "preset": False
    }

# ── WEATHER ─────────────────────────────────────────────────────────────────
def fetch_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&timezone=America/New_York"
        "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        "&daily=temperature_2m_min,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max"
    )
    return requests.get(url).json()

# ── OUTFIT LOGIC ────────────────────────────────────────────────────────────
def outfit(temp, rain, wind):
    if temp < 32: return "🥶", "Heavy Coat"
    if temp < 45: return "🧣", "Winter Jacket"
    if temp < 60: return "🧥", "Light Jacket"
    if rain > 60: return "☂️", "Umbrella"
    if wind > 20: return "💨", "Windbreaker"
    if temp < 80: return "👕", "T-Shirt Weather"
    return "😎", "Summer Vibes"

# ── INPUT ───────────────────────────────────────────────────────────────────
location = st.text_input(
    "Enter city or state",
    value="New York City"
)

if st.button("Get Outfit"):
    geo = geocode(location)

    if "error" in geo:
        st.error("Location not found")
        st.stop()

    st.success(f"Location: {geo['name']}")

    # ── STATE PRESET HANDLING ──
    if geo.get("preset"):
        st.info("Using default city for state (no API call needed)")
        st.stop()

    data = fetch_weather(geo["lat"], geo["lon"])

    hourly = data["hourly"]
    daily = data["daily"]

    temps = [to_f(t) for t in hourly["temperature_2m"]]
    rain = hourly["precipitation_probability"]
    wind = [to_mph(w) for w in hourly["wind_speed_10m"]]

    tf, wf = temps[0], wind[0]
    rf = rain[0]

    emoji, label = outfit(tf, rf, wf)

    st.subheader(f"{emoji} {label}")

    st.metric("Temp", f"{tf}°F")
    st.metric("Rain", f"{rf}%")
    st.metric("Wind", f"{wf} mph")

    # ── 7 DAY ───────────────────────────────────────────────────────────────
    dmin = [to_f(x) for x in daily["temperature_2m_min"]]
    dmax = [to_f(x) for x in daily["temperature_2m_max"]]

    days = [
        datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a")
        for d in daily["time"]
    ]

    fig, ax = plt.subplots()
    ax.plot(days, dmin, label="Min Temp")
    ax.plot(days, dmax, label="Max Temp")
    ax.fill_between(days, dmin, dmax, alpha=0.2)
    ax.legend()

    st.pyplot(fig)

st.caption("Done ✔")
