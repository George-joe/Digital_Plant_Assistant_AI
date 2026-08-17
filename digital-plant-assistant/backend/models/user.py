from database.extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(50), default="🌱 Rookie")
    xp_points = db.Column(db.Integer, default=0)
    plants_owned = db.Column(db.Integer, default=0)
    streak_days = db.Column(db.Integer, default=0)
    phone_number = db.Column(db.String(20), nullable=True)
    telegram_chat_id = db.Column(db.String(50), nullable=True)
    profile_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # relationship to plants
    plants = db.relationship('Plant', backref='owner', lazy=True, cascade="all, delete-orphan")
