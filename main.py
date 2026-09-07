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
        
        prompt = f"""
        Create a detailed travel itinerary for the destination '{request.destination}' for {request.days} days.
        Language of response: {request.language}.
        Trip Date: {request.date}.
        Travelers: {request.travelers}.
        Budget: {request.budget}.
        Pace: {request.pace}.
        Interests: {request.interests}.
        
        You MUST return the response ONLY as a valid JSON object (no markdown formatting like ```json, just raw JSON) matching this exact structure:
        {{
          "itinerary": [
            {{
              "day_number": 1,
              "title": "Short title for day 1",
              "activities": [
                {{
                  "time": "09:00",
                  "place": "Place or attraction name",
                  "description": "Short description of the activity"
                }},
                {{
                  "time": "13:00",
                  "place": "Restaurant or activity",
                  "description": "Short description"
                }}
              ]
            }}
          ]
        }}
        Make sure there are exactly {request.days} objects in the itinerary array, for each day from 1 to {request.days}. All text fields (titles, places, descriptions) must be written in {request.language}.
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
