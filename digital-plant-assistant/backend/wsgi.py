"""
wsgi.py — GrowZen WSGI entry point for production deployment.

Used by gunicorn:
    gunicorn wsgi:app

This wraps the Flask application factory so gunicorn can import it directly.
"""
from dotenv import load_dotenv
load_dotenv()

from app import create_app
import os

app = create_app()

# Initialize database and load AI model on startup
with app.app_context():
    from app import run_migrations
    from database.extensions import db
    
    run_migrations(app)
    db.create_all()
    
    # Load plant disease model into memory
    from services.diseaseDetection.plantVillageModel import load_plant_village_model
    load_plant_village_model()
    
    # Start background reminder scheduler
    from scheduler.reminder_scheduler import start_scheduler
    start_scheduler(app)

if __name__ == "__main__":
    app.run()
