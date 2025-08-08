from flask import Flask, request, jsonify
import platform
import socket
import subprocess
import sys, os
import psutil  # For battery info
from pymongo.errors import DuplicateKeyError
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import robots_col

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])


# -------------------- Utilities --------------------
def mac_from_ip(ip):
    try:
        arp_output = subprocess.check_output("arp -a", shell=True, encoding='utf-8')
        for line in arp_output.splitlines():
            if ip in line:
                parts = line.split()
                if len(parts) > 3:
                    return parts[3]
    except subprocess.CalledProcessError:
        return "Not Available"
    return "Not Available"

def get_ip_address():
    hostname = socket.gethostname()
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        ip_address = "Not Available"
    return ip_address

def get_device_info():
    ip_address = get_ip_address()
    return {
        "device_id": "",  # Expect this from frontend
        "os": platform.system(),
        "os_version": platform.version(),
        "mac_address": mac_from_ip(ip_address),
        "ip_address": ip_address,
    }


# -------------------- Routes --------------------
@app.route("/", methods=["GET"])
def identify_robot():
    """Check if device is already registered as a robot"""
    device_info = get_device_info()
    robot = robots_col.find_one({
        "$or": [
            {"mac_address": device_info["mac_address"]},
            {"ip_address": device_info["ip_address"]}
        ]
    })

    if robot:
        robot["_id"] = str(robot["_id"])
        return jsonify({"registered": True, "robot": robot}), 200
    else:
        return jsonify({"registered": False, "device_info": device_info}), 200


@app.route("/battery", methods=["GET"])
def battery_status():
    battery = psutil.sensors_battery()
    if battery:
        return jsonify({
            "percent": battery.percent,
            "charging": battery.power_plugged,
            "warning": battery.percent < 30 and not battery.power_plugged
        }), 200
    return jsonify({"error": "Battery info not available"}), 500


@app.route("/register", methods=["POST"])
def register_robot():
    data = request.get_json()

    device_id = data.get("device_id", "").strip()
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400

    robot_data = {
        "device_id": device_id,
        "os": data.get("os", "").strip(),
        "os_version": data.get("os_version", "").strip(),
        "mac_address": data.get("mac_address", "").strip(),
        "ip_address": data.get("ip_address", "").strip(),
        "latitude": data.get("latitude", "").strip(),
        "longitude": data.get("longitude", "").strip(),
        "battery_percent": data.get("battery_percent", "").strip()
    }

    try:
        robots_col.update_one(
            {"device_id": device_id},
            {"$set": robot_data},
            upsert=True
        )
        return jsonify({"message": "Robot registered successfully"}), 201
    except DuplicateKeyError:
        return jsonify({"error": "Device already registered"}), 400
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# -------------------- Main --------------------
if __name__ == '__main__':
    try:
        robots_col.create_index([("device_id", 1)], unique=True)
    except Exception as e:
        print(f"Index creation error: {e}")

    app.run(host='0.0.0.0', port=5000, debug=True)
