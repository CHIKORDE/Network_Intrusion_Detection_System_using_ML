from flask import Flask, render_template, request, redirect, url_for, session, flash
import joblib
import numpy as np
from collections import Counter
import hashlib
import os
from datetime import datetime
import mysql.connector

#database coonection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # default XAMPP user
        password="",        # default empty password
        database="nids_ai"
    )


# Load model and preprocessor
model = joblib.load("model/nids_model.pkl")
preprocessor = joblib.load("model/preprocessor.pkl")
label_encoder = joblib.load("model/label_encoder.pkl")

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# In-memory user storage (in production, use a proper database)
users_db = {}
history_counter = Counter()

features = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Fwd IAT Mean",
    "Bwd IAT Mean",
    "SYN Flag Count"
]

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

@app.route("/")
def home():
    """Landing page route"""
    return render_template("home.html")

@app.route("/home")
def home_redirect():
    """Alternative home route"""
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            # ---------- ADMIN LOGIN (plain text password) ----------
            if user["username"].lower() == "admin":
                if password != user["password"]:   # no hashing
                    flash("Invalid username or password!", "error")
                    return render_template("login.html")

                # login admin
                session["username"] = "admin"
                session["login_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return redirect(url_for("admin"))

            # ---------- NORMAL USER LOGIN (hashed password) ----------
            if verify_password(password, user["password"]):
                session["username"] = username
                session["login_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password!", "error")
        else:
            flash("Invalid username or password!", "error")

    return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")
        fav_car = request.form.get("fav_car")     # <-- ADDED

        # Basic validations
        if not username or not password or not email or not fav_car:
            flash("All fields are required!", "error")

        elif len(password) < 6:
            flash("Password must be at least 6 characters long!", "error")

        elif password != confirm_password:
            flash("Passwords do not match!", "error")

        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (username, password, email, fav_car, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, hash_password(password), email, fav_car.lower(), datetime.now()))

            conn.commit()
            cursor.close()
            conn.close()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
    
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully!", "info")
    return redirect(url_for("home"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Main dashboard for logged-in users (renamed from index)"""
    if "username" not in session:
        flash("Please login to access the dashboard!", "warning")
        return redirect(url_for("login"))
    
    prediction = None
    confidence = None
    
    if request.method == "POST":
        try:
            input_data = [float(request.form[feat]) for feat in features]
            X = np.array(input_data).reshape(1, -1)
            X_scaled = preprocessor.transform(X)
            
            # Get prediction and probability
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO predictions (username, prediction, confidence, timestamp)
            VALUES (%s, %s, %s, %s)
            """, (session["username"], prediction, confidence, datetime.now()))

            conn.commit()
            cursor.close()
            conn.close()



            pred = model.predict(X_scaled)
            prediction = label_encoder.inverse_transform(pred)[0]

            if hasattr(model, 'predict_proba'):
                pred_proba = model.predict_proba(X_scaled)
                confidence = max(pred_proba[0]) * 100
            else:
                confidence = 95.0  # Default confidence when probability not available
            
            history_counter[prediction] += 1
            flash(f"Prediction completed: {prediction} (Confidence: {confidence:.1f}%)", "info")
            
        except Exception as e:
            prediction = f"Error: {str(e)}"
            flash(f"Prediction error: {str(e)}", "error")

    return render_template("index.html", 
                         features=features, 
                         prediction=prediction,
                         confidence=confidence,
                         history=dict(history_counter),
                         username=session.get("username"),
                         login_time=session.get("login_time"))



@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # get user info
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user_data = cursor.fetchone()

    # get prediction counts
    cursor.execute("""
        SELECT prediction, COUNT(*) as count FROM predictions
        WHERE username=%s GROUP BY prediction
    """, (username,))
    rows = cursor.fetchall()

    prediction_history = {row["prediction"]: row["count"] for row in rows}

    # recent predictions
    cursor.execute("""
        SELECT * FROM predictions
        WHERE username=%s ORDER BY timestamp DESC LIMIT 10
    """, (username,))
    recent_predictions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        username=username,
        user_data=user_data,
        prediction_history=prediction_history,
        recent_predictions=recent_predictions,
        total_predictions=sum(prediction_history.values())
    )

@app.route('/admin')
def admin():
    if 'username' not in session or session['username'].lower() != 'admin':
        flash("Admin access only!", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, username, email, created_at, last_login
        FROM users
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("admin.html", users=users)


@app.route("/admin/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    # Only admin can delete users
    if 'username' not in session or session['username'].lower() != 'admin':
        flash("Admin access only!", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch user
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    if not user:
        flash("User not found!", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('admin'))

    if user['username'].lower() == 'admin':
        flash("Cannot delete the admin account!", "warning")
        cursor.close()
        conn.close()
        return redirect(url_for('admin'))

    # Delete user
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash(f"User '{user['username']}' deleted successfully.", "success")
    return redirect(url_for('admin'))

@app.route("/about")
def about():
    """About page with system information"""
    return render_template("about.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    # Example user settings (normally fetched from DB)
    user_settings = {
        "email_notifications": True,
        "dark_mode": False,
        "language": "English"
    }

    if request.method == "POST":
        # Update settings from form data
        user_settings["email_notifications"] = bool(request.form.get("email_notifications"))
        user_settings["dark_mode"] = bool(request.form.get("dark_mode"))
        user_settings["language"] = request.form.get("language")

        flash("Settings updated successfully!", "success")
        # Here you would save updates to DB

    return render_template("settings.html", settings=user_settings)


@app.route("/api/stats")
def api_stats():
    """API endpoint for statistics (JSON response)"""
    stats = {
        "total_users": len(users_db),
        "total_predictions": sum(history_counter.values()),
        "prediction_types": dict(history_counter),
        "active_sessions": len([user for user in session if 'username' in session])
    }
    return stats

@app.errorhandler(404)
def not_found(error):
    """Custom 404 error handler"""
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error handler"""
    return render_template("500.html"), 500

# Context processor to make common variables available in all templates
@app.context_processor
def inject_common_vars():
    return {
        'current_year': datetime.now().year,
        'app_name': 'NIDS AI',
        'version': '1.0.0'
    }

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        fav_car = request.form.get("fav_car", "").lower()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()    # <-- correct variable name

        cursor.close()
        conn.close()

        if not user:
            flash("Email not found!", "error")

        elif (user.get("fav_car") or "").lower() != fav_car:
            flash("Security answer incorrect!", "error")

        else:
            return redirect(url_for("reset_password", email=email))

    return render_template("forgot_password.html")



@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    email = request.args.get("email")  # from URL ?email=...
    if not email:
        flash("Invalid request! No email provided.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or not confirm_password:
            flash("All fields are required!", "error")

        elif new_password != confirm_password:
            flash("Passwords do not match!", "error")

        elif len(new_password) < 6:
            flash("Password must be at least 6 characters long!", "error")

        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE users SET password=%s WHERE email=%s",
                (hash_password(new_password), email)
            )
            conn.commit()
            cursor.close()
            conn.close()

            flash("Password reset successful! Please login.", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html", email=email)



if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory for CSS, JS, images if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
        os.makedirs('static/css')
        os.makedirs('static/js')
        os.makedirs('static/images')
    
    app.run(debug=True)