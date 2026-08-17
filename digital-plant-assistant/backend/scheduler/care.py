from datetime import datetime, timedelta
from database.extensions import db
from models.plant import PlantSchedule

def calculate_next_care_dates(plant_id, care_type="water"):
    """
    Recalculates dates based on plant id and care type
    care_type: 'water', 'fertilizer'
    """
    schedule = PlantSchedule.query.filter_by(plant_id=plant_id).first()
    if not schedule:
        return
        
    now = datetime.utcnow()
    
    if care_type == "water":
        schedule.last_watered = now
        schedule.next_watering_date = now + timedelta(days=schedule.water_frequency_days)
    # Add other types here
    
    db.session.commit()
    return schedule
