# FitBuddy – AI Fitness Plan Generator 🏋️

A full-stack web application that uses **Google Gemini AI** to generate personalized 7-day workout plans and nutrition tips based on your fitness goals.

---

## Tech Stack

| Layer      | Technology                              |
|------------|----------------------------------------|
| Backend    | FastAPI + Uvicorn                       |
| AI         | Google Gemini 1.5 Pro & Gemini Flash    |
| Database   | SQLite + SQLAlchemy ORM                 |
| Frontend   | HTML5 + CSS3 + Jinja2 Templates         |

---

## Project Structure

```
FitBuddy_AI/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── routes.py                # All route handlers
│   ├── database.py              # DB engine, session, CRUD helpers
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic request schemas
│   ├── gemini_generator.py      # Gemini 1.5 Pro – workout plan
│   ├── gemini_flash_generator.py# Gemini Flash – nutrition tips
│   └── updated_plan.py          # Gemini 1.5 Pro – plan updates
├── templates/
│   ├── index.html               # Homepage / input form
│   ├── result.html              # Plan display + feedback form
│   └── all_users.html           # Admin dashboard
├── static/
│   └── css/
│       └── style.css            # Global stylesheet
├── run.py                       # Convenience launcher
├── requirements.txt
├── .env.example                 # API key template
└── README.md
```

---

## Setup Instructions (VS Code)

### 1. Prerequisites
- Python 3.10+ installed
- VS Code with the **Python** extension
- A free Google Gemini API key → https://aistudio.google.com/app/apikey

### 2. Clone / Open the Project
Open the `FitBuddy_AI` folder in VS Code:
```
File → Open Folder → C:\Users\kumar\OneDrive\Documents\FitBuddy_AI
```

### 3. Create & Activate a Virtual Environment
Open the VS Code **Terminal** (`Ctrl + `` ` ``) and run:
```bash
python -m venv fitbuddy-env
fitbuddy-env\Scripts\activate        # Windows
# source fitbuddy-env/bin/activate   # macOS / Linux
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Your API Key
Copy the example env file and add your key:
```bash
copy .env.example .env              # Windows
# cp .env.example .env              # macOS / Linux
```
Open `.env` and replace `your_gemini_api_key_here` with your actual key:
```
GOOGLE_API_KEY=AIzaSy...your_real_key_here
```

### 6. Run the Application
```bash
python run.py
# or equivalently:
uvicorn app.main:app --reload
```

### 7. Open in Browser
| URL                              | Purpose                        |
|----------------------------------|-------------------------------|
|            | Main application (homepage)    |
| http://127.0.0.1:8000/view-all-users | Admin dashboard           |
| http://127.0.0.1:8000/docs       | Interactive API documentation  |

---

## Usage

### Generate a Plan
1. Go to **http://127.0.0.1:8000**
2. Fill in your Name, User ID, Age, Weight, Goal, and Intensity
3. Click **⚡ Generate My Plan**
4. View your personalized 7-day workout plan + nutrition tip

### Re fine Your Plan with Feedback
1. On the result page, scroll to **Refine Your Plan**
2. Enter feedback (e.g. *"Add more rest days, include yoga"*)
3. Click **🔄 Update My Plan** — Gemini will revise the plan

### Admin Panel
- Visit **http://127.0.0.1:8000/view-all-users** to see all users and their plans

---

## API Endpoints

| Method | Endpoint           | Description                             |
|--------|--------------------|-----------------------------------------|
| GET    | `/`                | Homepage (input form)                   |
| POST   | `/generate-workout`| Generate 7-day plan + nutrition tip     |
| POST   | `/submit-feedback` | Update plan based on feedback           |
| GET    | `/view-all-users`  | Admin panel – all users & plans         |

---

## Notes
- The SQLite database (`app/fitbuddy.db`) is created automatically on first run.
- Generating a plan for an existing User ID will not duplicate the user; the plan is updated.
- Gemini API calls require a valid `GOOGLE_API_KEY` — without it, placeholder messages are shown.
http://127.0.0.1:8000