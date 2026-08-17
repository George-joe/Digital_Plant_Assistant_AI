import os
import time
import logging
import json
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename

from database.extensions import db
from models.plant import Plant, HealthReport, WeeklyPhoto
from models.user import User
from services.plantnet_service import identify_plant
from services.chatbot.groqService import (
    generate_chat_response, generate_plant_insights
)
from services.diseaseDetection.plantVillageModel import analyze_leaf_disease
from services.weather_service import get_weather_data
from utils.helpers import add_xp, update_level, get_authenticated_user

logger = logging.getLogger(__name__)

plants_bp = Blueprint('plants', __name__)

def createTreatmentTasks(plant_id, disease):
    """
    Automatically creates tasks after diagnosis securely without wiping everything.
    """
    from models.plant import CareTask
    from database.extensions import db
    from datetime import datetime
    
    is_healthy = not disease or "healthy" in disease.lower()
    
    # Debug log (Part 6)
    print("Tasks created for disease:", disease)
    
    if not is_healthy:
        task_texts = [
            "Remove infected leaves",
            "Avoid overhead watering",
            "Apply fungicide",
            "Improve airflow"
        ]
        task_type = "treatment"
    else:
        task_texts = [
            "Water plant",
            "Check sunlight",
            "Inspect leaves"
        ]
        task_type = "Care"

    for label in task_texts:
        existing = CareTask.query.filter_by(plant_id=plant_id, label=label).first()
        if not existing:
            db.session.add(CareTask(
                plant_id=plant_id,
                label=label,
                task_type=task_type,
                is_completed=False,
                xp_reward=10,
                created_at=datetime.utcnow()
            ))
    db.session.commit()


@plants_bp.route("/api/identify-plant", methods=["POST"])
def detect_plant():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = request.files["image"]
    user_id = request.form.get("user_id") or session.get("user_id")
    
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Step 2: Fix File Upload System (UUID + Validation)
        import uuid
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        if not allowed_file(image.filename):
            current_app.logger.error(f"Invalid file format: {image.filename}")
            return jsonify({"error": "Invalid file format. Please upload jpg, jpeg, png, or webp."}), 400

        ext = image.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"plant_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        
        # Step 6: Debugging System
        current_app.logger.info(f"UPLOAD IDENTIFY START: {image.filename}")
        current_app.logger.info(f"SAVING TO: {filepath}")
        
        image.save(filepath)
        
        # Step 3: Fix Database Storage (Relative)
        db_relative_path = f"uploads/{unique_filename}"
        current_app.logger.info(f"DB STORED PATH (Pre-save): {db_relative_path}")

        # 1. Identify plant (PlantNet API)
        current_app.logger.info("Calling PlantNet API for identification...")
        result = identify_plant(filepath)
        
        # STEP 3: Fallback System (DO NOT stop pipeline on PlantNet failure)
        best_match = {}
        plantnet_ok = False
        if "error" in result:
            current_app.logger.warning(f"PlantNet failed or timed out: {result['error']}. Using CNN fallback.")
        elif "results" in result and result["results"]:
            best_match = result["results"][0]
            plantnet_ok = True
        
        species_info    = best_match.get("species", {})
        common_names    = species_info.get("commonNames", [])
        scientific_name = species_info.get("scientificName", "")
        
        # PlantNet plant name — may be empty if PlantNet failed
        plantnet_name = common_names[0] if common_names else scientific_name

        # 2. Run Disease Detection (PlantVillage CNN) — always runs
        health_result = analyze_leaf_disease(filepath)
        is_healthy = health_result.get("is_healthy", True)
        disease_name = health_result.get("disease_name", "Healthy")
        treatment = health_result.get("treatment", "Maintain regular care.")
        confidence_health = health_result.get("confidence", health_result.get("probability", 100))
        status = health_result.get("status", "Healthy" if is_healthy else "Diseased")

        # PART 1 FIX: Extract plant name from CNN model label as fallback
        # The model always gives us "Tomato" from "Tomato___Septoria_leaf_spot"
        model_plant = health_result.get("plant_name") or health_result.get("plant") or ""

        # Priority: PlantNet common name → PlantNet scientific → CNN model plant → "Unknown"
        if plantnet_name and plantnet_name.lower() not in ("", "unknown"):
            final_plant = plantnet_name
        elif model_plant and model_plant.lower() not in ("", "unknown"):
            final_plant = model_plant
        else:
            final_plant = "Unknown"

        current_app.logger.info(f"[GROWZEN] Plant extracted: PlantNet='{plantnet_name}' | CNN='{model_plant}' | Final='{final_plant}'")
        current_app.logger.info(f"[GROWZEN] Disease: '{disease_name}' | Confidence: {confidence_health}% | Status: '{status}'")

        # 3. Return preview (do not save to DB yet)
        return jsonify({
            # The exact requested keys:
            "plant_name": final_plant,
            "disease_name": disease_name,
            "confidence": confidence_health,
            "status": status,
            
            # Legacy payload ensuring frontend doesn't break
            "success": True,
            "name": final_plant,
            "scientific": scientific_name or final_plant,
            "image_url": f"/{db_relative_path}",
            "is_healthy": is_healthy,
            "disease": disease_name,
            "treatment": treatment,
            "health_score": health_result.get("health_score", 0),
            "severity": health_result.get("severity", "Low"),
            "disease_confidence": confidence_health
        }), 200


    except Exception as e:
        current_app.logger.error(f"Internal Server Error in /identify-plant: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "plant_name": "Unknown",
            "disease_name": "Detection Failed",
            "confidence": 0,
            "status": "Uncertain"
        }), 500

@plants_bp.route("/api/plants", methods=["POST"])
def create_plant():
    """Final step: Save the confirmed plant from the preview screen into the DB."""
    data = request.json or {}
    user = get_authenticated_user()
    user_id = user.id if user else data.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user ID"}), 400

    # Clean numeric fields safely
    conf = 0
    try:
        conf = int(float(data.get("confidence") or 0))
    except (ValueError, TypeError):
        pass

    hscore = 100
    try:
        hscore = int(float(data.get("health_score") if data.get("health_score") is not None else 100))
    except (ValueError, TypeError):
        pass

    new_plant = Plant(
        user_id=user_id,
        name=data.get("name") or data.get("plant_name") or "Unknown Plant",
        scientific=data.get("scientific") or data.get("scientific_name"),
        confidence=conf,
        image_url=data.get("image_url"),
        status="Healthy" if data.get("is_healthy", True) else "Sick",
        last_disease=data.get("disease") if not data.get("is_healthy", True) else None,
        health_score=hscore,
        nickname=data.get("nickname") or "",
        location=data.get("location") or "Indoor",
        pot_size=data.get("pot_size") or "Medium"
    )
    db.session.add(new_plant)
    db.session.commit() # Now we have new_plant.id

    # Initialize default care schedule
    from models.plant import PlantSchedule
    schedule = PlantSchedule(
        plant_id=new_plant.id,
        water_frequency_days=3,
        watering_interval=7,
        fertilizer_frequency_days=14,
        sunlight_pref="Indirect Sunlight",
        humidity_pref="Moderate",
        last_watered=datetime.utcnow(),
        next_watering_date=datetime.utcnow() + timedelta(days=3),
        last_fertilized=datetime.utcnow(),
        next_fertilizer_date=datetime.utcnow() + timedelta(days=14)
    )
    db.session.add(schedule)

    # Move image to permanent storage
    image_url = data.get("image_url")
    if image_url and "/uploads/" in image_url and "unsplash" not in image_url:
        try:
            import shutil
            temp_filename = os.path.basename(image_url)
            temp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], temp_filename)
            
            if os.path.exists(temp_path):
                ext = temp_filename.rsplit('.', 1)[1].lower() if '.' in temp_filename else 'jpg'
                new_filename = f"plant_{new_plant.id}.{ext}"
                new_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "plants", new_filename)
                
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.move(temp_path, new_path)
                
                new_plant.image_url = f"/uploads/plants/{new_filename}"
                current_app.logger.info(f"[GROWZEN] Image saved at path: {new_path}")
        except Exception as img_err:
            current_app.logger.error(f"[GROWZEN] Failed to persist image: {str(img_err)}")

    # Save initial health report
    prob = conf or 100
    try:
        prob = int(float(data.get("disease_confidence") or conf or 100))
    except (ValueError, TypeError):
        pass

    report = HealthReport(
        plant_id=new_plant.id,
        diagnosis=data.get("disease", "Healthy"),
        probability=prob,
        severity=data.get("severity", "Low"),
        treatment=data.get("treatment", "Maintain regular care."),
        image_path=new_plant.image_url
    )
    db.session.add(report)

    # Generate initial treatment and care tasks
    createTreatmentTasks(new_plant.id, data.get("disease"))

    # Award user XP for adding plant
    try:
        from utils.helpers import handle_add_plant_xp
        handle_add_plant_xp(user_id)
    except Exception as xp_err:
        current_app.logger.error(f"[GROWZEN] XP reward error: {xp_err}")

    db.session.commit()

    return jsonify({
        "success": True, 
        "id": new_plant.id, 
        "message": "Plant saved successfully", 
        "image_url": new_plant.image_url,
        "plant": {
            "id": new_plant.id,
            "name": new_plant.name,
            "scientific": new_plant.scientific,
            "health_score": new_plant.health_score,
            "status": new_plant.status,
            "image_url": new_plant.image_url
        }
    }), 201


