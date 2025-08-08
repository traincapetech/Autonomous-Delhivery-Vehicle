import os
import sys
from bson import ObjectId
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from flask import request, session, redirect, url_for
from werkzeug.security import generate_password_hash
from flask import Flask, request, render_template, redirect, url_for, session, flash

VENDOR_PHOTO_FOLDER = os.path.join("static", "uploads", "profile")
STORE_PHOTO_FOLDER = os.path.join("static", "uploads", "store")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import users_col, vendors_col, robots_col, orders_col, admins_col, products_col

app = Flask(__name__)
app.secret_key = "super_secret_key"
bcrypt = Bcrypt(app)

UPLOAD_FOLDER = 'static/uploads'
PAN_FOLDER = os.path.join(UPLOAD_FOLDER, 'pan')
AADHAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'aadhar')


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def current_time_ist():
    utc_time = datetime.now(timezone.utc)
    ist_offset = 5.5
    ist_time = utc_time.timestamp() + (ist_offset * 3600)
    return datetime.fromtimestamp(ist_time).strftime("%Y-%m-%d %H:%M:%S")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

        personal_image = request.files.get("personal_image")
        store_image = request.files.get("store_image")
        pan_file = request.files.get("pan_card")
        aadhar_file = request.files.get("aadhar_card")

        if not all([personal_image, store_image, pan_file, aadhar_file]):
            return render_template("vendor_register.html", error="All files are required")

        if not allowed_file(personal_image.filename):
            return render_template("vendor_register.html", error="Invalid personal image format")
        if not allowed_file(store_image.filename):
            return render_template("vendor_register.html", error="Invalid store image format")
        if not allowed_file(pan_file.filename):
            return render_template("vendor_register.html", error="Invalid PAN file format")
        if not allowed_file(aadhar_file.filename):
            return render_template("vendor_register.html", error="Invalid Aadhar file format")

        os.makedirs(PAN_FOLDER, exist_ok=True)
        os.makedirs(AADHAR_FOLDER, exist_ok=True)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        username = data.get("username")
        
        personal_filename = secure_filename(username + "_profile_" + personal_image.filename)
        store_filename = secure_filename(username + "_store_" + store_image.filename)
        pan_filename = secure_filename(username + "_PAN_" + pan_file.filename)
        aadhar_filename = secure_filename(username + "_AADHAR_" + aadhar_file.filename)

        personal_path = os.path.join(UPLOAD_FOLDER, personal_filename)
        store_path = os.path.join(UPLOAD_FOLDER, store_filename)
        pan_path = os.path.join(PAN_FOLDER, pan_filename)
        aadhar_path = os.path.join(AADHAR_FOLDER, aadhar_filename)

        personal_image.save(personal_path)
        store_image.save(store_path)
        pan_file.save(pan_path)
        aadhar_file.save(aadhar_path)

        vendor = {
            "name": data.get("name"),
            "username": username,
            "email": data.get("email"),
            "password": hashed_pw,
            "contact_no": data.get("contact_no"),
            "dob": data.get("dob"),
            "store_name": data.get("store_name"),
            "pan_card_file": pan_path,
            "aadhar_card_file": aadhar_path,
            "photo": f"uploads/{personal_filename}",
            "store_photo": f"uploads/{store_filename}",
            "store_since": data.get("store_since"),
            "store_address": data.get("store_address"),
            "timestamp": data.get("timestamp"),
            "device_info": data.get("device_info"),
            "location": data.get("location"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
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
    selected_filter = request.args.get('filter')

    query = {"vendor_id": str(vendor_id)}
    if selected_filter:
        query["category"] = {"$regex": f"^{selected_filter}", "$options": "i"}

    products = list(products_col.find(query))

    for product in products:
        product['_id_str'] = str(product['_id'])

    vendor = vendors_col.find_one({"_id": ObjectId(vendor_id)})

    return render_template(
        "vendor_dashboard.html",
        products=products,
        selected_filter=selected_filter,
        vendor=vendor 
    )

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'vendor' not in session:
        return redirect(url_for('login'))

    categories = [
        "Automotive > Bike Accessories > Helmets",
        "Automotive > Car Accessories > Cleaning",
        "Automotive > Car Accessories > Seat Covers",
        "Automotive > Tools & Equipment",

        "Beauty & Personal Care > Fragrances > Perfume",
        "Beauty & Personal Care > Hair Care > Shampoos",
        "Beauty & Personal Care > Hair Care > Styling",
        "Beauty & Personal Care > Makeup > Eyes",
        "Beauty & Personal Care > Makeup > Lips",
        "Beauty & Personal Care > Skincare > Moisturizers",
        "Beauty & Personal Care > Skincare > Serums",
        "Beauty & Personal Care > Tools > Hair Dryers",

        "Books & Stationery > Art Supplies > Paints",
        "Books & Stationery > Books > Academic",
        "Books & Stationery > Books > Fiction",
        "Books & Stationery > Books > Non-Fiction",
        "Books & Stationery > Office Supplies > Notebooks",

        "Electronics > Accessories > Chargers",
        "Electronics > Accessories > Headphones",
        "Electronics > Accessories > Smartwatches",
        "Electronics > Cameras",
        "Electronics > Laptops",
        "Electronics > Laptops > Business Laptops",
        "Electronics > Laptops > Gaming Laptops",
        "Electronics > Mobiles",
        "Electronics > Mobiles > Accessories",
        "Electronics > Mobiles > Smartphones",
        "Electronics > Tablets",

        "Fashion > Accessories > Bags",
        "Fashion > Accessories > Jewelry",
        "Fashion > Accessories > Sunglasses",
        "Fashion > Kids > Boys Clothing",
        "Fashion > Kids > Girls Clothing",
        "Fashion > Men > Bottoms",
        "Fashion > Men > Footwear",
        "Fashion > Men > Tops",
        "Fashion > Women > Bottoms",
        "Fashion > Women > Dresses",
        "Fashion > Women > Footwear",
        "Fashion > Women > Tops",

        "Food > Breads > Naan",
        "Food > Breads > Paratha",
        "Food > Breads > Puri",
        "Food > Chinese > Chow Mein",
        "Food > Chinese > Fried Rice",
        "Food > Chinese > Manchurian",
        "Food > Desserts > Gulab Jamun",
        "Food > Desserts > Ice Cream",
        "Food > Desserts > Rasgulla",
        "Food > North Indian > Dal Tadka",
        "Food > North Indian > Paneer Butter Masala",
        "Food > North Indian > Rajma Chawal",
        "Food > Snacks & Street Food > Chaat",
        "Food > Snacks & Street Food > Pakora",
        "Food > Snacks & Street Food > Samosa",
        "Food > South Indian > Dosa",
        "Food > South Indian > Idli",
        "Food > South Indian > Medu Vada",
        "Food > South Indian > Upma",
        "Food > Thali > Mini Thali",
        "Food > Thali > Veg Thali",
        "Food > Thali > Combo Meals",
        "Food > Beverages > Lassi",
        "Food > Beverages > Masala Chai",
        "Food > Beverages > Soft Drinks",
        "Food > Beverages > Tea & Coffee",

        "Grocery > Beverages > Juices",
        "Grocery > Beverages > Soft Drinks",
        "Grocery > Beverages > Tea & Coffee",
        "Grocery > Breakfast Items > Cereals",
        "Grocery > Breakfast Items > Jam & Spreads",
        "Grocery > Breakfast Items > Oats & Muesli",
        "Grocery > Canned & Packaged Food > Canned Vegetables",
        "Grocery > Canned & Packaged Food > Instant Noodles",
        "Grocery > Canned & Packaged Food > Ready to Eat Meals",
        "Grocery > Dairy > Butter & Cheese",
        "Grocery > Dairy > Milk",
        "Grocery > Dairy > Yogurt & Curd",
        "Grocery > Food Staples > Atta, Flour & Sooji",
        "Grocery > Food Staples > Lentils & Pulses",
        "Grocery > Food Staples > Oil & Ghee",
        "Grocery > Food Staples > Rice & Grains",
        "Grocery > Food Staples > Salt, Sugar & Jaggery",
        "Grocery > Household Supplies > Cleaning Tools",
        "Grocery > Household Supplies > Detergents",
        "Grocery > Household Supplies > Dishwashing",
        "Grocery > Household Supplies > Paper & Disposables",
        "Grocery > Organic Products",
        "Grocery > Personal Care > Bath & Body",
        "Grocery > Personal Care > Oral Care",
        "Grocery > Personal Care > Sanitary Needs",
        "Grocery > Snacks > Biscuits & Cookies",
        "Grocery > Snacks > Chips & Crackers",
        "Grocery > Snacks > Chocolates",
        "Grocery > Snacks > Dry Fruits & Nuts",
        "Grocery > Spices & Masalas",
        "Grocery > Staples > Baking Essentials",

        "Home & Kitchen",
        "Home & Kitchen > Appliances > Irons",
        "Home & Kitchen > Appliances > Vacuum Cleaners",
        "Home & Kitchen > Appliances > Water Purifiers",
        "Home & Kitchen > Bedding > Bedsheets",
        "Home & Kitchen > Bedding > Blankets & Comforters",
        "Home & Kitchen > Bedding > Pillows",
        "Home & Kitchen > Cookware > Cookware Sets",
        "Home & Kitchen > Cookware > Pressure Cookers",
        "Home & Kitchen > Decor > Clocks",
        "Home & Kitchen > Decor > Curtains & Accessories",
        "Home & Kitchen > Decor > Lighting",
        "Home & Kitchen > Decor > Wall Art",
        "Home & Kitchen > Dining > Dinner Sets",
        "Home & Kitchen > Dining > Glassware",
        "Home & Kitchen > Dining > Serveware",
        "Home & Kitchen > Kitchen Appliances",
        "Home & Kitchen > Kitchen Appliances > Blenders",
        "Home & Kitchen > Kitchen Appliances > Microwaves",
        "Home & Kitchen > Storage > Organizers",
        "Home & Kitchen > Storage > Racks & Shelves",
        "Home & Kitchen > Tools > Cleaning Tools",
        "Home & Kitchen > Tools > Hardware & Repair",

        "Pet Supplies > Cats > Food",
        "Pet Supplies > Cats > Litter",
        "Pet Supplies > Dogs > Food",
        "Pet Supplies > Dogs > Toys",
        "Pet Supplies > Fish & Aquatics > Tanks",

        "Sports & Outdoors > Camping > Tents",
        "Sports & Outdoors > Cycling > Bicycles",
        "Sports & Outdoors > Cycling > Helmets",
        "Sports & Outdoors > Fitness > Dumbbells",
        "Sports & Outdoors > Fitness > Yoga Mats",
        "Sports & Outdoors > Sportswear > Men",
        "Sports & Outdoors > Sportswear > Women",

        "Toys & Baby Products > Baby Gear > Car Seats",
        "Toys & Baby Products > Baby Gear > Strollers",
        "Toys & Baby Products > Diapers & Wipes",
        "Toys & Baby Products > Feeding > Bottles",
        "Toys & Baby Products > Toys > Action Figures",
        "Toys & Baby Products > Toys > Educational"
    ]

    units = ["kg", "liter", "dozen", "piece"]

    if request.method == 'POST':
        data = request.form
        vendor_id = session['vendor']['vendor_id']
        images = request.files.getlist('images')
        image_filenames = []

        for image in images[:5]:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                image_filenames.append(filename)

        product = {
            "vendor_id": vendor_id,
            "name": data.get("name"),
            "category": data.get("category"),
            "quantity_with_unit": f"{data.get('quantity')} {data.get('unit')}",
            "price": float(data.get("price", 0)),
            "expiry_date": data.get("expiry_date"),
            "return_policy": data.get("return_policy"),
            "manufacturer_details": data.get("manufacturer_details"),
            "marketer_details": data.get("marketer_details"),
            "country_of_origin": data.get("country_of_origin"),
            "customer_care": data.get("customer_care"),
            "disclaimer": data.get("disclaimer"),
            "image_paths": image_filenames,
            "timestamp": current_time_ist()
        }

        products_col.insert_one(product)
        return redirect(url_for('dashboard'))

    return render_template("add_product.html", categories=categories, units=units)

@app.route('/vendor/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'vendor' not in session:
        return redirect(url_for('login'))

    product = products_col.find_one({"_id": ObjectId(product_id)})

    if not product or product["vendor_id"] != session["vendor"]["vendor_id"]:
        return "Unauthorized or product not found", 403

    if request.method == 'POST':
        data = request.form

        updated_fields = {
            "name": data.get("name"),
            "category": data.get("category"),
            "quantity_with_unit": f"{data.get('quantity')} {data.get('unit')}",
            "price": float(data.get("price", 0)),
            "expiry_date": data.get("expiry_date"),
            "return_policy": data.get("return_policy"),
            "manufacturer_details": data.get("manufacturer_details"),
            "marketer_details": data.get("marketer_details"),
            "country_of_origin": data.get("country_of_origin"),
            "customer_care": data.get("customer_care"),
            "disclaimer": data.get("disclaimer"),
        }

        image = request.files.get('image')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updated_fields["image_paths"] = [filename]

        products_col.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": updated_fields}
        )
        return redirect(url_for('dashboard'))

    return render_template("edit_product.html", product=product)

@app.route('/vendor/delete_product_image/<product_id>/<image_filename>', methods=['POST'])
def delete_product_image(product_id, image_filename):
    if 'vendor' not in session:
        return redirect(url_for('login'))

    product = products_col.find_one({"_id": ObjectId(product_id)})

    if not product or product["vendor_id"] != session["vendor"]["vendor_id"]:
        return "Unauthorized or product not found", 403

    updated_images = [img for img in product.get("image_paths", []) if img != image_filename]

    products_col.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"image_paths": updated_images}}
    )

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    if os.path.exists(image_path):
        os.remove(image_path)

    return redirect(url_for('edit_product', product_id=product_id))

