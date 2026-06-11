"""
=============================================================================
Digital Shield – Smart Emergency Safety System
app_user.py  |  Flask Application for Users
=============================================================================
Project   : Digital Shield – Women & Pregnancy Emergency Safety System
Version   : 1.0.0
Description:
    User-facing Flask application providing:
    - Session-based authentication (register / login / logout)
    - Dashboard with Women SOS and Pregnancy SOS trigger buttons
    - Emergency contact management
    - Alert history retrieval
    - Location storage API
    Running on http://127.0.0.1:5000
=============================================================================
"""

import json
import os
import traceback
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

try:
    import database as db
    DB_INIT_ERROR = None
except Exception as e:
    db = None
    DB_INIT_ERROR = traceback.format_exc()

# ──────────────────────────────────────────────────────────────────────────────
# App Configuration
# ──────────────────────────────────────────────────────────────────────────────
_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    static_folder=os.path.join(_dir, "static"),
    template_folder=os.path.join(_dir, "templates"),
)
app.secret_key = os.environ.get("USER_SECRET_KEY", "digital_shield_user_secret_key_2024_secure")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching in dev
CORS(app)

# Initialize database on startup
if db:
    db.init_db()


# ── Force no-cache on every response (dev only) ───────────────────────────────
@app.after_request
def add_no_cache_headers(response):
    """Prevent browser from caching JS/CSS during development."""
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


