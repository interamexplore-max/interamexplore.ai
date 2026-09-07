import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class TripRequest(BaseModel):
    language: str = "עברית"
    destination: str
    days: int
    travelers: str
    interests: str
    date: str = "בקרוב"
    budget: str = "בינוני / משפחתי"
    pace: str = "מאוזן"

@app.get("/")
def read_root():
    return {"status": "OK"}

@app.post("/api/generate-trip")
async def generate_trip(request: TripRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing")
    
    if request.language == "English":
        prompt = f"""Create a travel itinerary for '{request.destination}' for {request.days} days in English. 
Return ONLY a valid JSON object without any markdown formatting (no ```json):
{{
  "itinerary": [
    {{
      "day_number": 1,
      "title": "Day title",
      "activities": [
        {{"time": "09:00", "place": "Place name", "description": "Description"}}
      ]
    }}
  ]
}}"""
    else:
        prompt = f"""צור מסלול טיול ליעד '{request.destination}' למשך {request.days} ימים בעברית בלבד. 
החזר אך ורק אובייקט JSON תקין ללא שום מעטפת markdown (ללא ```json):
{{
  "itinerary": [
    {{
      "day_number": 1,
      "title": "כותרת ליום",
      "activities": [
        {{"time": "09:00", "place": "שם המקום", "description": "תיאור הפעילות"}}
      ]
    }}
  ]
}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                print(f"Gemini API Error details: {response.text}")
                raise HTTPException(status_code=500, detail=f"Google API Error: {response.text}")
            
            res_data = response.json()
            text_response = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            return json.loads(text_response.strip())
            
        except Exception as e:
            print(f"Server Exception: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
