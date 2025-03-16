# Ollama Web Interface

A simple web interface for interacting with a local Ollama instance. This application allows you to:
- Dynamically update the system prompt
- Chat with your local Ollama models
- See real-time responses in a modern interface

## Prerequisites

- Python 3.7+
- A local Ollama instance running (default: http://localhost:11434)
- The llama2 model installed in Ollama (or modify the code to use a different model)

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Make sure your Ollama instance is running and accessible at http://localhost:11434

2. Start the web application:
```bash
python app.py
```

3. Open your browser and navigate to http://localhost:8000

## Usage

- The left panel allows you to update the system prompt that will be used for all subsequent interactions
- The right panel is your chat interface where you can send messages and see responses
- Press Enter to send a message (Shift+Enter for new line)
- The interface will show status messages for both prompt updates and chat interactions

## Note

The application uses the llama2 model by default. To use a different model, modify the `model` parameter in the `/get_response` route in `app.py`. 