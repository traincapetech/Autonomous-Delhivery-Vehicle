### m4G + GPS

import serial
import time
import pynmea2
import requests

SIM7600_PORT = "/dev/ttyS0"
SIM7600_BAUD = 115200

EXT_GPS_PORT = "/dev/ttyAMA1"
EXT_GPS_BAUD = 9600

SERVER_URL = "http://your-server.com/api/update_location"

# Initialize serial connections
sim7600 = serial.Serial(SIM7600_PORT, SIM7600_BAUD, timeout=1)
ext_gps = serial.Serial(EXT_GPS_PORT, EXT_GPS_BAUD, timeout=1)

def send_at(command, delay=1):
    """Send AT command to SIM7600 and return response"""
    sim7600.write((command + '\r\n').encode())
    time.sleep(delay)
    response = sim7600.read(sim7600.in_waiting or 64).decode(errors="ignore")
    return response

def init_sim7600_gps():
    """Enable SIM7600 GPS"""
    print("[SIM7600] Enabling GPS...")
    send_at("AT+CGNSPWR=1", 2)
    send_at("AT+CGNSSEQ=RMC", 1)

def get_sim7600_location():
    resp = send_at("AT+CGNSINF", 1)
    # Format: +CGNSINF: 1,1,20210101123456.000,28.7041,77.1025, ...
    if "+CGNSINF" in resp:
        try:
            parts = resp.split(',')
            fix_status = parts[1]
            if fix_status == '1':
                lat = parts[3]
                lon = parts[4]
                return float(lat), float(lon)
        except Exception:
            pass
    return None, None

def get_external_gps_location():
    try:
        line = ext_gps.readline().decode('ascii', errors='replace')
        if line.startswith('$GPGGA') or line.startswith('$GPRMC'):
            msg = pynmea2.parse(line)
            if msg.latitude and msg.longitude:
                return msg.latitude, msg.longitude
    except Exception:
        pass
    return None, None

def send_to_server(lat, lon, source="SIM7600"):
    payload = {
        "latitude": lat,
        "longitude": lon,
        "source": source,
        "timestamp": time.time()
    }
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=5)
        print(f"[SERVER] Sent: {payload} | Response: {response.status_code}")
    except Exception as e:
        print(f"[SERVER] Error: {e}")

def main():
    print("Initializing modules...")
    init_sim7600_gps()

    while True:
        lat, lon = get_sim7600_location()
        if lat and lon:
            print(f"[SIM7600 GPS] Lat: {lat}, Lon: {lon}")
            send_to_server(lat, lon, "SIM7600")
        else:
            print("[SIM7600 GPS] No fix, trying external GPS...")

            lat, lon = get_external_gps_location()
            if lat and lon:
                print(f"[External GPS] Lat: {lat}, Lon: {lon}")
                send_to_server(lat, lon, "External GPS")
            else:
                print("[External GPS] No fix")

        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")