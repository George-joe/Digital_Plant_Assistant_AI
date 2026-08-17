from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging
from database.extensions import db
from models.plant import Plant, Reminder, CareTask
from models.user import User
from utils.telegram_utils import send_telegram

def check_reminders(app):
    try:
        with app.app_context():
            now = datetime.now().strftime("%H:%M")
            today_date = datetime.now().date()
            current_dt = datetime.now()
            
            print("Scheduler running")
            print("Current time:", now)
            
            reminders = Reminder.query.filter_by(is_active=True, notification_type="telegram").all()
            print("Reminders found:", reminders)
            
            for r in reminders:
                # 2. Match exact minute
                r_time_str = r.reminder_time.strftime("%H:%M") if r.reminder_time else r.time
                if r_time_str != now:
                    continue
                    
                # 1. Start date check
                if r.start_date and r.start_date.date() > today_date:
                    continue
                
                # Prevent duplicate sends using last_sent_at (Only send if not already sent in this minute)
                if r.last_sent_at and r.last_sent_at.strftime("%H:%M") == now and r.last_sent_at.date() == today_date:
                    continue
                
                message = (
                    "🌱 GrowZen Reminder\n"
                    "💧 Time to water your plant!\n"
                    "Stay consistent 🌿"
                )
                
                # Failsafe around Telegram 
                try:
                    success = send_telegram(r.telegram_chat_id, message)
                    if success:
                        r.last_sent_at = current_dt
                        db.session.commit()
                except Exception as tg_err:
                    logging.error(f"Telegram failed for reminder {r.id}: {str(tg_err)}")

    except Exception as e:
        logging.error(f"Error in check_reminders: {str(e)}")

def check_auto_task_reminders(app):
    try:
        with app.app_context():
            now = datetime.utcnow()
            
            # Fetch all plants that have a schedule
            plants = Plant.query.all()
            for plant in plants:
                if not plant.schedule or not plant.schedule.last_watered:
                    continue
                
                last_watered_at = plant.schedule.last_watered
                time_diff = now - last_watered_at
                
                if time_diff > timedelta(hours=7):
                    # Prevent duplicate sends using last_reminder_sent_at
                    if plant.last_reminder_sent_at and plant.last_reminder_sent_at > (now - timedelta(hours=7)):
                        continue
                        
                    user = User.query.get(plant.user_id)
                    if not user or not user.telegram_chat_id: continue
                    
                    message = (
                        "⚠️ GrowZen Alert\n\n"
                        "Your plant has not been watered for 7 hours!\n\n"
                        f"Plant: {plant.name}\n"
                        "Please water it soon 💧"
                    )
                    
                    print("Sending to:", user.telegram_chat_id)
                    
                    try:
                        success = send_telegram(user.telegram_chat_id, message)
                        if success:
                            plant.last_reminder_sent_at = now
                            db.session.commit()
                    except Exception as tg_err:
                        logging.error(f"Telegram failed for 7h alert (plant {plant.id}): {str(tg_err)}")
                        
    except Exception as e:
        logging.error(f"Error in check_auto_task_reminders: {str(e)}")

def triggerReminderNow(app):
    """Alias for manual test support."""
    logging.info("Manual trigger requested...")
    check_reminders(app)
    check_auto_task_reminders(app)

def start_scheduler(app):
    """Start background scheduler with 1-minute interval."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_reminders(app), 'interval', minutes=1)
    scheduler.add_job(lambda: check_auto_task_reminders(app), 'interval', minutes=1)
    scheduler.start()
    logging.info("GrowZen Scheduler started (1m intervals)")
    return scheduler
