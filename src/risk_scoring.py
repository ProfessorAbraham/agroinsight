# risk_scoring.py
import datetime

def calculate_risk_score(ndvi_current, ndvi_past, weather, pest_reports):
    """
    Simple example combining NDVI drop, weather, and pest reports to a risk score between 0 and 1.
    
    Args:
      ndvi_current (float): Latest NDVI
      ndvi_past (float): NDVI from previous period
      weather (dict): {'temp': float, 'humidity': float, 'rain': float}
      pest_reports (list): List of dicts with 'severity' keys ('few', 'many')
    
    Returns:
      float: risk score [0-1]
    """
    risk = 0.0
    
    # NDVI drop: bigger drop = higher risk
    if ndvi_current is not None and ndvi_past is not None:
        ndvi_drop = ndvi_past - ndvi_current
        if ndvi_drop > 0.05:
            risk += min(ndvi_drop * 5, 0.5)  # max 0.5 from NDVI
    
    # Weather contribution
    if weather:
        if 20 <= weather['temp'] <= 35:
            risk += 0.2  # favorable temp for pests
        if weather['humidity'] >= 70:
            risk += 0.2
    
    # Pest reports severity
    for report in pest_reports:
        if report.get('severity') == 'many':
            risk += 0.2
        elif report.get('severity') == 'few':
            risk += 0.1
    
    return min(risk, 1.0)
