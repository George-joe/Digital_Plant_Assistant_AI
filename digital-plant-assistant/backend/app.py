from dotenv import load_dotenv
load_dotenv()

import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from database.extensions import db

def validate_env_vars():
    required_keys = {
        "PLANTNET_API_KEY": os.getenv("PLANTNET_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY"),
        "PLANT_DISEASE_MODEL_PATH": os.getenv("PLANT_DISEASE_MODEL_PATH")
    }
    missing = []
    for name, value in required_keys.items():  
        if not value:
            missing.append(name)
    
    if missing:
        print(f"[Startup] WARNING: Missing API keys ({', '.join(missing)}). Some features may be disabled.")
    else:
        print("[Startup] All critical API keys found [OK]")

def run_migrations(app):
    """Add any missing columns to existing tables without destroying data."""
    import sqlite3
    import os
    
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_uri.startswith('sqlite:///'):
        return
    
    if db_uri.startswith('sqlite:////'):
        db_path = db_uri[len('sqlite:////'):]
    else:
        db_filename = db_uri[len('sqlite:///'):]
        db_path = os.path.join(app.instance_path, db_filename)
    
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        migrations = [
            ("user", "profile_url",   "ALTER TABLE user ADD COLUMN profile_url VARCHAR(255)"),
            ("user", "phone_number",  "ALTER TABLE user ADD COLUMN phone_number VARCHAR(20)"),
            ("user", "telegram_chat_id", "ALTER TABLE user ADD COLUMN telegram_chat_id VARCHAR(50)"),
            ("user", "plants_owned",  "ALTER TABLE user ADD COLUMN plants_owned INTEGER DEFAULT 0"),
            ("user", "streak_days",   "ALTER TABLE user ADD COLUMN streak_days INTEGER DEFAULT 0"),
            ("user", "xp_points",     "ALTER TABLE user ADD COLUMN xp_points INTEGER DEFAULT 0"),
            ("user", "level",         "ALTER TABLE user ADD COLUMN level VARCHAR(50) DEFAULT '[Rookie]'"),
            ("plant", "health_score",  "ALTER TABLE plant ADD COLUMN health_score INTEGER DEFAULT 100"),
            ("plant", "disease_name",  "ALTER TABLE plant ADD COLUMN disease_name VARCHAR(200)"),
            ("plant", "nickname",      "ALTER TABLE plant ADD COLUMN nickname VARCHAR(100)"),
            ("health_report", "ai_follow_up_questions", "ALTER TABLE health_report ADD COLUMN ai_follow_up_questions TEXT"),
            ("health_report", "user_answers",           "ALTER TABLE health_report ADD COLUMN user_answers TEXT"),
            ("health_report", "final_score",             "ALTER TABLE health_report ADD COLUMN final_score INTEGER"),
            ("health_report", "image_path",              "ALTER TABLE health_report ADD COLUMN image_path VARCHAR(200)"),
            ("plant", "location",      "ALTER TABLE plant ADD COLUMN location VARCHAR(50) DEFAULT 'Indoor'"),
            ("plant", "pot_size",      "ALTER TABLE plant ADD COLUMN pot_size VARCHAR(20)"),
            ("plant", "tracking_mode", "ALTER TABLE plant ADD COLUMN tracking_mode VARCHAR(20) DEFAULT 'weekly'"),
            ("weekly_photo", "photo_date",      "ALTER TABLE weekly_photo ADD COLUMN photo_date DATETIME"),
            ("weekly_photo", "photo_date_user",  "ALTER TABLE weekly_photo ADD COLUMN photo_date_user DATETIME"),
            ("weekly_photo", "ai_analysis",      "ALTER TABLE weekly_photo ADD COLUMN ai_analysis TEXT"),
            ("weekly_photo", "growth_insights",  "ALTER TABLE weekly_photo ADD COLUMN growth_insights TEXT"),
            ("weekly_photo", "disease_detected", "ALTER TABLE weekly_photo ADD COLUMN disease_detected VARCHAR(200)"),
            ("weekly_photo", "tracking_mode",    "ALTER TABLE weekly_photo ADD COLUMN tracking_mode VARCHAR(20) DEFAULT 'weekly'"),
            ("weekly_photo", "health_score",     "ALTER TABLE weekly_photo ADD COLUMN health_score INTEGER"),
            ("weekly_photo", "is_diagnosis",     "ALTER TABLE weekly_photo ADD COLUMN is_diagnosis BOOLEAN DEFAULT 0"),
            ("plant", "last_disease",   "ALTER TABLE plant ADD COLUMN last_disease VARCHAR(200)"),
            ("plant", "last_scanned",   "ALTER TABLE plant ADD COLUMN last_scanned DATETIME"),
            ("reminder", "time", "ALTER TABLE reminder ADD COLUMN time VARCHAR(5)"),
            ("reminder", "repeat_schedule", "ALTER TABLE reminder ADD COLUMN repeat_schedule VARCHAR(50)"),
            ("reminder", "notification_type", "ALTER TABLE reminder ADD COLUMN notification_type VARCHAR(20)"),
            ("reminder", "telegram_chat_id", "ALTER TABLE reminder ADD COLUMN telegram_chat_id VARCHAR(50)"),
            ("reminder", "last_triggered_at", "ALTER TABLE reminder ADD COLUMN last_triggered_at DATETIME"),
            ("reminder", "is_active",         "ALTER TABLE reminder ADD COLUMN is_active BOOLEAN DEFAULT 1"),
            ("reminder", "user_id",           "ALTER TABLE reminder ADD COLUMN user_id INTEGER"),
            ("reminder", "message",           "ALTER TABLE reminder ADD COLUMN message VARCHAR(255)"),
            ("reminder", "reminder_time",     "ALTER TABLE reminder ADD COLUMN reminder_time TIME"),
            ("reminder", "last_sent_at",      "ALTER TABLE reminder ADD COLUMN last_sent_at DATETIME"),
            ("weekly_photo", "confidence",    "ALTER TABLE weekly_photo ADD COLUMN confidence INTEGER"),
            ("plant", "last_reminder_sent_at", "ALTER TABLE plant ADD COLUMN last_reminder_sent_at DATETIME"),
            ("care_task", "last_reminder_sent_at", "ALTER TABLE care_task ADD COLUMN last_reminder_sent_at DATETIME"),
            ("care_task", "xp_reward", "ALTER TABLE care_task ADD COLUMN xp_reward INTEGER DEFAULT 0"),
            ("care_task", "reset_date", "ALTER TABLE care_task ADD COLUMN reset_date DATETIME"),
            ("plant_schedule", "watering_interval", "ALTER TABLE plant_schedule ADD COLUMN watering_interval INTEGER DEFAULT 7")
        ]

        table_cols = {}
        for tbl, col_name, sql in migrations:
            if tbl not in table_cols:
                cursor.execute(f"PRAGMA table_info({tbl})")
                table_cols[tbl] = {row[1] for row in cursor.fetchall()}
            if col_name not in table_cols[tbl]:
                try:
                    cursor.execute(sql)
                    print(f"[DB Migration] Added column: {tbl}.{col_name}")
                except Exception as col_err:
                    print(f"[DB Migration] Skipped {tbl}.{col_name}: {col_err}")

        # Data Migration for consolidated disease field
        try:
            cursor.execute("UPDATE plant SET last_disease = disease_name WHERE (last_disease IS NULL OR last_disease = '') AND (disease_name IS NOT NULL AND disease_name != '')")
            print("[DB Migration] Consolidated disease_name into last_disease [OK]")
        except Exception:
            pass

        conn.commit()
        conn.close()
        print("[DB Migration] All migrations finalized.")

    except Exception as e:
        print(f"[DB Migration] Warning: {e}")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Force UPLOAD_FOLDER to static/uploads
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app.config["UPLOAD_FOLDER"] = os.path.abspath(os.path.join(base_dir, "static", "uploads"))
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.logger.info(f"UPLOAD SYSTEM INITIALIZED: {app.config['UPLOAD_FOLDER']}")

    # Initialize Extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)

    # Register Blueprints
    from routes.ui import ui_bp
    from routes.auth import auth_bp
    from routes.plant_routes import plants_bp
    from routes.chat_routes import ai_bp
    from routes.community import community_bp
    from routes.reminder_routes import reminders_bp
    from routes.weather_routes import weather_bp
    from routes.disease_detection_routes import disease_bp
    from routes.analytics_routes import analytics_bp

    app.register_blueprint(ui_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(plants_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(disease_bp)
    app.register_blueprint(analytics_bp)

    # Serve uploads explicitly if necessary (though they are in static/)
    @app.route("/uploads/<path:filename>")
    def serve_image(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ROOT CONNECTION FIX: Global JSON Error Handlers
    # Prevents HTML error pages from crashing frontend res.json() parsing routines
    from flask import jsonify
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"success": False, "error": "Unauthorized endpoint access"}), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint or resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    validate_env_vars()
    app = create_app()
    with app.app_context():
        # First run migrations on existing DB (adds missing columns)
        run_migrations(app)
        # Then create any completely new tables
        db.create_all()
        print("[GrowZen] Database ready [OK]")
        
        # Load PlantVillage model at startup (Point 1)
        from services.diseaseDetection.plantVillageModel import load_plant_village_model
        load_plant_village_model()

        # Start background reminder scheduler (Bug 8 Fix: pass app so it reuses context)
        from scheduler.reminder_scheduler import start_scheduler
        start_scheduler(app)
    app.run(debug=True)
