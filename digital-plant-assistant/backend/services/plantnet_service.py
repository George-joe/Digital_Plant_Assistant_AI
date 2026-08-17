import logging
import requests
import os

def identify_plant(image_path):
    url = "https://my-api.plantnet.org/v2/identify/all"
    api_key = os.getenv("PLANTNET_API_KEY")
    if not api_key:
        logging.error("PLANTNET_API_KEY is not configured.")
        return {"error": "PlantNet API key missing"}
        
    for attempt in range(2):
        try:
            with open(image_path, "rb") as img:
                res = requests.post(
                    url,
                    params={"api-key": api_key},
                    files={"images": img},
                    data={"organs": "leaf"},
                    timeout=5
                )

            if res.status_code == 401:
                logging.error("PlantNet API: Unauthorized - check API key.")
                return {"error": "PlantNet API: Unauthorized"}
            if res.status_code == 429:
                logging.error("PlantNet API: Rate limit exceeded.")
                return {"error": "PlantNet API: Rate limit reached"}
            if res.status_code != 200:
                logging.error(f"PlantNet API ({url}) failed with status {res.status_code}: {res.text}")
                return {"error": f"PlantNet API Error ({res.status_code})"}

            data = res.json()

            if not data.get("results"):
                return {"error": "No plant detected"}

            return data

        except requests.exceptions.Timeout:
            logging.error(f"PlantNet API network timeout (attempt {attempt+1}).")
            if attempt == 1:
                return {"error": "PlantNet timeout — try again"}
        except requests.exceptions.RequestException as e:
            logging.error(f"PlantNet API network error: {str(e)}")
            return {"error": "PlantNet Network Error"}
        except Exception as e:
            logging.error(f"PlantNet API exception: {str(e)}")
            return {"error": str(e)}
