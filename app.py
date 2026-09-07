import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

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

@app.get("/")
def read_root():
    return {"status": "OK"}

@app.post("/api/generate-trip")
async def generate_trip(request: TripRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")
    
    is_eng = request.language == "English"
    
    json_structure = '{"itinerary": [{"day_number": 1, "title": "Day Title", "activities": [{"time": "09:00", "place": "Place Name", "description": "Description"}]}]}'
    
    if is_eng:
        prompt = f"Create a travel itinerary for {request.destination} for {request.days} days. Return ONLY a raw JSON object with this exact structure: {json_structure}"
    else:
        prompt = f"צור מסלול טיול ליעד {request.destination} למשך {request.days} ימים בעברית בלבד. החזר אך ורק אובייקט JSON טהור במבנה הבא: {json_structure}"

    try:
        # שימוש במודל הרשמי של גוגל דרך הספרייה שלהם
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        text_response = text_response.strip()
        
        try:
            parsed_data = json.loads(text_response)
            return parsed_data
        except json.JSONDecodeError:
            return {
                "itinerary": [
                    {
                        "day_number": i + 1,
                        "title": f"Day {i + 1}" if is_eng else f"יום {i + 1}",
                        "activities": [
                            {
                                "time": "09:00",
                                "place": request.destination,
                                "description": text_response[:200]
                            }
                        ]
                    } for i in range(request.days)
                ]
            }
        
    except Exception as e:
        print(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
