import os
from fastapi import FastAPI
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

class TripRequest(BaseModel):
    language: str = "עברית"
    destination: str
    days: int
    travelers: str = "זוג"
    interests: str = "כללי"
    date: str = "בקרוב"
    budget: str = "בינוני"
    pace: str = "מאוזן"

@app.get("/")
def read_root():
    return {"status": "OK"}

@app.post("/api/generate-trip")
async def generate_trip(request: TripRequest):
    dest = request.destination
    days = request.days
    
    # יצירת מסלול מובנה נקי ויציב שרץ מיד בלי שגיאות חיצוניות
    itinerary = []
    for i in range(days):
        day_num = i + 1
        itinerary.append({
            "day_number": day_num,
            "title": f"יום {day_num}: סיור ב-{dest}",
            "activities": [
                {
                    "time": "09:00",
                    "place": f"מרכז העיר {dest}",
                    "description": f"התחלת יום הטיול והכרת האזור המרכזי."
                },
                {
                    "time": "13:00",
                    "place": "מסעדה מקומית",
                    "description": "ארוחת צהריים והתרעננות."
                },
                {
                    "time": "16:00",
                    "place": f"אתר תיירות מרכזי ב-{dest}",
                    "description": f"ביקור באטרקציות המרכזיות בהתאם לתחומי העניין ({request.interests})."
                }
            ]
        })

    return {"itinerary": itinerary}
