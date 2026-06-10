"""
=============================================================================
Digital Shield – Smart Emergency Safety System
database.py  |  Database initialization and helper utilities
=============================================================================
Project   : Digital Shield – Women & Pregnancy Emergency Safety System
Version   : 1.0.0
Purpose   : Provides SQLite schema creation, CRUD helpers for all 5 tables.
Tables    : users, emergency_contacts, emergency_alerts,
            pregnancy_alerts, admin_logs
=============================================================================
"""

import sqlite3
import os

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
DATABASE = os.path.join(os.path.dirname(__file__), "women_safety.db")


def get_db():
    """Open a new database connection for the current request context."""
    conn = sqlite3.connect(DATABASE, timeout=20)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    # Enable WAL mode for better concurrency and fewer 'database locked' errors
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# Schema Initialization
# ──────────────────────────────────────────────────────────────────────────────
def init_db():
    """Create all database tables if they do not already exist."""
    conn = get_db()
    cursor = conn.cursor()

    # ── Table: users ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            mobile        TEXT    NOT NULL UNIQUE,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            address       TEXT,
            blood_group   TEXT,
            is_admin      INTEGER DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Table: emergency_contacts ─────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name       TEXT    NOT NULL,
            phone      TEXT    NOT NULL,
            relation   TEXT,
            type       TEXT    DEFAULT 'women',   -- 'women' or 'pregnancy'
            created_at TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Table: emergency_alerts (Women SOS) ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_alerts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            latitude      REAL,
            longitude     REAL,
            address       TEXT,
            message       TEXT    DEFAULT 'SOS – Women Emergency',
            status        TEXT    DEFAULT 'sent',
            notified_contacts TEXT,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Table: pregnancy_alerts ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pregnancy_alerts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            latitude      REAL,
            longitude     REAL,
            address       TEXT,
            message       TEXT    DEFAULT 'SOS – Pregnancy Emergency',
            status        TEXT    DEFAULT 'sent',
            notified_contacts TEXT,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Table: admin_logs ─────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action     TEXT    NOT NULL,
            details    TEXT,
            created_at TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] All tables initialized successfully.")


# ──────────────────────────────────────────────────────────────────────────────
# User Helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_user_by_email(email: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user


