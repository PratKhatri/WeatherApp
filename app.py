from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = "321a86bed1bbac71338dec7d6581d1dd"

# ----------------- Helper Functions -----------------
def kelvin_to_celsius(k):
    return k - 273.15

def kelvin_to_fahrenheit(k):
    return (k * 9/5) - 459.67

def format_temp(k, unit="F"):
    return round(kelvin_to_fahrenheit(k), 1) if unit=="F" else round(kelvin_to_celsius(k), 1)

def get_weather_emoji(weather_id):
    if 200 <= weather_id <= 232: return "⛈"
    elif 300 <= weather_id <= 321: return "🌦"
    elif 500 <= weather_id <= 531: return "🌧"
    elif 600 <= weather_id <= 622: return "❄"
    elif 701 <= weather_id <= 741: return "🌫"
    elif weather_id == 762: return "🌋"
    elif weather_id == 771: return "💨"
    elif weather_id == 781: return "🌪"
    elif weather_id == 800: return "☀"
    elif 801 <= weather_id <= 804: return "☁"
    return "❔"

def get_bg_color(weather_id):
    if 200 <= weather_id <= 531: return "#a3c1ad"  # rain
    elif 600 <= weather_id <= 622: return "#e0f7fa"  # snow
    elif weather_id == 800: return "#fff3cd"  # clear
    return "#d6e0f0"  # cloudy

def format_time(utc_seconds, tz_offset=0):
    return (datetime.utcfromtimestamp(utc_seconds) + timedelta(seconds=tz_offset)).strftime("%I:%M %p")

def load_recent():
    try:
        with open("recent.txt", "r") as file:
            cities = file.readlines()[-5:]
            return [c.strip() for c in cities]
    except FileNotFoundError:
        return []

def save_city(city):
    recent = load_recent()
    if city not in recent:
        with open("recent.txt", "a") as file:
            file.write(city + "\n")

# ----------------- Routes -----------------
@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    forecast = []
    city = ""
    unit = "F"

    if request.method == "POST":
        city = request.form.get("city") or request.form.get("recent_city")
        unit = request.form.get("unit", "F")

        if city:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}"

            try:
                data = requests.get(url).json()
                forecast_data = requests.get(forecast_url).json()
                tz_offset = data.get("timezone", 0)

                weather = {
                    "city": city,
                    "temperature": format_temp(data["main"]["temp"], unit),
                    "unit": unit,
                    "description": data["weather"][0]["description"].capitalize(),
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "feels_like": format_temp(data["main"]["feels_like"], unit),
                    "temp_min": format_temp(data["main"]["temp_min"], unit),
                    "temp_max": format_temp(data["main"]["temp_max"], unit),
                    "sunrise": format_time(data["sys"]["sunrise"], tz_offset),
                    "sunset": format_time(data["sys"]["sunset"], tz_offset),
                    "local_time": format_time(datetime.utcnow().timestamp(), tz_offset),
                    "emoji": get_weather_emoji(data["weather"][0]["id"]),
                    "bg_color": get_bg_color(data["weather"][0]["id"]),
                    "icon_url": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
                }

                # Forecast (first 5)
                for item in forecast_data["list"][:5]:
                    dt = datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S")
                    temp = format_temp(item["main"]["temp"], unit)
                    icon_url = f"http://openweathermap.org/img/wn/{item['weather'][0]['icon']}@2x.png"
                    forecast.append((dt.strftime("%a %I%p"), temp, icon_url))

                save_city(city)

            except Exception as e:
                weather = None

    return render_template("index.html", weather=weather, forecast=forecast, recent=load_recent(), city=city, unit=unit)

# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(debug=True)
