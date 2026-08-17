"""
Reminder routes — create, list, delete, and toggle plant care reminders.
Also contains weather endpoint endpoints.
"""
from flask import Blueprint, request, jsonify, session
from database.extensions import db
from models.plant import Plant, Reminder
from models.user import User
from datetime import datetime
import os
from utils.helpers import get_authenticated_user

reminders_bp = Blueprint('reminders', __name__)


# ─── REMINDERS ─────────────────────────────────────────────────────────────

@reminders_bp.route("/api/reminders", methods=["POST"])
def create_reminder_v2():
    """
    Fixed endpoint for saving reminders from the frontend.
    """
    data = request.get_json()
    print("Reminder data received:", data)
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Bug 7 Fix: Use shared helper (Bearer token + session)
    print("Auth header:", request.headers.get("Authorization"))
    user = get_authenticated_user()
    print("User:", user)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user.id
        
    # PART 2: FIX FORM DATA STRUCTURE (Mapping)
    plant_id = data.get("plant_id")
    start_date_str = data.get("start_date")
    # Time fallback: frontend uses "time" or "reminder_time"
    time_str = data.get("reminder_time") or data.get("time") 
    notification_type = data.get("notification_type")
    repeat_schedule = data.get("repeat_type") or data.get("repeat_schedule")
    telegram_chat_id = data.get("chat_id") or data.get("telegram_chat_id")
    
    # 1. Validation
    if not all([plant_id, start_date_str, time_str, notification_type]):
        errors = [f for f in ["plant_id", "start_date", "time", "notification_type"] if not data.get(f)]
        print(f"Validation Error: Missing fields {errors}") # PART 7: LOGGING
        return jsonify({"success": False, "error": f"Missing required fields: {', '.join(errors)}"}), 400
        
    if notification_type == "telegram" and not telegram_chat_id:
        print("Validation Error: Telegram Chat ID missing") # PART 7: LOGGING
        return jsonify({"success": False, "error": "Telegram Chat ID is required for Telegram notifications"}), 400
        
    # PART 5: PREVENT DUPLICATE REMINDERS
    existing = Reminder.query.filter_by(
        plant_id=plant_id,
        time=time_str,
        repeat_schedule=repeat_schedule
    ).first()
    if existing:
        print(f"Validation Error: Reminder already exists for plant {plant_id} at {time_str}")
        return jsonify({"success": False, "error": "Reminder already exists for this time"}), 400

    try:
        # Convert start_date from YYYY-MM-DD to datetime object
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        
        # Parse time string into python time object
        parsed_time = datetime.strptime(time_str, "%H:%M").time()
        
        print("Incoming reminder data:", data)
        print("Parsed time:", parsed_time)
        
        # 2. Database Insert
        new_reminder = Reminder(
            user_id=user_id,
            plant_id=plant_id,
            start_date=start_date,
            time=time_str,                   # Kept for backward compatibility
            reminder_time=parsed_time,       # New field
            repeat_schedule=repeat_schedule,
            notification_type=notification_type,
            telegram_chat_id=telegram_chat_id,
            is_active=True
        )
        
        db.session.add(new_reminder)
        db.session.commit()
        
        print(f"Reminder saved: ID {new_reminder.id} for plant {plant_id}") # PART 7: LOGGING
        return jsonify({"success": True, "message": "Reminder saved successfully", "reminder_id": new_reminder.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error saving reminder: {e}")
        return jsonify({"error": str(e)}), 500

@reminders_bp.route("/api/plant/<int:plant_id>/reminders", methods=["GET"])
def get_reminders(plant_id):
    reminders = Reminder.query.filter_by(plant_id=plant_id, is_active=True).all()
    return jsonify([_reminder_dict(r) for r in reminders])


@reminders_bp.route("/api/reminder/<int:reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    # Bug 7 Fix: Use shared helper
    user = get_authenticated_user()
    r = Reminder.query.get(reminder_id)
    if not r:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify({"success": True})


@reminders_bp.route("/api/user/telegram", methods=["POST"])
def update_telegram_chat_id():
    # Bug 7 Fix: Use shared helper
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    body = request.get_json() or {}
    chat_id = body.get("telegram_chat_id") or body.get("chat_id")
    
    user.telegram_chat_id = chat_id
    db.session.commit()
    return jsonify({"success": True, "telegram_chat_id": user.telegram_chat_id})


@reminders_bp.route("/api/reminders/trigger-test", methods=["POST"])
def trigger_reminder_test():
    """
    PART 9: Manual test support.
    Triggers a reminder check immediately for the authenticated user.
    """
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not user.telegram_chat_id:
        return jsonify({"error": "No Telegram Chat ID configured for this user"}), 400
        
    from scheduler.reminder_scheduler import triggerReminderNow
    from flask import current_app
    
    try:
        triggerReminderNow(current_app._get_current_object())
        return jsonify({"success": True, "message": "Manual trigger executed. Check Telegram."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _reminder_dict(r):
    return {
        "id": r.id,
        "plant_id": r.plant_id,
        "reminder_type": r.notification_type,
        "reminder_time": r.time,
        "repeat": r.repeat_schedule,
        "is_active": r.is_active,
        "start_date": r.start_date.isoformat() if r.start_date else None,
        "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None,
    }
