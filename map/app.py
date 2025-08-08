from flask import Flask, render_template, request, jsonify
import openrouteservice
from dotenv import load_dotenv
import os

load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")

if not ORS_API_KEY:
    raise ValueError("ORS_API_KEY not found in .env file")

app = Flask(__name__)

client = openrouteservice.Client(key=ORS_API_KEY)

START = (77.0823103, 28.6076646)   # 28.6076646,77.0823103

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/route", methods=["POST"])
def get_route():
    data = request.json
    dest_lat = data.get("lat")
    dest_lng = data.get("lng")

    if not dest_lat or not dest_lng:
        return jsonify({"error": "Invalid destination"}), 400

    DEST = (dest_lng, dest_lat) 

    try:
        route = client.directions(
            coordinates=[START, DEST],
            profile='driving-car',
            format='geojson'
        )

        coords = [(lat, lng) for lng, lat in route['features'][0]['geometry']['coordinates']]
        summary = route['features'][0]['properties']['summary']
        distance_m = summary['distance']

        speed_kmh = 50
        distance_km = distance_m / 1000
        duration_hr = distance_km / speed_kmh
        duration_min = round(duration_hr * 60)

        return jsonify({
            "path": coords,
            "duration_min": duration_min,
            "distance_km": round(distance_km, 2)
        })

    except Exception as e:
        print("Routing error:", e)
        return jsonify({"error": "Route calculation failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)
