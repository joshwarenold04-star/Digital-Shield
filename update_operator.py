from werkzeug.security import generate_password_hash
import sqlite3

conn = sqlite3.connect('women_safety.db')
pw_hash = generate_password_hash('Josh@321')
# Update the existing admin user with the new email and password hash
conn.execute(
    "UPDATE users SET email=?, password_hash=? WHERE id=1",
    ('joshwafrancis03@gmail.com', pw_hash)
)
conn.commit()
conn.close()
print("Operator credentials updated successfully.")
