from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from datetime import datetime, timezone
import sys, os, bcrypt
from functools import wraps

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import users_col, vendors_col, robots_col, orders_col, admins_col

app = Flask(__name__, template_folder="templates")

# Use OS secure random secret key (no hardcoding)
app.secret_key = os.urandom(24)


# -------------------- UTILITIES --------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# -------------------- ROUTES --------------------

@app.route('/')
@login_required
def index():
    # Fetch all collections
    users = list(users_col.find())
    vendors = list(vendors_col.find())
    robots = list(robots_col.find())
    orders = list(orders_col.find())

    # Convert IDs to strings
    for collection in (users, vendors, robots, orders):
        for item in collection:
            item["_id"] = str(item["_id"])

    # Map user/vendor names into orders
    user_map = {str(u["_id"]): u.get("username", "N/A") for u in users}
    vendor_map = {str(v["_id"]): v.get("store_name", "N/A") for v in vendors}

    for order in orders:
        order["user_name"] = user_map.get(order.get("user_id"), "N/A")
        order["vendor_name"] = vendor_map.get(order.get("vendor_id"), "N/A")

    return render_template(
        "admin_dashboard.html",
        admin=session["admin"],
        users=users,
        vendors=vendors,
        robots=robots,
        orders=orders
    )



@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        admin = admins_col.find_one({"username": username})
        if admin and verify_password(password, admin["password"]):
            session["admin"] = username
            return redirect(url_for("index"))
        else:
            return render_template("admin_login.html", error="Invalid username or password")

    return render_template("admin_login.html")


@app.route('/logout')
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# -------------------- FILTERED ORDERS PAGE --------------------

@app.route('/orders_page')
@login_required
def orders_page():
    user_id = request.args.get('user_id')
    vendor_id = request.args.get('vendor_id')

    query = {}
    if user_id:
        query['user_id'] = user_id
    if vendor_id:
        query['vendor_id'] = vendor_id

    orders = list(orders_col.find(query))

    users = {str(u["_id"]): u.get("username", "N/A") for u in users_col.find()}
    vendors = {str(v["_id"]): v.get("store_name", "N/A") for v in vendors_col.find()}

    for order in orders:
        order["_id"] = str(order["_id"])
        order["user_name"] = users.get(order.get("user_id"), "N/A")
        order["vendor_name"] = vendors.get(order.get("vendor_id"), "N/A")

    return render_template("orders_page.html", orders=orders)



# -------------------- ROBOTS ONLINE STATUS API --------------------

@app.route('/robots_status')
@login_required
def robots_status():
    """Returns latest robot status (online/offline, working/free, location, battery)"""
    robots = list(robots_col.find())

    for robot in robots:
        robot["_id"] = str(robot["_id"])  # Mongo ObjectId
        robot["device_id"] = robot.get("device_id", "N/A")

        # Online/offline detection (last_updated within 10 seconds)
        last_update = robot.get("last_updated")
        if last_update:
            time_diff = (datetime.now(timezone.utc) - datetime.fromisoformat(last_update)).total_seconds()
            robot["online"] = time_diff < 10
        else:
            robot["online"] = False

        # Working status: check if robot is assigned to an order
        assigned_order = orders_col.find_one({"assigned_robot": robot["_id"], "status": {"$in": ["Processing", "Assigned"]}})
        if assigned_order:
            robot["working_status"] = f"Working on Order {assigned_order['_id']}"
        else:
            robot["working_status"] = "Free"

    return jsonify(robots)



# -------------------- MAIN --------------------

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5003, debug=True)
