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
        self.username = user_data.get("username", "Unknown")
        self.email = user_data.get("email", "")
        self.avatar = user_data.get("avatar", "/static/images/default-avatar.png")


@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            print(f"Debug: Loaded user {user_data.get('username')}")
            return User(user_data)
        else:
            print(f"Debug: Failed to find user with ID {user_id}")
            return None
    except Exception as e:
        print(f"Error loading user: {str(e)}")
        return None


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
    try:
        # First check if there are any meals at all (simpler query for debugging)
        basic_meals = list(mongo.db.meals.find())
        print(f"Debug: Found {len(basic_meals)} total meals in database")

        if len(basic_meals) == 0:
            # No meals in database yet
            return render_template("feed.html", meals=[])

        # Now try the full pipeline
        pipeline = [
            {"$sort": {"created_at": -1}},  # Newest first
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user",
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "caption": 1,
                    "meal_type": 1,
                    "created_at": 1,
                    "likes": 1,
                    "comments": 1,
                    "user_id": 1,
                    "user": 1,
                }
            },
        ]

        # Get the aggregation result
        aggregated_meals = list(mongo.db.meals.aggregate(pipeline))
        print(f"Debug: After aggregation, found {len(aggregated_meals)} meals")

        # Manually format the meals for the template
        formatted_meals = []
        for meal in aggregated_meals:
            # Format the meal data
            meal_data = {
                "_id": str(meal["_id"]),
                "caption": meal.get("caption", ""),
                "meal_type": meal.get("meal_type", "other"),
                "created_at": meal.get("created_at", datetime.now()),
                "likes": meal.get("likes", []),
                "comments": meal.get("comments", []),
            }

            # Handle user data
            users = meal.get("user", [])
            if users:
                # We found a user
                user = users[0]
                meal_data["username"] = user.get("username", "Unknown User")
                meal_data["user_avatar"] = user.get(
                    "avatar", "/static/images/default-avatar.png"
                )
            else:
                # No user found
                meal_data["username"] = "Unknown User"
                meal_data["user_avatar"] = "/static/images/default-avatar.png"

            formatted_meals.append(meal_data)

        return render_template("feed.html", meals=formatted_meals)

    except Exception as e:
        print(f"Error in meal_feed: {str(e)}")
        return render_template("feed.html", meals=[])


@app.route("/add_meal", methods=["POST"])
@login_required
def add_meal():
    try:
        data = request.json
        meal_date = data.get("date")
        meal_text = data.get("meal")
        meal_type = data.get("meal_type", "other")

        # Print debug info about current user
        print(
            f"Debug in add_meal: Current user ID is {current_user.id} of type {type(current_user.id)}"
        )

        # Create meal document - store user_id as both string and ObjectId to help debug
        new_meal = {
            "user_id": ObjectId(current_user.id),  # Store as ObjectId
            "user_id_str": current_user.id,  # Also store as string for debugging
            "caption": meal_text,
            "meal_type": meal_type,
            "meal_date": (
                datetime.strptime(meal_date, "%Y-%m-%d")
                if meal_date
                else datetime.now()
            ),
            "created_at": datetime.utcnow(),
            "likes": [],
            "comments": [],
        }

        # Insert into database
        result = mongo.db.meals.insert_one(new_meal)
        print(f"Debug: Added new meal with ID {result.inserted_id}")

        # Verify the meal was added correctly
        added_meal = mongo.db.meals.find_one({"_id": result.inserted_id})
        print(
            f"Debug: Verified meal in DB: {added_meal['caption']}, user_id: {added_meal['user_id']}"
        )

        return jsonify({"success": True, "meal_id": str(result.inserted_id)})
    except Exception as e:
        print(f"Error adding meal: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/update_meal/<meal_id>", methods=["POST"])
@login_required
def update_meal(meal_id):
    try:
        data = request.json
        meal_date = data.get("date")
        meal_text = data.get("meal")
        meal_type = data.get("meal_type", "other")

        # Check if meal exists and belongs to current user
        meal = mongo.db.meals.find_one({"_id": ObjectId(meal_id)})
        if not meal:
            return jsonify({"error": "Meal not found"}), 404

        # Check if user owns this meal
        meal_user_id = meal.get("user_id")
        if str(meal_user_id) != current_user.id and meal_user_id != current_user.id:
            return (
                jsonify({"error": "You don't have permission to edit this meal"}),
                403,
            )

        # Update the meal
        update_data = {
            "caption": meal_text,
            "meal_type": meal_type,
        }

        # Only update date if provided
        if meal_date:
            update_data["meal_date"] = datetime.strptime(meal_date, "%Y-%m-%d")

        mongo.db.meals.update_one({"_id": ObjectId(meal_id)}, {"$set": update_data})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_meal/<meal_id>", methods=["POST"])
