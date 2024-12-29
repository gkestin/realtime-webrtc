from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import random
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# Get API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class SessionResponse(BaseModel):
    session_id: str
    token: str

class WeatherResponse(BaseModel):
    temperature: float
    unit: str

@app.get("/session")
async def get_session():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.openai.com/v1/realtime/sessions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                "model": "gpt-4o-realtime-preview-2024-12-17",
                "voice": "echo"
            }
        )
        return response.json()

@app.get("/weather/{location}")
async def get_weather(location: str):
    # First get coordinates for the location
    try:
        async with httpx.AsyncClient() as client:
            # Get coordinates for location
            geocoding_response = await client.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
            )
            geocoding_data = geocoding_response.json()
            
            if not geocoding_data.get("results"):
                return {"error": f"Could not find coordinates for {location}"}
                
            lat = geocoding_data["results"][0]["latitude"]
            lon = geocoding_data["results"][0]["longitude"]
            
            # Get weather data
            weather_response = await client.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m"
            )
            weather_data = weather_response.json()
            
            temperature = weather_data["current"]["temperature_2m"]
            return WeatherResponse(temperature=temperature, unit="celsius")
            
    except Exception as e:
        return {"error": f"Could not get weather data: {str(e)}"}

# Serve index.html at the root path
@app.get("/")
async def read_root():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8888))
    uvicorn.run(app, host="0.0.0.0", port=port) 