@plants_bp.route("/api/plants", methods=["GET"])
def get_my_plants():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    plants = Plant.query.filter_by(user_id=user.id).order_by(Plant.created_at.desc()).all()
    plant_list = []
    for p in plants:
        next_water = None
        if p.schedule and p.schedule.next_watering_date:
            next_water = p.schedule.next_watering_date.isoformat()
            
        plant_list.append({
            "id": p.id,
            "name": p.name,
            "scientific": p.scientific,
            "status": p.status,
            "image": p.image_url,
            "image_url": p.image_url, # [GROWZEN] Consistent naming
            "image_path": p.image_url, # Alias for STEP 3
            "confidence": p.confidence,
            "health_score": p.health_score,
            "disease_name": p.last_disease,
            "disease": p.last_disease, # Alias for STEP 3
            "nickname": p.nickname,
            "location": p.location,
            "next_watering_date": next_water
        })
        
    return jsonify({
        "success": True, 
        "data": plant_list, 
        "plants": plant_list # Support both legacy and requested format
    })

@plants_bp.route("/api/user/<int:user_id>/plants", methods=["GET"])
def get_user_plants(user_id):
    # Bug 1 Fix: Accept Bearer token OR session (not hard session-only check)
    user = get_authenticated_user()
    if not user or user.id != user_id:
        # Last resort: allow if the URL user_id matches any authenticated user
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
    
    plants = Plant.query.filter_by(user_id=user_id).order_by(Plant.created_at.desc()).all()
    
    plant_list = []
    for p in plants:
        # Simplistic next watering calculation
        next_water = None
        if p.schedule and p.schedule.next_watering_date:
            next_water = p.schedule.next_watering_date.isoformat()
            
        plant_list.append({
            "id": p.id,
            "name": p.name,
            "scientific": p.scientific,
            "status": p.status,
            "image": p.image_url,
            "image_url": p.image_url, # [GROWZEN] Consistent naming
            "confidence": p.confidence,
            "health_score": p.health_score,
            "disease_name": p.last_disease,
            "nickname": p.nickname,
            "location": p.location,
            "next_watering_date": next_water
        })
        
    return jsonify(plant_list)


@plants_bp.route("/api/user/onboard", methods=["POST"])
def onboard_user():
    """
    Bug 2 Fix: Missing route that onboarding.js calls to save answers and compute user level.
    """
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    answers = request.json.get("answers", {}) if request.json else {}
    logger.info(f"[Onboard] user_id={user.id}, answers={answers}")

    # Compute level from onboarding answers
    # answers keys are 0-3 (stringified because JSON keys are strings)
    plants_owned = str(answers.get("0", answers.get(0, "0")))
    experience   = str(answers.get("2", answers.get(2, "Beginner")))

    if experience == "Advanced" or "15" in plants_owned:
        level = "🏆 Master"
    elif experience == "Intermediate" or "6" in plants_owned:
        level = "⭐ Expert"
    else:
        level = "🌱 Rookie"

    user.level = level
    db.session.commit()
    logger.info(f"[Onboard] Saved level={level} for user_id={user.id}")
    return jsonify({"success": True, "level": level})


