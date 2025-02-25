from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize Flask App
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017")
db = client["user_auth_db"]
users_collection = db["users"]

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "signin"

# User Model for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"_id": user_id})
    if user_data:
        return User(user_data["_id"], user_data["email"])
    return None

# 📝 Route: Home Page
@app.route("/")
def home():
    return render_template("index.html")

# 📝 Route: Registration
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    phone_number = request.form.get("phone_number")
    address = request.form.get("address")
    registration_number = request.form.get("registration_number")
    password = request.form.get("password")

    if users_collection.find_one({"email": email}):
        flash("Email already registered!", "danger")
        return redirect(url_for("home"))

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "_id": email,
        "name": name,
        "email": email,
        "phone_number": phone_number,
        "address": address,
        "registration_number": registration_number,
        "password": hashed_password
    })

    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("signin"))

# 📝 Route: Login
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({"_id": email})
        if user and check_password_hash(user["password"], password):
            login_user(User(user["_id"], user["email"]))
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password", "danger")
        return redirect(url_for("signin"))

    return render_template("signin.html")

# 📝 Route: Dashboard (Protected)
@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome, {current_user.email}! <a href='/logout'>Logout</a>"

# 📝 Route: Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out!", "info")
    return redirect(url_for("signin"))

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