# ──────────────────────────────────────────────────────────────────────────────
# Helper: Login Required Decorator
# ──────────────────────────────────────────────────────────────────────────────
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        user = db.get_user_by_id(session["user_id"])
        if not user or not user.get("is_admin"):
            session.clear()
            flash("Operator/Admin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────────────────────────────────────
# Public Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Landing page – shown to all visitors."""
    if DB_INIT_ERROR:
        return f"<pre>DATABASE INIT ERROR:\n{DB_INIT_ERROR}</pre>", 500
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/lockscreen")
def lockscreen():
    """Lock screen simulation page – always accessible."""
    return render_template("lockscreen.html")


# ──────────────────────────────────────────────────────────────────────────────
# Authentication Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration – creates account and initial contacts."""
    if request.method == "POST":
        full_name   = request.form.get("full_name", "").strip()
        mobile      = request.form.get("mobile", "").strip()
        email       = request.form.get("email", "").strip().lower()
        password    = request.form.get("password", "")
        address     = request.form.get("address", "").strip()
        blood_group = request.form.get("blood_group", "").strip()

        # Basic server-side validation
        if not all([full_name, mobile, email, password]):
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("register"))

        # Check duplicates
        if db.get_user_by_email(email):
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        if db.get_user_by_mobile(mobile):
            flash("Mobile number already registered. Please use a different number or login.", "warning")
            return redirect(url_for("register"))


        # Create user
        pw_hash = generate_password_hash(password)
        db.create_user(full_name, mobile, email, pw_hash, address, blood_group)

        # Save up to 3 emergency contacts
        contact_names  = request.form.getlist("contact_name[]")
        contact_phones = request.form.getlist("contact_phone[]")
        contact_rels   = request.form.getlist("contact_relation[]")
        user = db.get_user_by_email(email)
        for i in range(min(3, len(contact_names))):
            if contact_names[i].strip() and contact_phones[i].strip():
                db.add_contact(
                    user["id"],
                    contact_names[i].strip(),
                    contact_phones[i].strip(),
                    contact_rels[i] if i < len(contact_rels) else "",
                )

        db.log_action(user["id"], "REGISTER", f"New user registered: {email}")
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login – validates credentials (email or mobile) and starts session."""
    if request.method == "POST":
        email_or_mobile = request.form.get("email", "").strip()
        password        = request.form.get("password", "")

        # Try to find user by email first
        user = db.get_user_by_email(email_or_mobile.lower())
        if not user:
            # Try to find user by mobile number
            user = db.get_user_by_mobile(email_or_mobile)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"]   = user["id"]
            session["user_name"] = user["full_name"]
            session["is_admin"]  = bool(user["is_admin"])
            
            if session["is_admin"]:
                db.log_action(user["id"], "ADMIN_LOGIN", f"Operator console access: {user['email']}")
                flash(f"Console Access Granted: {user['full_name']} 🛡️", "success")
                return redirect(url_for("admin_dashboard"))
            else:
                db.log_action(user["id"], "LOGIN", f"User logged in: {user['email']}")
                flash(f"Welcome back, {user['full_name']}! 🛡️", "success")
                return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """End user session and redirect to landing page."""
    if "user_id" in session:
        try:
            if session.get("is_admin"):
                db.log_action(session["user_id"], "ADMIN_LOGOUT", "Operator logged out")
            else:
                db.log_action(session["user_id"], "LOGOUT", "User logged out")
        except Exception as e:
            print(f"Failed to log logout action: {e}")
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for("index"))


# ──────────────────────────────────────────────────────────────────────────────
# Protected Page Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard – displays SOS buttons and recent alerts."""
    user    = db.get_user_by_id(session["user_id"])
    alerts  = db.get_user_alerts(session["user_id"])[:5]
    contacts = db.get_contacts(session["user_id"])
    return render_template("dashboard.html", user=user, alerts=alerts, contacts=contacts)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile – view and edit personal info."""
    user = db.get_user_by_id(session["user_id"])
    if request.method == "POST":
        full_name   = request.form.get("full_name", "").strip()
        mobile      = request.form.get("mobile", "").strip()
        address     = request.form.get("address", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        # Check if mobile is already taken by another user
        existing_user = db.get_user_by_mobile(mobile)
        if existing_user and existing_user["id"] != session["user_id"]:
            flash("Mobile number is already registered by another user.", "warning")
            return redirect(url_for("profile"))

        db.update_user(session["user_id"], full_name, mobile, address, blood_group)
        session["user_name"] = full_name
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/contacts", methods=["GET", "POST"])
@login_required
def contacts():
    """Emergency contact management page."""
    user_contacts = db.get_contacts(session["user_id"])
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        phone    = request.form.get("phone", "").strip()
        relation = request.form.get("relation", "").strip()
        ctype    = request.form.get("type", "women")
        if name and phone:
            db.add_contact(session["user_id"], name, phone, relation, ctype)
            flash("Contact added successfully.", "success")
        else:
            flash("Name and phone are required.", "danger")
        return redirect(url_for("contacts"))
    return render_template("contacts.html", contacts=user_contacts)


@app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
@login_required
def delete_contact(contact_id):
    """Delete an emergency contact."""
    db.delete_contact(contact_id, session["user_id"])
    flash("Contact removed.", "info")
    return redirect(url_for("contacts"))


@app.route("/history")
@login_required
def history():
    """Alert history page."""
    alerts = db.get_user_alerts(session["user_id"])
    return render_template("history.html", alerts=alerts)


# ──────────────────────────────────────────────────────────────────────────────
# REST API – SOS Alert Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/api/sos/women", methods=["POST"])
@login_required
def api_sos_women():
    """
    POST /api/sos/women
    Body (JSON): { latitude, longitude, address }
    Saves alert to DB and returns simulated notification status.
    """
    data      = request.get_json(silent=True) or {}
    latitude  = data.get("latitude")
    longitude = data.get("longitude")
    address   = data.get("address", "Location captured via GPS")

    # Retrieve emergency contacts for notification list
    contacts   = db.get_contacts(session["user_id"])
    notified   = [c["name"] for c in contacts] or ["Parents", "Police", "Friends"]
    notified_str = ", ".join(notified)

    # Persist alert
    db.save_women_alert(session["user_id"], latitude, longitude, address, notified_str)
    db.log_action(session["user_id"], "WOMEN_SOS", f"Lat:{latitude}, Lon:{longitude}")

    return jsonify({
        "success": True,
        "message": "🚨 Alert Sent Successfully! Help is on the way.",
        "notified": notified,
        "location": {"latitude": latitude, "longitude": longitude, "address": address},
    })


@app.route("/api/sos/pregnancy", methods=["POST"])
@login_required
def api_sos_pregnancy():
    """
    POST /api/sos/pregnancy
    Body (JSON): { latitude, longitude, address }
    Saves pregnancy alert and returns simulated notification status.
    """
    data      = request.get_json(silent=True) or {}
    latitude  = data.get("latitude")
    longitude = data.get("longitude")
    address   = data.get("address", "Location captured via GPS")

    contacts     = db.get_contacts(session["user_id"])
    notified     = [c["name"] for c in contacts] or ["Doctor", "Hospital", "Family"]
    notified_str = ", ".join(notified)

    db.save_pregnancy_alert(session["user_id"], latitude, longitude, address, notified_str)
    db.log_action(session["user_id"], "PREGNANCY_SOS", f"Lat:{latitude}, Lon:{longitude}")

    return jsonify({
        "success": True,
        "message": "🏥 Medical Help Requested! Ambulance & Doctor notified.",
        "notified": notified,
        "location": {"latitude": latitude, "longitude": longitude, "address": address},
    })


# ──────────────────────────────────────────────────────────────────────────────
# REST API – Contacts & History
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/api/contacts", methods=["GET"])
@login_required
def api_get_contacts():
    """GET /api/contacts – Return current user's emergency contacts as JSON."""
    contacts = db.get_contacts(session["user_id"])
    return jsonify([dict(c) for c in contacts])


