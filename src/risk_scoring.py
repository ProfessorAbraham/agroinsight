# risk_scoring.py
import datetime

def calculate_risk_prediction(ndvi_current, ndvi_past, weather, pest_reports, kebele_name):
    """
    Calculate a predicted pest/disease risk report as JSON-like dict.
    Returns detailed info about predicted crop risk, symptom, severity, location, risk level,
    and preventive recommendations (English & Amharic).

    Args:
      ndvi_current (float or None): Latest NDVI value
      ndvi_past (float or None): Past NDVI baseline
      weather (dict): {'temp': float, 'humidity': float, 'rain': float}
      pest_reports (list): List of dicts with 'crop', 'symptom', 'severity' keys
      kebele_name (str): Name of the kebele/location

    Returns:
      dict: structured prediction report
    """
    # Default crop/symptom/severity if no pest reports
    crop = "unknown"
    symptom = "unknown"
    severity = "none"
    predicted_pest = "Unknown Pest"

    # Simple logic to infer crop/symptom/severity from pest_reports if any
    if pest_reports:
        # Take the most severe report as basis
        sorted_reports = sorted(pest_reports, key=lambda x: {'none':0, 'few':1, 'many':2}.get(x['severity'], 0), reverse=True)
        top_report = sorted_reports[0]
        crop = top_report.get('crop', "unknown")
        symptom = top_report.get('symptom', "unknown")
        severity = top_report.get('severity', "none")

        # Example: if symptom contains 'holes', predict Fall Armyworm
        if 'hole' in symptom.lower():
            predicted_pest = "Fall Armyworm"
        else:
            predicted_pest = "General Pest"

    # Calculate risk score
    risk = 0.0

    if ndvi_current is not None and ndvi_past is not None:
        ndvi_drop = ndvi_past - ndvi_current
        if ndvi_drop > 0.05:
            risk += min(ndvi_drop * 5, 0.5)

    if weather:
        if 20 <= weather.get('temp', 0) <= 35:
            risk += 0.2
        if weather.get('humidity', 0) >= 70:
            risk += 0.2

    for report in pest_reports:
        sev = report.get('severity', 'none')
        if sev == 'many':
            risk += 0.2
        elif sev == 'few':
            risk += 0.1

    risk = min(risk, 1.0)

    # Map risk score to risk level
    if risk >= 0.7:
        risk_level = "high"
    elif risk >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Preventive recommendations based on risk level
    recommendations = {
        "high": {
            "english": "Urgently apply recommended treatments such as spraying neem extract or ash-water mix within 1 day.",
            "amharic": "በፍጥነት እንደ ምንጭ ኒም አብራሪ ወይም ማጥቢያ ውሃ አንድ ቀን ውስጥ ይቅበሉ።"
        },
        "medium": {
            "english": "Monitor fields closely and consider preventive spraying within 2 days.",
            "amharic": "ስለ እባብ እጅግ በጥንቃቄ ይመልከቱ እና በ2 ቀናት ውስጥ መታጠቢያ ያስቡ።"
        },
        "low": {
            "english": "No immediate action needed. Maintain good field hygiene.",
            "amharic": "ምንም አስቸኳይ እርምጃ የለም። ጥሩ መንገድ አስተዳደር ይቀጥሉ።"
        }
    }

    rec = recommendations[risk_level]

    return {
        "crop": crop,
        "symptom": symptom + " (predicted)",
        "severity": severity + " (predicted)",
        "location": kebele_name,
        "risk_score": risk,
        "prediction": {
            "pest": predicted_pest,
            "risk_level": risk_level,
            "recommendation": rec
        }
    }
