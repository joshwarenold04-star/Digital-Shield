"""
=============================================================================
Digital Shield – Smart Emergency Safety System
database.py  |  Database connection and helper utilities (Supabase)
=============================================================================
Project   : Digital Shield – Women & Pregnancy Emergency Safety System
Version   : 1.0.0
Purpose   : Provides CRUD helpers for Supabase PostgreSQL.
Tables    : users, emergency_contacts, emergency_alerts,
            pregnancy_alerts, admin_logs
=============================================================================
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ──────────────────────────────────────────────────────────────────────────────
# Schema Initialization
# ──────────────────────────────────────────────────────────────────────────────
def init_db():
    """No-op for Supabase. Tables must be created via SQL Editor."""
    print("[DB] Supabase connected. Ensure tables are created in Supabase SQL Editor.")

# ──────────────────────────────────────────────────────────────────────────────
# User Helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_user_by_email(email: str):
    response = supabase.table("users").select("*").eq("email", email).execute()
    return response.data[0] if response.data else None

def get_user_by_mobile(mobile: str):
    response = supabase.table("users").select("*").eq("mobile", mobile).execute()
    return response.data[0] if response.data else None

def get_user_by_id(user_id: int):
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else None

def create_user(full_name, mobile, email, password_hash, address="", blood_group=""):
    supabase.table("users").insert({
        "full_name": full_name,
        "mobile": mobile,
        "email": email,
        "password_hash": password_hash,
        "address": address,
        "blood_group": blood_group
    }).execute()

def update_user(user_id, full_name, mobile, address, blood_group):
    supabase.table("users").update({
        "full_name": full_name,
        "mobile": mobile,
        "address": address,
        "blood_group": blood_group
    }).eq("id", user_id).execute()

def get_all_users():
    response = supabase.table("users").select("id, full_name, email, mobile, blood_group, is_admin, created_at").execute()
    return response.data

# ──────────────────────────────────────────────────────────────────────────────
# Emergency Contact Helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_contacts(user_id: int):
    response = supabase.table("emergency_contacts").select("*").eq("user_id", user_id).execute()
    return response.data

def add_contact(user_id, name, phone, relation, contact_type="women"):
    supabase.table("emergency_contacts").insert({
        "user_id": user_id,
        "name": name,
        "phone": phone,
        "relation": relation,
        "type": contact_type
    }).execute()

def delete_contact(contact_id, user_id):
    supabase.table("emergency_contacts").delete().eq("id", contact_id).eq("user_id", user_id).execute()

# ──────────────────────────────────────────────────────────────────────────────
# Alert Helpers
# ──────────────────────────────────────────────────────────────────────────────
def save_women_alert(user_id, latitude, longitude, address, notified):
    supabase.table("emergency_alerts").insert({
        "user_id": user_id,
        "latitude": latitude,
        "longitude": longitude,
        "address": address,
        "notified_contacts": notified
    }).execute()

def save_pregnancy_alert(user_id, latitude, longitude, address, notified):
    supabase.table("pregnancy_alerts").insert({
        "user_id": user_id,
        "latitude": latitude,
        "longitude": longitude,
        "address": address,
        "notified_contacts": notified
    }).execute()

def get_user_alerts(user_id: int):
    """Return combined women + pregnancy alerts for a user, newest first."""
    try:
        w_res = supabase.table("emergency_alerts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    except Exception:
        w_res = type('obj', (object,), {'data': []})()
    try:
        p_res = supabase.table("pregnancy_alerts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    except Exception:
        p_res = type('obj', (object,), {'data': []})()
    
    women = [{"type": "women", **r} for r in w_res.data]
    preg = [{"type": "pregnancy", **r} for r in p_res.data]
    
    all_alerts = women + preg
    all_alerts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return all_alerts

def get_all_alerts():
    """Return all alerts (admin view)."""
    # Supabase join: select user info as well
    w_res = supabase.table("emergency_alerts").select("*, users(*)").execute()
    p_res = supabase.table("pregnancy_alerts").select("*, users(*)").execute()
    
    women = []
    for r in w_res.data:
        u = r.get("users", {}) or {}
        women.append({
            "id": r["id"],
            "user_id": r["user_id"],
            "full_name": u.get("full_name"),
            "mobile": u.get("mobile"),
            "blood_group": u.get("blood_group"),
            "home_address": u.get("address"),
            "type": "Women SOS",
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "address": r["address"],
            "status": r["status"],
            "created_at": r["created_at"]
        })
        
    preg = []
    for r in p_res.data:
        u = r.get("users", {}) or {}
        preg.append({
            "id": r["id"],
            "user_id": r["user_id"],
            "full_name": u.get("full_name"),
            "mobile": u.get("mobile"),
            "blood_group": u.get("blood_group"),
            "home_address": u.get("address"),
            "type": "Pregnancy SOS",
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "address": r["address"],
            "status": r["status"],
            "created_at": r["created_at"]
        })

    all_alerts = women + preg
    all_alerts.sort(key=lambda x: x["created_at"], reverse=True)
    return all_alerts

# ──────────────────────────────────────────────────────────────────────────────
# Admin Log Helpers
# ──────────────────────────────────────────────────────────────────────────────
def log_action(user_id, action, details=""):
    supabase.table("admin_logs").insert({
        "user_id": user_id,
        "action": action,
        "details": details
    }).execute()

def get_admin_logs(limit=50):
    res = supabase.table("admin_logs").select("*, users(full_name)").order("created_at", desc=True).limit(limit).execute()
    logs = []
    for r in res.data:
        logs.append({
            "id": r["id"],
            "full_name": r.get("users", {}).get("full_name") if r.get("users") else None,
            "action": r["action"],
            "details": r["details"],
            "created_at": r["created_at"]
        })
    return logs

def get_stats():
    """Summary statistics for admin dashboard."""
    users_count = supabase.table("users").select("id", count="exact").execute().count
    women_alerts_count = supabase.table("emergency_alerts").select("id", count="exact").execute().count
    preg_alerts_count = supabase.table("pregnancy_alerts").select("id", count="exact").execute().count
    contacts_count = supabase.table("emergency_contacts").select("id", count="exact").execute().count
    
    return {
        "total_users": users_count or 0,
        "total_women_alerts": women_alerts_count or 0,
        "total_pregnancy_alerts": preg_alerts_count or 0,
        "total_contacts": contacts_count or 0,
    }

def update_alert_status(alert_type: str, alert_id: int, status: str):
    """Update status of a women or pregnancy alert."""
    table = "emergency_alerts" if alert_type.lower() in ("women", "women sos") else "pregnancy_alerts"
    supabase.table(table).update({"status": status}).eq("id", alert_id).execute()