@plants_bp.route("/api/plant/<int:plant_id>", methods=["GET"])
def get_plant(plant_id):
    """Get a single plant by its ID"""
    try:
        current_app.logger.info(f"[DEBUG] get_plant called for plant_id: {plant_id}")
        p = Plant.query.get(plant_id)
        if not p:
            current_app.logger.error(f"[DEBUG] Plant not found for plant_id: {plant_id}")
            return jsonify({"error": "Plant not found"}), 404
            
        current_app.logger.info(f"[DEBUG] Found plant: name={p.name}, scientific={p.scientific}, image_url={p.image_url}, last_scanned={p.last_scanned}")
        
        next_water = None
        water_freq = 7
        sunlight = "Indirect Sunlight"
        
        if p.schedule:
            next_water = p.schedule.next_watering_date.isoformat() if p.schedule.next_watering_date else None
            water_freq = p.schedule.water_frequency_days
            sunlight = p.schedule.sunlight_pref

        # [DEBUG] Mandatory log (Part 2)
        print("Returning plant:", p.name, "disease:", p.last_disease, "confidence:", p.confidence, "last_scanned:", p.last_scanned)
        return jsonify({
            "success": True,
            "data": {
                "id": p.id,
                "name": p.name,
                "disease": p.last_disease,
                "confidence": p.confidence,
                "last_scanned": p.last_scanned.isoformat() if p.last_scanned else None,
                "last_watered_at": p.schedule.last_watered.isoformat() if (p.schedule and p.schedule.last_watered) else None,
                "plant": {
                    "id": p.id,
                    "name": p.name,
                    "scientific": p.scientific,
                    "status": p.status,
                    "image": p.image_url,
                    "image_url": p.image_url,
                    "image_path": p.image_url,
                    "confidence": p.confidence,
                    "health_score": p.health_score,
                    "disease_name": p.last_disease,
                    "last_disease": p.last_disease,
                    "disease": p.last_disease,
                    "nickname": p.nickname,
                    "location": p.location,
                    "pot_size": p.pot_size,
                    "tracking_mode": p.tracking_mode,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "growth_stage": p.growth_stage,
                    "last_scanned": p.last_scanned.isoformat() if p.last_scanned else None,
                    "next_watering_date": next_water,
                    "last_watered_at": p.schedule.last_watered.isoformat() if (p.schedule and p.schedule.last_watered) else None,
                    "water_freq": water_freq,
                    "sunlight": sunlight,
                    "watering_interval": getattr(p.schedule, 'watering_interval', 7) if p.schedule else 7
                }
            }
        })
    except Exception as e:
        current_app.logger.error(f"[DEBUG] Error in get_plant for plant_id {plant_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@plants_bp.route("/api/plant/<int:plant_id>", methods=["DELETE"])
def delete_plant(plant_id):
    p = Plant.query.get(plant_id)
    if not p:
        return jsonify({"error": "Plant not found"}), 404
        
    # Bug 1 Fix: Use shared helper (accepts session OR Bearer token)
    user = get_authenticated_user()
    if not user or p.user_id != user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    db.session.delete(p)
    db.session.commit()
    return jsonify({"success": True})


@plants_bp.route("/api/detect-disease", methods=["POST"])
def detect_disease():
    """
    Consolidated diagnosis endpoint.
    STEP 1: Wrap in try-except, print traceback, safe response.
    STEP 3: Ensure pure detection (pass expected plant).
    STEP 8: Save in static/uploads, store uploads/filename.
    STEP 10: Create Task.
    """
    try:
        import traceback
        import uuid
        import os
        from datetime import datetime
        import json
        from flask import request, jsonify, current_app
        from models.plant import Plant, HealthReport, CareTask
        # db is already imported at module level from database.extensions
        from services.diseaseDetection.plantVillageModel import analyze_leaf_disease

        plant_id = request.form.get("plant_id")
        file = request.files.get('file') or request.files.get('image')
        user_note = request.form.get("note", request.form.get("notes", "Auto Scan (Diagnosis)"))
        
        if not file:
            return jsonify({"error": "No image uploaded"}), 400
            
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        plant = None
        if plant_id:
            try:
                plant_id = int(plant_id)
                plant = Plant.query.get(plant_id)
            except ValueError:
                return jsonify({"error": "Invalid plant_id format"}), 400
            if not plant:
                return jsonify({'error': 'Plant not found'}), 404

        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file format. Please upload jpg, jpeg, png, or webp."}), 400

        # Image Handling Fix
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"diag_{uuid.uuid4().hex}.{ext}"
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "static/uploads")
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Relative path for DB
        db_stored_path = f"uploads/{unique_filename}"

        # 1. Run AI analysis
        expected_context = plant.scientific or plant.name if plant else None
        try:
            analysis_result = analyze_leaf_disease(file_path, expected_plant=expected_context)
        except Exception as ai_err:
            current_app.logger.error(f"AI Model Error: {ai_err}")
            traceback.print_exc()
            return jsonify({"error": "AI Model failed to process image"}), 500

        if "error" in analysis_result:
            return jsonify({"error": analysis_result["error"]}), 400

        # Extract results
        status = analysis_result.get("status", "Uncertain")
        confidence = analysis_result.get("confidence", 0)
        health_score = analysis_result.get("healthScore", 0)
        disease_display = analysis_result.get("disease", "Unknown")
        plant_name_detected = analysis_result.get("plant", "Unknown")
        treatment = analysis_result.get("treatment", "Standard care.")

        report_id = None
        # 5. Update plant record ONLY if plant exists
        if plant:
            plant.last_scanned = datetime.utcnow()
            plant.health_score = health_score
            plant.image_url = db_stored_path
            plant.status = status
            
            if plant_name_detected and plant_name_detected != "Unknown":
                plant.scientific = plant_name_detected

            # 6. Save Health Report
            import json
            report = HealthReport(
                plant_id=plant_id,
                diagnosis=disease_display,
                probability=int(confidence),
                severity=analysis_result.get("severity", "Low"),
                treatment=treatment,
                image_path=db_stored_path,
                ai_follow_up_questions=json.dumps(analysis_result.get("ai_follow_up_questions", []))
            )
            db.session.add(report)
            
            # [FIX] PART 1: Save disease to plant (ALWAYS, not only on Diseased)
            plant.disease = disease_display  # Direct column if exists
            plant.last_disease = disease_display
            plant.confidence = int(confidence)
            print("Saved disease:", plant.last_disease)
            
            # [FIX] PART 2: Create Timeline entry (WeeklyPhoto) immediately
            try:
                week_count = WeeklyPhoto.query.filter_by(plant_id=plant.id).count()
                tl_entry = WeeklyPhoto(
                    plant_id=plant.id,
                    image_url="/" + db_stored_path,
                    week_number=week_count + 1,
                    photo_date_user=datetime.utcnow(),
                    health_score=health_score,
                    disease_detected=disease_display,
                    confidence=int(confidence),
                    notes=user_note,
                    tracking_mode="auto",
                    is_diagnosis=True,
                    ai_analysis=treatment
                )
                db.session.add(tl_entry)
            except Exception as tl_err:
                current_app.logger.error(f"[GROWZEN] Failed to save diagnosis timeline entry: {tl_err}")
                
            db.session.commit()
            report_id = report.id
            
            # [GROWZEN] Create Treatment Tasks deterministic 
            createTreatmentTasks(plant.id, disease_display)

        # Debug Log (Terminal) — Step 15
        print(f"----- DETECT-DISEASE ROUTE SUCCESS -----")
        print(f"[GROWZEN] Image received: {file_path}")
        print(f"[GROWZEN] Plant ID: {plant_id}")
        print(f"[GROWZEN] Model prediction: {plant_name_detected} / {disease_display}")
        print(f"[GROWZEN] Confidence: {confidence}%")
        print(f"[GROWZEN] Plant extracted: {plant_name_detected}")
        print(f"Diagnosis saved: {plant.last_disease}")
        print(f"Tasks created: {CareTask.query.filter_by(plant_id=plant.id).count()} tasks active")
        if report_id:
            print(f"[GROWZEN] Report saved: report_id={report_id}")
        print("----------------------------------------")

        _now_iso = datetime.utcnow().isoformat() + "Z"
        return jsonify({
            # STEP 2: Strict envelope (required by spec)
            "success": True,
            "data": {
                "plant": plant_name_detected,
                "disease": disease_display,
                "confidence": round(confidence, 2),
                "status": status,
                "image_path": f"/static/{db_stored_path}",
                "timestamp": _now_iso
            },
            # Flat legacy fields (frontend backwards compat)
            "plant": plant_name_detected,
            "disease": disease_display,
            "confidence": round(confidence, 2),
            "plant_name": plant_name_detected,
            "disease_name": disease_display,
            "status": status,
            "name": plant.name if plant else plant_name_detected,
            "healthScore": health_score,
            "health_score": health_score,
            "aiConfidence": round(confidence, 2),
            "treatment": treatment,
            "image_url": f"/static/{db_stored_path}",
            "report_id": report_id,
            "redirect": "/plant" if status == "Diseased" else None
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Internal Server Error in /diagnose: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "plant_name": "Unknown",
            "disease_name": "Detection Failed",
            "confidence": 0,
            "status": "Uncertain"
        }), 500


