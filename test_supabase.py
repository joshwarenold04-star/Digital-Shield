import urllib.request
import json
import os

url = "https://oraxhvfudvqvnemydvpf.supabase.co/rest/v1/users"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9yYXhodmZ1ZHZxdm5lbXlkdnBmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwODAyMTYsImV4cCI6MjA5NjY1NjIxNn0.50ndLtZJ8yMOFQiLTJep-xGomqqNlGPfB2Of75NPB5Y"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

data = {
    "full_name": "Test User",
    "mobile": "1234567890",
    "email": "test@example.com",
    "password_hash": "hash",
    "address": "test address",
    "blood_group": "A+"
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Response:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Error body:", e.read().decode('utf-8'))
except Exception as e:
    print("Error:", str(e))
