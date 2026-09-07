import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json

app = FastAPI()

# --- הגדרת CORS שמאפשרת לאתר שלך לדבר עם השרת ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# הגדרת מפתח ה-API מתוך משתני הסביבה של Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class TripRequest(BaseModel):
    destination: str
    days: int
    travelers: str
    interests: str
    date: str = "בקרוב"
    budget: str = "בינוני / משפחתי"
    pace: str = "מאוזן"

@app.post("/api/generate-trip")
def generate_trip(request: TripRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="מפתח ה-API של Gemini אינו מוגדר בשרת.")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        צור מסלול טיול מפורט עבור היעד '{request.destination}' למשך {request.days} ימים.
        תאריך הטיול: {request.date}.
        המסלול מיועד עבור: {request.travelers}.
        תקציב מועדף: {request.budget}.
        קצב הטיול: {request.pace}.
        תחומי עניין עיקריים: {request.interests}.
        
        חובה להחזיר את התשובה אך ורק במבנה JSON תקין (ללא מעטפות טקסט נוספות כמו markdown) בדיוק במבנה הבא:
        {{
          "itinerary": [
            {{
              "day_number": 1,
              "title": "כותרת קצרה ליום הראשון (למשל: הגעה וסיור היכרות)",
              "activities": [
                {{
                  "time": "09:00",
                  "place": "שם המקום או האטרקציה",
                  "description": "תיאור קצרצר על הפעילות באותו זמן"
                }},
                {{
                  "time": "13:00",
                  "place": "שם המסעדה או הפעילות",
                  "description": "תיאור קצרצר"
                }}
              ]
            }}
          ]
        }}
        דאג שיהיו בדיוק {request.days} אובייקטים במערך ה-itinerary, עבור כל יום ויום מ-1 עד {request.days}.
        """

        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        trip_data = json.loads(text_response.strip())
        return trip_data

    except Exception as e:
        print(f"Error generating trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה ביצירת המסלול: {str(e)}")
