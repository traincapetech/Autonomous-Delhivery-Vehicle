import multiprocessing
from user.user_app import UserApp
from vendor.vendor_app import vendor_app
from robot.robot_app import robot_app
from server.server_app import server_app

def run_user_app():
    UserApp.run(host='0.0.0.0', port=5001, debug=True)

def run_vendor_app():
    vendor_app.run(host='0.0.0.0', port=5002, debug=True)

def run_robot_app():
    robot_app.run(host='0.0.0.0', port=5000, debug=True)

def run_server_app():
    server_app.run(host='0.0.0.0', port=5003, debug=True)

if __name__ == '__main__':
    # Start each Flask app in a separate process
    user_process = multiprocessing.Process(target=run_user_app)
    vendor_process = multiprocessing.Process(target=run_vendor_app)
    robot_process = multiprocessing.Process(target=run_robot_app)
    server_process = multiprocessing.Process(target=run_server_app)

    user_process.start()
    vendor_process.start()
    robot_process.start()
    server_process.start()

    # Wait for processes to finish (optional)
    user_process.join()
    vendor_process.join()
    robot_process.join()
    server_process.join()
