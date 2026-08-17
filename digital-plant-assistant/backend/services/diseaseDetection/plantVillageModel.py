import os
import logging
import numpy as np
import json

logger = logging.getLogger(__name__)

# ─── Module-level cache ────────────────────────────────────────────────────────
_model       = None
_class_labels = None


# ─── STEP 4: Load Model + class_indices.json ──────────────────────────────────
def load_plant_village_model():
    global _model, _class_labels

    if _model is not None:
        return _model, _class_labels

    # Resolve paths
    base_dir = os.path.dirname(__file__)
    for _ in range(4):
        base_dir = os.path.dirname(base_dir)

    env_path   = os.getenv("PLANT_DISEASE_MODEL_PATH",
                           "ai/plant-disease-model/model/plant_disease_model.keras")
    model_path = env_path if os.path.isabs(env_path) else os.path.join(base_dir, env_path)
    labels_path = os.path.join(os.path.dirname(model_path), "class_indices.json")

    if not os.path.exists(model_path):
        logger.error(f"[GROWZEN] Model NOT FOUND: {model_path}")
        import sys; sys.exit(1)

    try:
        import tensorflow as tf
        _model = tf.keras.models.load_model(model_path)

        if os.path.exists(labels_path):
            with open(labels_path, "r") as f:
                raw = json.load(f)
            # Support both list and dict formats
            if isinstance(raw, list):
                _class_labels = {str(i): name for i, name in enumerate(raw)}
            else:
                _class_labels = {str(k): v for k, v in raw.items()}
            logger.info(f"[GROWZEN] class_indices.json loaded: {len(_class_labels)} classes")
        else:
            # Fallback to PlantVillage standard (38-class) in triple-underscore format
            _class_labels = {str(i): c for i, c in enumerate([
                "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___Healthy",
                "Blueberry___Healthy",
                "Cherry___Powdery_mildew", "Cherry___Healthy",
                "Corn___Cercospora_leaf_spot", "Corn___Common_rust", "Corn___Northern_Leaf_Blight", "Corn___Healthy",
                "Grape___Black_rot", "Grape___Esca", "Grape___Leaf_blight", "Grape___Healthy",
                "Orange___Huanglongbing",
                "Peach___Bacterial_spot", "Peach___Healthy",
                "Pepper___Bacterial_spot", "Pepper___Healthy",
                "Potato___Early_blight", "Potato___Late_blight", "Potato___Healthy",
                "Raspberry___Healthy",
                "Soybean___Healthy",
                "Squash___Powdery_mildew",
                "Strawberry___Leaf_scorch", "Strawberry___Healthy",
                "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight",
                "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites",
                "Tomato___Target_Spot", "Tomato___Yellow_Leaf_Curl_Virus", "Tomato___Mosaic_Virus",
                "Tomato___Healthy",
            ])}
            logger.warning("[GROWZEN] class_indices.json NOT FOUND — using built-in fallback labels.")

        logger.info("[GROWZEN] Plant disease model loaded successfully.")
        return _model, _class_labels

    except Exception as e:
        logger.error(f"[GROWZEN] Failed to load model: {e}")
        import sys; sys.exit(1)


# ─── STEP 8: Label Formatting ─────────────────────────────────────────────────
def _parse_label(raw_name: str):
    """
    Convert 'Tomato___Late_blight' →  plant='Tomato', disease='Late Blight'
    Handles single (_), double (__), or triple (___) underscore separators.
    """
    import re
    # Split on triple underscore first, then double, then single
    if "___" in raw_name:
        parts = raw_name.split("___", 1)
    elif "__" in raw_name:
        parts = raw_name.split("__", 1)
    else:
        # Try splitting on first underscore
        parts = raw_name.split("_", 1)

    plant_raw   = parts[0].strip()
    disease_raw = parts[1].strip() if len(parts) > 1 else "Unknown"

    # Clean plant name: strip commas, parentheses, extra words like _bell
    plant_name  = re.sub(r"[,_()\[\]]", " ", plant_raw).split()[0].title()
    # Clean disease name: replace underscores with spaces, capitalize
    disease_name = re.sub(r"_+", " ", disease_raw).strip().title()

    return plant_name, disease_name


