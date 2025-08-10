# streamlit_app.py
import streamlit as st
import pandas as pd
import datetime
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import uvicorn

# --- MOCK DATA GENERATION ---

KEBELES = ['Kebele A', 'Kebele B', 'Kebele C']

def generate_mock_data():
    today = datetime.date.today()
    dates = [today - datetime.timedelta(days=i) for i in range(30)]  # last 30 days

    data = []
    for kebele in KEBELES:
        for date in dates:
            ndvi = round(random.uniform(0.2, 0.9), 2)
            temp = round(random.uniform(15, 35), 1)
            humidity = round(random.uniform(30, 80), 1)
            pest_severity = random.choice(['low', 'medium', 'high'])
            data.append({
                'kebele': kebele,
                'date': date,
                'ndvi': ndvi,
                'temp': temp,
                'humidity': humidity,
                'pest_severity': pest_severity,
            })
    return pd.DataFrame(data)

MOCK_DATA = generate_mock_data()

# --- RISK PREDICTION LOGIC ---

def predict_risk(row):
    risk = 'low'
    if row['pest_severity'] == 'high' or row['ndvi'] < 0.3 or row['temp'] > 30:
        risk = 'high'
    elif row['pest_severity'] == 'medium' or (0.3 <= row['ndvi'] < 0.5) or (25 < row['temp'] <= 30):
        risk = 'medium'
    return risk

MOCK_DATA['risk'] = MOCK_DATA.apply(predict_risk, axis=1)

# --- STREAMLIT DASHBOARD ---

st.title("AgroInsight: Pest Risk Dashboard")

kebele_select = st.selectbox("Select Kebele", KEBELES)
days_back = st.slider("Days back to show", 1, 30, 14)

today = datetime.date.today()
start_date = today - datetime.timedelta(days=days_back)

filtered = MOCK_DATA[(MOCK_DATA['kebele'] == kebele_select) & (MOCK_DATA['date'] >= start_date)]

st.subheader(f"Predictions for {kebele_select} (Last {days_back} days)")
st.line_chart(filtered.set_index('date')[['ndvi', 'temp']])

st.subheader("Risk Levels Over Time")
risk_colors = {'low': 'green', 'medium': 'orange', 'high': 'red'}
filtered['risk_color'] = filtered['risk'].map(risk_colors)
st.bar_chart(filtered.set_index('date')['risk'].apply(lambda x: {'low': 0, 'medium': 1, 'high': 2}[x]))

# Show latest risk prediction
latest = filtered.sort_values('date').iloc[-1]
st.markdown(f"### Latest Risk Prediction ({latest['date']}): **{latest['risk'].upper()}**")

# --- FASTAPI SERVER FOR API ENDPOINT ---

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/latest_prediction/{kebele_name}")
def get_latest_prediction(kebele_name: str):
    df = MOCK_DATA[MOCK_DATA['kebele'] == kebele_name]
    if df.empty:
        return {"error": "Kebele not found"}
    latest_row = df.sort_values('date').iloc[-1]
    return {
        "kebele": kebele_name,
        "date": str(latest_row['date']),
        "ndvi": latest_row['ndvi'],
        "temp": latest_row['temp'],
        "humidity": latest_row['humidity'],
        "pest_severity": latest_row['pest_severity'],
        "risk": latest_row['risk'],
    }

# Run FastAPI in background thread alongside Streamlit
def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if 'api_thread' not in st.session_state:
    import threading
    st.session_state.api_thread = threading.Thread(target=run_api, daemon=True)
    st.session_state.api_thread.start()
