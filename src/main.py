# main.py
import datetime
import ee
from db import get_connection, create_tables, create_metadata_table, get_last_run_date, set_last_run_date
from satellite import fetch_ndvi_for_kebele
from weather import fetch_weather_for_kebele
from risk_scoring import calculate_risk_score
import alerts

def main():
    # Initialize Earth Engine
    ee.Initialize(project='youtube-scrape-462207')

    conn = get_connection()
    create_tables(conn)
    create_metadata_table(conn)  # create metadata table for last run date

    # Example kebele info - extend or fetch from DB
    kebeles = [
        {'name': 'Adama', 'lat': 8.55, 'lon': 39.27},
        # add more kebeles here
    ]

    # Get last run date from DB or default 14 days ago
    last_run_str = get_last_run_date(conn)
    if last_run_str is None:
        last_run_date = datetime.date.today() - datetime.timedelta(days=14)
    else:
        last_run_date = datetime.datetime.strptime(last_run_str, '%Y-%m-%d').date()

    today = datetime.date.today()
    start_date_str = last_run_date.strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')

    print(f"Fetching data from {start_date_str} to {end_date_str}...")

    # OpenWeatherMap API key
    weather_api_key = '236bcfdce4f533e65b2a62bf1182aa9c'

    for kebele in kebeles:
        ndvi_current = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'], start_date_str, end_date_str)
        
        # Baseline NDVI from 14-21 days ago
        past_date_start = today - datetime.timedelta(days=21)
        past_date_end = today - datetime.timedelta(days=14)
        ndvi_past = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'],
                                          past_date_start.strftime('%Y-%m-%d'), past_date_end.strftime('%Y-%m-%d'))

        weather = fetch_weather_for_kebele(kebele['lat'], kebele['lon'], weather_api_key)

        # Fetch pest reports within this period
        c = conn.cursor()
        c.execute('SELECT severity FROM pest_reports WHERE kebele=? AND report_time >= ?', (kebele['name'], start_date_str))
        pest_reports = [{'severity': row[0]} for row in c.fetchall()]

        risk = calculate_risk_score(ndvi_current, ndvi_past, weather, pest_reports)
        print(f"Risk score for {kebele['name']}: {risk:.2f}")

        if risk >= 0.5:
            # Get farmers phone numbers
            c.execute('SELECT name, phone FROM farmers WHERE kebele=?', (kebele['name'],))
            farmers = [{'name': r[0], 'phone': r[1]} for r in c.fetchall()]
            alert_message = f"Alert: High pest/disease risk in {kebele['name']} (score: {risk:.2f}). Take precautions!"
            alerts.alert_farmers(farmers, alert_message)

    # Update last run date after successful run
    set_last_run_date(conn, end_date_str)
    conn.close()

    # Display sent SMS mock messages (only works nicely in Jupyter/Colab)
    alerts.display_sent_messages()

if __name__ == "__main__":
    main()
