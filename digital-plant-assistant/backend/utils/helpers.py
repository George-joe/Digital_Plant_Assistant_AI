from database.extensions import db
from models.user import User
from flask import session, request


def get_authenticated_user():
    """
    Shared auth helper — accepts BOTH Flask session and Bearer token.
    Frontend stores user_id as the access_token in localStorage and sends:
      Authorization: Bearer <user_id>
    This allows session-less clients (SPA) to authenticate without cookies.
    """
    # 1. Try Flask session first (same-origin browser requests)
    user_id = session.get("user_id")

    # 2. Fall back to Authorization: Bearer <user_id> header
    if not user_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            user_id = auth_header.split(" ", 1)[1].strip()

    # 3. Also accept user_id in JSON body or form (for endpoints that send it)
    if not user_id:
        if request.is_json:
            user_id = request.json.get("user_id") if request.json else None
        if not user_id:
            user_id = request.form.get("user_id")

    if not user_id:
        return None

    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


def add_xp(user_id, xp_amount):
    user = User.query.get(user_id)
    if not user:
        return None
        
    user.xp_points += xp_amount
    update_level(user)
    db.session.commit()
    return user

def update_level(user):
    xp = user.xp_points or 0
    if xp >= 500:   new_level = "🏆 Master"
    elif xp >= 250: new_level = "⭐ Expert"
    elif xp >= 100: new_level = "🌿 Grower"
    else:           new_level = "🌱 Rookie"
    
    if user.level != new_level:
        user.level = new_level
        
def handle_watering_streak(user_id):
    user = User.query.get(user_id)
    if not user:
        return
    user.streak_days += 1
    add_xp(user_id, 5) # +5 XP for watering

def handle_add_photo_xp(user_id):
    add_xp(user_id, 8) # +8 XP for updating plant photo

def handle_add_plant_xp(user_id):
    user = User.query.get(user_id)
    if not user:
        return
    user.plants_owned += 1
    add_xp(user_id, 20) # +20 XP for adding plant

def handle_diagnose_disease_xp(user_id):
    add_xp(user_id, 10) # +10 XP for diagnosis

def handle_weekly_photo_xp(user_id):
    add_xp(user_id, 30) # +30 XP for uploading weekly/timeline photo
