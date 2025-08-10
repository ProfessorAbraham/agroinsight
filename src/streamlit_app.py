# streamlit_app.py
import streamlit as st
import datetime
import ee
from db import get_connection, create_tables, create_metadata_table, get_last_run_date, set_last_run_date
from satellite import fetch_ndvi_for_kebele
from weather import fetch_weather_for_kebele
from risk_scoring import calculate_risk_prediction
import alerts

@st.cache_resource(show_spinner=False)
def init_earth_engine():
    ee.Initialize(project='youtube-scrape-462207')
    return True

def main():
    # Initialize Earth Engine
    init_earth_engine()

    conn = get_connection()
    create_tables(conn)
    create_metadata_table(conn)
    c = conn.cursor()

    st.title("AgroInsight Risk Prediction & Management")

    # Sidebar registration
    st.sidebar.header("Register")
    registration_type = st.sidebar.selectbox("Register as", ["Add Kebele", "Add Farmer"])

    if registration_type == "Add Kebele":
        kebele_name = st.sidebar.text_input("Kebele Name")
        lat = st.sidebar.text_input("Latitude (e.g. 8.55)")
        lon = st.sidebar.text_input("Longitude (e.g. 39.27)")
        if st.sidebar.button("Add Kebele"):
            try:
                c.execute("INSERT INTO kebeles (name, latitude, longitude) VALUES (?, ?, ?)", 
                          (kebele_name, float(lat), float(lon)))
                conn.commit()
                st.sidebar.success(f"Kebele '{kebele_name}' added.")
            except Exception as e:
                st.sidebar.error(f"Error adding kebele: {e}")

    elif registration_type == "Add Farmer":
        farmer_name = st.sidebar.text_input("Farmer Name")
        phone = st.sidebar.text_input("Phone Number")
        c.execute("SELECT name FROM kebeles")
        kebeles_list = [row[0] for row in c.fetchall()]
        farmer_kebele = st.sidebar.selectbox("Select Kebele", kebeles_list)
        if st.sidebar.button("Add Farmer"):
            try:
                c.execute("INSERT INTO farmers (name, phone, kebele) VALUES (?, ?, ?)", 
                          (farmer_name, phone, farmer_kebele))
                conn.commit()
                st.sidebar.success(f"Farmer '{farmer_name}' added.")
            except Exception as e:
                st.sidebar.error(f"Error adding farmer: {e}")

    st.markdown("---")

    # Run Risk Prediction button
    if st.button("Run Prediction Now"):
        last_run_str = get_last_run_date(conn)
        if last_run_str is None:
            last_run_date = datetime.date.today() - datetime.timedelta(days=14)
        else:
            last_run_date = datetime.datetime.strptime(last_run_str, '%Y-%m-%d').date()

        today = datetime.date.today()
        if last_run_date >= today:
            st.info(f"No new data to fetch. Last run date ({last_run_date}) is today or later.")
        else:
            start_date_str = last_run_date.strftime('%Y-%m-%d')
            end_date_str = today.strftime('%Y-%m-%d')

            st.write(f"Fetching data from {start_date_str} to {end_date_str}...")

            c.execute('SELECT name, latitude, longitude FROM kebeles')
            kebeles = [{'name': row[0], 'lat': row[1], 'lon': row[2]} for row in c.fetchall()]

            weather_api_key = '236bcfdce4f533e65b2a62bf1182aa9c'
            results = []
            alert_messages = []

            progress_text = "Processing kebeles..."
            my_bar = st.progress(0, text=progress_text)

            for idx, kebele in enumerate(kebeles):
                ndvi_current = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'], start_date_str, end_date_str)

                past_start = today - datetime.timedelta(days=21)
                past_end = today - datetime.timedelta(days=14)
                ndvi_past = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'],
                                                  past_start.strftime('%Y-%m-%d'), past_end.strftime('%Y-%m-%d'))

                weather = fetch_weather_for_kebele(kebele['lat'], kebele['lon'], weather_api_key)

                c.execute('SELECT crop, symptom, severity FROM pest_reports WHERE kebele=? AND report_time >= ?',
                          (kebele['name'], start_date_str))
                pest_reports = [{'crop': row[0], 'symptom': row[1], 'severity': row[2]} for row in c.fetchall()]

                risk_report = calculate_risk_prediction(ndvi_current, ndvi_past, weather, pest_reports, kebele['name'])
                results.append(risk_report)

                risk_level = risk_report.get('prediction', {}).get('risk_level', 'low')
                if risk_level in ['medium', 'high']:
                    c.execute('SELECT name, phone FROM farmers WHERE kebele=?', (kebele['name'],))
                    farmers = [{'name': r[0], 'phone': r[1]} for r in c.fetchall()]
                    alert_message = (f"Predicted pest risk level {risk_level} in {kebele['name']} for {risk_report.get('crop','unknown')}.\n"
                                     f"Recommendation: {risk_report['prediction']['recommendation']['english']}")
                    alerts.alert_farmers(farmers, alert_message)
                    alert_messages.append(alert_message)

                my_bar.progress((idx + 1) / len(kebeles), text=f"Processed {idx + 1} of {len(kebeles)} kebeles")

            set_last_run_date(conn, end_date_str)

            st.subheader("Risk Prediction Results")
            for res in results:
                st.json(res)

            st.subheader("Alert Messages Sent")
            for msg in alert_messages:
                st.markdown(f"- {msg}")

    conn.close()

if __name__ == "__main__":
    main()
