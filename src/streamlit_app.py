import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

# --------- Constants ---------
API_BASE_URL = "http://localhost:8000"  # Update with your API base URL

# Colors for risk levels
RISK_COLORS = {'low': '#4CAF50', 'medium': '#FFC107', 'high': '#F44336'}

ETHIOPIAN_TOWNS = [
    "Addis Ababa", "Adama", "Hawassa", "Bahir Dar", "Mekelle",
    "Dire Dawa", "Gondar", "Jijiga", "Jimma", "Shashamane"
]

# --------- Helper functions ---------
def fetch_prediction(location: str):
    try:
        response = requests.get(f"{API_BASE_URL}/predictions/{location}", timeout=3)
        if response.status_code == 200:
            return response.json()
        # silently ignore bad status
    except Exception:
        # silently ignore connection errors or any exceptions
        pass
    return None

def risk_level_to_numeric(risk):
    mapping = {'low': 1, 'medium': 2, 'high': 3}
    return mapping.get(risk.lower(), 0)

def trend_arrow(current, previous):
    if current > previous:
        return "▲"
    elif current < previous:
        return "▼"
    else:
        return "→"

# --------- Streamlit page config ---------
st.set_page_config(page_title="AgroInsight Dashboard", page_icon="🌱", layout="wide")

# --------- Page Header ---------
st.title("🌱 AgroInsight: Smart Farming Dashboard")
st.markdown(
    """
    This dashboard provides **real-time monitoring and actionable insights** on crop health and pest risks 
    to empower Ethiopian farmers for improved yield and resilience.
    """
)

# --------- Sidebar ---------
st.sidebar.header("Select Location")

selected_town = st.sidebar.selectbox("Select Town:", ETHIOPIAN_TOWNS)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **About AgroInsight**  
    Data is collected from satellite monitoring and AI pest detection models.
    
    Developed to help Ethiopian farmers monitor crop health and receive early warnings on pest outbreaks.
    """
)

# --------- Fetch prediction ---------
prediction = fetch_prediction(selected_town)

# --------- Demo fallback if API fails ---------
if not prediction:
    st.info("Using demo data (API not reachable).")
    prediction = {
        "crop": "maize",
        "symptom": "yellow spots",
        "severity": "medium",
        "location": selected_town,
        "detection": {
            "pest": "Fall Armyworm",
            "risk_level": "medium",
            "recommendation": {
                "english": "Spray neem extract or ash-water mix within 2 days.",
                "amharic": "በሁለት ቀናት ውስጥ የኒም ጭማቂ ወይም የአመድ እና የውሃ ውህድ ይርጩ።"
            }
        }
    }

# --------- Display Overview ---------
st.subheader(f"📊 Current Prediction Overview: {selected_town}")

risk = prediction["detection"]["risk_level"]
risk_color = RISK_COLORS.get(risk, "gray")

col1, col2, col3 = st.columns([1, 2, 2])

# Pest risk level big indicator
col1.markdown(f"<h2 style='color:{risk_color};'>● {risk.upper()} RISK</h2>", unsafe_allow_html=True)
col1.caption("Current Pest Risk Level")

# Crop and symptom info
col2.markdown(f"**Crop:** {prediction['crop'].title()}")
col2.markdown(f"**Symptom:** {prediction['symptom'].title()}")
col2.markdown(f"**Severity:** {prediction['severity'].title()}")

# Pest and recommendation
col3.markdown(f"**Detected Pest:** {prediction['detection']['pest']}")
col3.markdown(f"**Recommendation (English):** {prediction['detection']['recommendation']['english']}")
col3.markdown(f"**ምክር (Amharic):** {prediction['detection']['recommendation']['amharic']}")

st.markdown("---")

# --------- Simulated Historical Data ---------
days_to_show = 30
dates = pd.date_range(end=date.today(), periods=days_to_show)

random.seed(42)  # for reproducibility
hist_data = {
    "date": dates,
    "ndvi": [round(0.4 + 0.3 * (i / days_to_show) + random.uniform(-0.05, 0.05), 2) for i in range(days_to_show)],
    "temp": [round(18 + 5 * (i / days_to_show) + random.uniform(-1.5, 1.5), 1) for i in range(days_to_show)],
    "humidity": [round(40 + 10 * (1 - i / days_to_show) + random.uniform(-3, 3), 1) for i in range(days_to_show)],
    "risk": [random.choices(["low", "medium", "high"], weights=[0.5,0.3,0.2])[0] for _ in range(days_to_show)],
}

df = pd.DataFrame(hist_data)

# --------- Environmental trends ---------
st.subheader("🌡️ Environmental Trends")

fig_env = make_subplots(specs=[[{"secondary_y": True}]])

fig_env.add_trace(
    go.Scatter(
        x=df['date'], y=df['ndvi'], name="NDVI", mode="lines+markers",
        line=dict(color=RISK_COLORS['low']),
        hovertemplate='Date: %{x|%Y-%m-%d}<br>NDVI: %{y:.2f}<extra></extra>'
    ),
    secondary_y=False
)

fig_env.add_trace(
    go.Scatter(
        x=df['date'], y=df['temp'], name="Temperature (°C)", mode="lines+markers",
        line=dict(color=RISK_COLORS['high']),
        hovertemplate='Date: %{x|%Y-%m-%d}<br>Temp: %{y:.1f}°C<extra></extra>'
    ),
    secondary_y=True
)

fig_env.update_layout(
    hovermode="x unified",
    title="NDVI and Temperature Trends",
    legend=dict(orientation='h', y=1.1),
    margin=dict(t=40)
)
fig_env.update_yaxes(title_text="NDVI", secondary_y=False, range=[0,1])
fig_env.update_yaxes(title_text="Temperature (°C)", secondary_y=True)
st.plotly_chart(fig_env, use_container_width=True)

fig_humidity = px.line(
    df,
    x='date',
    y='humidity',
    title="Humidity Trend (%)",
    markers=True,
    labels={"humidity": "Humidity (%)", "date": "Date"},
)
fig_humidity.update_traces(line_color="#1f77b4")
st.plotly_chart(fig_humidity, use_container_width=True)

st.markdown("---")

# --------- Pest Risk Trends ---------
st.subheader("🦗 Pest Risk Level Over Time")

risk_fig = px.bar(
    df,
    x='date',
    y=[1]*len(df),
    color='risk',
    color_discrete_map=RISK_COLORS,
    labels={"date": "Date", "risk": "Pest Risk"},
    title="Pest Risk Levels",
    hover_data={'risk': True, 'date': False}
)
risk_fig.update_layout(
    yaxis=dict(showticklabels=False, showgrid=False),
    showlegend=True,
    margin=dict(t=40)
)
st.plotly_chart(risk_fig, use_container_width=True)

max_risk_day = df.loc[df['risk'].apply(risk_level_to_numeric).idxmax()]
st.markdown(
    f"**Highest Risk Day:** {max_risk_day['date'].strftime('%Y-%m-%d')} with risk level "
    f"<span style='color:{RISK_COLORS[max_risk_day['risk']]}'>"
    f"{max_risk_day['risk'].upper()}</span>",
    unsafe_allow_html=True
)

st.markdown("---")

# --------- Historical Data Table ---------
st.subheader("📋 Historical Environmental Data")
st.dataframe(df.set_index('date').sort_index(ascending=False), use_container_width=True)
