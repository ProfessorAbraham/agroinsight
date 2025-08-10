# risk_scoring.py
import datetime

def analyze_crop_risk(kebele_name, crop_type, ndvi_current, ndvi_past, weather, pest_reports):
    """
    Analyze crop risk and return a detailed structured output.

    Args:
      kebele_name (str): Location name
      crop_type (str): Crop being analyzed
      ndvi_current (float): Latest NDVI
      ndvi_past (float): NDVI from previous period
      weather (dict): {'temp': float, 'humidity': float, 'rain': float}
      pest_reports (list): List of dicts with 'severity' keys ('few', 'many')

    Returns:
      dict: Structured risk analysis
    """
    risk_score = 0.0
    likely_pest = None
    likely_symptom = None
    severity_label = "low"

    # NDVI drop analysis
    if ndvi_current is not None and ndvi_past is not None:
        ndvi_drop = ndvi_past - ndvi_current
        if ndvi_drop > 0.05:
            risk_score += min(ndvi_drop * 5, 0.5)
            likely_symptom = "yellowing or damaged leaves"

    # Weather pattern analysis (example rules)
    if weather:
        if 20 <= weather['temp'] <= 35 and weather['humidity'] >= 70:
            risk_score += 0.3
            likely_pest = "Fall Armyworm"
            likely_symptom = "leaf holes"
        elif weather['humidity'] < 40 and weather['temp'] > 30:
            likely_pest = "Stem Borer"
            likely_symptom = "wilting stems"

    # Pest reports analysis
    for report in pest_reports:
        if report.get('severity') == 'many':
            risk_score += 0.2
            severity_label = "many"
        elif report.get('severity') == 'few':
            risk_score += 0.1
            severity_label = "few"

    # Final risk level classification
    if risk_score >= 0.7:
        risk_level = "high"
    elif risk_score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Recommendations (basic examples)
    recommendations = {
        "Fall Armyworm": {
            "english": "Spray neem extract or ash-water mix within 2 days.",
            "amharic": "እባክዎ በ2 ቀናት ውስጥ  አብራሪ ኒም ኤክስትራክተር ይርጩ።"
        },
        "Stem Borer": {
            "english": "Destroy affected stems and apply recommended pesticide.",
            "amharic": "የተጎዱ ግንዶችን አስወግዱ እና ኬሚካል ይጠቀሙ።"
        },
        "Unknown": {
            "english": "Monitor crop daily and consult local extension officer.",
            "amharic": "የእርሻዎን በየቀኑ ይከታተሉ እና ከአካባቢ መምሪያ ባለሙያ ጋር ይወያዩ።"
        }
    }

    pest_key = likely_pest if likely_pest else "Unknown"

    return {
        "crop": crop_type,
        "symptom": likely_symptom if likely_symptom else "unknown",
        "severity": severity_label,
        "location": kebele_name,
        "detection": {
            "pest": pest_key,
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "recommendation": recommendations[pest_key]
        }
    }
