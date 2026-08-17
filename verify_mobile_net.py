import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'digital-plant-assistant', 'backend'))

import services.diseaseDetection.plantVillageModel as pvm
from services.diseaseDetection.plantVillageModel import analyze_leaf_disease
import json
import random

print(f"DEBUG: Importing plantVillageModel from: {pvm.__file__}")

def verify():
    dataset_base = os.path.join(os.getcwd(), 'ai', 'plant-disease-model', 'dataset', 'PlantVillage', 'PlantVillage')
    
    # Pick a random image from the dataset for testing
    classes = [d for d in os.listdir(dataset_base) if os.path.isdir(os.path.join(dataset_base, d))]
    random_class = random.choice(classes)
    class_path = os.path.join(dataset_base, random_class)
    random_img = random.choice(os.listdir(class_path))
    test_img_path = os.path.join(class_path, random_img)
    
    print(f"Testing on class: {random_class}")
    print(f"Image: {test_img_path}")
    
    # Run analysis
    result = analyze_leaf_disease(test_img_path)
    
    print("\n--- Result ---")
    print(json.dumps(result, indent=2))
    
    # Basic assertions
    assert "disease" in result
    assert "confidence" in result
    assert "severity" in result
    assert "treatment" in result
    
    print("\nVerification Successful!")

if __name__ == "__main__":
    verify()
