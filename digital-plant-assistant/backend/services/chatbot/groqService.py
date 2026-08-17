import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configure Logging
logger = logging.getLogger(__name__)

# Initialize Groq Client
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

SYSTEM_PROMPT = (
    "You are Growzen AI, a plant care assistant that helps users with plant identification, "
    "plant diseases, watering schedules, soil advice, and gardening tips. "
    "Always respond with helpful plant-care guidance."
)

def generate_chat_response(message, plant_context=None):
    """
    Generate a chatbot response using Groq Llama3.
    """
    if not message:
        logger.warning("generate_chat_response called with empty message")
        return "No message provided."

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        user_content = message
        if plant_context:
            user_content = f"Context: User is asking about their plant: {plant_context}. Message: {message}"
            
        messages.append({"role": "user", "content": user_content})
        
        model_to_use = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        logger.info(f"Sending request to Groq API with model: {model_to_use}")
        completion = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            max_tokens=250,
            temperature=0.7,
            timeout=15.0
        )
        
        if completion.choices and completion.choices[0].message.content:
            response_text = completion.choices[0].message.content
            logger.info("Successfully received response from Groq API")
            return response_text
        
        logger.error("Groq API returned an empty response")
        return "AI service returned an empty response. Please try again."

    except Exception as e:
        error_msg = f"Groq API Error: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Print for terminal debugging
        print(f"!!! GROQ ERROR !!!: {error_msg}")
        return f"AI Error: {str(e)}"

def test_groq_connection():
    """
    Test the connection to Groq API with a simple 'hello' message.
    """
    try:
        logger.info("Testing Groq API connection...")
        model_to_use = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        completion = client.chat.completions.create(
            model=model_to_use,
            messages=[{"role": "user", "content": "Hello, respond with 'OK' if you can hear me."}],
            max_tokens=10
        )
        if completion.choices:
            logger.info("Groq connection test successful.")
            return True, completion.choices[0].message.content
        return False, "No response received"
    except Exception as e:
        logger.error(f"Groq connection test failed: {str(e)}")
        return False, str(e)

def generate_plant_insights(disease_name, treatment):
    """
    Helper to generate additional insights for a detected disease.
    """
    prompt = f"The plant has been diagnosed with {disease_name}. The treatment is {treatment}. Provide 2-3 additional specific gardening tips for this situation."
    return generate_chat_response(prompt)
