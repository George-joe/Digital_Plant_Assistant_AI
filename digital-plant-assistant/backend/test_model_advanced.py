import os
import json
import numpy as np
import tensorflow as tf
import cv2
import sys

# --- CONFIGURATION PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Navigate up two levels from backend to reach digital-plant-assistant-ai root
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DATASET_PATH = os.path.join(ROOT_DIR, "ai", "plant-disease-model", "dataset", "PlantVillage", "PlantVillage")
MODEL_PATH = os.path.join(ROOT_DIR, "ai", "plant-disease-model", "model", "plant_disease_model.keras")
LABELS_PATH = os.path.join(ROOT_DIR, "ai", "plant-disease-model", "model", "class_indices.json")

# Number of images to test per class

IMAGES_PER_CLASS = 3

def load_data():
    """STEP 2: Load model and mapping"""
    print(f"Loading Model from: {MODEL_PATH}")
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        sys.exit(1)
        
    model = tf.keras.models.load_model(MODEL_PATH)
    
    with open(LABELS_PATH, 'r') as f:
        raw_labels = json.load(f)
        if isinstance(raw_labels, list):
            class_map = {i: label for i, label in enumerate(raw_labels)}
        else:
            class_map = {int(k): v for k, v in raw_labels.items()}
            
    return model, class_map

def preprocess_image(image_path):
    """STEP 3: Read, convert, resize, normalize, add batch dim"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    img = img.astype('float32') / 255.0
    return np.expand_dims(img, axis=0)

def extract_plant_name(label):
    """Extract plant name robustly despite inconsistent underscores."""
    label_lower = label.lower()
    if label_lower.startswith("tomato"): return "Tomato"
    if label_lower.startswith("potato"): return "Potato"
    if label_lower.startswith("pepper"): return "Pepper"
    
    # Fallback to standard split if unknown
    if "___" in label:
        return label.split("___")[0]
    return label.split("_")[0]

def validate_model():
    model, class_map = load_data()
    
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        sys.exit(1)
        
    classes = [d for d in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, d))]
    print(f"\nFound {len(classes)} classes in dataset.")
    print(f"Testing up to {IMAGES_PER_CLASS} image(s) per class...\n")
    
    total_tested = 0
    correct_disease = 0
    correct_plant = 0
    mismatches = []
    
    for expected_label in classes:
        class_folder = os.path.join(DATASET_PATH, expected_label)
        images = [f for f in os.listdir(class_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not images:
            continue
            
        # Select up to IMAGES_PER_CLASS
        selected_images = images[:IMAGES_PER_CLASS]
        
        for image_name in selected_images:
            image_path = os.path.join(class_folder, image_name)
            
            img_array = preprocess_image(image_path)
            if img_array is None:
                continue
                
            # STEP 4: PREDICTION
            preds = model.predict(img_array, verbose=0)
            pred_idx = np.argmax(preds[0])
            predicted_label = class_map.get(pred_idx, "Unknown")
            confidence = np.max(preds[0]) * 100
            
            # STEP 5: VALIDATION LOGIC
            expected_plant = extract_plant_name(expected_label)
            predicted_plant = extract_plant_name(predicted_label)
            
            plant_match = expected_plant == predicted_plant
            disease_match = expected_label == predicted_label
            
            if plant_match:
                correct_plant += 1
            if disease_match:
                correct_disease += 1
                
            total_tested += 1
            
            warnings = []
            if not plant_match:
                warnings.append("⚠️ Cross-plant error detected!")
            if not disease_match and confidence > 80:
                warnings.append("⚠️ HIGH CONFIDENCE ERROR")
                
            if not disease_match:
                mismatches.append({
                    "expected": expected_label,
                    "predicted": predicted_label,
                    "confidence": confidence,
                    "warnings": warnings,
                    "image": image_name
                })
                
            # STEP 6: OUTPUT FORMAT
            print("-" * 50)
            print(f"Image: {image_path}")
            print(f"Expected: {expected_label}")
            print(f"Predicted: {predicted_label}")
            print(f"Confidence: {confidence:.2f}%")
            print(f"Plant Match: {'✅' if plant_match else '❌'}")
            print(f"Disease Match: {'✅' if disease_match else '❌'}")
            if warnings:
                print("Warnings:")
                for w in warnings:
                    print(f"    - {w}")

    # STEP 7: FINAL METRICS
    print("\n" + "=" * 50)
    print("                FINAL ACCURACY REPORT")
    print("=" * 50)
    print(f"Total Classes in Dataset: {len(classes)}")
    print(f"Total Images Tested:      {total_tested}")
    print(f"Correct Plant Matches:    {correct_plant}")
    print(f"Correct Disease Matches:  {correct_disease}")
    print(f"Wrong Predictions:        {total_tested - correct_disease}")
    
    plant_acc = (correct_plant / total_tested) * 100 if total_tested > 0 else 0
    disease_acc = (correct_disease / total_tested) * 100 if total_tested > 0 else 0
    
    print(f"\nPlant Accuracy:   {plant_acc:.2f}%")
    print(f"Disease Accuracy: {disease_acc:.2f}%")
    print(f"Overall Accuracy: {disease_acc:.2f}%")
    print("=" * 50)
    
    # STEP 8: CONFUSION REPORT
    if mismatches:
        print("\nMISMATCH DETAILS (Confusion Cases):")
        # Group by expected class for readability
        for expected in classes:
            class_mismatches = [m for m in mismatches if m['expected'] == expected]
            if class_mismatches:
                print(f"\n[ {expected} ]")
                for m in class_mismatches:
                    print(f"  ❌ Predicted: {m['predicted']} | Confidence: {m['confidence']:.2f}%")
                    for w in m['warnings']:
                        print(f"      {w}")
    else:
        print("\n🎉 Perfect scores! No mismatches found.")
    print("-" * 50)

if __name__ == "__main__":
    validate_model()
