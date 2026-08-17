from flask import Blueprint, request, jsonify

weather_bp = Blueprint('weather', __name__)

@weather_bp.route("/api/weather", methods=["GET"])
def weather():
    from services.weather_service import get_weather_data
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if lat and lon:
        data = get_weather_data(float(lat), float(lon))
    else:
        # Default to Bangalore
        data = get_weather_data(12.97, 77.59)
    return jsonify(data)

@weather_bp.route("/api/geocode", methods=["GET"])
def geocode():
    from services.weather_service import get_geocode_data
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "No query provided"}), 400
    return jsonify(get_geocode_data(q))
