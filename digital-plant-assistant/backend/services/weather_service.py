import logging
import requests
import os

def _error_response(msg="Weather data currently unavailable"):
    return {
        "ok": False,
        "temp": "--",
        "apparent": "--",
        "humidity": "--",
        "wind": "--",
        "condition": "Unknown",
        "city": "Unknown",
        "icon": "❓",
        "advice": msg
    }

def get_weather_data(lat: float, lon: float):
    """
    Fetch real-time weather from OpenWeather API.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        logging.error("OPENWEATHER_API_KEY is missing.")
        return _error_response()

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric"
        }
        res = requests.get(url, params=params, timeout=8)
        
        if res.status_code == 401:
            logging.error("OpenWeather API: Unauthorized - check API key.")
            return _error_response("Invalid API Key")
        if res.status_code == 429:
            logging.error("OpenWeather API: Rate limit exceeded.")
            return _error_response("Rate limit reached")
        if res.status_code != 200:
            logging.error(f"OpenWeather API failed: {res.status_code} - {res.text}")
            return _error_response()
            
        data = res.json()
        main = data.get("main", {})
        wind_data = data.get("wind", {})
        weather_list = data.get("weather", [{}])
        weather_main = weather_list[0]
        
        temp = round(main.get("temp", 0), 1)
        humidity = main.get("humidity", 0)
        wind_speed = round(wind_data.get("speed", 0), 1)
        description = weather_main.get("description", "clear sky").capitalize()
        icon_code = weather_main.get("icon", "01d")
        city = data.get("name", "Unknown City")
        
        # Map OpenWeather icon to emoji if needed, or just use description
        # For simplicity, I'll keep the icon mapping or provide a default
        icon_emoji = _get_emoji_for_icon(icon_code)

        advice = _generate_advice(temp, humidity, weather_main.get("id", 800), 0) # precip data varies in OW

        return {
            "ok": True,
            "temp": temp,
            "apparent": round(main.get("feels_like", temp), 1),
            "humidity": humidity,
            "wind": wind_speed,
            "condition": description,
            "city": city,
            "icon": icon_emoji,
            "advice": advice
        }

    except requests.exceptions.Timeout:
        logging.error("OpenWeather API network timeout.")
        return _error_response()
    except Exception as e:
        logging.error(f"OpenWeather API exception: {str(e)}")
        return _error_response()


def _get_emoji_for_icon(icon_code):
    """Maps OpenWeather icon codes to emojis."""
    mapping = {
        "01": "☀️", "02": "⛅", "03": "☁️", "04": "☁️",
        "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"
    }
    return mapping.get(icon_code[:2], "🌡️")


def get_weather_advice(lat, lon):
    """Backwards-compatible single-string advice for old callers."""
    data = get_weather_data(lat, lon)
    if not data.get("ok"):
        return "Weather data unavailable. Check your connection."
    return f"{data['icon']} {data['temp']}°C, {data['condition']}. {data['advice']}"


def _generate_advice(temp, humidity, code, precip):
    """Rule-based smart plant advice based on weather conditions."""
    # OpenWeather condition codes: https://openweathermap.org/weather-conditions
    is_rainy = code < 600 or precip > 0
    
    if is_rainy:
        return "Skip watering today — your plants are getting natural rain. Check for waterlogging."
    if temp > 35:
        return "Extreme heat! Water twice today and move sensitive plants to shade."
    if temp > 28:
        return "Hot and dry — increase watering frequency and mist leaves to cool plants."
    if temp < 5:
        return "Near-freezing! Bring outdoor plants inside and hold off on watering."
    if humidity < 30:
        return "Very dry air — mist your plants or use a humidifier near tropical species."
    if humidity > 80:
        return "High humidity — watch for fungal issues. Ensure good airflow around plants."
    
    return "Good growing conditions today. Maintain regular watering and check soil moisture."


def get_geocode_data(query: str):
    """
    Fetch lat/lon for a city name using OpenWeather Geocoding API.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "API Key missing"}

    try:
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": query,
            "limit": 1,
            "appid": api_key
        }
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                return {"lat": data[0]["lat"], "lon": data[0]["lon"], "name": data[0]["name"]}
        return {"error": "Location not found"}
    except Exception as e:
        return {"error": str(e)}


def _error_response(msg="Weather data currently unavailable"):
    return {
        "ok": False,
        "temp": "--",
        "apparent": "--",
        "humidity": "--",
        "wind": "--",
        "city": "Unknown",
        "condition": msg,
        "icon": "🌡️",
        "advice": "Maintain your regular care schedule.",
    }
