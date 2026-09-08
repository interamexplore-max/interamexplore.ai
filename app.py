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

    prompt = f"""
    You are an expert, professional travel agent and senior tour guide at InteramExplore.
    Create a highly detailed, rich, and deeply personalized travel itinerary for {data.destination} for {data.days} days.
    Travelers: {data.travelers}.
    Travel Date: {data.date}.
    Budget Level: {data.budget}.
    Pace: {data.pace}.
    Interests & Preferences: {data.interests}.
    Language: {data.language} (if Hebrew, write the entire response in fluent, natural Hebrew. If English, write in English).

    CRITICAL REQUIREMENTS FOR THE ITINERARY:
    1. Avoid generic descriptions. Every single activity MUST include real, specific, and well-known place names (e.g., specific restaurants, cafes, museums, viewpoints, parks, or hotels).
    2. For each day, provide a rich breakdown of times (Morning, Afternoon, Evening) with specific names of locations.
    3. Structure the output strictly as a JSON object with the following schema:
    {{
      "itinerary": [
        {{
          "day_number": 1,
          "title": "Short catchy title for the day",
          "activities": [
            {{
              "time": "09:00",
              "place": "Real specific name of place/attraction/restaurant",
              "description": "Detailed, rich description of what to do there, tips, and why it fits the traveler."
            }}
          ]
        }}
      ]
    }}
    Return ONLY valid JSON. No markdown backticks outside, no extra text.
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        itinerary_data = json.loads(cleaned_text.strip())
        return itinerary_data

    except Exception as e:
        print(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "InteramExplore AI is running successfully!"}
