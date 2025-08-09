# weather.py
import requests

def fetch_weather_for_kebele(center_lat, center_lon, api_key):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={center_lat}&lon={center_lon}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()

        temp = data['main']['temp']
        humidity = data['main']['humidity']
        rain = data.get('rain', {}).get('1h', 0)

        print(f"Weather at ({center_lat},{center_lon}): Temp={temp}°C, Humidity={humidity}%, Rain={rain}mm")
        return {'temp': temp, 'humidity': humidity, 'rain': rain}
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None