def _write_debug_log(msg):
    try:
        with open("backend_debug_logs.txt", "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass

@plants_bp.route("/api/detect-disease/<int:plant_id>", methods=["POST"])
def health_check(plant_id):
    """Stand-alone health check that updates the plant's timeline"""
    try:
        if 'image' not in request.files:
            msg = f"[STEP 5] API Called:\n- plantId: {plant_id}\n- image path: MISSING (No image uploaded)"
            current_app.logger.error(msg)
            _write_debug_log("=== BACKEND ===\n" + msg)
            return jsonify({'error': 'No image uploaded'}), 400
            
        file = request.files['image']
        if file.filename == '':
            current_app.logger.error(f"[DEBUG] Empty filename for plant_id: {plant_id}")
            return jsonify({'error': 'No selected file'}), 400

        plant = Plant.query.get(plant_id)
        if not plant:
            current_app.logger.error(f"[DEBUG] Plant not found for plant_id: {plant_id}")
            return jsonify({'error': 'Plant not found'}), 404
            
        current_app.logger.info(f"[DEBUG] Found plant in health_check: name={plant.name}, current scientific={plant.scientific}")

        # Step 2: Fix File Upload System (UUID + Validation)
        import uuid
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        if not allowed_file(file.filename):
            current_app.logger.error(f"Invalid file format: {file.filename}")
            return jsonify({"error": "Invalid file format. Please upload jpg, jpeg, png, or webp."}), 400

        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"health_{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        
        # Step 6: Debugging System
        current_app.logger.info(f"UPLOAD HEALTH START: {file.filename}")
        current_app.logger.info(f"SAVING TO: {file_path}")
        
        file.save(file_path)
        
        # Step 3: Fix Database Storage (Relative)
        db_stored_path = f"uploads/{unique_filename}"
        current_app.logger.info(f"DB STORED PATH: {db_stored_path}")
        
        msg5 = f"\n=== BACKEND ===\n[STEP 5] API Called:\n- plantId: {plant_id}\n- image path: {file_path}"
        current_app.logger.info(msg5)
        _write_debug_log(msg5)

        user_note = request.form.get("note", request.form.get("notes", "Auto Scan (Health Check)"))

        analysis_result = analyze_leaf_disease(file_path)
        
        msg6 = f"\n[STEP 6] AI Result:\n- {json.dumps(analysis_result)}"
        current_app.logger.info(msg6)
        _write_debug_log(msg6)

        # Only return error if there's a real error key AND no analysis data
        if "error" in analysis_result and not analysis_result.get("disease_name"):
            msg = analysis_result.get("error", "Unable to analyze image. Please upload another leaf photo.")
            current_app.logger.error(f"[DEBUG] Analysis failed for plant_id {plant_id}: {msg}")
            return jsonify({"error": msg}), 400
            
        cnn_confidence = analysis_result.get("confidence", 0)
        detected_plant = analysis_result.get("detected_plant", "unknown")

        current_app.logger.info(f"[DEBUG] Parsed values. detected_plant={detected_plant}, disease={analysis_result.get('raw_disease', 'N/A')}, health_score={analysis_result.get('health_score', 'N/A')}, confidence={cnn_confidence}")

    except Exception as e:
        current_app.logger.error(f"[DEBUG] Unexpected error in health_check for plant_id {plant_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred during analysis"}), 500

    # STEP 6: Never block — analysis_result always contains valid data from new service
    # Uncertain status is only set when there's a genuine read failure (image is null)
    if analysis_result.get("status") == "Uncertain" and not analysis_result.get("disease_name"):
        return jsonify({
            "success": True,
            "status": "Uncertain",
            "message": analysis_result.get("error", "Unable to read image. Please retry."),
            "disease": "Unknown",
            "health_score": 0,
            "initial_confidence": 0,
        }), 200

    # Use flat response fields from the updated analyze_leaf_disease service
    follow_up_qs   = analysis_result.get("ai_follow_up_questions", [])
    cnn_health_score = analysis_result.get("health_score", analysis_result.get("healthScore", 0))
    cnn_disease      = analysis_result.get("disease_name", analysis_result.get("disease", "Healthy"))
    cnn_severity     = analysis_result.get("severity", "low")
    cnn_is_healthy   = analysis_result.get("is_healthy", True)
    detected_plant   = analysis_result.get("plant_name", analysis_result.get("plant", "Unknown"))

    # Mismatch check — log only, never block
    expected_plant_name = plant.name or ""
    mismatch_warning = None
    import re as _re
    def _norm(n): return _re.sub(r'[^a-z0-9]', '', n.lower())
    if expected_plant_name and _norm(detected_plant) and \
       _norm(detected_plant) not in _norm(expected_plant_name) and \
       _norm(expected_plant_name) not in _norm(detected_plant):
        mismatch_warning = f"Detected as {detected_plant}, scanning {expected_plant_name}."
        current_app.logger.info(f"[GROWZEN] Plant mismatch (non-blocking): {mismatch_warning}")

    # Save initial report
    report = HealthReport(
        plant_id=plant_id,
        diagnosis=cnn_disease,
        probability=int(cnn_confidence * 100),
        severity=10 if cnn_severity in ("Severe", "high") else (5 if cnn_severity in ("Medium", "medium") else 1),
        treatment=analysis_result.get("treatment", ""),
        image_path=db_stored_path, # Using image_path as requested in Step 3
        ai_follow_up_questions=json.dumps(follow_up_qs)
    )
    db.session.add(report)

    # --- Immediately write CNN results to the plant record ---
    plant.last_scanned  = datetime.utcnow()
    plant.health_score  = cnn_health_score
    # Bug 3 Fix: confidence already 0-100, do NOT multiply by 100
    plant.confidence    = int(cnn_confidence)
    plant.last_disease  = cnn_disease if not cnn_is_healthy else "Healthy"
    plant.status        = "Healthy" if cnn_is_healthy else ("Sick" if cnn_severity == "Severe" else "Needs Attention")
    
    # Update species if identified (Point 3)
    if detected_plant and detected_plant != "unknown":
        plant.scientific = detected_plant

    # Update plant image to the latest health scan (Point 2)
    plant.image_url = db_stored_path
    
    # [FIX] Generate a Timeline Entry
    try:
        from datetime import datetime
        week_count = WeeklyPhoto.query.filter_by(plant_id=plant.id).count()
        tl_entry = WeeklyPhoto(
            plant_id=plant.id,
            image_url="/" + db_stored_path,
            week_number=week_count + 1,
            photo_date_user=datetime.utcnow(),
            health_score=cnn_health_score,
            disease_detected=cnn_disease,
            confidence=int(cnn_confidence),
            notes=user_note,
            tracking_mode="auto",
            is_diagnosis=True,
            ai_analysis=analysis_result.get("treatment", "Maintain regular care.")
        )
        db.session.add(tl_entry)
    except Exception as tl_err:
        current_app.logger.error(f"[GROWZEN] Failed to save health check timeline entry: {tl_err}")

    # [GROWZEN] Create Treatment Tasks
    createTreatmentTasks(plant.id, cnn_disease)

    save_data_str = f"species: {detected_plant}, health_score: {cnn_health_score}, confidence: {cnn_confidence}, status: {plant.status}, image_url: {unique_filename}"
    msg7 = f"\n[STEP 7] DB Save Attempt:\n- data being saved: {save_data_str}"
    current_app.logger.info(msg7)
    _write_debug_log(msg7)
    
    try:
        db.session.commit()
        msg8 = f"\n[STEP 8] DB Save Status:\n- success\n- None"
        current_app.logger.info(msg8)
        _write_debug_log(msg8)
    except Exception as e:
        db.session.rollback()
        msg8e = f"\n[STEP 8] DB Save Status:\n- failed\n- {str(e)}"
        current_app.logger.error(msg8e)
        _write_debug_log(msg8e)
        return jsonify({"error": "Failed to save diagnosis to database."}), 500
        
    # 3. DATABASE VERIFICATION (Immediate Fetch)
    verification_plant = Plant.query.get(plant_id)
    verify_str = f"species: {verification_plant.scientific}, healthScore: {verification_plant.health_score}, aiConfidence: {verification_plant.confidence}, lastScan: {verification_plant.last_scanned}"
    msg9 = f"\n[STEP 9] DB Verification Fetch:\n- {verify_str}"
    current_app.logger.info(msg9)
    _write_debug_log(msg9)
    
    response_data = {
        "success": True,
        "report_id": report.id,
        # Top-level flat fields read by plant.js frontend
        "name": verification_plant.name,
        "plant": verification_plant.name,           # frontend reads data.plant (string)
        "species": verification_plant.scientific or detected_plant,
        "disease": cnn_disease if not cnn_is_healthy else "Healthy",  # frontend reads data.disease
        "diagnosis": cnn_disease if not cnn_is_healthy else "Healthy",
        "diseaseStatus": "Sick" if not cnn_is_healthy else "Healthy",
        "status": "Sick" if not cnn_is_healthy else "Healthy",
        "aiConfidence": int(cnn_confidence),       # frontend reads data.aiConfidence
        "confidence": int(cnn_confidence),
        "healthScore": cnn_health_score,           # frontend reads data.healthScore
        "health_score": cnn_health_score,
        "severity": cnn_severity,
        "treatment": report.treatment,
        "initial_confidence": int(cnn_confidence),
        "is_healthy": cnn_is_healthy,
        "ai_follow_up_questions": follow_up_qs,
        "image_url": f"/uploads/{unique_filename}",
        "mismatch_warning": mismatch_warning,
        # Nested plant object kept for backward compatibility
        "plant_data": {
            "id": verification_plant.id,
            "name": verification_plant.name,
            "scientific": verification_plant.scientific,
            "status": verification_plant.status,
            "image": verification_plant.image_url,
            "confidence": verification_plant.confidence,
            "health_score": verification_plant.health_score,
            "disease_name": verification_plant.last_disease,
            "last_scanned": verification_plant.last_scanned.isoformat() if verification_plant.last_scanned else None
        }
    }
    
    msg10 = f"\n[STEP 10] API Response Sent:\n- {json.dumps(response_data)}"
    current_app.logger.info(msg10)
    _write_debug_log(msg10)
    return jsonify(response_data), 201


