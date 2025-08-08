import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def create_admin():
    admin_col = db["admins"]
    username = "admin"
    password = "admin123"
    hashed_pw = bcrypt.generate_password_hash(password).decode()

    admin_col.insert_one({
        "username": username,
        "password": hashed_pw,
        "role": "admin"
    })
    print("Admin created successfully! Username: admin, Password: 1234")

if __name__ == "__main__":
    create_admin()
