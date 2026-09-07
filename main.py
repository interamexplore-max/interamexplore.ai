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

@app.post("/api/generate-trip")
async def generate_trip(request: TripRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="מפתח ה-API אינו מוגדר ב-Render.")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # איתור דינמי של מודל זמין מחשבון ה-API
        models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        model_name = "models/gemini-1.5-flash"
        try:
            models_res = await client.get(models_url)
            if models_res.status_code == 200:
                models_data = models_res.json()
                for m in models_data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        model_name = m.get("name")
                        break
        except Exception as e:
            print(f"Model lookup warning: {e}")

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

        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                print(f"Gemini API Error: {response.text}")
                raise HTTPException(status_code=500, detail=f"שגיאה מתשובת גוגל: {response.text}")
            
            res_data = response.json()
            text_response = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            trip_data = json.loads(text_response.strip())
            return trip_data

        except Exception as e:
            print(f"Execution Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"שגיאה בשרת: {str(e)}")