@plants_bp.route("/api/diagnosis/submit/<int:report_id>", methods=["POST"])
def submit_diagnosis(report_id):
    """
    Refine plant diagnosis score based on user answers to follow-up questions.
    """
    report = HealthReport.query.get(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
        
    plant = Plant.query.get(report.plant_id)
    payload = request.json
    answers = payload.get("answers", {})
    user_note = payload.get("note", payload.get("notes", "")) # [GROWZEN] Accept user note
    
    import json
    report.user_answers = json.dumps(answers)
    
    # Calculate health score refinement based on user answers
    # Weight: 60% Image AI Confidence, 40% User Answers
    image_score = report.probability # 0-100
    user_score = 100
    
    # Simple logic to reduce score based on "bad" indicators
    negatives = 0
    if "dry" in str(answers.get("leaf_condition", "")).lower(): negatives += 1
    if "spotted" in str(answers.get("leaf_condition", "")).lower(): negatives += 1
    if "outdoor" in str(answers.get("indoor_outdoor", "")).lower(): negatives += 0.5
    
    start_time = str(answers.get("issue_start", "")).lower()
    if "week" in start_time: negatives += 1
    elif "month" in start_time: negatives += 2
    
    user_score = max(0, 100 - (negatives * 15))
    final_score = int((image_score * 0.6) + (user_score * 0.4))
    report.final_score = final_score
    
    # Update plant health status
    is_healthy = report.diagnosis.lower() == "healthy" or "healthy" in report.diagnosis.lower()
    
    if not is_healthy:
        plant.status = "Sick"
        plant.last_disease = report.diagnosis
        plant.health_score = final_score
    else:
        if final_score < 70:
            plant.status = "Needs Attention"
        else:
            plant.status = "Healthy"
        plant.health_score = final_score
        
    plant.confidence = report.probability
    from datetime import datetime
    plant.last_scanned = datetime.utcnow()
    
    db.session.commit()
    current_app.logger.info(f"[GROWZEN] Diagnosis saved for plant {plant.id}: {report.diagnosis} ({final_score}%)")

    # [GROWZEN] Create Treatment Tasks
    createTreatmentTasks(plant.id, report.diagnosis)
    
    # Always ensure core daily tasks exist if not already there
    # (Checking for 'Watering' and 'Environment' broadly)
    
    db.session.commit()
    
    print(f"Diagnosis saved: {plant.last_disease}")
    print(f"Tasks created: {CareTask.query.filter_by(plant_id=plant.id).count()} tasks active")

    # [GROWZEN] PART 8: DIAGNOSIS → TIMELINE INTEGRATION
    try:
        tl_entry = WeeklyPhoto(
            plant_id=plant.id,
            image_url=report.image_path,
            photo_date_user=datetime.utcnow(),
            health_score=final_score,
            disease_detected=report.diagnosis,
            confidence=int(report.probability),
            notes=user_note or "Auto Scan (Diagnosis)", # [GROWZEN] Save user note
            tracking_mode="auto",
            is_diagnosis=True,
            ai_analysis=f"Final diagnosis: {report.diagnosis}. Health score: {final_score}%."
        )
        db.session.add(tl_entry)
        db.session.commit()
    except Exception as tl_err:
        current_app.logger.error(f"[GROWZEN] Failed to save diagnosis timeline entry: {tl_err}")
    
    return jsonify({
        "success": True,
        "final_health_score": final_score,
        "status": plant.status,
        "treatment": "Treatment tasks available in Care Plan.",
        "diagnosis": report.diagnosis,
        "report_id": report.id,
        "note": user_note
    })



@plants_bp.route("/api/plant/<int:plant_id>/photo", methods=["POST"])
def upload_plant_photo(plant_id):
    """Upload a new plant photo, run AI growth + disease analysis, save timeline entry."""
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404

    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = request.files["image"]
    notes = request.form.get("notes", "")
    tracking_mode = request.form.get("tracking_mode", "weekly")
    photo_date_str = request.form.get("photo_date")

    filename = secure_filename(f"photo_{plant_id}_{int(time.time())}_{image.filename}")
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "static/uploads")
    file_path = os.path.join(upload_folder, filename)
    image.save(file_path)

    # Find previous photo for comparison
    prev_photo = WeeklyPhoto.query.filter_by(plant_id=plant_id).order_by(WeeklyPhoto.created_at.desc()).first()
    prev_path = None
    if prev_photo:
        prev_filename = prev_photo.image_url
        if prev_filename and not prev_filename.startswith("/") and not prev_filename.startswith("http"):
            candidate = os.path.join(upload_folder, prev_filename)
            if os.path.exists(candidate):
                prev_path = candidate

    # Debug logging — Step 15
    print(f"[GROWZEN] Image received for timeline upload: {file_path}")

    # Run AI analysis using PlantVillage model
    analysis = analyze_leaf_disease(file_path)

    # Debug logging — Step 15
    print(f"[GROWZEN] Model prediction: {analysis.get('plant_name', '?')} / {analysis.get('disease_name', '?')}")
    print(f"[GROWZEN] Confidence: {analysis.get('confidence', 0)}%")
    print(f"[GROWZEN] Plant extracted: {analysis.get('plant_name', 'Unknown')}")

    # STEP 6: FIX — use correct keys returned by analyze_leaf_disease
    analysis_disease = analysis.get("disease_name", analysis.get("disease", "Healthy"))
    analysis_is_healthy = analysis.get("is_healthy", True)
    analysis_health_score = analysis.get("health_score", 0)
    analysis_confidence = analysis.get("confidence", 0)
    analysis_treatment = analysis.get("treatment", "")

    # Determine user-supplied date
    photo_date_user = None
    if photo_date_str:
        try:
            from datetime import datetime as dt
            photo_date_user = dt.strptime(photo_date_str, "%Y-%m-%d")
        except ValueError:
            pass

    week_count = WeeklyPhoto.query.filter_by(plant_id=plant_id).count()
    photo = WeeklyPhoto(
        plant_id=plant_id,
        image_url="/uploads/" + filename, # [GROWZEN] Store full project-relative path
        week_number=week_count + 1,
        notes=notes,
        tracking_mode=tracking_mode,
        photo_date_user=photo_date_user,
        health_score=analysis_health_score,
        confidence=int(analysis_confidence),
        disease_detected=analysis_disease,
        ai_analysis=analysis_treatment,
        growth_insights=None
    )
    db.session.add(photo)

    # STEP 6: Care Plan Generation + Groq expanded treatment
    if not analysis_is_healthy and analysis_treatment:
        from models.plant import CareTask
        # Remove old treatment tasks to keep care plan current
        CareTask.query.filter_by(plant_id=plant_id, task_type="Treatment").delete()

        # Try Groq for expanded treatment plan
        groq_treatment = analysis_treatment
        try:
            from services.chatbot.groqService import generate_chat_response
            prompt = "Give 3-5 plant care tasks for " + analysis_disease
            groq_resp = generate_chat_response(prompt)
            if groq_resp and not groq_resp.startswith("AI Error") and not groq_resp.startswith("AI service"):
                groq_treatment = groq_resp
        except Exception as groq_err:
            current_app.logger.warning(f"[GROWZEN] Groq task generation failed (using fallback): {groq_err}")

        lines = groq_treatment.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if (line.startswith("Day ") or line.startswith("-") or
                    line.startswith("*") or (len(line) > 2 and line[1:3] == ". ")):
                clean_text = line.lstrip("-*0123456789. \t")
                # Normalize "Day X - Action" → "Day X — Action"
                if " - " in clean_text and clean_text.lower().startswith("day"):
                    parts = clean_text.split(" - ", 1)
                    if len(parts) == 2:
                        clean_text = f"{parts[0].strip()} — {parts[1].strip()}"
                if len(clean_text) > 5:
                    task_type = "Treatment"
                    task = CareTask(
                        plant_id=plant.id,
                        task_type=task_type,
                        label=clean_text[:250],
                        is_completed=False
                    )
                    db.session.add(task)

    # Update plant health + last scanned
    plant.health_score = analysis_health_score
    plant.last_scanned = datetime.utcnow()
    plant.confidence = int(analysis_confidence)
    if not analysis_is_healthy:
        plant.status = "Sick"
        plant.last_disease = analysis_disease
    else:
        plant.status = "Healthy"
        plant.last_disease = None

    db.session.commit()
    print(f"Diagnosis saved: {plant.last_disease}")
    print(f"Tasks created: {CareTask.query.filter_by(plant_id=plant.id).count()} tasks active")
    print(f"[GROWZEN] Timeline entry saved: photo_id={photo.id}, disease={analysis_disease}, health={analysis_health_score}")

    return jsonify({
        "success": True,
        "photo_id": photo.id,
        "image_url": "/uploads/" + filename,
        "health_score": analysis_health_score,
        "disease_detected": analysis_disease,
        "disease_name": analysis_disease,
        "confidence": analysis_confidence,
        "ai_analysis": analysis_treatment,
        "is_healthy": analysis_is_healthy,
        "note": notes
    }), 201

