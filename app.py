import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json

app = FastAPI()

# הפעלת CORS לחיבור חלק בין ה-Frontend לשרת ב-Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# הגדרת מפתח ה-API של Gemini מתוך משתני הסביבה
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class TripRequest(BaseModel):
    destination: str
    days: int
    travelers: str
    interests: str
    date: str
    budget: str
    pace: str
    language: str = "עברית"

@app.post("/api/generate-trip")
async def generate_trip(data: TripRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing on the server.")

    # פרומפט מקצועי, ממוקד וקשיח למניעת תקלות שפה ותוכן שטחי
    prompt = f"""
    You are an expert, professional travel agent and senior tour guide at Interam Explore.
    Create a highly detailed, professional, and deeply personalized travel itinerary for {data.destination} for {data.days} days.
    
    Travelers: {data.travelers}.
    Travel Date: {data.date}.
    Budget Level: {data.budget}.
    Pace: {data.pace}.
    Interests & Preferences: {data.interests}.
    
    CRITICAL LANGUAGE INSTRUCTION:
    - The requested language is: {data.language}.
    - If the language is English, write the ENTIRE response (titles, descriptions, travel info, tips) strictly in fluent English.
    - If the language is Hebrew, write the ENTIRE response strictly in fluent Hebrew. Do NOT mix languages.

    CRITICAL CONTENT REQUIREMENTS:
    1. Avoid generic descriptions entirely (e.g., do not write "visit a local restaurant"). Every activity MUST include real, specific, and well-known place names (specific restaurants, cafes, museums, viewpoints, parks, or hotels).
    2. Include logistical data for each activity: travel time/distance from the previous location, and recommended duration of stay.
    3. Add a professional tip (Pro Tip) for each day or key activity.
    4. Structure the output strictly as a valid JSON object with the exact schema below. Do not wrap it with anything other than valid JSON.

    Required JSON Schema:
    {{
      "itinerary": [
        {{
          "day_number": 1,
          "title": "Catchy title for the day",
          "daily_tip": "Important logistical tip for this day (e.g., book tickets in advance)",
          "activities": [
            {{
              "time": "09:00",
              "place": "Real specific name of place/attraction/restaurant",
              "description": "Detailed description of what to do there and why it fits.",
              "travel_info": "Distance / travel time from previous spot (e.g., 15 mins drive)",
              "duration": "Recommended stay: 2 hours"
            }}
          ],
          "accommodation_recommendation": "Recommended area or hotel to stay tonight"
        }}
      ]
    }}
    
    Return ONLY valid JSON. No markdown code blocks like ```json outside, just the raw JSON text or standard clean JSON.
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        cleaned_text = response.text.strip()
        # ניקוי בטוח של מעטפות מרקדון במידה והמודל בכל זאת מחזיר כאלו
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        itinerary_data = json.loads(cleaned_text.strip())
        return itinerary_data

    except Exception as e:
        print(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "Interam Explore AI Backend is running successfully!"}