def get_user_by_mobile(mobile: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE mobile = ?", (mobile,)).fetchone()
    conn.close()
    return user



def get_user_by_id(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def create_user(full_name, mobile, email, password_hash, address="", blood_group=""):
    conn = get_db()
    conn.execute(
        """INSERT INTO users (full_name, mobile, email, password_hash, address, blood_group)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (full_name, mobile, email, password_hash, address, blood_group),
    )
    conn.commit()
    conn.close()


def update_user(user_id, full_name, mobile, address, blood_group):
    conn = get_db()
    conn.execute(
        """UPDATE users SET full_name=?, mobile=?, address=?, blood_group=?
           WHERE id=?""",
        (full_name, mobile, address, blood_group, user_id),
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_db()
    users = conn.execute(
        "SELECT id, full_name, email, mobile, blood_group, is_admin, created_at FROM users"
    ).fetchall()
    conn.close()
    return users


# ──────────────────────────────────────────────────────────────────────────────
# Emergency Contact Helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_contacts(user_id: int):
    conn = get_db()
    contacts = conn.execute(
        "SELECT * FROM emergency_contacts WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return contacts


def add_contact(user_id, name, phone, relation, contact_type="women"):
    conn = get_db()
    conn.execute(
        "INSERT INTO emergency_contacts (user_id, name, phone, relation, type) VALUES (?,?,?,?,?)",
        (user_id, name, phone, relation, contact_type),
    )
    conn.commit()
    conn.close()


def delete_contact(contact_id, user_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM emergency_contacts WHERE id=? AND user_id=?",
        (contact_id, user_id),
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# Alert Helpers
# ──────────────────────────────────────────────────────────────────────────────
def save_women_alert(user_id, latitude, longitude, address, notified):
    conn = get_db()
    conn.execute(
        """INSERT INTO emergency_alerts (user_id, latitude, longitude, address, notified_contacts)
           VALUES (?,?,?,?,?)""",
        (user_id, latitude, longitude, address, notified),
    )
    conn.commit()
    conn.close()


def save_pregnancy_alert(user_id, latitude, longitude, address, notified):
    conn = get_db()
    conn.execute(
        """INSERT INTO pregnancy_alerts (user_id, latitude, longitude, address, notified_contacts)
           VALUES (?,?,?,?,?)""",
        (user_id, latitude, longitude, address, notified),
    )
    conn.commit()
    conn.close()


def get_user_alerts(user_id: int):
    """Return combined women + pregnancy alerts for a user, newest first."""
    conn = get_db()
    women = conn.execute(
        """SELECT id, 'women' as type, latitude, longitude, address, message, status, created_at
           FROM emergency_alerts WHERE user_id=? ORDER BY created_at DESC""",
        (user_id,),
    ).fetchall()
    preg = conn.execute(
        """SELECT id, 'pregnancy' as type, latitude, longitude, address, message, status, created_at
           FROM pregnancy_alerts WHERE user_id=? ORDER BY created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    # Merge and sort by created_at descending
    all_alerts = [dict(r) for r in women] + [dict(r) for r in preg]
    all_alerts.sort(key=lambda x: x["created_at"], reverse=True)
    return all_alerts


def get_all_alerts():
    """Return all alerts (admin view)."""
    conn = get_db()
    women = conn.execute(
        """SELECT ea.id, u.id as user_id, u.full_name, u.mobile, u.blood_group, u.address as home_address, 'Women SOS' as type,
                  ea.latitude, ea.longitude, ea.address, ea.status, ea.created_at
           FROM emergency_alerts ea JOIN users u ON ea.user_id = u.id
           ORDER BY ea.created_at DESC"""
    ).fetchall()
    preg = conn.execute(
        """SELECT pa.id, u.id as user_id, u.full_name, u.mobile, u.blood_group, u.address as home_address, 'Pregnancy SOS' as type,
                  pa.latitude, pa.longitude, pa.address, pa.status, pa.created_at
           FROM pregnancy_alerts pa JOIN users u ON pa.user_id = u.id
           ORDER BY pa.created_at DESC"""
    ).fetchall()
    conn.close()
    all_alerts = [dict(r) for r in women] + [dict(r) for r in preg]
    all_alerts.sort(key=lambda x: x["created_at"], reverse=True)
    return all_alerts


# ──────────────────────────────────────────────────────────────────────────────
# Admin Log Helpers
# ──────────────────────────────────────────────────────────────────────────────
def log_action(user_id, action, details=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO admin_logs (user_id, action, details) VALUES (?,?,?)",
        (user_id, action, details),
    )
    conn.commit()
    conn.close()


def get_admin_logs(limit=50):
    conn = get_db()
    logs = conn.execute(
        """SELECT al.id, u.full_name, al.action, al.details, al.created_at
           FROM admin_logs al
           LEFT JOIN users u ON al.user_id = u.id
           ORDER BY al.created_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in logs]


def get_stats():
    """Summary statistics for admin dashboard."""
    conn = get_db()
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "total_women_alerts": conn.execute("SELECT COUNT(*) FROM emergency_alerts").fetchone()[0],
        "total_pregnancy_alerts": conn.execute("SELECT COUNT(*) FROM pregnancy_alerts").fetchone()[0],
        "total_contacts": conn.execute("SELECT COUNT(*) FROM emergency_contacts").fetchone()[0],
    }
    conn.close()
    return stats


def update_alert_status(alert_type: str, alert_id: int, status: str):
    """Update status of a women or pregnancy alert."""
    conn = get_db()
    table = "emergency_alerts" if alert_type.lower() in ("women", "women sos") else "pregnancy_alerts"
    conn.execute(f"UPDATE {table} SET status=? WHERE id=?", (status, alert_id))
    conn.commit()
    conn.close()
