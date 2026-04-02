import requests
import os

API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not API_KEY:
    raise SystemExit("Missing GOOGLE_API_KEY environment variable")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
headers = {"Content-Type": "application/json"}
data = {"contents": [{"parts": [{"text": "Test"}]}]}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
