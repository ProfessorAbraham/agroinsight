from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(title="AgroInsight API")

ETHIOPIAN_TOWNS = [
    "Addis Ababa",
    "Adama",
    "Hawassa",
    "Bahir Dar",
    "Mekelle",
    "Dire Dawa",
    "Gondar",
    "Jijiga",
    "Jimma",
    "Shashamane"
]

CROPS = ["maize", "teff", "wheat", "sorghum", "barley"]

SYMPTOMS = ["leaf holes", "yellow spots", "wilted leaves", "stem borers", "powdery mildew"]

PESTS = [
    {"name": "Fall Armyworm", "severity_levels": ["low", "medium", "high"]},
    {"name": "Aphids", "severity_levels": ["low", "medium", "high"]},
    {"name": "Maize Weevil", "severity_levels": ["low", "medium", "high"]},
    {"name": "Stem Borer", "severity_levels": ["low", "medium", "high"]},
]

RECOMMENDATIONS = {
    "Fall Armyworm": {
        "low": {
            "english": "Monitor crops closely and maintain field hygiene.",
            "amharic": "ሰብሎችን በቅርበት ይከታተሉ እንዲሁም የእርሻዎን ንፅህና ይጠብቁ።"
        },
        "medium": {
            "english": "Spray neem extract or ash-water mix within 2 days.",
            "amharic": "በሁለት ቀናት ውስጥ የኒም ጭማቂ ወይም የአመድ እና የውሃ ውህድ ይርጩ።"
        },
        "high": {
            "english": "Apply recommended pesticides immediately and remove infected plants.",
            "amharic": "የተመከሩትን ፀረ-ተባይ መድኃኒቶች በአስቸኳይ ይርጩ እና የተበከሉ ተክሎችን ያስወግዱ።"
        }
    },
    "Aphids": {
        "low": {
            "english": "Encourage natural predators like ladybugs.",
            "amharic": "እንደ ጥንዚዛ ያሉ ተፈጥሯዊ አዳኞችን ያበረታቱ።"
        },
        "medium": {
            "english": "Use insecticidal soap spray every 5 days.",
            "amharic": "በየ 5 ቀኑ የፀረ-ነፍሳት ሳሙና ውህድ ይርጩ።"
        },
        "high": {
            "english": "Apply systemic insecticides and remove severely infested plants.",
            "amharic": "ሲስተሚክ ፀረ-ተባይ መድኃኒቶችን ይርጩ እና በጠና የተበከሉ ተክሎችን ያስወግዱ።"
        }
    },
    # Add other pest recommendations similarly...
}

class Recommendation(BaseModel):
    english: str
    amharic: str

class Detection(BaseModel):
    pest: str
    risk_level: str
    recommendation: Recommendation

class Prediction(BaseModel):
    crop: str
    symptom: str
    severity: str
    location: str
    detection: Detection

def generate_mock_prediction(location: str) -> Prediction:
    crop = random.choice(CROPS)
    symptom = random.choice(SYMPTOMS)
    severity = random.choice(["few", "many", "severe"])

    pest_info = random.choice(PESTS)
    pest_name = pest_info["name"]
    risk_level = random.choice(pest_info["severity_levels"])

    recommendation = RECOMMENDATIONS.get(pest_name, {}).get(risk_level, {
        "english": "No specific recommendation available.",
        "amharic": "ምንም ልዩ ምክር አልተገኘም።"
    })

    return Prediction(
        crop=crop,
        symptom=symptom,
        severity=severity,
        location=location,
        detection=Detection(
            pest=pest_name,
            risk_level=risk_level,
            recommendation=Recommendation(
                english=recommendation["english"],
                amharic=recommendation["amharic"]
            )
        )
    )

@app.get("/")
async def root():
    return {"message": "Welcome to AgroInsight API"}

@app.get("/predictions/{location}", response_model=Prediction)
async def get_prediction(location: str):
    if location not in ETHIOPIAN_TOWNS:
        return {"error": "Location not supported."}
    prediction = generate_mock_prediction(location)
    return prediction
