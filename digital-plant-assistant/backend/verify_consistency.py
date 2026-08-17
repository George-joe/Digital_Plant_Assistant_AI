import requests
import json
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

def test_water_consistency():
    session = requests.Session()
    
    # 1. Login
    print("Logging in...")
    test_email = "test_consistency_new@example.com"
    res = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email,
        "password": "testpassword"
    })
    
    if res.status_code != 200:
        print("Login failed, attempting registration...")
        reg_res = session.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test User",
            "email": test_email,
            "password": "testpassword"
        })
        print(f"Registration response: {reg_res.status_code}")
        
        login_res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "testpassword"
        })
        res = login_res
    
    if res.status_code != 200:
        print(f"Critical: Authentication failed ({res.status_code}): {res.text}")
        return

    login_data = res.json()
    token = login_data.get("access_token")
    user_id = login_data.get("user", {}).get("id")
    
    print(f"Logged in as User ID: {user_id}")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create a plant
    print("Creating a plant...")
    res = session.post(f"{BASE_URL}/api/plants", json={
        "user_id": user_id,
        "name": "Consistency Test Plant",
        "scientific": "Testus",
        "health_score": 80
    }, headers=headers)
    
    plant_resp = res.json()
    plant_id = plant_resp.get("id") or plant_resp.get("plant_id")
    if not plant_id:
        print(f"Failed to create plant: {plant_resp}")
        return
    print(f"Created plant ID: {plant_id}")
    
    # 3. Check initial analytics
    print("Checking initial analytics...")
    res = session.get(f"{BASE_URL}/api/analytics/summary", headers=headers)
    data = res.json()
    initial_history = data.get("watering_history", {}).get("data", [])
    print(f"Initial watering history: {initial_history}")
    
    # 4. Water the plant
    print(f"Watering plant {plant_id}...")
    res = session.post(f"{BASE_URL}/api/plant/{plant_id}/water", headers=headers)
    print(f"Watering response: {res.json()}")
    
    # 5. Check updated analytics
    print("Checking updated analytics...")
    res = session.get(f"{BASE_URL}/api/analytics/summary", headers=headers)
    data = res.json()
    updated_history = data.get("watering_history", {}).get("data", [])
    consistency = data.get("water_consistency")
    
    print(f"Updated watering history: {updated_history}")
    print(f"Water consistency: {consistency}%")
    
    # Today's value (last in the list) should be > 0
    if updated_history and updated_history[-1] > 0:
        print("SUCCESS: Today's watering is included in analytics!")
    else:
        print("FAILED: Today's watering is missing from analytics.")

if __name__ == "__main__":
    test_water_consistency()
