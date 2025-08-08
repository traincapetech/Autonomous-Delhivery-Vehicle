# delivery_bot_system/db_config.py
from pymongo import MongoClient

# MongoDB URI - replace with your own if using MongoDB Atlas
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "delivery_bot"

# Create MongoDB client and database
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
vendors_col = db["vendors"]
products_col = db["products"]
orders_col = db["orders"]
robots_col = db["robots"]
admins_col = db["admins"]   