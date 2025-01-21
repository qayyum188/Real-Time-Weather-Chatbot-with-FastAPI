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
from typing import Dict, Optional, List
from uuid import uuid4
from db_models import DatabaseManager
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app and database
app = FastAPI(title="Intelligent Weather Chatbot")
db = DatabaseManager()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Load environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEATHER_BASE_URL = "http://api.weatherapi.com/v1"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt
SYSTEM_PROMPT = """You are a friendly and helpful weather assistant. Your primary focus is on weather-related information and queries.
You can engage in basic greetings and pleasantries, but always try to steer the conversation towards weather-related topics.
Use the available functions to fetch real-time weather data when needed."""

# Define OpenAI function tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather information for a specific city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name to get weather data for"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

async def get_weather_data(city: str, session_id: str = None) -> Optional[Dict]:
    """Fetch weather data from the WeatherAPI"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WEATHER_BASE_URL}/current.json",
                params={"key": WEATHER_API_KEY, "q": city, "aqi": "no"}
            )
            
            if response.status_code == 200:
                weather_data = response.json()
                # Store weather data
                await db.store_weather_data(city, weather_data)
                return weather_data
            logger.error(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return None

async def process_message(message: str, session_id: str) -> str:
    """Process user message using OpenAI function calling"""
    try:
        # Initial chat completion with function calling
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            tools=tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # Check if function call is needed
        if assistant_message.tool_calls:
            # Process function calls
            function_responses = []
            for tool_call in assistant_message.tool_calls:
                if tool_call.function.name == "get_current_weather":
                    # Parse function arguments
                    function_args = json.loads(tool_call.function.arguments)
                    city = function_args.get("city")
                    
                    # Get weather data
                    weather_data = await get_weather_data(city)
                    
                    if weather_data:
                        function_responses.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(weather_data)
                        })
                    else:
                        function_responses.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": f"Could not fetch weather data for {city}"})
                        })

            # Second chat completion with function results
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
                assistant_message,
            ]

            # Add function results
            for resp in function_responses:
                messages.append({
                    "role": "tool",
                    "tool_call_id": resp["tool_call_id"],
                    "content": resp["output"]
                })

            final_response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
            )
            
            return final_response.choices[0].message.content
        
        return assistant_message.content

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return "I apologize, but I'm having trouble processing your request. Could you please try again?"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid4())
    logger.info(f"WebSocket connection established with session_id: {session_id}")
    
    try:
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received message: {message}")

            # Store user message
            await db.store_message(session_id, "user", message)

            # Process message
            response = await process_message(message, session_id)

            # Store assistant response
            await db.store_message(session_id, "assistant", response)
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