# NOTE: get_plant_tasks was removed — duplicate of get_care_tasks (below).
# get_care_tasks is the canonical implementation and now includes progress_msg.



@plants_bp.route("/api/plant/<int:plant_id>/water", methods=["POST"])
def water_plant(plant_id):
    """Mark plant as watered with 7-hour cooldown and sync with task."""
    from models.plant import PlantSchedule, CareTask, Plant
    from models.user import User
    from utils.helpers import add_xp
    from datetime import datetime, timedelta
    
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404
        
    if not plant.schedule:
        plant.schedule = PlantSchedule(plant_id=plant.id)
        db.session.add(plant.schedule)
        db.session.commit()

    now = datetime.utcnow()
    last_watered = plant.schedule.last_watered
    
    # Check 7-hour cooldown
    if last_watered and (now - last_watered) < timedelta(hours=7):
        diff = timedelta(hours=7) - (now - last_watered)
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        wait_msg = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        return jsonify({"success": False, "error": "Already watered recently", "wait_time": wait_msg}), 400

    # Streak logic & XP
    user = User.query.get(plant.user_id)
    if last_watered:
        days_diff = (now.date() - last_watered.date()).days
        if user:
            if days_diff == 1:
                user.streak_days = (user.streak_days or 0) + 1
            elif days_diff > 1:
                user.streak_days = 0
    else:
        if user: user.streak_days = 1
        
    add_xp(plant.user_id, 5)

    # Update watering status
    from models.plant import WaterLog
    db.session.add(WaterLog(plant_id=plant_id, watered_at=now))
    
    plant.schedule.last_watered = now
    freq = plant.schedule.water_frequency_days or 7
    plant.schedule.next_watering_date = now + timedelta(days=freq)
    
    # Sync with "Watering" tasks
    watering_tasks = CareTask.query.filter(
        CareTask.plant_id==plant_id,
        CareTask.is_completed==False,
        db.or_(CareTask.task_type.ilike("%water%"), CareTask.label.ilike("%water%"))
    ).all()
    
    tasks_completed = 0
    for task in watering_tasks:
        task.is_completed = True
        task.completed_at = now
        task.reset_date = now
        tasks_completed += 1
        
    db.session.commit()
    current_app.logger.info(f"[GROWZEN] Plant {plant_id} watered manually. +5 XP. {tasks_completed} tasks synced.")
    
    return jsonify({
        "success": True, 
        "message": "Plant watered successfully! +5 XP", 
        "last_watered": now.isoformat(),
        "tasks_synced": tasks_completed,
        "xp_earned": 5
    })


@plants_bp.route("/api/plant/<int:plant_id>/timeline", methods=["GET"])
def get_plant_timeline(plant_id):
    """Fetch all chronological photo instances mapped to standard Timeline UI hooks."""
    current_app.logger.info(f"Fetching Photo Timeline for plant_id {plant_id}")
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404

    # [GROWZEN] Include both timeline entries and diagnosis scans in chronological feed
    photos = WeeklyPhoto.query.filter_by(plant_id=plant_id).order_by(WeeklyPhoto.created_at.desc()).all()

    timeline_data = []
    for idx, p in enumerate(photos):
        eff_date = p.photo_date_user or p.created_at
        entry_number = idx + 1
        
        # Calculate N-th day difference to approximate UI 'notes'
        first_date = photos[0].photo_date_user or photos[0].created_at
        day_diff = (eff_date - first_date).days + 1

        timeline_data.append({
            "id": p.id,
            "image_url": p.image_url if p.image_url.startswith("/") else f"/uploads/{p.image_url}",
            "created_at": eff_date.isoformat(),
            "health_score": p.health_score or getattr(plant, "health_score", 0),
            "disease_detected": p.disease_detected,
            "ai_analysis": p.ai_analysis,
            "notes": p.notes,
            "tracking_mode": p.tracking_mode,
            "entry_number": entry_number,
            "day_number": day_diff
        })

    return jsonify({"success": True, "timeline": timeline_data})


@plants_bp.route("/api/plant/<int:plant_id>/growth-summary", methods=["GET"])
def growth_summary(plant_id):
    """Return aggregated growth chart data and overall trend summary."""
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404

    photos = WeeklyPhoto.query.filter_by(plant_id=plant_id).order_by(WeeklyPhoto.created_at.asc()).all()
    if not photos:
        return jsonify({"success": True, "has_data": False, "photos": [], "chart": {}})

    chart_labels = []
    chart_scores = []
    for idx, p in enumerate(photos):
        effective_date = p.photo_date_user or p.created_at
        label = f"Entry {idx+1}" if idx < 3 else effective_date.strftime("%b %d")
        chart_labels.append(label)
        chart_scores.append(p.health_score or 0)

    latest = photos[-1]
    first = photos[0]
    trend = "Stable"
    if len(photos) > 1:
        delta = (latest.health_score or 0) - (first.health_score or 0)
        if delta > 10:
            trend = "Improving"
        elif delta < -10:
            trend = "Declining"

    disease_series = [p.disease_detected for p in photos if p.disease_detected and p.disease_detected.lower() != "healthy"]
    recovery_note = None
    if disease_series and (latest.disease_detected is None or latest.disease_detected.lower() == "healthy"):
        recovery_note = f"Plant has recovered from {disease_series[0]}!"

    return jsonify({
        "success": True,
        "has_data": True,
        "chart": {
            "labels": chart_labels,
            "scores": chart_scores
        },
        "latest_health": latest.health_score or 0,
        "overall_trend": trend,
        "total_entries": len(photos),
        "latest_disease": latest.disease_detected or "Healthy",
        "latest_insights": latest.growth_insights,
        "recovery_note": recovery_note
    })

