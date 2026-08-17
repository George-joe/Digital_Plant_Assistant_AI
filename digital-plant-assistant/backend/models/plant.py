from database.extensions import db
from datetime import datetime

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    scientific = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default="Healthy")
    image_url = db.Column(db.String(200), nullable=True)
    confidence = db.Column(db.Integer, nullable=True)
    health_score = db.Column(db.Integer, nullable=True)
    last_disease = db.Column(db.String(200), nullable=True)   # Consolidated: last confirmed disease or healthy
    last_scanned = db.Column(db.DateTime, nullable=True)
    nickname = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(50), default="Indoor")
    pot_size = db.Column(db.String(20), nullable=True)
    tracking_mode = db.Column(db.String(20), default="weekly")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    growth_stage = db.Column(db.String(50), default="Seedling")
    last_reminder_sent_at = db.Column(db.DateTime, nullable=True)

    schedule = db.relationship('PlantSchedule', backref='plant', uselist=False, lazy=True, cascade="all, delete-orphan")
    health_reports = db.relationship('HealthReport', backref='plant', lazy=True, cascade="all, delete-orphan")
    reminders = db.relationship('Reminder', backref='plant', lazy=True, cascade="all, delete-orphan")
    photos = db.relationship('WeeklyPhoto', backref='plant', lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship('CareTask', backref='plant', lazy=True, cascade="all, delete-orphan")
    water_logs = db.relationship('WaterLog', backref='plant', lazy=True, cascade="all, delete-orphan")


class HealthReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    diagnosis = db.Column(db.String(100), nullable=False)
    probability = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    treatment = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(200), nullable=True)
    ai_follow_up_questions = db.Column(db.Text, nullable=True)
    user_answers = db.Column(db.Text, nullable=True)
    final_score = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CareTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    task_type = db.Column(db.String(50), default="Care")
    label = db.Column(db.String(255), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_reminder_sent_at = db.Column(db.DateTime, nullable=True)
    xp_reward = db.Column(db.Integer, default=0)
    reset_date = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "plant_id": self.plant_id,
            "title": self.label,
            "completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "task_type": self.task_type,
            "label": self.label,
            "is_completed": self.is_completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "xp_reward": self.xp_reward,
            "reset_date": self.reset_date.isoformat() if self.reset_date else None
        }

class PlantSchedule(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    water_frequency_days = db.Column(db.Integer, default=3)
    watering_interval = db.Column(db.Integer, default=7)
    fertilizer_frequency_days = db.Column(db.Integer, default=14)
    sunlight_pref = db.Column(db.String(50), default="Indirect Sunlight")
    humidity_pref = db.Column(db.String(50), default="Moderate")
    last_watered = db.Column(db.DateTime, default=datetime.utcnow)
    next_watering_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_fertilized = db.Column(db.DateTime, default=datetime.utcnow)
    next_fertilizer_date = db.Column(db.DateTime, default=datetime.utcnow)


class Reminder(db.Model):
    """Plant care reminder — supports in-app and Telegram notification types."""
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(5), nullable=True)               # HH:MM format
    reminder_time = db.Column(db.Time, nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    repeat_schedule = db.Column(db.String(50), nullable=True)
    notification_type = db.Column(db.String(20), nullable=True) # "in_app" or "telegram"
    telegram_chat_id = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.String(255), nullable=True)


class WeeklyPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    week_number = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    photo_date_user = db.Column(db.DateTime, nullable=True)
    ai_analysis = db.Column(db.Text, nullable=True)
    growth_insights = db.Column(db.Text, nullable=True)
    disease_detected = db.Column(db.String(200), nullable=True)
    tracking_mode = db.Column(db.String(20), default='weekly')
    health_score = db.Column(db.Integer, nullable=True)
    confidence = db.Column(db.Integer, nullable=True)
    is_diagnosis = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WaterLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    watered_at = db.Column(db.DateTime, default=datetime.utcnow)