# ─── STEP 5: Preprocessing ─────────────────────────────────────────────────────
def _preprocess(image_path: str):
    """
    EXACTLY match training: PIL Image, convert to RGB (removes Alpha),
    resize 224x224, and apply MobileNetV2 Native Preprocessing.
    Returns (img_array, img_batch) or (None, None) on failure.
    """
    try:
        from PIL import Image
        import numpy as np
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        
        # 1. Ensure input image is ALWAYS RGB
        image = Image.open(image_path).convert("RGB")
        
        # 3. Ensure correct pipeline: resize
        image = image.resize((224, 224))
        
        # Convert to numpy array
        img_array = np.array(image, dtype=np.float32)
        
        # Expand dims (batch)
        img_batch = np.expand_dims(img_array, axis=0)
        
        # Apply preprocess_input (DO NOT use img / 255.0)
        img_batch = preprocess_input(img_batch)
        
        return img_array, img_batch
    except Exception as e:
        logger.error(f"[GROWZEN DEBUG] Preprocessing error: {e}")
        return None, None


# ─── STEP 11: Treatment Lookup ────────────────────────────────────────────────
_TREATMENTS = {
    "early blight":   "Remove infected leaves. Apply copper-based fungicide. Avoid overhead watering. Improve air circulation.",
    "late blight":    "Remove infected foliage immediately. Apply mancozeb or chlorothalonil fungicide. Ensure good drainage.",
    "leaf mold":      "Improve ventilation. Apply copper or sulphur fungicide. Reduce humidity.",
    "bacterial spot": "Remove infected leaves. Apply copper-based bactericide. Avoid working with wet plants.",
    "septoria":       "Remove infected leaves. Apply chlorothalonil. Mulch around base to prevent soil splash.",
    "spider mites":   "Apply neem oil or insecticidal soap. Increase air humidity. Remove heavily infested leaves.",
    "target spot":    "Apply copper fungicide. Remove infected tissue. Improve air circulation.",
    "mosaic virus":   "Remove infected plants. Control aphid vectors. No chemical cure — prevent spread.",
    "yellow leaf curl": "Control whitefly population. Remove infected plants. Use reflective mulches.",
    "powdery mildew": "Apply potassium bicarbonate or sulfur spray. Improve air circulation.",
    "black rot":      "Remove infected tissue. Apply copper fungicide. Avoid overhead irrigation.",
    "healthy":        "Plant appears healthy. Maintain regular watering schedule and ensure adequate sunlight.",
}

def _get_treatment(disease_name: str) -> str:
    dn = disease_name.lower()
    for key, text in _TREATMENTS.items():
        if key in dn:
            return text
    return "Monitor plant health. Ensure proper watering, sunlight, and nutrition."


# ─── STEP 10: Health Score ────────────────────────────────────────────────────
def _calc_health(confidence: float, is_healthy: bool) -> int:
    """
    Spec-compliant formula:
      Diseased: health = 100 - confidence  (e.g. 94% confident disease → 6% health)
      Healthy:  health = confidence         (e.g. 92% confident healthy → 92% health)
    Both values are clamped to [0, 100].
    """
    if is_healthy:
        return max(0, min(100, int(confidence)))
    else:
        return max(0, min(100, 100 - int(confidence)))


