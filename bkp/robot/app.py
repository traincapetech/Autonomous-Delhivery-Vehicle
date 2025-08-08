from flask import Flask, render_template, request, redirect, url_for, jsonify
import platform
import socket
import subprocess
import sys, os
import psutil  # For battery info
from pymongo.errors import DuplicateKeyError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import users_col, vendors_col, robots_col, orders_col, admins_col

app = Flask(__name__)

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
        "device_id": "",
        "os": platform.system(),
        "os_version": platform.version(),
        "mac_address": mac_from_ip(ip_address),
        "ip_address": ip_address,
    }

@app.route('/')
def home():
    device_info = get_device_info()

    # First try to find robot by MAC or IP
    robot = robots_col.find_one({
        "$or": [
            {"mac_address": device_info["mac_address"]},
            {"ip_address": device_info["ip_address"]}
        ]
    })

    if robot:
        return render_template("waiting.html", device_info=robot)
    else:
        return render_template("home.html", device_info=device_info)


@app.route('/battery')
def battery():
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent
        charging = battery.power_plugged
        return jsonify({
            "percent": percent,
            "charging": charging,
            "warning": percent < 30 and not charging
        })
    return jsonify({"error": "Battery info not available"}), 500

@app.route('/register', methods=['POST'])
def register():
    device_id = request.form.get('device_id', '').strip()
    os_name = request.form.get('os', '').strip()
    os_version = request.form.get('os_version', '').strip()
    mac_address = request.form.get('mac_address', '').strip()
    ip_address = request.form.get('ip_address', '').strip()
    latitude = request.form.get('latitude', '').strip()
    longitude = request.form.get('longitude', '').strip()
    battery_percent = request.form.get('battery_percent', '').strip()

    if not device_id:
        return "Device ID is required", 400

    robot_data = {
        "device_id": device_id,
        "os": os_name,
        "os_version": os_version,
        "mac_address": mac_address,
        "ip_address": ip_address,
        "latitude": latitude,
        "longitude": longitude,
        "battery_percent": battery_percent,
    }

    try:
        robots_col.update_one(
            {"device_id": device_id},
            {"$set": robot_data},
            upsert=True
        )
    except DuplicateKeyError:
        return "Device already registered", 400
    except Exception as e:
        return f"Database error: {str(e)}", 500

    return redirect(url_for('thank_you'))


@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    try:
        robots_col.create_index([("device_id", 1)], unique=True)
    except Exception as e:
        print(f"Index creation error: {e}")

    app.run(host='0.0.0.0', port=5000, debug=True)