@login_required
def delete_meal(meal_id):
    try:
        # Check if meal exists and belongs to current user
        meal = mongo.db.meals.find_one({"_id": ObjectId(meal_id)})
        if not meal:
            return jsonify({"error": "Meal not found"}), 404

        # Check if user owns this meal
        meal_user_id = meal.get("user_id")
        if str(meal_user_id) != current_user.id and meal_user_id != current_user.id:
            return (
                jsonify({"error": "You don't have permission to delete this meal"}),
                403,
            )

        # Delete the meal
        mongo.db.meals.delete_one({"_id": ObjectId(meal_id)})

        return jsonify({"success": True})
    except Exception as e:
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
        print(f"Insights: Retrieving data for user {current_user.id}")

        user_meals = list(mongo.db.meals.find({"user_id": ObjectId(current_user.id)}))
        print(f"Insights: Found {len(user_meals)} meals")

        # Basic stats
        meal_count = len(user_meals)
        recent_meals = user_meals[:5] if meal_count > 0 else []

        # Process meal data for chart
        meal_data = {}
        months = []
        meal_counts = []

        # Track favorite foods and meal types
        food_counts = {}
        meal_types = {}

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

                # Count meal types
                meal_type = meal.get("meal_type", "other")
                if meal_type in meal_types:
                    meal_types[meal_type] += 1
                else:
                    meal_types[meal_type] = 1

                # Count foods (using caption as food name for simplicity)
                caption = meal.get("caption", "").strip()
                if caption:
                    if caption in food_counts:
                        food_counts[caption] += 1
                    else:
                        food_counts[caption] = 1

            # Prepare data for charts
            months = list(meal_data.keys())
            meal_counts = list(meal_data.values())

            # Get favorite food
            favorite_food = (
                max(food_counts, key=food_counts.get) if food_counts else "N/A"
            )

            # Get favorite meal type
            favorite_meal_type = (
                max(meal_types, key=meal_types.get) if meal_types else "N/A"
            )

            # Get meal type distribution for pie chart
            meal_type_labels = list(meal_types.keys())
            meal_type_values = list(meal_types.values())

        else:
            favorite_food = "N/A"
            favorite_meal_type = "N/A"
            meal_type_labels = []
            meal_type_values = []

        return render_template(
            "insights.html",
            meal_count=meal_count,
            favorite_food=favorite_food,
            favorite_meal_type=favorite_meal_type,
            recent_meals=recent_meals,
            months=months,
            meal_counts=meal_counts,
            meal_type_labels=meal_type_labels,
            meal_type_values=meal_type_values,
        )

    except Exception as e:
        print(f"Error in insights page: {str(e)}")
        flash("Error loading insights. Please try again.", "danger")
        return redirect(url_for("home"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/calendar")
@login_required
def calendar():
    try:
        print(f"Debug: Retrieving meals for user ID: {current_user.id}")
        print(f"Debug: User ID type: {type(current_user.id)}")

        # First let's check what's in the database with a simpler query
        all_meals = list(mongo.db.meals.find())
        print(f"Debug: Total meals in database: {len(all_meals)}")

        # Now try to get user-specific meals - first with string ID
        user_meals_str = list(mongo.db.meals.find({"user_id": current_user.id}))
        print(f"Debug: Found {len(user_meals_str)} meals with string user_id")

        # Try with ObjectId
        user_meals = list(mongo.db.meals.find({"user_id": ObjectId(current_user.id)}))
        print(f"Debug: Found {len(user_meals)} meals with ObjectId user_id")

        # Combine results to make sure we get all meals
        combined_meals = user_meals + user_meals_str

        # Format meals for calendar
        formatted_meals = []
        for meal in combined_meals:
            meal_date = meal.get("meal_date")
            print(
                f"Debug: Processing meal: {meal.get('caption')} with date {meal_date}"
            )
            if meal_date:
                formatted_meals.append(
                    {
                        "id": str(meal["_id"]),
                        "title": meal["caption"],
                        "start": meal_date.strftime("%Y-%m-%d"),
                        "extendedProps": {  # Changed: meal_type is now under extendedProps
                            "meal_type": meal.get("meal_type", "other")
                        },
                    }
                )

        print(f"Debug: Formatted {len(formatted_meals)} meals for calendar")
        return render_template("calendar.html", meals=formatted_meals)

    except Exception as e:
        print(f"Error in calendar route: {str(e)}")
        return render_template("calendar.html", meals=[])


@app.route("/test_db")
def test_db():
    try:
        # Check if connection is established
        client_info = mongo.cx.server_info()
        db_names = mongo.cx.list_database_names()

        # Check if we can access the database
        collection_names = mongo.db.list_collection_names()

        # Try to perform a simple operation
        count = mongo.db.meals.count_documents({})

        return f"""
        <h3>MongoDB Connection Test</h3>
        <p>Connection successful!</p>
        <p>MongoDB version: {client_info.get('version')}</p>
        <p>Available databases: {', '.join(db_names)}</p>
        <p>Collections in mealsDB: {', '.join(collection_names)}</p>
        <p>Number of meals: {count}</p>
        """
    except Exception as e:
        # Detailed error information
        error_detail = str(e)
        connection_string = app.config.get("MONGO_URI", "")
        # Hide the password in the connection string for security
        if "mongodb+srv://" in connection_string:
            safe_connection = connection_string.split("@")[0].split(":")
            safe_connection = (
                f"{safe_connection[0]}:****@" + connection_string.split("@")[1]
            )
        else:
            safe_connection = "Connection string not found"

        return f"""
        <h3>MongoDB Connection Failed</h3>
        <p>Error: {error_detail}</p>
        <p>Connection string (password hidden): {safe_connection}</p>
        <p>Check that:</p>
        <ul>
            <li>Your .env file exists and has the correct MONGO_URI</li>
            <li>Your MongoDB Atlas username and password are correct</li>
            <li>Your IP address is in the MongoDB Atlas Network Access list</li>
            <li>Your database name is correct (mealsDB)</li>
        </ul>
        """


@app.route("/fix_meals")
@login_required
def fix_meals():
    try:
        # This route will fix meals with inconsistent user_id format
        all_meals = list(mongo.db.meals.find())
        fixed_count = 0

        for meal in all_meals:
            user_id = meal.get("user_id")
            if isinstance(user_id, str):
                # Convert string user_id to ObjectId
                mongo.db.meals.update_one(
                    {"_id": meal["_id"]}, {"$set": {"user_id": ObjectId(user_id)}}
                )
                fixed_count += 1

        return f"Fixed {fixed_count} meals with string user_id."
    except Exception as e:
        return f"Error fixing meals: {str(e)}"


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
