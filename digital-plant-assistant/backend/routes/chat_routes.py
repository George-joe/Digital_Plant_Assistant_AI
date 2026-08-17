import logging
from flask import Blueprint, request, jsonify
from services.chatbot.groqService import generate_chat_response

logger = logging.getLogger(__name__)
ai_bp = Blueprint('ai', __name__)


@ai_bp.route("/api/test-ai", methods=["GET"])
def test_ai():
    """Endpoint to verify Groq API connectivity."""
    from services.chatbot.groqService import test_groq_connection
    success, message = test_groq_connection()
    if success:
        return jsonify({"status": "success", "message": "Groq API connected!", "response": message}), 200
    else:
        return jsonify({"status": "error", "message": "Groq API connection failed", "error": message}), 500

@ai_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "message" not in data:
        logger.warning("Empty or invalid chat request received")
        return jsonify({"error": "No message provided"}), 400
    
    message = data.get("message")
    logger.info(f"Chat request received: {message[:50]}...")
    
    try:
        reply = generate_chat_response(message)
        
        # If the reply starts with "AI Error:", we treat it as a service error
        if reply.startswith("AI Error:"):
            logger.error(f"Chat service error: {reply}")
            return jsonify({"reply": reply, "error": "AI service error"}), 503
            
        return jsonify({"reply": reply}), 200
    except Exception as e:
        logger.error(f"Unexpected error in chat route: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
