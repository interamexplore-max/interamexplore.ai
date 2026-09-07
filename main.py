import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import json

app = FastAPI(title="Interam AI Trip Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# שליפת מפתח ה-API בצורה מאובטחת מהסביבה של השרת
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

class TripRequest(BaseModel):
    destination: str
    days: int
    travelers: str
    interests: str

@app.post("/api/generate-trip")
async def generate_trip(request: TripRequest):
    prompt = f"""
    אתה מתכנן טיולים מקצועי ומומחה בסוכנות נסיעות. צור מסלול טיול מפורט ליעד '{request.destination}' במשך {request.days} ימים.
    הרכב הנוסעים: {request.travelers}.
    תחומי עניין עיקריים: {request.interests}.
    
    הקפד על:
    1. חלוקה גאוגרפית הגיונית לכל יום (ללא נסיעות ארוכות מדי באותו יום).
    2. שילוב אטרקציות ופעילויות שמתאימות במדויק להרכב הנוסעים.
    3. תיאור קצר ומושך לכל פעילות כולל שעה מומלצת (למשל: 09:00, 13:00, 16:00).
    
    עליך להחזיר את התשובה אך ורק במבנה JSON חוקי המכיל מערך בשם 'itinerary', שכל איבר בו מייצג יום וכולל:
    - day_number (מספר היום, מספר שלם)
    - title (כותרת קצרה ליום, למשל: "הגעה וסיור היכרות באגמים")
    - activities (מערך של פעילויות, שלכל אחת יש time, place, ו-description).
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        itinerary_data = json.loads(response.text)
        return itinerary_data

    except Exception as e:
        print(f"שגיאה בייצור המסלול: {e}")
        raise HTTPException(status_code=500, detail="אירעה שגיאה בייצור המסלול באמצעות ה-AI.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)