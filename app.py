from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os
import uuid
from datetime import datetime, timedelta


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

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # Use environment variable
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Use environment variable
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")

mail = Mail(app)

# Token Serializer
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

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

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Registration
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

# Login
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

# Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome, {current_user.email}! <a href='/logout'>Logout</a>"

# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out!", "info")
    return redirect(url_for("signin"))

# Forgot Password
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        print("Email entered:", email)  # Debugging

        user = users_collection.find_one({"_id": email})
        if user:
            print("User found in database")

            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            print("Generated reset URL:", reset_url)  # Debugging

            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_url}"
            
            try:
                mail.send(msg)
                print("✅ Email sent successfully")  # Debugging
                flash("A password reset link has been sent to your email.", "info")
            except Exception as e:
                print("❌ Error sending email:", e)  # Debugging
                flash("Failed to send email.", "danger")

            return redirect(url_for("forgot_password"))  # Stay on forgot-password page

        print("❌ Email not found in database")  # Debugging
        flash("Email not found.", "danger")

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
        print("Decoded email from token:", email)  # Debugging
    except Exception as e:
        print("❌ Invalid or expired token:", e)  # Debugging
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("password")
        hashed_password = generate_password_hash(new_password)
        users_collection.update_one({"_id": email}, {"$set": {"password": hashed_password}})
        
        flash("Your password has been updated! Please sign in.", "success")
        return redirect(url_for("signin"))  # Redirect to sign-in page after reset

    return render_template("reset_password.html", token=token)

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