# ─── MAIN ENTRY: analyze_leaf_disease ────────────────────────────────────────
def analyze_leaf_disease(image_path: str, expected_plant: str = None) -> dict:
    """
    Full disease analysis pipeline.
    STEP 6: NEVER blocks — always returns a prediction.
    STEP 12: Returns plant_name, disease_name, confidence, status.
    STEP 11: Detailed debug logging.
    """
    logger.info(f"[GROWZEN DEBUG] Image received: {image_path}")

    model, labels = load_plant_village_model()

    if model is None or labels is None:
        return _error_result("Model not loaded")

    # ─ Preprocess ──────────────────────────────────────────────────────────────
    img_array, img_batch = _preprocess(image_path)

    if img_array is None:
        logger.error(f"[GROWZEN DEBUG] Failed to read image: {image_path}")
        return _error_result(f"Cannot read image file: {image_path}")

    if np.all(img_array == 0):
        logger.warning("[GROWZEN DEBUG] Image is completely black — but continuing prediction anyway.")
        # STEP 6: Still run prediction, don't block

    logger.info(f"[GROWZEN DEBUG] Image processed successfully: shape={img_array.shape}")
    logger.info(f"[GROWZEN DEBUG] Pixel range before model: min={np.min(img_array)}, max={np.max(img_array)}")

    # ─ Predict ─────────────────────────────────────────────────────────────────
    try:
        print(f"[DEBUG] Image shape before prediction: {img_batch.shape}")
        preds = model.predict(img_batch, verbose=0)[0]
        print(f"[DEBUG] Prediction probabilities: {preds.tolist()}")
    except Exception as e:
        logger.error(f"[GROWZEN DEBUG] Model prediction error: {e}")
        return _error_result(f"Prediction failed: {e}")

    class_idx   = int(np.argmax(preds))
    print(f"[DEBUG] Predicted class index: {class_idx}")
    probability = float(preds[class_idx])
    confidence  = round(probability * 100, 2)

    raw_name = labels.get(str(class_idx), labels.get(class_idx, "Unknown___Unknown"))

    # STEP 8: DEBUG OUTPUT
    logger.info(f"[GROWZEN DEBUG] Prediction vector array: {preds.tolist()}")
    logger.info(f"[GROWZEN DEBUG] Prediction index: {class_idx}")
    logger.info(f"[GROWZEN DEBUG] Raw label / Predicted class: {raw_name}")
    logger.info(f"[GROWZEN DEBUG] Confidence: {confidence}%")

    # Top-3 for diagnostics
    top3_idx = np.argsort(preds)[::-1][:3]
    top3 = [(labels.get(str(i), str(i)), round(float(preds[i])*100, 2)) for i in top3_idx]
    logger.info(f"[GROWZEN DEBUG] Top-3: {top3}")

    # ─ STEP 8: Parse label ─────────────────────────────────────────────────────
    plant_name, disease_name = _parse_label(raw_name)

    # STRICT MODE: The system MUST detect the plant itself. No DB overrides.
    final_plant = plant_name

    logger.info(f"[GROWZEN DEBUG] Extracted plant: {final_plant}")
    logger.info(f"[GROWZEN DEBUG] Extracted disease: {disease_name}")

    # ─ STEP 7: Status logic (NEVER uncertain for valid images) ─────────────────
    is_healthy = "healthy" in disease_name.lower()

    # STEP 6: NO confidence-based blocking. Always return a result.
    if is_healthy:
        status = "Healthy"
    else:
        status = "Diseased"

    health_score = _calc_health(confidence, is_healthy)
    treatment    = _get_treatment(disease_name)

    if health_score >= 80:
        severity = "low"
    elif health_score >= 50:
        severity = "medium"
    else:
        severity = "high"

    # ─ STEP 11: Final debug print ───────────────────────────────────────────────
    print("=" * 50)
    print(f"[GROWZEN] Detection Result")
    print(f"  Image:      {image_path}")
    print(f"  Index:      {class_idx}")
    print(f"  Raw Label:  {raw_name}")
    print(f"  Plant:      {final_plant}")
    print(f"  Disease:    {disease_name}")
    print(f"  Confidence: {confidence}%")
    print(f"  Status:     {status}")
    print(f"  Health:     {health_score}")
    print(f"  Top-3:      {top3}")
    print("=" * 50)

    # ─ STEP 12: Final output format ────────────────────────────────────────────
    return {
        # Primary fields (STEP 12)
        "plant_name":   final_plant,
        "disease_name": disease_name,
        "confidence":   confidence,
        "status":       status,

        # Aliases for backward compatibility
        "plant":        final_plant,
        "disease":      disease_name,
        "detected_plant": final_plant,
        "raw_disease":  disease_name,
        "raw_label":    raw_name,

        # Health & severity
        "health_score": health_score,
        "healthScore":  health_score,
        "severity":     severity,
        "is_healthy":   is_healthy,
        "treatment":    treatment,

        # Probability as 0-100 int
        "probability":  int(confidence),

        # Follow-up questions
        "ai_follow_up_questions": [
            "When did you first notice this issue?",
            "Is the plant indoors or outdoors?",
            "How often do you water? (daily/weekly)",
            "Describe the leaf condition (yellowing, spots, wilting, etc.)",
        ]
    }


def _error_result(msg: str) -> dict:
    """Return a safe error response that never blocks the pipeline."""
    logger.error(f"[GROWZEN] Error result: {msg}")
    return {
        "plant_name":   "Unknown",
        "disease_name": "Detection Failed",
        "confidence":   0.0,
        "status":       "Uncertain",
        "disease":      "Detection Failed",
        "plant":        "Unknown",
        "health_score": 0,
        "healthScore":  0,
        "severity":     "none",
        "is_healthy":   True,
        "treatment":    "Please retry with a clear, well-lit photo of a single leaf.",
        "probability":  0,
        "error":        msg,
        "ai_follow_up_questions": []
    }
