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
    You are an expert travel agent at InteramExplore. Create a detailed travel itinerary for {data.destination} for {data.days} days.
    Travelers: {data.travelers}. Date: {data.date}. Budget: {data.budget}. Pace: {data.pace}. Interests: {data.interests}.
    Language: {data.language}.
    Structure the output strictly as a JSON object with this schema:
    {{
      "itinerary": [
        {{
          "day_number": 1,
          "title": "Title in {data.language}",
          "activities": [
            {{
              "time": "09:00",
              "place": "Place name",
              "description": "Description in {data.language}"
            }}
          ]
        }}
      ]
    }}
    Return ONLY valid JSON. No markdown backticks outside.
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return json.loads(cleaned_text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "InteramExplore AI is running successfully!"}
