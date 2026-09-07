import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class TripRequest(BaseModel):
    language: str = "עברית"
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
        raise HTTPException(status_code=500, detail="מפתח ה-API אינו מוגדר.")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # התאמת שפת ההנחיה באופן מלא לפי בחירת המשתמש
        if request.language == "English":
            prompt = f"""
            You are a professional travel agent. Create a complete, detailed travel itinerary for the destination '{request.destination}' for {request.days} days.
            CRITICAL RULE: The ENTIRE response must be strictly in English. Every single word, including day titles, activity places, and descriptions, must be written in English only. Do not use any Hebrew words.
            
            Trip Date: {request.date}.
            Travelers: {request.travelers}.
            Budget: {request.budget}.
            Pace: {request.pace}.
            Interests: {request.interests}.
            
            Return the response ONLY as a valid JSON object (no markdown formatting like ```json, just raw JSON) matching this exact structure:
            {{
              "itinerary": [
                {{
                  "day_number": 1,
                  "title": "Short title for day 1 in English",
                  "activities": [
                    {{
                      "time": "09:00",
                      "place": "Place or attraction name in English",
                      "description": "Short description of the activity in English"
                    }}
                  ]
                }}
              ]
            }}
            Make sure there are exactly {request.days} objects in the itinerary array, for each day from 1 to {request.days}.
            """
        else:
            prompt = f"""
            צור מסלול טיול מפורט עבור היעד '{request.destination}' למשך {request.days} ימים בעברית בלבד.
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
                  "title": "כותרת קצרה ליום הראשון בעברית",
                  "activities": [
                    {{
                      "time": "09:00",
                      "place": "שם המקום בעברית",
                      "description": "תיאור הפעילות בעברית"
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
        raise HTTPException(status_code=500, detail=f"שגיאה: {str(e)}")