@plants_bp.route("/api/tasks", methods=["GET"])
def get_all_tasks():
    from models.plant import CareTask
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    plant_id_arg = request.args.get("plant_id")
    if plant_id_arg == "ALL":
        plants = Plant.query.filter_by(user_id=user.id).all()
        plant_ids = [p.id for p in plants]
    elif plant_id_arg:
        try:
            # Ensure the user owns this plant
            p_id = int(plant_id_arg)
            p = Plant.query.get(p_id)
            if p and p.user_id == user.id:
                plant_ids = [p_id]
            else:
                return jsonify({"error": "Unauthorized"}), 403
        except ValueError:
            return jsonify({"error": "Invalid plant_id"}), 400
    else:
        return jsonify({"error": "Missing or invalid plant_id param"}), 400
        
    all_tasks = CareTask.query.filter(CareTask.plant_id.in_(plant_ids)).all()
    
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    for t in all_tasks:
        if t.is_completed and t.completed_at and (now - t.completed_at) > timedelta(hours=24):
            t.is_completed = False
            t.completed_at = None
            t.reset_date = None
    db.session.commit()
    
    task_list = []
    for t in all_tasks:
        task_list.append({
            "id": t.id,
            "plant_id": t.plant_id,
            "plant_name": t.plant.name if t.plant else "Unknown",
            "image_url": t.plant.image_url if t.plant else "",
            "title": t.title if hasattr(t, 'title') else t.label,
            "label": t.label,
            "task_type": t.task_type.value if hasattr(t.task_type, "value") else str(t.task_type),
            "completed": t.is_completed
        })
        
    return jsonify({"success": True, "tasks": task_list})


@plants_bp.route("/api/plant/<int:plant_id>/tasks", methods=["GET"])
def get_care_tasks(plant_id):
    """Return care tasks for this plant, with treatment progress tracking."""
    from models.plant import CareTask
    include_completed = request.args.get("include_completed", "false").lower() == "true"

    from datetime import timedelta
    now = datetime.utcnow()
    
    q = CareTask.query.filter_by(plant_id=plant_id)
    all_tasks = q.order_by(CareTask.created_at.asc()).all()
    
    # [GROWZEN] Auto Reset Tasks
    for t in all_tasks:
        # Strict 24h reset logic
        if t.is_completed and t.completed_at and (now - t.completed_at) > timedelta(hours=24):
            t.is_completed = False
            t.completed_at = None
            t.reset_date = None
            
    db.session.commit()

    # Filter based on instruction
    if not include_completed:
        tasks = [t for t in all_tasks if not t.is_completed]
    # Calculate X of Y today tasks
    total_today = len(all_tasks)
    
    # [FIX] PART 5: Ensure tasks always exist
    if total_today == 0:
        default_tasks = [
            "Water your plant",
            "Check sunlight exposure",
            "Inspect leaves for pests"
        ]
        for idx, label in enumerate(default_tasks):
            t = CareTask(
                plant_id=plant_id,
                task_type="Care",
                label=label,
                is_completed=False,
                xp_reward=10
            )
            db.session.add(t)
            all_tasks.append(t)
        db.session.commit()
        total_today = len(all_tasks)
        if not include_completed:
            tasks = [t for t in all_tasks if not t.is_completed]
        else:
            tasks = all_tasks

    done_today = sum(1 for t in all_tasks if t.is_completed)
    if total_today > 0:
        progress_msg = f"{done_today} of {total_today} tasks done"
    else:
        progress_msg = "No tasks for today."

    return jsonify({
        "success": True,
        "tasks": [t.to_dict() for t in tasks],
        "progress_msg": progress_msg,
        "is_completed": all(t.is_completed for t in tasks) if tasks else True
    })


