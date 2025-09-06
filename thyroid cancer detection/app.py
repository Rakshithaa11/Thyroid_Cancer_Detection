from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from predictor import predict_thyroid
import random
import string

app = Flask(__name__)
app.secret_key = "thyroid_secret_key"  # replace in production

# ------------------------------ #
# MySQL Configuration
# ------------------------------ #
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",           # put your MySQL password here if any
    "database": "thyroid_model"
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ------------------------------ #
# Helpers
# ------------------------------ #
def current_user_role():
    return session.get("role")

def login_required(role=None):
    if "user_id" not in session:
        flash("Please log in to continue.", "warning")
        return False
    if role and session.get("role") != role:
        flash("Unauthorized access.", "danger")
        return False
    return True

def generate_temp_password(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ------------------------------ #
# Public pages
# ------------------------------ #
@app.route("/")
def landing():
    return render_template("landing.html", active_page="landing")

@app.route("/about")
def about():
    return render_template("about.html", active_page="about")

# ------------------------------ #
# Auth: Register / Login
# ------------------------------ #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "").strip().lower()

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if role not in ("doctor", "patient"):
            flash("Please select a valid role.", "danger")
            return redirect(url_for("register"))

        pw_hash = generate_password_hash(password)

        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, role, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (username, email, pw_hash, role),
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Error as err:
            flash(f"Database error: {err}", "danger")
            return redirect(url_for("register"))
        finally:
            if cur: cur.close()
            if conn: conn.close()

    return render_template("register.html", active_page="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("role_selection"))
    return render_template("login.html", active_page="login")

@app.route("/role_selection")
def role_selection():
    return render_template("role_selection.html", active_page="role_selection")

@app.route("/login/doctor", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        return handle_login("doctor")
    return render_template("role_login.html", role="doctor", active_page="doctor_login")

@app.route("/login/patient", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        return handle_login("patient")
    return render_template("role_login.html", role="patient", active_page="patient_login")

def handle_login(role):
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND role=%s", (email, role))
        user = cur.fetchone()
    except Error as err:
        flash(f"Database error: {err}", "danger")
        return redirect(url_for(f"{role}_login"))
    finally:
        if cur: cur.close()
        if conn: conn.close()

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        flash(f"Welcome, {user['username']}!", "success")
        return redirect(url_for("doctor_dashboard" if role == "doctor" else "patient_dashboard"))

    flash("Invalid email or password.", "danger")
    return redirect(url_for(f"{role}_login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

# ------------------------------ #
# Dashboards
# ------------------------------ #
@app.route("/patient_dashboard")
def patient_dashboard():
    if not login_required("patient"):
        return redirect(url_for("login"))
    return render_template(
        "patient_dashboard.html",
        username=session.get("username"),
        active_page="patient_dashboard",
    )

@app.route("/doctor_dashboard")
def doctor_dashboard():
    if not login_required("doctor"):
        return redirect(url_for("login"))
    return render_template(
        "doctor_dashboard.html",
        username=session.get("username"),
        active_page="doctor_dashboard",
    )

# ------------------------------ #
# Doctor Features
# ------------------------------ #
@app.route("/thyroid_predictions")
def thyroid_predictions():
    if not login_required("doctor"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            tp.prediction_id,
            p.full_name AS patient_name,
            p.age,
            p.gender,
            tp.tsh,
            tp.t3,
            tp.t4,
            tp.symptom,
            tp.result,
            tp.predicted_at
        FROM thyroid_predictions tp
        JOIN patients p ON tp.patient_id = p.patient_id
        ORDER BY tp.predicted_at DESC
    """)
    predictions = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("thyroid_predictions.html", predictions=predictions)

@app.route("/appointments")
def view_appointments():
    if not login_required("doctor"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            a.appointment_id,
            p.full_name AS patient_name,
            d.full_name AS doctor_name,
            d.specialization,
            a.appointment_date,
            a.status,
            a.notes
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC
    """)
    appointments = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("appointments.html", appointments=appointments)

@app.route("/patients")
def view_patients():
    if not login_required("doctor"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            u.user_id,
            u.username,
            u.email,
            u.created_at,
            p.full_name,
            p.age,
            p.gender
        FROM users u
        JOIN patients p ON u.user_id = p.user_id
        WHERE u.role = 'patient'
        ORDER BY u.created_at DESC
    """)
    patients = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("patients.html", patients=patients)

@app.route("/doctors")
def view_doctors():
    if not login_required("doctor"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            u.user_id,
            u.username,
            u.email,
            u.created_at,
            d.full_name,
            d.specialization,
            d.contact_number
        FROM users u
        JOIN doctors d ON u.user_id = d.user_id
        WHERE u.role = 'doctor'
        ORDER BY u.created_at DESC
    """)
    doctors = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("doctors.html", doctors=doctors)

# ThyroCheck
@app.route('/thyrocheck', methods=['GET', 'POST'])
def thyrocheck():
    # ✅ Allow only doctors
    if not login_required("doctor"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            # Collect form data
            name = request.form['name']
            age = request.form['age']
            gender = request.form['gender']
            tsh = float(request.form['tsh'])
            t3 = float(request.form['t3'])
            t4 = float(request.form['t4'])

            # ✅ Handle multiple symptoms
            symptoms_list = request.form.getlist('symptoms')
            symptoms = ", ".join(symptoms_list) if symptoms_list else "None"

            # Check if patient already exists
            cursor.execute("SELECT * FROM patients WHERE full_name = %s", (name,))
            patient = cursor.fetchone()

            if patient:
                # Already exists → use existing record
                patient_id = patient['patient_id']
                db_name = patient['full_name']
                db_age = patient['age']
                db_gender = patient['gender']
            else:
                # Not found → auto-register patient under current doctor
                cursor.execute("""
                    INSERT INTO patients (user_id, full_name, age, gender)
                    VALUES (%s, %s, %s, %s)
                """, (session['user_id'], name, age, gender))
                conn.commit()

                patient_id = cursor.lastrowid
                db_name, db_age, db_gender = name, age, gender

            # Run prediction
            result = predict_thyroid(tsh, t3, t4)

            # Save prediction
            cursor.execute("""
                INSERT INTO thyroid_predictions 
                (patient_id, name, age, gender, tsh, t3, t4, symptom, result, predicted_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id, db_name, db_age, db_gender,
                tsh, t3, t4, symptoms, result, datetime.now()
            ))
            conn.commit()

            flash("✅ Prediction saved successfully!", "success")
            return redirect(url_for('thyrocheck'))

        except Exception as e:
            flash(f"❌ Error: {str(e)}", "danger")
            return redirect(url_for('thyrocheck'))

    # ✅ Fetch predictions with patient details
    cursor.execute("""
        SELECT tp.*
        FROM thyroid_predictions tp
        ORDER BY tp.predicted_at DESC
    """)
    predictions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("thyroid_predictions.html", predictions=predictions)


# ------------------------------ #
# Run
# ------------------------------ #
if __name__ == "__main__":
    app.run(debug=True)
