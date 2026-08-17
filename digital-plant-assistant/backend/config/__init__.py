import os

# Base directory is the backend folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-plant-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    # External APIs
    PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Meta WhatsApp Cloud API
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Weather
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