@plants_bp.route("/api/plant/upload-progress", methods=["POST"])
def upload_progress():
    """
    STEP 5: Convenience endpoint for timeline photo upload.
    Accepts multipart/form-data: image (file), plant_id (form), note (form, optional).
    Runs CNN, saves WeeklyPhoto, creates care tasks, returns timeline entry.
    """
    plant_id = request.form.get("plant_id")
    if not plant_id:
        return jsonify({"error": "plant_id is required"}), 400
    try:
        plant_id = int(plant_id)
    except ValueError:
        return jsonify({"error": "Invalid plant_id"}), 400

    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404

    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    # Delegate to the existing photo upload endpoint logic by rewriting request context
    # We simply call the core upload function directly to avoid code duplication
    image = request.files["image"]
    note = request.form.get("note", request.form.get("notes", ""))

    import uuid
    ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    unique_filename = f"progress_{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "static/uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    image.save(file_path)

    print(f"[GROWZEN] upload-progress: Image received: {file_path}")

    analysis = analyze_leaf_disease(file_path)
    analysis_disease = analysis.get("disease_name", analysis.get("disease", "Healthy"))
    analysis_is_healthy = analysis.get("is_healthy", True)
    analysis_health_score = analysis.get("health_score", 0)
    analysis_confidence = analysis.get("confidence", 0)
    analysis_treatment = analysis.get("treatment", "")

    print(f"[GROWZEN] upload-progress: Prediction: {analysis.get('plant_name','?')} / {analysis_disease} @ {analysis_confidence}%")

    week_count = WeeklyPhoto.query.filter_by(plant_id=plant_id).count()
    photo = WeeklyPhoto(
        plant_id=plant_id,
        image_url="/uploads/" + unique_filename, # [GROWZEN] Store full project-relative path
        week_number=week_count + 1,
        notes=note,
        tracking_mode="weekly",
        health_score=analysis_health_score,
        confidence=int(analysis_confidence),
        disease_detected=analysis_disease,
        ai_analysis=analysis_treatment,
    )
    db.session.add(photo)

    # Auto-generate care tasks if diseased
    if not analysis_is_healthy and analysis_treatment:
        from models.plant import CareTask
        CareTask.query.filter_by(plant_id=plant_id, task_type="Treatment").delete()
        for line in analysis_treatment.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("-") or line.startswith("*") or line.startswith("Day "):
                clean = line.lstrip("-*0123456789Day. \t").strip()
                if len(clean) > 5:
                    lt = clean.lower()
                    ttype = "Watering" if "water" in lt else "Treatment" if "fungicide" in lt or "spray" in lt else "Pruning" if "remove" in lt or "prune" in lt else "Care"
                    db.session.add(CareTask(plant_id=plant_id, task_type=ttype, label=clean[:250], is_completed=False))

    plant.health_score = analysis_health_score
    plant.last_scanned = datetime.utcnow()
    plant.confidence = int(analysis_confidence)
    plant.status = "Healthy" if analysis_is_healthy else "Sick"
    plant.last_disease = None if analysis_is_healthy else analysis_disease
    db.session.commit()

    print(f"[GROWZEN] upload-progress: Saved photo_id={photo.id}, task_generated={not analysis_is_healthy}")
    return jsonify({
        "success": True,
        "photo_id": photo.id,
        "image_url": f"/uploads/{unique_filename}",
        "health_score": analysis_health_score,
        "disease_detected": analysis_disease,
        "disease_name": analysis_disease,
        "confidence": analysis_confidence,
        "is_healthy": analysis_is_healthy,
        "note": note,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 201

@plants_bp.route("/api/plant/tasks/<int:task_id>", methods=["PATCH"])
def toggle_care_task(task_id):
    """Toggle completion status of a specific CareTask."""
    from models.plant import CareTask
    task = CareTask.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    is_completed = request.json.get("is_completed", True)
    task.is_completed = is_completed
    from datetime import datetime
    now_dt = datetime.utcnow()
    
    if is_completed:
        task.completed_at = now_dt
        task.reset_date = now_dt
        
        # XP VALUES (watering=5, sunlight[environment]=3, inspection[care]=4, treatment=10)
        t_type = str(task.task_type).lower()
        xp_amount = 4 # default to inspection (4)
        if "water" in t_type: xp_amount = 5
        elif "sun" in t_type or "environment" in t_type: xp_amount = 3
        elif "treatment" in t_type: xp_amount = 10
        
        task.xp_reward = xp_amount
        
        # Add XP to user safely
        from models.plant import Plant
        plant = Plant.query.get(task.plant_id)
        if plant:
            from utils.helpers import add_xp
            add_xp(plant.user_id, xp_amount)
    else:
        task.completed_at = None
        task.reset_date = None

    db.session.commit()
    return jsonify({"success": True, "is_completed": task.is_completed, "xp_reward": getattr(task, 'xp_reward', 0)})


@plants_bp.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    """Mark a task as completed, track streaks, and return XP reward info."""
    from models.plant import CareTask, PlantSchedule, Plant
    from models.user import User
    from utils.helpers import add_xp
    from datetime import datetime, timedelta
    
    task = CareTask.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    now_dt = datetime.utcnow()
    xp_amount = getattr(task, 'xp_reward', 0) or 10
    
    if not task.is_completed:
        task.is_completed = True
        task.completed_at = now_dt
        task.reset_date = now_dt
        
        t_type = str(task.task_type).lower()
        t_label = str(task.label).lower()
        
        if xp_amount == 0 or xp_amount == 10:
            xp_amount = 4
            if "water" in t_type or "water" in t_label: xp_amount = 5
            elif "sun" in t_type or "environment" in t_type: xp_amount = 3
            elif "treatment" in t_type: xp_amount = 10
            task.xp_reward = xp_amount
            
        plant = Plant.query.get(task.plant_id)
        if plant:
            add_xp(plant.user_id, xp_amount)
            
            # If watering, sync schedule & streak tracking
            if "water" in t_type or "water" in t_label:
                if not plant.schedule:
                    plant.schedule = PlantSchedule(plant_id=plant.id)
                    db.session.add(plant.schedule)
                
                last_w = plant.schedule.last_watered
                user = User.query.get(plant.user_id)
                if last_w:
                    days_diff = (now_dt.date() - last_w.date()).days
                    if user:
                        if days_diff == 1:
                            user.streak_days = (user.streak_days or 0) + 1
                        elif days_diff > 1:
                            user.streak_days = 0
                else:
                    if user: user.streak_days = 1
                    
                plant.schedule.last_watered = now_dt
                freq = plant.schedule.water_frequency_days or 7
                plant.schedule.next_watering_date = now_dt + timedelta(days=freq)

        db.session.commit()
        current_app.logger.info(f"[GROWZEN] Task completed: {task.label} for plant {task.plant_id} (+{xp_amount} XP)")

    return jsonify({
        "success": True,
        "task_id": task.id,
        "is_completed": True,
        "xp_earned": xp_amount,
        "message": f"Task completed! +{xp_amount} XP"
    })


@plants_bp.route("/api/user/<int:user_id>/stats", methods=["GET"])
def user_stats(user_id):
    """Return garden summary stats + pending care tasks for the dashboard."""
    from models.user import User
    from models.plant import CareTask
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    plants = Plant.query.filter_by(user_id=user_id).all()
    plant_ids = [p.id for p in plants]
    
    total = len(plants)
    healthy = sum(1 for p in plants if (p.health_score or 0) >= 80)
    monitor  = sum(1 for p in plants if 60 <= (p.health_score or 0) < 80)
    needs_attn = sum(1 for p in plants if 40 <= (p.health_score or 0) < 60)
    sick = sum(1 for p in plants if (p.health_score or 0) < 40)
    avg_health = int(sum(p.health_score or 0 for p in plants) / total) if total else 0

    # Fetch real pending tasks from DB (Filter out 'Treatment' for dashboard directly - Step 9)
    pending_tasks = CareTask.query.filter(
        CareTask.plant_id.in_(plant_ids), 
        CareTask.is_completed == False,
        CareTask.task_type != "Treatment"
    ).order_by(CareTask.created_at.desc()).all()
    
    tasks = []
    for t in pending_tasks:
        p = next((pl for pl in plants if pl.id == t.plant_id), None)
        if not p: continue
        
        img_url = p.image_url or ""
        if img_url and not img_url.startswith("http") and not img_url.startswith("/uploads/"):
            img_url = "/uploads/" + img_url
            
        tasks.append({
            "id": t.id,
            "plant_id": p.id,
            "plant_name": p.name,
            "plant_img": img_url,
            "type": t.task_type.lower(),
            "label": t.label,
            "priority": "high" if t.task_type in ["Treatment", "Watering"] else "medium"
        })

    # XP level thresholds
    xp = user.xp_points or 0
    if xp >= 500:   level_label = "🏆 Master"
    elif xp >= 250: level_label = "⭐ Expert"
    elif xp >= 100: level_label = "🌿 Grower"
    else:           level_label = "🌱 Rookie"

    next_level_xp = 100 if xp < 100 else 250 if xp < 250 else 500 if xp < 500 else 1000
    prev_level_xp = 0  if xp < 100 else 100 if xp < 250 else 250 if xp < 500 else 500
    progress_pct  = int(((xp - prev_level_xp) / (next_level_xp - prev_level_xp)) * 100)

    return jsonify({
        "success": True,
        "summary": {
            "total": total, "healthy": healthy, "monitor": monitor,
            "needs_attention": needs_attn, "sick": sick, "avg_health": avg_health
        },
        "tasks": tasks[:15],
        "xp": xp,
        "level": level_label,
        "streak": user.streak_days or 0,
        "xp_progress": min(100, progress_pct)
    })


@plants_bp.route("/api/user/<int:user_id>/award-xp", methods=["POST"])
def award_xp(user_id):
    """Award XP points for specific user actions."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    action = request.json.get("action", "")
    xp_map = {
        "add_plant":     20,
        "water_plant":    5,
        "add_photo":     10,
        "diagnose":      15,
        "complete_task":  3,
        "streak_bonus":  10,
    }
    earned = xp_map.get(action, 0)
    if not earned:
        return jsonify({"error": f"Unknown action: {action}"}), 400

    from utils.helpers import add_xp
    add_xp(user_id, earned)
    
    return jsonify({"success": True, "xp": user.xp_points, "earned": earned, "level": user.level})


# ── Keep the existing garden-tip route below ──────────────────────────────
@plants_bp.route("/api/garden-tip", methods=["GET"])
def garden_tip():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    
    weather_context = "Clear, 25°C"
    if lat and lon:
        try:
            w_data = get_weather_data(lat, lon)
            curr = w_data.get("current_weather", {})
            weather_context = f"Temperature: {curr.get('temperature')}°C, Wind: {curr.get('windspeed')}km/h"
        except Exception as e:
            logger.warning(f"Could not fetch weather for tip: {e}")
            
    prompt = f"Given this current weather data ({weather_context}), provide a personalized one-sentence care tip for an indoor or balcony plant garden."
    
    try:
        tip = generate_chat_response(prompt, "General Garden")
        return jsonify({"tip": tip})
    except Exception as e:
        logger.error(f"Error generating garden tip: {e}")
        return jsonify({"tip": "Keep an eye on moisture levels and ensure your plants get adequate sunlight today!"})