@app.route("/api/history", methods=["GET"])
@login_required
def api_get_history():
    """GET /api/history – Return current user's combined alert history."""
    alerts = db.get_user_alerts(session["user_id"])
    return jsonify(alerts)


# ──────────────────────────────────────────────────────────────────────────────
# Admin & Operator Protected Pages & APIs
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Main emergency dispatch feed console."""
    stats = db.get_stats()
    return render_template("operator_dashboard.html", stats=stats)


@app.route("/admin/users")
@admin_required
def admin_users():
    """Platform user rosters and console promotion page."""
    all_users = db.get_all_users()
    return render_template("operator_users.html", users=all_users)


@app.route("/admin/logs")
@admin_required
def admin_logs():
    """System activity logs audit page."""
    audit_logs = db.get_admin_logs(limit=100)
    return render_template("operator_logs.html", logs=audit_logs)


@app.route("/api/operator/alerts", methods=["GET"])
@admin_required
def api_get_alerts():
    """GET /api/operator/alerts - Fetch all platform alerts."""
    return jsonify(db.get_all_alerts())


@app.route("/api/operator/contacts/<int:user_id>", methods=["GET"])
@admin_required
def api_get_user_contacts(user_id):
    """GET /api/operator/contacts/<user_id> - Fetch specific user's emergency contacts."""
    contacts = db.get_contacts(user_id)
    return jsonify([dict(c) for c in contacts])


@app.route("/api/operator/change_status/<alert_type>/<int:alert_id>", methods=["POST"])
@admin_required
def api_change_status(alert_type, alert_id):
    """
    POST /api/operator/change_status/<alert_type>/<alert_id>
    """
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    
    valid_statuses = ["sent", "responding", "dispatched", "resolved", "false_alarm"]
    if status not in valid_statuses:
        return jsonify({"success": False, "message": "Invalid status value"}), 400
        
    db.update_alert_status(alert_type, alert_id, status)
    db.log_action(session["user_id"], "UPDATE_STATUS", f"Alert {alert_id} ({alert_type}) set to {status}")
    return jsonify({"success": True})


@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def api_admin_stats():
    """GET /api/admin/stats - Return live system metrics."""
    return jsonify(db.get_stats())


@app.route("/api/admin/make_admin/<int:user_id>", methods=["POST"])
@admin_required
def make_admin(user_id):
    """Promote a registered user to admin/operator role."""
    # Since we use Supabase now, we should update using Supabase client
    db.supabase.table("users").update({"is_admin": True}).eq("id", user_id).execute()
    db.log_action(session["user_id"], "MAKE_ADMIN", f"Promoted user ID {user_id} to Console Operator")
    return jsonify({"success": True})


# ──────────────────────────────────────────────────────────────────────────────
# App Entry Point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Local development server
    print("=" * 60)
    print("  Digital Shield - Unified System (Port 5000)")
    print("  Server running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
else:
    # Vercel serverless entry point
    def handler(event, context):
        """Return the Flask WSGI app for Vercel deployments."""
        return app
