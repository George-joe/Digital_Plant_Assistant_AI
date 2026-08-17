from app import create_app
from database.extensions import db
from models.user import User
from models.plant import Plant, PlantSchedule
from werkzeug.security import generate_password_hash

app = create_app()

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Add Dummy User
        u = User(id=1, name='Test User', email='test@test.com', password_hash=generate_password_hash('password123'), level='🌱 Rookie', xp_points=50, plants_owned=1, streak_days=2)
        db.session.add(u)
        db.session.commit()
        
        # Add Plant
        p = Plant(id=1, user_id=1, name='Lavender', scientific='Lavandula', image_url='https://images.unsplash.com/photo-1596728042571-7f8eaf1de5b2?w=500', 
                  confidence=95, status='Healthy', health_score=100, last_disease='Healthy')
        db.session.add(p)
        db.session.commit()
        
        # Add Schedule
        s = PlantSchedule(plant_id=1, water_frequency_days=4, sunlight_pref='Full Sun', humidity_pref='Moderate')
        db.session.add(s)
        db.session.commit()
        print('Success seeding database!')

if __name__ == '__main__':
    seed()
