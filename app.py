from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId

app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/mealsDB"
mongo = PyMongo(app)

# Set up Flask-Login and Flask-Bcrypt
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

# Secret key for session management
app.secret_key = "your_secret_key_here"

# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])  # Flask-Login requires a string ID
        self.username = user_data["username"]
        self.email = user_data["email"]

    def get_id(self):
        return self.id  # This is required by Flask-Login

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Home page route
@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return render_template("calendar.html", username=current_user.username)


# Registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if mongo.db.users.find_one({"email": email}):
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password
        })
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user_data = mongo.db.users.find_one({"email": email})

        if user_data and bcrypt.check_password_hash(user_data["password"], password):
            user = User(user_data)
            login_user(user)  # Pass the User object to login_user
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    
    return render_template("login.html")

# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
