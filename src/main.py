# main.py
import datetime
import ee
from db import get_connection, create_tables, create_metadata_table, get_last_run_date, set_last_run_date
from satellite import fetch_ndvi_for_kebele
from weather import fetch_weather_for_kebele
from risk_scoring import calculate_risk_prediction
import alerts

def main():
    # Initialize Earth Engine
    ee.Initialize(project='youtube-scrape-462207')

    conn = get_connection()
    create_tables(conn)
    create_metadata_table(conn)

    # Dynamically load kebeles from DB
    c = conn.cursor()
    c.execute('SELECT name, latitude, longitude FROM kebeles')
    kebeles = [{'name': row[0], 'lat': row[1], 'lon': row[2]} for row in c.fetchall()]
    if not kebeles:
        print("No kebeles found in DB. Please add kebele data.")
        return

    last_run_str = get_last_run_date(conn)
    if last_run_str is None:
        last_run_date = datetime.date.today() - datetime.timedelta(days=14)
    else:
        last_run_date = datetime.datetime.strptime(last_run_str, '%Y-%m-%d').date()

    today = datetime.date.today()
    # if last_run_date >= today:
    #     print(f"No new data to fetch. Last run date ({last_run_date}) is today or later.")
    #     return

    start_date_str = last_run_date.strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')

    print(f"Fetching data from {start_date_str} to {end_date_str}...")

    weather_api_key = '236bcfdce4f533e65b2a62bf1182aa9c'

    for kebele in kebeles:
        ndvi_current = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'], start_date_str, end_date_str)

        # Baseline NDVI 14-21 days ago
        past_start = today - datetime.timedelta(days=21)
        past_end = today - datetime.timedelta(days=14)
        ndvi_past = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'],
                                          past_start.strftime('%Y-%m-%d'), past_end.strftime('%Y-%m-%d'))

        weather = fetch_weather_for_kebele(kebele['lat'], kebele['lon'], weather_api_key)

        # Fetch pest reports since last run date
        c.execute('SELECT crop, symptom, severity FROM pest_reports WHERE kebele=? AND report_time >= ?',
                  (kebele['name'], start_date_str))
        pest_reports = [{'crop': row[0], 'symptom': row[1], 'severity': row[2]} for row in c.fetchall()]

        risk_report = calculate_risk_prediction(ndvi_current, ndvi_past, weather, pest_reports, kebele['name'])

        print(f"Risk report for {kebele['name']}:\n{risk_report}")

        risk_level = risk_report.get('prediction', {}).get('risk_level', 'low')

        if risk_level in ['medium', 'high']:
            c.execute('SELECT name, phone FROM farmers WHERE kebele=?', (kebele['name'],))
            farmers = [{'name': r[0], 'phone': r[1]} for r in c.fetchall()]
            alert_message = (f"Predicted pest risk level {risk_level} in {kebele['name']} for {risk_report['crop']}.\n"
                             f"Recommendation: {risk_report['prediction']['recommendation']['english']}")
            alerts.alert_farmers(farmers, alert_message)

    set_last_run_date(conn, end_date_str)
    conn.close()

    alerts.display_sent_messages()

if __name__ == "__main__":
    main()