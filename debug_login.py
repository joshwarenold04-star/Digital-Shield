"""Verify login works for a@b with password 'password'."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from werkzeug.security import check_password_hash
import urllib.request
import json

url = "https://oraxhvfudvqvnemydvpf.supabase.co/rest/v1/users?email=eq.a%40b&select=id,full_name,email,mobile,is_admin,password_hash"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9yYXhodmZ1ZHZxdm5lbXlkdnBmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwODAyMTYsImV4cCI6MjA5NjY1NjIxNn0.50ndLtZJ8yMOFQiLTJep-xGomqqNlGPfB2Of75NPB5Y"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as response:
    users = json.loads(response.read().decode('utf-8'))

if not users:
    print("[FAIL] User a@b not found!")
else:
    user = users[0]
    print(f"User found: {user['full_name']} ({user['email']})")
    print(f"Is Admin: {user['is_admin']}")
    
    result = check_password_hash(user['password_hash'], 'password')
    if result:
        print("[OK] Password 'password' matches! Login will work.")
    else:
        print("[FAIL] Password check failed!")
