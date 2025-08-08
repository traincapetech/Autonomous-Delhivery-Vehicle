# delivery_bot_system/db_init.py
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone

# MongoDB connection
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "delivery_bot"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
vendors_col = db["vendors"]
products_col = db["products"]
orders_col = db["orders"]
robots_col = db["robots"]

# Indexes for fast queries and uniqueness
users_col.create_index([("email", ASCENDING)], unique=True)
users_col.create_index([("username", ASCENDING)], unique=True)
vendors_col.create_index([("email", ASCENDING)], unique=True)
vendors_col.create_index([("username", ASCENDING)], unique=True)
products_col.create_index([("vendor_id", ASCENDING)])
orders_col.create_index([("user_id", ASCENDING)])
orders_col.create_index([("vendor_id", ASCENDING)])
robots_col.create_index([("name", ASCENDING)], unique=True)

print("Collections and indexes created successfully!")

# Example document structures
sample_user = {
    "name": "John Doe",
    "username": "johnd",
    "email": "john@example.com",
    "password": "hashed_password_here",
    "contact_no": "9876543210",
    "dob": "1995-05-01",
    "device_info": {"os": "Android", "ip": "192.168.1.10", "app_version": "1.0"},
    "location": {"lat": 28.7041, "lon": 77.1025},
    "browsing_history": [],
    "past_purchases": [],
    "created_at": datetime.now(timezone.utc)
}

sample_vendor = {
    "name": "FreshMart",
    "username": "freshmart",
    "email": "vendor@example.com",
    "password": "hashed_password_here",
    "contact_no": "9998887777",
    "dob": "1990-02-15",
    "store_name": "FreshMart Store",
    "store_location": {"lat": 28.7041, "lon": 77.1025},
    "device_info": {"os": "Windows", "ip": "192.168.1.20", "app_version": "1.0"},
    "created_at": datetime.now(timezone.utc)
}

sample_robot = {
    "name": "Bot-01",
    "battery_level": 95,
    "current_latitude": 28.7041,
    "current_longitude": 77.1025,
    "status": "Free",
    "created_at": datetime.now(timezone.utc)
}

print("Sample structures ready (not inserted by default).")
