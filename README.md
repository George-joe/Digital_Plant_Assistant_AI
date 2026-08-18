# 🌱 GrowZen — AI-Powered Plant Care Assistant

> **GrowZen** is a full-stack web application that helps plant owners monitor, diagnose, and care for their plants using artificial intelligence, personalized reminders, and growth analytics.

[![Python](https://img.shields.io/badge/Python-3.11.9-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green?logo=flask)](https://flask.palletsprojects.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.21.0-orange?logo=tensorflow)](https://www.tensorflow.org/)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-purple)](https://render.com/)

---

## Overview

GrowZen combines AI plant disease detection, a Groq-powered chatbot, smart care scheduling, Telegram-based reminders, and a gamified progression system — all in a single web application. Users can track multiple plants, receive automated alerts, and get AI-generated care advice.

---

## Problem

Keeping plants healthy is harder than it looks. Most people:
- Forget watering schedules and overwater or underwater their plants
- Cannot identify diseases or pests until visible damage has occurred
- Have no way to track their plants' health progress over time
- Do not know the right care routines for different species

---

## Solution

GrowZen provides:
- **AI disease detection** from a photo of any leaf (MobileNetV2 + PlantVillage dataset, 35 plant classes)
- **Automated care schedules** tailored to each plant's species and stage
- **Telegram reminders** when it is time to water or when a plant has not been watered for 7+ hours
- **Weekly photo timeline** to track a plant's growth visually over time
- **AI chatbot** (powered by Groq's llama-3.3-70b) for any plant care question
- **Analytics dashboard** showing garden health trends, disease distribution, and task completion
- **Gamification** with XP points, levels, streaks, and a community leaderboard

---

## Features

- 🔐 **User authentication** — Sign up, log in, user profile with avatar
- 🌿 **Plant management** — Add, edit, delete plants; track species, pot size, location, growth stage
- 📋 **Care schedules** — Auto-generated watering, fertilizing, and pruning tasks per plant
- ✅ **Care tasks** — Complete tasks to earn XP; tasks reset automatically on schedule
- 🔔 **Smart reminders** — Custom Telegram reminders at specific times
- 📱 **Telegram notifications** — Automated 7-hour unwatered alerts sent to your Telegram chat
- 🩺 **Disease detection** — Upload a leaf photo; AI detects disease with confidence score and treatment advice
- 🔍 **Plant identification** — Identify unknown plants via PlantNet API from any photo
- 💬 **AI Plant Doctor chatbot** — Ask any plant care question via Groq LLM
- 📸 **Photo timeline** — Upload weekly growth photos; AI analyses and compares them over time
- 📊 **Analytics dashboard** — Health score trends, disease distribution charts, task completion rates
- 🏆 **Gamification** — XP points, levels (Rookie → Master), streaks, community leaderboard
- 🌤️ **Weather widget** — Real-time local weather via OpenWeather API
- 🛒 **Marketplace** — Browse plant care products (community feature)
- 👥 **Community feed** — Share plant updates with the GrowZen community
- 🧭 **Onboarding flow** — Guided setup for new users

---

## Technology Stack

### Frontend
- HTML5, CSS3, Vanilla JavaScript
- Chart.js (analytics charts)
- Google Fonts — Inter

### Backend
- Python 3.11.9
- Flask 3.1.3 (blueprint architecture)
- Flask-SQLAlchemy 3.1.1
- Flask-CORS

### Database
- SQLite (local development)

### AI & Machine Learning
- TensorFlow 2.21.0 / Keras
- MobileNetV2 (transfer learning) — plant disease detection
- PlantVillage dataset (35 disease classes across common plant species)
- Pillow + OpenCV — image preprocessing

### APIs
- [PlantNet API](https://plantnet.org/) — plant species identification
- [Groq API](https://groq.com/) — LLM chatbot (llama-3.3-70b-versatile)
- [OpenWeather API](https://openweathermap.org/) — weather data
- [Telegram Bot API](https://core.telegram.org/bots/api) — push notifications

### Automation
- APScheduler (BackgroundScheduler) — 1-minute interval reminder checks

### Deployment
- Gunicorn (WSGI server)
- Render (free web service)

---

## Project Structure

```
digital-plant-assistant-ai/
├── digital-plant-assistant/
│   └── backend/
│       ├── app.py                  # Flask application factory + DB migrations
│       ├── wsgi.py                 # Gunicorn entry point
│       ├── config/                 # Flask configuration class
│       ├── models/                 # SQLAlchemy models (User, Plant, Reminder, etc.)
│       ├── routes/                 # Flask blueprints
│       │   ├── auth.py             # Login / signup / logout
│       │   ├── plant_routes.py     # Plant CRUD, diagnosis, watering, tasks
│       │   ├── analytics_routes.py # Garden health analytics
│       │   ├── chat_routes.py      # AI chatbot (Groq)
│       │   ├── community.py        # Community feed & leaderboard
│       │   ├── reminder_routes.py  # Telegram reminders
│       │   ├── weather_routes.py   # Weather widget
│       │   └── ui.py               # HTML page routes
│       ├── services/
│       │   ├── diseaseDetection/   # MobileNetV2 disease detection pipeline
│       │   ├── plantnet_service.py # PlantNet species identification
│       │   ├── chatbot/            # Groq LLM integration
│       │   └── weather_service.py  # OpenWeather integration
│       ├── scheduler/
│       │   └── reminder_scheduler.py  # APScheduler background jobs
│       ├── utils/
│       │   ├── telegram_utils.py   # Telegram Bot API helper
│       │   └── disease_mapping.py  # Disease name/treatment mapping
│       ├── templates/              # Jinja2 HTML templates (11 pages)
│       ├── static/
│       │   ├── css/                # Stylesheets (per-page + design system)
│       │   └── js/                 # JavaScript (per-page logic)
│       ├── requirements.txt
│       └── .env.example
├── ai/
│   └── plant-disease-model/
│       ├── model/
│       │   ├── plant_disease_model.keras   # Trained MobileNetV2 model (28 MB)
│       │   └── class_indices.json          # 35-class label mapping
│       └── scripts/                        # Training scripts
├── render.yaml                 # Render deployment config
├── .gitignore
├── .python-version
└── README.md
```

---

## Requirements

- **Python** 3.11.9
- **External API keys** (see Environment Variables section)
- The AI model file is included in the repository (`ai/plant-disease-model/model/`)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/George-joe/Digital_Plant_Assistant_AI.git
cd Digital_Plant_Assistant_AI
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
cd digital-plant-assistant/backend
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy the example file
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux

# Edit .env and fill in your API keys
```

---

## Environment Variables

Create a `.env` file inside `digital-plant-assistant/backend/` with the following variables:

| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `SECRET_KEY` | Flask session secret key | Generate any strong random string |
| `DATABASE_URL` | Database connection URL | Leave as `sqlite:///database.db` for local dev |
| `PLANTNET_API_KEY` | Plant species identification | [my.plantnet.org](https://my.plantnet.org/) |
| `GROQ_API_KEY` | AI chatbot (Groq LLM) | [console.groq.com](https://console.groq.com/) |
| `OPENWEATHER_API_KEY` | Weather widget | [openweathermap.org/api](https://openweathermap.org/api) |
| `TELEGRAM_BOT_TOKEN` | Telegram reminders | Create via [@BotFather](https://t.me/BotFather) on Telegram |
| `PLANT_DISEASE_MODEL_PATH` | Path to the AI model | `ai/plant-disease-model/model/plant_disease_model.keras` |

---

## Running Locally

```bash
# From the backend directory:
cd digital-plant-assistant/backend

python app.py
```

The application will be available at: **https://growzen.onrender.com/**

Alternatively, from the project root, run `start.bat` (Windows).

---

## Usage

1. **Create an account** — Go to `/signup`, enter your name, email, and password
2. **Log in** — Go to `/login`
3. **Add your first plant** — From the Dashboard, click "Add Plant" and upload a photo or identify by name
4. **Set up a care schedule** — GrowZen auto-generates watering and fertilizing tasks per plant
5. **Set a Telegram reminder** — Link your Telegram chat ID in Settings and create a reminder
6. **Diagnose a disease** — Open any plant profile → Diagnosis tab → upload a leaf photo
7. **Chat with the AI** — Use the floating chatbot on any page to ask plant care questions
8. **View Analytics** — Check the Analytics page for garden-wide health trends and statistics
9. **Earn XP** — Complete care tasks to level up from Rookie → Master
10. **Check the Community** — See the leaderboard and share plant updates

---

## AI / Machine Learning

### Model
GrowZen uses a **MobileNetV2** convolutional neural network fine-tuned on the **PlantVillage** dataset.

### Dataset
- **PlantVillage** — a publicly available dataset of 54,000+ leaf images across 38 disease conditions
- GrowZen's model covers **35 disease classes** across common plant species including Tomato, Potato, Pepper, Apple, Corn, Grape, Peach, Cherry, and more

### How it works
1. User uploads a leaf photo
2. Image is resized to 224×224 and preprocessed with MobileNetV2 native preprocessing
3. Model predicts the most likely disease class
4. A confidence score, health score, and treatment recommendation are returned
5. Results are saved to the plant's diagnosis history

### Model file
- `ai/plant-disease-model/model/plant_disease_model.keras` — 28 MB (committed to repository)
- `ai/plant-disease-model/model/class_indices.json` — class label mapping

---

## Telegram Integration

GrowZen uses the **Telegram Bot API** to send plant care reminders.

### How it works
1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram and copy the token to `.env`
2. Start a conversation with your bot and find your **Chat ID** (use [@userinfobot](https://t.me/userinfobot))
3. In GrowZen Settings, enter your Telegram Chat ID
4. Create a reminder with a specific time — GrowZen will message you on Telegram at that time
5. GrowZen also automatically sends an alert if a plant has not been watered for 7+ hours

### Required environment variable
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```
The real token must never be committed to GitHub.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Log in |
| POST | `/api/auth/signup` | Create account |
| GET | `/api/plants` | List all plants |
| POST | `/api/plants` | Add a plant |
| GET | `/api/plants/<id>` | Get plant details |
| POST | `/api/plants/<id>/diagnose` | AI disease detection |
| POST | `/api/plants/<id>/water` | Log a watering |
| GET | `/api/analytics/summary` | Garden health analytics |
| GET | `/api/community/feed` | Community feed |
| GET | `/api/community/leaderboard` | XP leaderboard |
| POST | `/api/chat` | AI chatbot message |
| GET | `/api/reminders` | List reminders |
| POST | `/api/reminders` | Create a reminder |

---

## Deployment

GrowZen is deployed on **Render** using the free web service plan.

### Deploy to Render

1. Fork or clone this repository to your GitHub account
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repository
4. Set the following:
   - **Root Directory**: `digital-plant-assistant/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --timeout 120 --workers 1`
   - **Python Version**: `3.11.9`
5. Add environment variables in the Render dashboard (see Environment Variables section)
6. Click **Deploy**

> The `render.yaml` file in the project root automates most of this configuration.

---

## Known Limitations

### Free Render Tier
- **Ephemeral filesystem** — The SQLite database and uploaded plant photos are stored in Render's temporary filesystem. They are **erased on every restart or redeploy**. This means all user data and photos are lost when the service restarts.
- **App sleep** — Render's free tier suspends the application after 15 minutes of inactivity. The next request will take 20–40 seconds to respond (cold start), and the AI model takes an additional 5–15 seconds to load.
- **Telegram reminders** — Scheduled reminders may be missed if the app is sleeping during the scheduled time.
- **Memory** — The free tier provides 512 MB RAM. TensorFlow with the MobileNetV2 model uses approximately 400–450 MB.

### For a production-grade deployment:
- Replace SQLite with **PostgreSQL** (Render provides a free PostgreSQL add-on)
- Replace local file uploads with **cloud object storage** (e.g., AWS S3, Cloudinary)
- Use a paid Render plan to prevent sleep

---

## Future Improvements

- [ ] PostgreSQL database for persistent storage on Render
- [ ] Cloud storage (S3 / Cloudinary) for uploaded plant photos
- [ ] Push notifications via Firebase (web push or mobile)
- [ ] Mobile app (React Native / Flutter)
- [ ] Integration with smart plant sensors (soil moisture, light)
- [ ] Multi-language support
- [ ] Expanded AI model with more plant species and diseases

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with 🌱 by George Joe*