@app.route("/update_profile", methods=["GET", "POST"])
def update_profile():
    if "vendor" not in session:
        return redirect(url_for("login"))

    vendor_id = session["vendor"]["vendor_id"]

    if request.method == "POST":
        vendor = vendors_col.find_one({"_id": ObjectId(vendor_id)})
        if not vendor:
            return "Vendor not found", 404

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        contact = request.form.get("contact")
        dob = request.form.get("dob")
        store_name = request.form.get("store_name")
        store_from = request.form.get("store_from")
        store_address = request.form.get("store_address")
        location = request.form.get("location")

        update_data = {
            "name": full_name,
            "email": email,
            "contact_no": contact,
            "dob": dob,
            "store_name": store_name,
            "store_from": store_from,
            "store_address": store_address,
            "location": location,
        }

        if password:
            update_data["password"] = generate_password_hash(password)

        vendor_photo = request.files.get("vendor_photo")
        store_photo = request.files.get("store_photo")

        if vendor_photo and vendor_photo.filename:
            filename = secure_filename(f"{vendor['email']}_PROFILE_{vendor_photo.filename}")
            photo_path = os.path.join(VENDOR_PHOTO_FOLDER, filename)
            vendor_photo.save(photo_path)
            update_data["photo"] = f"uploads/profile/{filename}"

        if store_photo and store_photo.filename:
            filename = secure_filename(f"{vendor['email']}_STORE_{store_photo.filename}")
            store_path = os.path.join(STORE_PHOTO_FOLDER, filename)
            store_photo.save(store_path)
            update_data["store_photo"] = f"uploads/store/{filename}"

        vendors_col.update_one({"_id": ObjectId(vendor_id)}, {"$set": update_data})

        session["vendor"]["vendor_name"] = full_name
        if "photo" in update_data:
            session["vendor"]["vendor_photo"] = update_data["photo"]

        vendor = vendors_col.find_one({"_id": ObjectId(vendor_id)})

        return render_template("update_profile.html", vendor=vendor)

    else:
        vendor = vendors_col.find_one({"_id": ObjectId(vendor_id)})
        if not vendor:
            return "Vendor not found", 404

        return render_template("update_profile.html", vendor=vendor)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5002', debug=True)
