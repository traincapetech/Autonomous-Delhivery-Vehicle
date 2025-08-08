# delivery_bot_system/user/user_app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone
from bson import ObjectId
import random, socket, platform, os

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import users_col, products_col, orders_col

app = Flask(__name__, template_folder="templates")
app.secret_key = "supersecretkey"  # Change in production
bcrypt = Bcrypt(app)


# ---------- Helpers ----------
def get_device_info():
    return {
        "device": platform.node(),
        "os": platform.system() + " " + platform.release(),
        "app_version": "1.0.0"
    }

def get_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


# ---------- Routes ----------

@app.route('/')
def user_home():
    # Require login
    if "username" not in session:
        return redirect(url_for('login_user'))

    products = list(products_col.find({}))
    for p in products:
        p["_id"] = str(p["_id"])
    return render_template('user_home.html',
                           products=products,
                           username=session["username"])


# Registration
@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        data = request.form

        if users_col.find_one({"username": data['username']}):
            return "Username already exists", 400

        hashed_pw = bcrypt.generate_password_hash(data['password']).decode()

        user = {
            "name": data['name'],
            "username": data['username'],
            "email": data['email'],
            "password": hashed_pw,
            "contact_no": data['contact_no'],
            "dob": data['dob'],
            "device_info": get_device_info(),
            "location": {},
            "browsing_history": [],
            "past_purchases": [],
            "created_at": datetime.now(timezone.utc)
        }

        users_col.insert_one(user)
        return redirect(url_for('login_user'))

    return render_template('user_register.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        data = request.form
        user = users_col.find_one({"username": data['username']})

        if not user or not bcrypt.check_password_hash(user['password'], data['password']):
            return "Invalid username or password", 401

        # Save login session
        session["username"] = user["username"]
        session["user_id"] = str(user["_id"])
        return redirect(url_for('user_home'))

    return render_template('user_login.html')


# Logout
@app.route('/logout')
def logout_user():
    session.clear()
    return redirect(url_for('login_user'))


# Place order
@app.route('/order', methods=['POST'])
def place_order():
    if "user_id" not in session:
        return redirect(url_for('login_user'))

    data = request.form
    otp_user = str(random.randint(100000, 999999))
    otp_vendor = str(random.randint(100000, 999999))
    eta_minutes = random.randint(15, 30)

    order = {
        "user_id": session["user_id"],
        "vendor_id": data['vendor_id'],
        "product_id": data['product_id'],
        "quantity": data['quantity'],
        "delivery_address": data['delivery_address'],
        "latitude": data.get('latitude'),
        "longitude": data.get('longitude'),
        "ip_address": get_ip(),
        "device_info": get_device_info(),
        "payment_status": data.get('payment_status', "Paid"),
        "payment_method": data.get('payment_method', "UPI"),
        "discount": data.get('discount', 0),
        "invoice": "INV-" + str(random.randint(1000, 9999)),
        "otp_user": otp_user,
        "otp_vendor": otp_vendor,
        "status": "Processing",
        "timestamp": datetime.now(timezone.utc)
    }

    result = orders_col.insert_one(order)

    return render_template('user_order.html',
                           otp_user=otp_user,
                           eta=f"{eta_minutes} minutes",
                           order_id=str(result.inserted_id))


if __name__ == "__main__":
    app.run(port=5001, debug=True)
