# Realtime Weather Chatbot

This project implements an AI-powered chatbot integrated with a FastAPI backend, designed to provide weather-related information in real time. The chatbot interacts with users, answering questions about weather conditions for cities worldwide.

## Features

- **AI-Powered Chatbot**: Utilizes WebSocket communication for real-time interactions.
- **Weather Queries**: Users can ask for temperature, humidity, wind speed, and more.
- **FastAPI Backend**: Lightweight and efficient backend with robust API endpoints.
- **Interactive Interface**: User-friendly web interface built using HTML, CSS, and JavaScript.
- **Function Handling**: Used function handling by implementing a dynamic `function_map` dictionary that allows flexible, runtime routing of method calls with type-safe, modular execution.

## Installation

Follow these steps to set up the project locally:

### Prerequisites
- Python 3.8 or later
- Virtual environment (optional but recommended)
- Git (for version control)

### Steps

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd weather-app-clean
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Application**:
   Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   The application will be available at `http://127.0.0.1:8000`.

## Usage

### Accessing the Chatbot
- Open a web browser and navigate to `http://127.0.0.1:8000`.
- Interact with the chatbot by typing queries in the input field.
- Example questions:
  - "What's the weather like in Paris?"
  - "Is it raining in Tokyo?"
  - "What’s the wind speed in New York?"

### Capabilities
- **Weather Information**: Current weather conditions for any city worldwide.
- **Friendly Conversations**: Engage in natural dialogue about weather-related topics.
- **Quick Suggestions**: Predefined suggestions for faster interaction.

## File Structure

```
weather-app-clean/
|-- main.py                 # FastAPI application entry point
|-- templates/
|   |-- base.html           # Base HTML template
|   |-- index.html          # Chatbot interface
|-- static/
|   |-- styles.css          # CSS for styling
|   |-- scripts.js          # JavaScript for frontend logic
|-- venv/                   # Virtual environment (ignored in .gitignore)
|-- requirements.txt        # Python dependencies
|-- README.md               # Project documentation
```

## Technologies Used

- **Frontend**:
  - HTML, CSS, JavaScript (Bootstrap for styling)
- **Backend**:
  - Python (FastAPI framework)
- **WebSocket**:
  - Real-time communication with the chatbot
- **API Integration**:
  - OpenWeatherMap API for weather data

## Contributing

Contributions are welcome! If you'd like to contribute:
- Fork the repository
- Create a feature branch
- Commit your changes
- Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Author

Created by Abdul Qayyum

