"""
=============================================================================
Digital Shield – Smart Emergency Safety System
app_operator.py  |  Flask Application for Operators & Administrators
=============================================================================
Project   : Digital Shield – Women & Pregnancy Emergency Safety System
Version   : 1.0.0
Description:
    Operator-facing Flask application providing:
    - Session-based operator authentication (login / logout) checking is_admin
    - Dispatch Center console with active and historical alerts feed
    - Dynamic incident inspection (victim details, emergency contacts, map)
    - Status management REST API (responding / dispatched / resolved)
    - Platform roster management (view users, promote to operator)
    - Security audit trails and stats tracking
    Running on http://127.0.0.1:5001
=============================================================================
"""

import json
import os
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from flask_cors import CORS
from werkzeug.security import check_password_hash
import database as db

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# App Configuration
# ──────────────────────────────────────────────────────────────────────────────
_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    static_folder=os.path.join(_dir, "static"),
    template_folder=os.path.join(_dir, "templates"),
)
app.secret_key = os.environ.get("OPERATOR_SECRET_KEY", "digital_shield_operator_secret_key_2024_secure")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching in dev
CORS(app)

# Initialize database on startup
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
# Helper: Operator Login Required Decorators
# ──────────────────────────────────────────────────────────────────────────────
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        user = db.get_user_by_id(session["user_id"])
        if not user or not user["is_admin"]:
            session.clear()
            flash("Operator/Admin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────────────────────────────────────
# Authentication Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    """Operator login – validates credentials and verifies is_admin privilege."""
    if "user_id" in session:
        user = db.get_user_by_id(session["user_id"])
        if user and user["is_admin"]:
            return redirect(url_for("dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            if bool(user["is_admin"]):
                session["user_id"]   = user["id"]
                session["user_name"] = user["full_name"]
                session["is_admin"]  = True
                db.log_action(user["id"], "ADMIN_LOGIN", f"Operator console access: {email}")
                flash(f"Console Access Granted: {user['full_name']} 🛡️", "success")
                return redirect(url_for("dashboard"))
            else:
                db.log_action(user["id"], "ADMIN_LOGIN_FAIL", f"Privilege escalation attempt: {email}")
                flash("Access Denied: This account does not possess operator credentials.", "danger")
        else:
            flash("Invalid operator email or password.", "danger")

    return render_template("operator_login.html")


@app.route("/logout")
@login_required
def logout():
    """End operator session."""
    db.log_action(session.get("user_id"), "ADMIN_LOGOUT", "")
    session.clear()
    flash("Operator console disconnected.", "info")
    return redirect(url_for("login"))


# ──────────────────────────────────────────────────────────────────────────────
# Protected Console Pages
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Main emergency dispatch feed console."""
    stats = db.get_stats()
    return render_template("admin.html", stats=stats)


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


# ──────────────────────────────────────────────────────────────────────────────
# REST API Endpoints for Operator Console
# ──────────────────────────────────────────────────────────────────────────────
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
    Body: { status: 'sent' | 'responding' | 'dispatched' | 'resolved' | 'false_alarm' }
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
    db.supabase.table("users").update({"is_admin": True}).eq("id", user_id).execute()
    db.log_action(session["user_id"], "MAKE_ADMIN", f"Promoted user ID {user_id} to Console Operator")
    return jsonify({"success": True})


# ──────────────────────────────────────────────────────────────────────────────
# App Entry Point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Digital Shield - Operator Console (Port 5001)")
    print("  Server running at: http://127.0.0.1:5001")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5001)
