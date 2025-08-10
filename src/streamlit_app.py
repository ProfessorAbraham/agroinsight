import streamlit as st
import datetime
import ee
from db import get_connection, create_tables, create_metadata_table, get_last_run_date, set_last_run_date
from satellite import fetch_ndvi_for_kebele
from weather import fetch_weather_for_kebele
from risk_scoring import calculate_risk_report

@st.cache_resource
def init_earth_engine():
    try:
        ee.Initialize(project='youtube-scrape-462207')
        return True
    except Exception as e:
        st.error(f"Error initializing Earth Engine: {e}")
        return False

ee_ready = init_earth_engine()

conn = get_connection()
create_tables(conn)
create_metadata_table(conn)

st.title("AgroInsight Risk Prediction & Management")

st.sidebar.header("Register")

registration_type = st.sidebar.selectbox("Register as", ["Add Kebele", "Add Farmer"])

if registration_type == "Add Kebele":
    kebele_name = st.sidebar.text_input("Kebele Name")
    lat = st.sidebar.text_input("Latitude (e.g. 8.55)")
    lon = st.sidebar.text_input("Longitude (e.g. 39.27)")
    if st.sidebar.button("Add Kebele"):
        try:
            c = conn.cursor()
            c.execute("INSERT INTO kebeles (name, latitude, longitude) VALUES (?, ?, ?)", (kebele_name, float(lat), float(lon)))
            conn.commit()
            st.sidebar.success(f"Kebele '{kebele_name}' added.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

elif registration_type == "Add Farmer":
    farmer_name = st.sidebar.text_input("Farmer Name")
    phone = st.sidebar.text_input("Phone Number")
    c = conn.cursor()
    c.execute("SELECT name FROM kebeles")
    kebeles_list = [row[0] for row in c.fetchall()]
    farmer_kebele = st.sidebar.selectbox("Select Kebele", kebeles_list)
    if st.sidebar.button("Add Farmer"):
        try:
            c.execute("INSERT INTO farmers (name, phone, kebele) VALUES (?, ?, ?)", (farmer_name, phone, farmer_kebele))
            conn.commit()
            st.sidebar.success(f"Farmer '{farmer_name}' added.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

st.markdown("---")

st.header("Run Risk Prediction")

last_run_str = get_last_run_date(conn)
if last_run_str:
    st.write(f"**Last prediction run:** {last_run_str}")
else:
    st.write("**Last prediction run:** Never")

run_button = st.button("Run Prediction Now")

if run_button:
    if not ee_ready:
        st.error("Earth Engine not initialized. Cannot run prediction.")
    else:
        last_run_date = datetime.date.today() - datetime.timedelta(days=14) if last_run_str is None else datetime.datetime.strptime(last_run_str, '%Y-%m-%d').date()
        today = datetime.date.today()
        if last_run_date >= today:
            st.info(f"No new data to fetch. Last run date ({last_run_date}) is today or later.")
        else:
            start_date_str = last_run_date.strftime('%Y-%m-%d')
            end_date_str = today.strftime('%Y-%m-%d')
            st.write(f"Fetching data from {start_date_str} to {end_date_str}...")

            c = conn.cursor()
            c.execute('SELECT name, latitude, longitude FROM kebeles')
            kebeles = [{'name': row[0], 'lat': row[1], 'lon': row[2]} for row in c.fetchall()]

            weather_api_key = '236bcfdce4f533e65b2a62bf1182aa9c'
            results = []

            for kebele in kebeles:
                try:
                    ndvi_current = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'], start_date_str, end_date_str)
                except Exception as e:
                    st.warning(f"Error fetching NDVI for {kebele['name']}: {e}")
                    ndvi_current = None

                past_start = today - datetime.timedelta(days=21)
                past_end = today - datetime.timedelta(days=14)
                try:
                    ndvi_past = fetch_ndvi_for_kebele(kebele['name'], kebele['lon'], kebele['lat'],
                                                      past_start.strftime('%Y-%m-%d'), past_end.strftime('%Y-%m-%d'))
                except Exception as e:
                    st.warning(f"Error fetching past NDVI for {kebele['name']}: {e}")
                    ndvi_past = None

                try:
                    weather = fetch_weather_for_kebele(kebele['lat'], kebele['lon'], weather_api_key)
                except Exception as e:
                    st.warning(f"Error fetching weather for {kebele['name']}: {e}")
                    weather = None

                c.execute('SELECT crop, symptom, severity FROM pest_reports WHERE kebele=? AND report_time >= ?',
                          (kebele['name'], start_date_str))
                pest_reports = [{'crop': row[0], 'symptom': row[1], 'severity': row[2]} for row in c.fetchall()]

                risk_report = calculate_risk_report(ndvi_current, ndvi_past, weather, pest_reports, kebele['name'])
                results.append(risk_report)

            set_last_run_date(conn, end_date_str)

            st.subheader("Risk Prediction Results")
            for res in results:
                st.json(res)

conn.close()
