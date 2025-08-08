import serial
import struct
import time
import matplotlib.pyplot as plt
import math

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=1)

def read_lidar_data():
    while True:
        raw = ser.read(9)
        if len(raw) < 9:
            continue
        try:
            start_flag = raw[0]
            if start_flag == 0xFA:
                angle = raw[1]
                dist = struct.unpack("<H", raw[2:4])[0] / 4.0
                print(f"Angle: {angle}°, Distance: {dist} mm")
        except Exception as e:
            print("Parse error:", e)

def realtime_plot():
    plt.ion()
    fig, ax = plt.subplots()
    scatter = ax.scatter([], [])
    ax.set_xlim(-5000, 5000)
    ax.set_ylim(-5000, 5000)
    ax.set_title("Real-Time LIDAR Scan")

    while True:
        raw = ser.read(9)
        if len(raw) < 9:
            continue

        try:
            start_flag = raw[0]
            if start_flag == 0xFA:
                angle = raw[1] * 1.0
                dist = struct.unpack("<H", raw[2:4])[0] / 4.0

                x = dist * 0.1 * (math.cos(math.radians(angle)))
                y = dist * 0.1 * (math.sin(math.radians(angle)))

                scatter.set_offsets([[x, y]])
                plt.draw()
                plt.pause(0.01)
        except:
            continue

if __name__ == "__main__":
    try:
        print("Starting LIDAR read...")
        read_lidar_data()
    except KeyboardInterrupt:
        print("Stopping LIDAR...")
        ser.close()
