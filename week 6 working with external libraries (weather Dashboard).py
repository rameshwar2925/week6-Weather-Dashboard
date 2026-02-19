import requests
import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# load API key
load_dotenv()
API_KEY = os.getenv("API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5"
CACHE_FILE = "weather_cache.json"
CACHE_DURATION = 600  # seconds


# ---------------- CACHE FUNCTIONS ---------------- #

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def get_cached_data(city, type_):
    cache = load_cache()
    key = f"{type_}_{city}"

    if key in cache:
        if time.time() - cache[key]["time"] < CACHE_DURATION:
            return cache[key]["data"]
    return None


def set_cache(city, type_, data):
    cache = load_cache()
    key = f"{type_}_{city}"
    cache[key] = {"data": data, "time": time.time()}
    save_cache(cache)


# ---------------- API FUNCTIONS ---------------- #

def fetch_weather(city):
    cached = get_cached_data(city, "current")
    if cached:
        return cached

    url = f"{BASE_URL}/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        set_cache(city, "current", data)
        return data
    except:
        return None


def fetch_forecast(city):
    cached = get_cached_data(city, "forecast")
    if cached:
        return cached

    url = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units=metric"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        set_cache(city, "forecast", data)
        return data
    except:
        return None


# ---------------- UTILITY FUNCTIONS ---------------- #

def convert_temp(temp, unit):
    if unit == "F":
        return temp * 9/5 + 32
    return temp


def format_weather(data, unit):
    temp = convert_temp(data["main"]["temp"], unit)
    feels = convert_temp(data["main"]["feels_like"], unit)

    return f"""
Current Weather in {data['name']}, {data['sys']['country']}
-----------------------------------
Temperature : {temp:.1f}°{unit} (Feels {feels:.1f}°{unit})
Condition   : {data['weather'][0]['description'].title()}
Humidity    : {data['main']['humidity']}%
Wind Speed  : {data['wind']['speed']} m/s
Pressure    : {data['main']['pressure']} hPa
Updated     : {datetime.fromtimestamp(data['dt'])}
"""


def format_forecast(data, unit):
    print("\n5-Day Forecast")
    print("----------------------------")

    daily = {}

    for item in data["list"]:
        date = item["dt_txt"].split()[0]
        temp = convert_temp(item["main"]["temp"], unit)

        if date not in daily:
            daily[date] = []
        daily[date].append(temp)

    for date, temps in list(daily.items())[:5]:
        print(f"{date}: {max(temps):.1f}° / {min(temps):.1f}°{unit}")


# ---------------- CLI INTERFACE ---------------- #

def main():
    print("🌤️ WEATHER DASHBOARD")
    print("========================")

    unit = "C"

    while True:
        print("\nOptions:")
        print("1. Search city weather")
        print("2. Change unit (C/F)")
        print("3. Quit")

        choice = input("Choose option: ")

        if choice == "1":
            city = input("Enter city name: ")

            current = fetch_weather(city)
            forecast = fetch_forecast(city)

            if current and forecast:
                print(format_weather(current, unit))
                format_forecast(forecast, unit)
            else:
                print("❌ Error fetching weather. Check city name or internet.")

        elif choice == "2":
            unit = "F" if unit == "C" else "C"
            print(f"Unit changed to {unit}")

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    if not API_KEY:
        print("⚠️ Please add API_KEY to .env file")
    else:
        main()
