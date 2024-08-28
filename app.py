from flask import Flask, request, jsonify
import requests
import os
import hmac
import hashlib
import json

app = Flask(__name__)

GITHUB_SECRET = os.getenv('GITHUB_SECRET')
ASANA_PERSONAL_ACCESS_TOKEN = os.getenv('ASANA_PERSONAL_ACCESS_TOKEN')
ASANA_PROJECT_ID = os.getenv('ASANA_PROJECT_ID')

def verify_github_signature(payload, signature):
    secret = GITHUB_SECRET.encode()
    computed_signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={computed_signature}", signature)

def create_asana_task(issue):
    headers = {
        "Authorization": f"Bearer {ASANA_PERSONAL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    task_data = {
        "data": {
            "name": issue["title"],
            "notes": issue["body"],
            "projects": [ASANA_PROJECT_ID],
            "assignee": issue["assignee"]["login"] if issue["assignee"] else None,
            "due_on": "2024-12-31"  # Default due date or extract from labels if available
        }
    }
    
    response = requests.post('https://app.asana.com/api/1.0/tasks', headers=headers, json=task_data)
    return response.json()

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    payload = request.get_data()

    if not verify_github_signature(payload, signature):
        return jsonify({"error": "Invalid signature"}), 400

    data = request.json
    if data.get('action') == 'opened' and data.get('issue'):
        issue = data['issue']
        asana_response = create_asana_task(issue)
        return jsonify(asana_response), 200

    return jsonify({"message": "Not an issue creation event"}), 200

if __name__ == '__main__':
    app.run(port=5000)
