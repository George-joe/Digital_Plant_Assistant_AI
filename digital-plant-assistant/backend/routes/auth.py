from flask import Blueprint, request, jsonify, session
from database.extensions import db
from models.user import User
import logging
from utils.helpers import get_authenticated_user

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.json
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return jsonify({"error": "Missing required fields"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already exists"}), 400

        new_user = User(
            name=name,
            email=email,
            password_hash=password # TEMP FIX: No hashing
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Log them in automatically by returning user data
        return jsonify({
            "success": True, 
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            },
            "access_token": str(new_user.id) # Simple mock token
        }), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        
        # DEBUG (Requested by user)
        print(f"[DEBUG] Stored User: {user.email if user else 'Not Found'}")
        print(f"[DEBUG] Stored Password (Plain): {user.password_hash if user else 'N/A'}")
        print(f"[DEBUG] Entered Password: {password}")

        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.password_hash != password:
            return jsonify({"error": "Incorrect password"}), 401

        session["user_id"] = user.id
        
        return jsonify({
            "success": True,
            "access_token": str(user.id), # Simple mock token for this demo
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "level": user.level,
                "xp_points": user.xp_points
            }
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"success": True})

@auth_bp.route("/api/auth/me", methods=["GET"])
@auth_bp.route("/api/user/settings", methods=["GET"])
def get_me():
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "level": user.level,
            "xp_points": user.xp_points,
            "streak_days": user.streak_days
        }
    }), 200
