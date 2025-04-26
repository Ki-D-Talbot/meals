
# Meal Tracking App

## Link to site
https://meals-4vjo.onrender.com

## Description

This project is a Flask-based web application that allows users to track their meals, plan meals using a calendar, and avoid the habit of eating the same meals repeatedly. Users can create an account, log in, and interact with the meal calendar. The app is connected to a **MongoDB** database, which stores user information, meal data, and meal categories.

## Current Features

- **User Authentication:**
  - Users can register and log in to the app.
  - Passwords are hashed and stored securely in MongoDB.

- **Meal Tracking:**
  - Users can view a calendar.
  - When a user clicks on a day, they can input their meals.
  - Meals that are not in the database are created as new categories. Previously entered meals can be searched and reused.

- **Database:**
  - MongoDB is used to store user data, meal categories, and meal entries.
  - The app uses **Flask-PyMongo** for MongoDB integration.
  
## Requirements

- **Python 3.7+**
- **Flask 2.x**
- **Flask-Bcrypt** (for password hashing)
- **Flask-Login** (for user session management)
- **Flask-PyMongo** (for MongoDB integration)
- **MongoDB** (local or cloud-based, MongoDB Atlas can be used for cloud-based hosting)
  
To install the necessary dependencies, run:

```bash
pip install -r requirements.txt
```

## Installation

1. **Install MongoDB:**
   - If you're running MongoDB locally, install it from [MongoDB's official website](https://www.mongodb.com/try/download/community).
   - Start the MongoDB server:
     ```bash
     mongod
     ```
   - Verify the installation by running `mongo` in another terminal to access the MongoDB shell.

2. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd meals-app
   ```

3. **Create a virtual environment:**
   - If you don't have a virtual environment set up yet:
     ```bash
     python -m venv venv
     ```
   - Activate the virtual environment:
     - **Windows**:
       ```bash
       venv\Scripts\activate
       ```
     - **Linux/Mac**:
       ```bash
       source venv/bin/activate
       ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Flask app:**

   ```bash
   python app.py
   ```

6. **Access the app:**
   - Open your web browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000) to access the app locally.

## Folder Structure

```
/meals-app
│
├── app.py              # Main application file (Flask app)
├── /templates
│   ├── login.html      # Login page template
│   ├── register.html   # Registration page template
│   └── calendar.html   # Home page (meal calendar)
├── /static
│   ├── /css
│   │   └── styles.css  # CSS file for styling (optional)
│   └── /images
│       └── placeholder.jpg # Placeholder image for meals (optional)
└── requirements.txt    # List of Python dependencies
```

## To Do

1. **Meal Posting**: Users will be able to enter meals and store them in the database. This will include categories for meal types (e.g., breakfast, lunch, dinner).
2. **Meal Photos**: Implement functionality to allow users to upload meal photos.
3. **Comments/Interactions**: Enable users to comment on meals and interact with others.
4. **Styling**: Add CSS for better visual presentation of the calendar and other pages.
5. **Deploying to Production**: Deploy the app on platforms like **Heroku** or **PythonAnywhere** once it's fully functional.

## Notes for Developers

- **MongoDB Integration**: The app uses **Flask-PyMongo** for easy connection to MongoDB. MongoDB collections store users and meal data.
- **User Management**: **Flask-Login** is used to manage user sessions. The user model is simple, with just a username, email, and password.
- **Password Security**: Passwords are hashed using **Flask-Bcrypt** before storage in the database.
- **Meal Categories**: If a user adds a new meal that hasn't been stored previously, the app creates a new category for it in the database.

## Troubleshooting

- **MongoDB Connection Error**: If you're encountering errors related to MongoDB connection, ensure that the MongoDB server is running (`mongod`), and that you're using the correct connection string (`mongodb://localhost:27017/mealsDB`).
- **Flask App Not Running**: Make sure you have activated your virtual environment and installed all the dependencies using `pip install -r requirements.txt`.
