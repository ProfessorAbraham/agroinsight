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

# --------- Helper functions ---------
def fetch_kebele_data(kebele_name: str, days: int = 30):
    try:
        response = requests.get(f"{API_BASE_URL}/kebele/{kebele_name}?days={days}")
        if response.status_code == 200:
            return response.json()
        st.error(f"Error fetching data: {response.text}")
    except Exception as e:
        st.error(f"Failed to connect to API: {str(e)}")
    return None

def fetch_kebeles():
    try:
        response = requests.get(f"{API_BASE_URL}/kebeles")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

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
st.sidebar.header("Filters & Info")

# Fetch kebeles list for dropdown
kebeles = fetch_kebeles() or ['Kebele A', 'Kebele B', 'Kebele C']
selected_kebele = st.sidebar.selectbox("Select Kebele:", kebeles)

days_to_show = st.sidebar.slider("Select Date Range (days):", min_value=7, max_value=90, value=30)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **About AgroInsight**  
    Data is collected from satellite monitoring and AI pest detection models.
    
    Developed to help Ethiopian farmers monitor crop health and receive early warnings on pest outbreaks.
    """
)

# --------- Fetch or fallback data ---------
data = fetch_kebele_data(selected_kebele, days_to_show)

if not data:
    st.warning("API unavailable, loading demo data...")
    demo_dates = [date.today() - timedelta(days=i) for i in range(days_to_show)]
    data = {
        "kebele": selected_kebele,
        "current_risk": random.choice(list(RISK_COLORS.keys())),
        "historical_data": [
            {
                "date": str(d),
                "ndvi": round(0.2 + 0.7 * (i/days_to_show), 2),
                "temp": round(15 + 20 * (i/days_to_show), 1),
                "humidity": round(30 + 50 * (1 - i/days_to_show), 1),
                "pest_severity": random.choice(['low', 'medium', 'high']),
                "risk": random.choice(['low', 'medium', 'high'])
            }
            for i, d in enumerate(demo_dates)
        ],
        "predictions": [
            {
                "crop": "maize",
                "symptom": "yellow spots",
                "severity": "medium",
                "location": selected_kebele,
                "detection": {
                    "pest": "Fall Armyworm",
                    "risk_level": "medium",
                    "recommendation": {
                        "english": "Spray neem extract or ash-water mix within 2 days.",
                        "amharic": "በሁለት ቀናት ውስጥ የኒም ጭማቂ ወይም የአመድ እና የውሃ ውህድ ይርጩ።"
                    }
                }
            }
        ]
    }

# --------- Data processing ---------
df = pd.DataFrame(data['historical_data'])
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# --------- Overview metrics ---------
st.subheader(f"📊 Current Overview: {selected_kebele}")

col1, col2, col3, col4, col5 = st.columns(5)

# Current Risk Level with colored dot
risk = data['current_risk']
risk_color = RISK_COLORS.get(risk, 'gray')
col1.markdown(f"<h3 style='color:{risk_color};'>● {risk.upper()}</h3>", unsafe_allow_html=True)
col1.caption("Current Pest Risk Level")

# Latest NDVI
latest_ndvi = df.iloc[-1]['ndvi']
prev_ndvi = df.iloc[-2]['ndvi'] if len(df) > 1 else latest_ndvi
col2.metric("Latest NDVI", f"{latest_ndvi:.2f}", delta=trend_arrow(latest_ndvi, prev_ndvi))

# Latest Temperature
latest_temp = df.iloc[-1]['temp']
prev_temp = df.iloc[-2]['temp'] if len(df) > 1 else latest_temp
col3.metric("Latest Temperature (°C)", f"{latest_temp:.1f}", delta=trend_arrow(latest_temp, prev_temp))

# Latest Humidity
latest_humidity = df.iloc[-1]['humidity']
prev_humidity = df.iloc[-2]['humidity'] if len(df) > 1 else latest_humidity
col4.metric("Latest Humidity (%)", f"{latest_humidity:.1f}", delta=trend_arrow(latest_humidity, prev_humidity))

# Average Risk Level last period
avg_risk_num = df['risk'].apply(risk_level_to_numeric).mean()
if avg_risk_num < 1.5:
    avg_risk_str = "LOW"
    avg_risk_color = RISK_COLORS['low']
elif avg_risk_num < 2.5:
    avg_risk_str = "MEDIUM"
    avg_risk_color = RISK_COLORS['medium']
else:
    avg_risk_str = "HIGH"
    avg_risk_color = RISK_COLORS['high']
col5.markdown(f"<h3 style='color:{avg_risk_color};'>{avg_risk_str}</h3>", unsafe_allow_html=True)
col5.caption(f"Average Risk (Last {days_to_show} days)")

st.markdown("---")

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

# Humidity trend as separate chart for clarity
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

# Bar chart for risk level with meaningful color and no y-axis clutter
risk_fig = px.bar(
    df,
    x='date',
    y=[1]*len(df),  # dummy for uniform bar height
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

# Highlight highest risk day
max_risk_day = df.loc[df['risk'].apply(risk_level_to_numeric).idxmax()]
st.markdown(
    f"**Highest Risk Day:** {max_risk_day['date'].strftime('%Y-%m-%d')} with risk level "
    f"<span style='color:{RISK_COLORS[max_risk_day['risk']]}'>"
    f"{max_risk_day['risk'].upper()}</span>",
    unsafe_allow_html=True
)

st.markdown("---")

# --------- Pest Predictions ---------
st.subheader("🔍 Recent Pest Predictions & Recommendations")

if data.get('predictions'):
    for pred in data['predictions']:
        with st.expander(f"{pred['crop'].title()} - {pred['symptom']} (Severity: {pred['severity'].title()})"):
            det = pred['detection']
            st.markdown(f"**Pest:** {det['pest']}")
            st.markdown(f"**Risk Level:** "
                        f"<span style='color:{RISK_COLORS.get(det['risk_level'], 'black')}; "
                        f"font-weight:bold'>{det['risk_level'].upper()}</span>", unsafe_allow_html=True)
            st.markdown(f"**Recommendation (English):** {det['recommendation']['english']}")
            st.markdown(f"**ምክር (Amharic):** {det['recommendation']['amharic']}")
else:
    st.info("No recent pest predictions available.")

st.markdown("---")

# --------- Historical Data Table ---------
st.subheader("📋 Historical Data")
st.dataframe(df.set_index('date').sort_index(ascending=False), use_container_width=True)
