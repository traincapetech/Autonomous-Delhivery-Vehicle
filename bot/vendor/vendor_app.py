from flask import Flask, request, render_template, redirect, url_for, session
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone
import os, sys, bcrypt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import users_col, vendors_col, robots_col, orders_col, admins_col

import os

app = Flask(__name__)
app.secret_key = "super_secret_key"
bcrypt = Bcrypt(app)


def current_time_ist():
    utc_time = datetime.now(timezone.utc)
    ist_offset = 5.5
    ist_time = utc_time.timestamp() + (ist_offset * 3600)
    return datetime.fromtimestamp(ist_time).strftime("%Y-%m-%d %H:%M:%S")


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form

        if vendors_col.find_one({"username": data.get("username")}):
            return render_template("vendor_register.html", error="Username already exists")
        if vendors_col.find_one({"email": data.get("email")}):
            return render_template("vendor_register.html", error="Email already exists")

        hashed_pw = bcrypt.generate_password_hash(data.get("password")).decode()

        vendor = {
            "name": data.get("name"),
            "username": data.get("username"),
            "email": data.get("email"),
            "password": hashed_pw,
            "contact_no": data.get("contact_no"),
            "dob": data.get("dob"),
            "store_name": data.get("store_name"),
            "store_location": {
                "lat": float(data.get('lat', 0)),
                "lon": float(data.get('lon', 0)),
                "address": data.get('address', "")
            },
            "device_info": {
                "device": data.get('device', ""),
                "os": data.get('os', ""),
                "app_version": data.get('app_version', "")
            },
            "created_at": current_time_ist()
        }

        vendors_col.insert_one(vendor)
        return redirect(url_for('login'))

    return render_template("vendor_register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        vendor = vendors_col.find_one({"username": data.get("username")})

        if not vendor or not bcrypt.check_password_hash(vendor['password'], data.get("password", "")):
            return render_template("vendor_login.html", error="Invalid credentials")

        session['vendor'] = {
            "username": vendor["username"],
            "vendor_id": str(vendor["_id"])
        }
        return redirect(url_for('dashboard'))

    return render_template("vendor_login.html")


@app.route('/logout')
def logout():
    session.pop('vendor', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'vendor' not in session:
        return redirect(url_for('login'))

    vendor_id = session['vendor']['vendor_id']
    products = list(products_col.find({"vendor_id": vendor_id}))
    return render_template("vendor_dashboard.html", products=products)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'vendor' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form
        vendor_id = session['vendor']['vendor_id']

        product = {
            "vendor_id": vendor_id,
            "name": data.get("name"),
            "quantity": int(data.get("quantity", 0)),
            "unit": data.get("unit"),
            "price": float(data.get("price", 0)),
            "expiry_date": data.get("expiry_date"),
            "return_policy": data.get("return_policy"),
            "manufacturer_details": data.get("manufacturer_details"),
            "marketer_details": data.get("marketer_details"),
            "country_of_origin": data.get("country_of_origin"),
            "customer_care": data.get("customer_care"),
            "disclaimer": data.get("disclaimer"),
            "store_location": {
                "lat": float(data.get('lat', 0)),
                "lon": float(data.get('lon', 0)),
                "address": data.get('address', "")
            },
            "device_info": {
                "device": data.get('device', ""),
                "os": data.get('os', ""),
                "app_version": data.get('app_version', "")
            },
            "image": data.get('image', None),
            "timestamp": current_time_ist()
        }

        products_col.insert_one(product)
        return redirect(url_for('dashboard'))

    return render_template("add_product.html")


if __name__ == '__main__':
    app.run(debug=True)
