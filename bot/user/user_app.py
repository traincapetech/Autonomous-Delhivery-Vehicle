from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime, timezone
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import users_col, products_col, orders_col

app = Flask(__name__)
app.secret_key = "supersecretkey" 

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

bcrypt = Bcrypt(app)

def current_time_ist():
    utc_time = datetime.now(timezone.utc)
    ist_offset = 5.5
    ist_time = utc_time.astimezone(timezone.utc).timestamp() + (ist_offset * 3600)
    return datetime.fromtimestamp(ist_time).strftime("%Y-%m-%d %H:%M:%S")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "CUSTOMER").strip()

    if not username or not password or not email:
        return jsonify({"error": "Username, email, and password are required"}), 400

    if users_col.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 409

    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": role,
        "created_at": current_time_ist()
    }

    users_col.insert_one(new_user)
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_col.find_one({"username": username})

    if user and bcrypt.check_password_hash(user["password"], password):
        session["user"] = {
            "username": user["username"],
            "role": user.get("role", "CUSTOMER")
        }
        return jsonify({
            "message": "Login successful",
            "role": user.get("role", "CUSTOMER"),
            "user": session["user"]
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401
    
@app.route("/product/<string:product_id>", methods=["GET"])
def get_product(product_id):
    try:
        product = products_col.find_one({"_id": ObjectId(product_id)})
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(serialize_product(product)), 200
    except Exception as e:
        return jsonify({"error": "Invalid product ID"}), 400

# Helper function to serialize product document
def serialize_product(product):
    return {
        "id": str(product.get("_id")),
        "name": product.get("name", ""),
        "description": product.get("description", ""),
        "image": product.get("image", ""),
        "price": product.get("price", 0),
        "quantity": product.get("quantity", ""),
        "expiry_date": product.get("expiry_date", ""),
        "return_policy": product.get("return_policy", ""),
        "unit": product.get("unit", ""),
        "manufacturer_name_address": product.get("manufacturer_name_address", ""),
        "marketer_name_address": product.get("marketer_name_address", ""),
        "country_of_origin": product.get("country_of_origin", ""),
        "customer_care_details": product.get("customer_care_details", ""),
        "disclaimer": product.get("disclaimer", "")
    }


@app.route("/home", methods=["GET"])
def home():
    try:
        products = list(products_col.find())
        return jsonify([serialize_product(p) for p in products]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/session", methods=["GET"])
def check_session():
    user = session.get("user")
    if user:
        return jsonify({"loggedIn": True, "username": user["username"], "role": user.get("role", "CUSTOMER")})
    return jsonify({"loggedIn": False})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
