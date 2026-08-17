import requests
import traceback
import sys
import json
import os

def test_diagnosis():
    # Remove old log if exists
    if os.path.exists("backend_debug_logs.txt"):
        os.remove("backend_debug_logs.txt")
        
    session = requests.Session()
    session.post("http://127.0.0.1:5000/api/auth/register", json={
        "username": "testuser",
        "password": "testpassword",
        "email": "test@test.com"
    })
        
    res = session.post("http://127.0.0.1:5000/api/auth/login", json={
        "username": "testuser",
        "password": "testpassword"
    })
    
    res = session.get("http://127.0.0.1:5000/api/auth/me")
    if res.status_code == 200:
        user_id = res.json().get("user_id")
    else:
        user_id = 1
    
    res = session.post("http://127.0.0.1:5000/api/plants", json={
        "user_id": user_id,
        "name": "Dummy Test Plant",
        "scientific_name": "Testus plantus",
        "location": "Indoor",
        "sunlight": "Direct",
        "water_frequency": 7,
        "health_status": "Healthy"
    })
    if res.status_code != 201:
        print("Failed to create plant.")
        return
        
    plant_data = res.json()
    plant_id = plant_data.get("id") or plant_data.get("plant_id")
        
    import cv2
    import numpy as np
    
    noise = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    cv2.imwrite("noisy_leaf.jpg", noise)
    
    OUT = []
    def log(msg):
        OUT.append(msg)
        
    log("\n=== FRONTEND ===")
    log(f"[STEP 1] Button Clicked:\n- plantId: {plant_id}\n- imageUrl: noisy_leaf.jpg\n")
    
    image_size = os.path.getsize("noisy_leaf.jpg")
    log(f'[STEP 2] API Request Payload:\n- {{\n  "plantId": "{plant_id}",\n  "image": "noisy_leaf.jpg",\n  "size": {image_size}\n}}\n')

    with open("noisy_leaf.jpg", "rb") as f:
        files = {"image": f}
        res = session.post(f"http://127.0.0.1:5000/api/detect-disease/{plant_id}", files=files)
        
    try:
        data = res.json()
        log(f"[STEP 3] API Response:\n- {json.dumps(data, indent=2)}\n")
        
        # Mapped values just like frontend does
        p = data.get("plant", {})
        mappedSpecies = p.get("scientific", p.get("species", "MISSING"))
        mappedHealth = p.get("health_score", "MISSING")
        mappedLastScan = p.get("last_scanned", "MISSING")
        confidence = p.get("confidence", "MISSING")
        
        log(f"[STEP 4] Mapped Values:\n- species: {mappedSpecies}\n- healthScore: {mappedHealth}\n- aiConfidence: {confidence}\n- lastScan: {mappedLastScan}\n")
        
    except Exception:
        log(f"[STEP 3] API Response:\n- MISSING (API Failed: {res.status_code})")
        
    # Read backend logs
    if os.path.exists("backend_debug_logs.txt"):
        with open("backend_debug_logs.txt", "r") as f:
            log(f.read().strip())
    else:
        log("\n=== BACKEND ===")
        log("MISSING (Check server logs)")
        
    with open("trace_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(OUT))

if __name__ == "__main__":
    test_diagnosis()
