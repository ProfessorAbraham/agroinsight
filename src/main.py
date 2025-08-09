# main.py
import datetime
from db import get_connection, create_tables
from satellite import fetch_ndvi_for_kebele
from weather import fetch_weather_for_kebele
from risk_scoring import calculate_risk_score
from alerts import alert_farmers
import ee

def main():
    # Initialize Earth Engine
    ee.Initialize(project='your-gcp-project-id')

    conn = get_connection()
    create_tables(conn)

    # Example kebele info - extend or fetch from DB
    kebeles = [
        {'name': 'Adama', 'lat': 8.55, 'lon': 39.27},
        # add more kebeles here
    ]

    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)

    # OpenWeatherMap API key
    weather_api_key = 'YOUR_OPENWEATHERMAP_API_KEY'

    for kebele in kebeles:
        ndvi_current = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'], str(seven_days_ago), str(today))
        # For simplicity, get NDVI 14 days ago (past baseline)
        past_date_start = today - datetime.timedelta(days=21)
        past_date_end = today - datetime.timedelta(days=14)
        ndvi_past = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'], str(past_date_start), str(past_date_end))

        weather = fetch_weather_for_kebele(kebele['lat'], kebele['lon'], weather_api_key)

        # Fetch pest reports from DB (simplified)
        c = conn.cursor()
        c.execute('SELECT severity FROM pest_reports WHERE kebele=? AND report_time >= ?', (kebele['name'], str(seven_days_ago)))
        pest_reports = [{'severity': row[0]} for row in c.fetchall()]

        risk = calculate_risk_score(ndvi_current, ndvi_past, weather, pest_reports)

        print(f"Risk score for {kebele['name']}: {risk}")

        if risk > 0.5:
            # Get farmers phone numbers
            c.execute('SELECT name, phone FROM farmers WHERE kebele=?', (kebele['name'],))
            farmers = [{'name': r[0], 'phone': r[1]} for r in c.fetchall()]
            alert_message = f"Alert: High pest/disease risk in {kebele['name']} (score: {risk:.2f}). Take precautions!"
            alert_farmers(farmers, alert_message)

    conn.close()

if __name__ == "__main__":
    main()
