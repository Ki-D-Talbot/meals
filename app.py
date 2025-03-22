import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_pymongo import PyMongo
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration with fallback values
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-123"),
    MONGO_URI=os.getenv("MONGO_URI", "mongodb://localhost:27017/mealsDB"),
    UPLOAD_FOLDER=os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "static/uploads"
    ),
    ALLOWED_EXTENSIONS={"png", "jpg", "jpeg", "gif"},
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
)

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# User class with additional fields
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.email = user_data["email"]
        self.avatar = user_data.get("avatar", "/static/images/default-avatar.png")


@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return User(user_data) if user_data else None


# File upload validation
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


# --- Routes ---
@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return redirect(url_for("meal_feed"))


# Authentication routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
        }

        mongo.db.users.insert_one(user_data)
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user_data = mongo.db.users.find_one({"email": email})

        if user_data and bcrypt.check_password_hash(user_data["password"], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# Meal functionality
@app.route("/feed")
@login_required
def meal_feed():
    meals = mongo.db.meals.find().sort("created_at", -1)
    return render_template("feed.html", meals=meals)


@app.route("/add_meal", methods=["POST"])
@login_required
def add_meal():
    try:
        data = request.json
        meal_date = data.get("date")
        meal_text = data.get("meal")
        meal_type = data.get("meal_type", "other")

        # Create meal document
        new_meal = {
            "user_id": current_user.id,
            "caption": meal_text,
            "meal_type": meal_type,
            "meal_date": datetime.strptime(meal_date, "%Y-%m-%d"),
            "created_at": datetime.utcnow(),
            "likes": [],
            "comments": [],
        }

        # Insert into database
        result = mongo.db.meals.insert_one(new_meal)

        return jsonify({"success": True, "meal_id": str(result.inserted_id)})
    except Exception as e:
        print(f"Error adding meal: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Social features
@app.route("/like/<meal_id>", methods=["POST"])
@login_required
def like_meal(meal_id):
    try:
        meal = mongo.db.meals.find_one({"_id": ObjectId(meal_id)})
        if not meal:
            return jsonify({"error": "Meal not found"}), 404
        # Add logic to handle liking a meal
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Insights
@app.route("/insights")
@login_required
def insights():
    try:
        # Get meals for the current user
        user_meals = list(mongo.db.meals.find({"user_id": current_user.id}))

        # Basic stats
        meal_count = len(user_meals)
        recent_meals = user_meals[:5] if meal_count > 0 else []

        # Process meal data for chart
        meal_data = {}
        months = []
        meal_counts = []

        if meal_count > 0:
            # Convert ObjectId and dates for JSON serialization
            for meal in user_meals:
                meal["_id"] = str(meal["_id"])

                # Ensure created_at is a datetime object
                if not isinstance(meal.get("created_at"), datetime):
                    meal["created_at"] = datetime.now()  # Default if no date

                # Count meals by month
                month_str = meal["created_at"].strftime("%B %Y")
                if month_str in meal_data:
                    meal_data[month_str] += 1
                else:
                    meal_data[month_str] = 1

            # Get the most active day (day with most meals)
            day_counts = {}
            for meal in user_meals:
                day_str = meal["created_at"].strftime("%A")
                if day_str in day_counts:
                    day_counts[day_str] += 1
                else:
                    day_counts[day_str] = 1
            most_active_day = (
                max(day_counts, key=day_counts.get) if day_counts else "N/A"
            )

            # Get favorite meal type
            meal_types = {}
            for meal in user_meals:
                meal_type = meal.get("meal_type", "other")
                if meal_type in meal_types:
                    meal_types[meal_type] += 1
                else:
                    meal_types[meal_type] = 1
            favorite_meal_type = (
                max(meal_types, key=meal_types.get) if meal_types else "N/A"
            )

            # Format data for Chart.js
            months = list(meal_data.keys())
            meal_counts = [meal_data[month] for month in months]
        else:
            most_active_day = "N/A"
            favorite_meal_type = "N/A"

        return render_template(
            "insights.html",
            meal_count=meal_count,
            most_active_day=most_active_day,
            favorite_meal_type=favorite_meal_type,
            recent_meals=recent_meals,
            months=months,
            meal_counts=meal_counts,
        )

    except Exception as e:
        # Log the error
        print(f"Error in insights route: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return render_template(
            "insights.html",
            meal_count=0,
            most_active_day="N/A",
            favorite_meal_type="N/A",
            recent_meals=[],
        )


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/calendar")
@login_required
def calendar():
    # Fetch user's meals for display in calendar
    user_meals = list(mongo.db.meals.find({"user_id": current_user.id}))

    # Format meals for calendar
    formatted_meals = []
    for meal in user_meals:
        meal_date = meal.get("meal_date")
        if meal_date:
            formatted_meals.append(
                {
                    "id": str(meal["_id"]),
                    "title": meal["caption"],
                    "start": meal_date.strftime("%Y-%m-%d"),
                    "meal_type": meal.get("meal_type", "other"),
                }
            )

    return render_template("calendar.html", meals=formatted_meals)


@app.route("/test_db")
def test_db():
    try:
        mongo.db.meals.find_one()
        return "Database connection is working!"
    except Exception as e:
        return f"Database connection failed: {e}"


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
