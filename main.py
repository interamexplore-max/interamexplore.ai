import os
import time
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
        print("ERROR: GEMINI_API_KEY is missing!")
        raise HTTPException(status_code=500, detail="מפתח ה-API אינו מוגדר ב-Render.")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if request.language == "English":
            prompt = f"""
            Create a travel itinerary for '{request.destination}' for {request.days} days in English only.
            Return ONLY a raw JSON object (no markdown formatting, no code blocks like ```json) with this exact structure:
            {{
              "itinerary": [
                {{
                  "day_number": 1,
                  "title": "Day title in English",
                  "activities": [
                    {{
                      "time": "09:00",
                      "place": "Place name",
                      "description": "Description"
                    }}
                  ]
                }}
              ]
            }}
            Make sure there are exactly {request.days} days.
            """
        else:
            prompt = f"""
            צור מסלול טיול ליעד '{request.destination}' למשך {request.days} ימים בעברית בלבד.
            החזר אך ורק אובייקט JSON טהור (ללא עיצוב markdown, ללא ```json) במבנה הבא בדיוק:
            {{
              "itinerary": [
                {{
                  "day_number": 1,
                  "title": "כותרת ליום בעברית",
                  "activities": [
                    {{
                      "time": "09:00",
                      "place": "שם המקום",
                      "description": "תיאור"
                    }}
                  ]
                }}
              ]
            }}
            וודא שיש בדיוק {request.days} ימים.
            """

        print(f"Sending prompt for {request.destination}, {request.days} days...")
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        print(f"Raw AI response received: {text_response[:100]}...")
        
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        trip_data = json.loads(text_response.strip())
        return trip_data

    except Exception as e:
        print(f"CRITICAL ERROR in generate_trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בשרת: {str(e)}")
