# 🌤️ What Should I Wear?

Curious about what to wear with the on-and-off-again chaotic weather?

Here ya go! https://ad-weather-app.streamlit.app/

This app gives you a quick, visually clean weather + outfit recommendation based on:
- your location
- date + time
- temperature
- rain probability
- wind conditions

Instead of opening 4 weather apps and still getting surprised by rain 12 minutes later.

---

# ✨ Features

## 🧥 Outfit Recommendations
Smart outfit suggestions based on:
- temperature
- precipitation chance
- wind speed

Examples:
- 🥶 Heavy Coat
- 🧣 Winter Jacket
- ☂️ Umbrella Needed
- 😎 Summer Vibes

---

## 🕒 Eastern Time Standardization

All forecasts are converted into **Eastern Time (ET)** for consistency.

No more:
- “Why is the sky suddenly turning dark gray at 2pm?”
- “Am I accidentally dressed for Texas?”
- “What's the weather right now? *(closes app)* Wait, what's the weather tomorrow?”

---

## 🌎 Flexible Location Search

Supports:
- cities
- states
- abbreviations

Examples:
- `New York City`
- `Florida`
- `FL`
- `Texas`
- `CA`

Built-in state defaults:
| Input | Default City |
|---|---|
| Florida / FL | Miami |
| New York / NY | New York City |
| California / CA | Los Angeles |
| Texas / TX | Houston |

---

## 📈 7-Day Forecast Chart

Interactive visualization showing:
- min/max temperatures
- wind trends
- rain probability

Useful for:
- trip planning
- outfit prep
- deciding if laundry can wait another day

---

## ⏳ Next 24 Hours Chart

Displays rolling hourly forecasts including:
- temperature ranges
- rain %
- wind speed

Perfect for:
- commuting
- events
- “Do I need a jacket tonight?”
- “Will this become a regret hoodie?”

---

# ⚙️ Tech Stack

- Python
- Streamlit
- Open-Meteo API
- Matplotlib
- Requests
- pytz

---

# 🧠 Forecast Logic

The app:
1. Geocodes your location
2. Pulls live weather forecast data
3. Converts weather metrics:
   - Celsius → Fahrenheit
   - km/h → mph
4. Applies outfit recommendation logic
5. Generates charts and summaries

---

# 🪄 Outfit Decision Logic

Examples:

| Weather Condition | Recommendation |
|---|---|
| < 32°F | 🥶 Heavy Coat |
| 32–45°F | 🧣 Winter Jacket |
| Rain > 60% | ☂️ Umbrella Needed |
| Wind > 20 mph | 💨 Windbreaker |
| Warm + Sunny | 😎 Summer Vibes |

---

# 🚀 Running Locally

Install dependencies:

```bash
pip install streamlit requests matplotlib pytz
```

Run the app:

```bash
streamlit run app.py
```

---

# 📌 Example Use Cases

- Morning outfit planning
- Travel prep
- Event planning
- Weather dashboards
- Learning Streamlit + APIs
- Avoiding weather-induced emotional damage

---

# ⚠️ Disclaimer

This app uses forecast data from Open-Meteo.

Weather apps are predictions, not promises.

If it suddenly rains sideways anyway:
that’s between you and the atmosphere.
