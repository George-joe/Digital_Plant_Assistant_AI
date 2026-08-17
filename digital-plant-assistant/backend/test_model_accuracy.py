import os
import json
import numpy as np
import tensorflow as tf
import cv2
import sys

# --- CONFIGURATION ---
DATASET_PATH = r"c:\Users\gkatt\Downloads\digital-plant-assistant-ai\ai\plant-disease-model\dataset\PlantVillage\PlantVillage"
MODEL_PATH = r"c:\Users\gkatt\Downloads\digital-plant-assistant-ai\ai\plant-disease-model\model\plant_disease_model.keras"
LABELS_PATH = r"c:\Users\gkatt\Downloads\digital-plant-assistant-ai\ai\plant-disease-model\model\class_indices.json"

def load_data():
    """Load class mapping and model."""
    print(f"Loading Model from: {MODEL_PATH}")
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        sys.exit(1)
    
    model = tf.keras.models.load_model(MODEL_PATH)
    
    print(f"Loading Labels from: {LABELS_PATH}")
    with open(LABELS_PATH, 'r') as f:
        raw_labels = json.load(f)
        if isinstance(raw_labels, list):
            class_map = {i: label for i, label in enumerate(raw_labels)}
        else:
            class_map = {int(k): v for k, v in raw_labels.items()}
            
    return model, class_map

def preprocess_image(image_path):
    """Resize to 224x224 and normalize to 1/255."""
    img = cv2.imread(image_path)
    if img is None:
        return None
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    img = img.astype('float32') / 255.0
    return np.expand_dims(img, axis=0)

def run_tests():
    model, class_map = load_data()
    
    classes = [d for d in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, d))]
    # Filter out common non-dataset folders if any
    classes = [c for c in classes if "PlantVillage" not in c]
    
    print(f"\nFound {len(classes)} classes in dataset.\nStarting validation...\n")
    
    total_tested = 0
    correct_count = 0
    mismatches = []
    
    for expected_label in classes:
        class_folder = os.path.join(DATASET_PATH, expected_label)
        images = [f for f in os.listdir(class_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not images:
            print(f"Warning: No images found for class {expected_label}")
            continue
            
        # Pick the first image
        image_name = images[0]
        image_path = os.path.join(class_folder, image_name)
        
        # Preprocess and Predict
        img_array = preprocess_image(image_path)
        if img_array is None:
            print(f"Error reading image: {image_path}")
            continue
            
        preds = model.predict(img_array, verbose=0)
        pred_idx = np.argmax(preds[0])
        predicted_label = class_map.get(pred_idx, "Unknown")
        confidence = np.max(preds[0]) * 100
        
        is_correct = predicted_label == expected_label
        status = "✅ CORRECT" if is_correct else "❌ WRONG"
        
        if is_correct:
            correct_count += 1
        else:
            mismatches.append({
                "expected": expected_label,
                "predicted": predicted_label,
                "confidence": confidence
            })
            
        total_tested += 1
        
        print("-" * 50)
        print(f"Image: {image_name}")
        print(f"Expected:  {expected_label}")
        print(f"Predicted: {predicted_label}")
        print(f"Confidence: {confidence:.1f}%")
        print(f"Status: {status}")

    # FINAL REPORT
    print("\n" + "=" * 50)
    print("                FINAL ACCURACY REPORT")
    print("=" * 50)
    print(f"Total Classes Tested: {total_tested}")
    print(f"Correct Predictions:  {correct_count}")
    print(f"Wrong Predictions:    {total_tested - correct_count}")
    
    accuracy = (correct_count / total_tested) * 100 if total_tested > 0 else 0
    print(f"Accuracy Score:       {accuracy:.2f}%")
    print("=" * 50)
    
    if mismatches:
        print("\nMISMATCH DETAILS (Confusion Cases):")
        for m in mismatches:
            print(f"- Expected [{m['expected']}] but predicted [{m['predicted']}] ({m['confidence']:.1f}% conf)")
    else:
        print("\nPerfect scores! No mismatches found.")
    print("-" * 50)

if __name__ == "__main__":
    run_tests()
