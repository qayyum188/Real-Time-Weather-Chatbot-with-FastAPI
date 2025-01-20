from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent Weather Chatbot")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# API Keys
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API Keys
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEATHER_BASE_URL = "http://api.weatherapi.com/v1"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt to keep the chatbot focused on weather
SYSTEM_PROMPT = """You are a friendly and helpful weather assistant. Your primary focus is on weather-related information and queries.
You can engage in basic greetings and pleasantries, but always try to steer the conversation towards weather-related topics.
If a user asks about non-weather topics, politely explain that you're a weather specialist and can only help with weather-related queries.
When users ask about weather, use the provided real-time weather data in your responses."""

async def get_weather_data(city: str) -> Optional[Dict]:
    """Fetch weather data from the API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WEATHER_BASE_URL}/current.json",
                params={"key": WEATHER_API_KEY, "q": city, "aqi": "no"}
            )
            
            if response.status_code == 200:
                return response.json()
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return None

def extract_city_from_message(message: str) -> Optional[str]:
    """
    Use GPT to extract city names from user messages
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract only the city name from the given text. Return only the city name without any additional text. If no city is mentioned, return 'None'."},
                {"role": "user", "content": message}
            ],
            temperature=0,
            max_tokens=50
        )
        city = response.choices[0].message.content.strip()
        return None if city.lower() == 'none' else city
    except Exception as e:
        logger.error(f"Error extracting city: {e}")
        return None

async def generate_weather_response(message: str, weather_data: Optional[Dict] = None) -> str:
    """
    Generate a natural language response using GPTT
    """
    try:
        context = "User message: " + message + "\n"
        if weather_data:
            context += f"""
Current weather data:
City: {weather_data['location']['name']}
Country: {weather_data['location']['country']}
Temperature: {weather_data['current']['temp_c']}°C ({weather_data['current']['temp_f']}°F)
Condition: {weather_data['current']['condition']['text']}
Humidity: {weather_data['current']['humidity']}%
Wind: {weather_data['current']['wind_kph']} km/h
Last Updated: {weather_data['current']['last_updated']}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble generating a response. Could you please try again?"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received message: {message}")

            # First, check if it's a general greeting or non-weather query
            if not any(word in message.lower() for word in ['weather', 'temperature', 'rain', 'wind', 'humid', 'forecast', 'climate', 'cold', 'hot', 'celsius', 'fahrenheit']):
                response = await generate_weather_response(message)
                await websocket.send_text(response)
                continue

            # Extract city from message using GPT
            city = extract_city_from_message(message)
            if not city:
                response = "I'm not sure which city you're asking about. Could you please specify a city name?"
                await websocket.send_text(response)
                continue

            # Get weather data
            weather_data = await get_weather_data(city)
            if weather_data:
                response = await generate_weather_response(message, weather_data)
            else:
                response = f"I'm sorry, but I couldn't find weather data for {city}. Could you please check the city name and try again?"

            await websocket.send_text(response)
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Intelligent Weather Chatbot"}
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Weather API server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)