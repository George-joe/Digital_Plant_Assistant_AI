from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import time
from services.diseaseDetection.plantVillageModel import analyze_leaf_disease

disease_bp = Blueprint('disease_detection', __name__)

@disease_bp.route("/api/disease-detection", methods=["POST"])
def detect_disease():
    """
    Standalone API for plant disease detection using the PlantVillage CNN model.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = request.files["image"]
    filename = secure_filename(f"api_scan_{int(time.time())}_{image.filename}")
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "static/uploads")
    filepath = os.path.join(upload_folder, filename)
    image.save(filepath)

    # Analyze Using PlantVillage Service
    result = analyze_leaf_disease(filepath)
    
    # The analyze_leaf_disease function now returns the strict dict:
    # { "disease": ..., "confidence": ..., "severity": ..., "treatment": ... }
    # Or an error dict if it failed.
    
    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)
