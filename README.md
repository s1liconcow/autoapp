# AI Auto Application

What if instead of generating application code, the AI *was* the application.  

Here is the AI when told to be a TODO application:

![TODO Application Sample Image 1](/images/sample1.png)
![TODO Application Sample Image 2](/images/sample2.png)

## Setup

0. Take a look at app/config/settings.py and configure your application.  Make sure redis is running locally.  

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

1. Start the web application:
```bash
source .env
python -m app.main
```

3. Open your browser and navigate to http://localhost:8000 (or the configured port)

## Usage

- The left panel allows you to update the system prompt or other configuration parameters that will be used for subsequent interactions.

## Note

- The application uses a default model. To use a different model, modify the configuration in the application. 