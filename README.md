# AI Auto Application

What if instead of generating application code, the AI *was* the application.  

Here is the AI when told to be a TODO application:

![TODO Application Sample Image 1](/images/sample1.png)
![TODO Application Sample Image 2](/images/sample2.png)


## How does it work?
Set the application type by setting the APPLICATION_TYPE environment variable.  The default is TODO

When the application starts up, we ask the AI to generate a plausible data model and sample data.  We then store this in redis.

Then we pass requests to the AI, allowing it to query redis and return a response template.  Tailwind and DaisyUI are included by default to give a consistent way to generate a UI.

## Does it work?

Kinda.  The UI can morph as you navigate because that isn't saved into the context and it sometimes fails to provide a renderable template.

## Setup

0. Take a look at app/config/settings.py and create a .env to setyo your application.  Make sure redis is running locally.  

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

## Future ideas

* manage application data entirely within the context window
* allow generating a DDL and using sqlite
* clone an existing application from its web traffic logs
* send it previous responses for UI consistency.
