import os
import time
import uvicorn
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
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if request.language == "English":
        prompt = f"""
        You are a professional travel agent. Create a complete, detailed travel itinerary for the destination '{request.destination}' for {request.days} days.
        CRITICAL RULE: The ENTIRE response must be strictly in English. Every single word must be in English only.
        Trip Date: {request.date}. Travelers: {request.travelers}. Budget: {request.budget}. Pace: {request.pace}. Interests: {request.interests}.
        
        Return the response ONLY as a valid JSON object (no markdown formatting like ```json, just raw JSON) matching this exact structure:
        {{
          "itinerary": [
            {{
              "day_number": 1,
              "title": "Short title for day 1 in English",
              "activities": [
                {{
                  "time": "09:00",
                  "place": "Place name in English",
                  "description": "Short description in English"
                }}
              ]
            }}
          ]
        }}
        Make sure there are exactly {request.days} objects in the itinerary array.
        """
    else:
        prompt = f"""
        צור מסלול טיול מפורט עבור היעד '{request.destination}' למשך {request.days} ימים בעברית בלבד.
        תאריך הטיול: {request.date}. נוסעים: {request.travelers}. תקציב: {request.budget}. קצב: {request.pace}. עניין: {request.interests}.
        
        חובה להחזיר אך ורק מבנה JSON תקין (ללא markdown) בדיוק במבנה הבא:
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
        דאג שיהיו בדיוק {request.days} אובייקטים במערך ה-itinerary.
        """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text_response = response.text.strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            trip_data = json.loads(text_response.strip())
            return trip_data

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"שגיאה ביצירת המסלול עקב עומס זמני, אנא נסה שוב בעוד רגע.")
            time.sleep(1.5)

# השורה הזו דואגת שהשרת יתחבר לפורט הנכון של Render אוטומטית
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
