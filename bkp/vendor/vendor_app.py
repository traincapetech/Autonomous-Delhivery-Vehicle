from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import vendors_col, products_col

app = Flask(__name__, template_folder="templates")
app.secret_key = "super_secret_key" 
bcrypt = Bcrypt(app)

# --------------------------
# Vendor Registration Page (HTML)
# --------------------------
@app.route('/register_page')
def register_page():
    return render_template('vendor_register.html')

# --------------------------
# Vendor Registration (API)
# --------------------------
@app.route('/register', methods=['POST'])
def register_vendor():
    data = request.form

    # Check duplicates
    if vendors_col.find_one({"username": data['username']}):
        return "Username already exists", 400
    if vendors_col.find_one({"email": data['email']}):
        return "Email already exists", 400

    hashed_pw = bcrypt.generate_password_hash(data['password']).decode()

    vendor = {
        "name": data['name'],
        "username": data['username'],
        "email": data['email'],
        "password": hashed_pw,
        "contact_no": data['contact_no'],
        "dob": data['dob'],
        "store_name": data['store_name'],
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
        "created_at": datetime.now(timezone.utc)
    }

    vendors_col.insert_one(vendor)
    return redirect(url_for('login_page'))


# --------------------------
# Vendor Login Page (HTML)
# --------------------------
@app.route('/login_page')
def login_page():
    return render_template('vendor_login.html')

# --------------------------
# Vendor Login (API)
# --------------------------
@app.route('/login', methods=['POST'])
def login_vendor():
    data = request.form  # from HTML form
    vendor = vendors_col.find_one({"username": data['username']})

    if not vendor or not bcrypt.check_password_hash(vendor['password'], data['password']):
        return "Invalid username or password", 401

    # Store vendor_id in session
    session['vendor_id'] = str(vendor['_id'])
    return redirect(url_for('vendor_home'))

# --------------------------
# Vendor Dashboard (HTML)
# --------------------------
@app.route('/')
def vendor_home():
    if 'vendor_id' not in session:
        return redirect(url_for('login_page'))

    vendor_id = session['vendor_id']
    products = list(products_col.find({"vendor_id": vendor_id}, {"_id": 0}))
    return render_template('vendor_dashboard.html', inventory=products)

# --------------------------
# Add Product Page + API
# --------------------------
@app.route('/add_product_page')
def add_product_page():
    if 'vendor_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('add_product.html')

@app.route('/product', methods=['POST'])
def add_product():
    if 'vendor_id' not in session:
        return "Unauthorized", 403

    data = request.form

    product = {
        "vendor_id": session['vendor_id'],
        "name": data['name'],
        "quantity": int(data['quantity']),
        "unit": data['unit'],
        "price": float(data['price']),
        "expiry_date": data['expiry_date'],
        "return_policy": data['return_policy'],
        "manufacturer_details": data['manufacturer_details'],
        "marketer_details": data['marketer_details'],
        "country_of_origin": data['country_of_origin'],
        "customer_care": data['customer_care'],
        "disclaimer": data['disclaimer'],
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
        "timestamp": datetime.now(timezone.utc)
    }

    products_col.insert_one(product)
    return redirect(url_for('vendor_home'))


if __name__ == "__main__":
    app.run(port=5002, debug=True)
