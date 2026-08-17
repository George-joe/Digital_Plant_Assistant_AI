import requests
import os
import logging

def send_telegram(chat_id, message):
    """
    Sends a message to a Telegram chat using the bot API.
    PART 1 & 2: Verify config and API call with logging.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("Telegram config missing: TELEGRAM_BOT_TOKEN not found.")
        return False
    
    if not chat_id:
        logging.warning("Telegram config missing: chat_id not provided.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    logging.info(f"Sending Telegram message to {chat_id}")
    try:
        response = requests.post(url, json=payload, timeout=10)
        logging.info(f"Telegram response status: {response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"Telegram error: {response.text}")
            
        response.raise_for_status()
        logging.info("Telegram message sent successfully")
        return True
    except Exception as e:
        logging.error(f"Telegram error: {str(e)}")
        # Part 7: Retry logic (internal to send_telegram, or handled by caller)
        try:
            logging.info("Retrying Telegram message send...")
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as retry_e:
            logging.error(f"Retry error sending Telegram: {str(retry_e)}")
            return False
