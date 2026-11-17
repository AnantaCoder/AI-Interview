import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"

def login_org():
    print("Logging in as organization...")
    payload = {
        "email": "org_test@example.com",
        "password": "password123"
    }
    resp = requests.post(f"{BASE_URL}/auth/signin", json=payload)
    if resp.status_code == 200:
        return resp.json().get("session", {}).get("access_token")
    elif resp.status_code == 404:
        # Org doesn't exist, create it
        print("Org not found. Signing up...")
        signup_payload = {
            "email": "org_test@example.com",
            "password": "password123",
            "full_name": "Test Organization",
            "user_type": "organization"
        }
        resp = requests.post(f"{BASE_URL}/auth/signup", json=signup_payload)
        resp.raise_for_status()
        return login_org()
    else:
        resp.raise_for_status()

def create_campaign(token):
    print("Creating a test campaign...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": "Senior Python Developer",
        "description": "Looking for a Python dev with FastAPI experience.",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["React"],
        "min_experience_years": 5,
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/campaigns/", json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json().get("id")

def test_generate_questions(token, campaign_id):
    print("Testing question generation...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "num_questions": 3,
        "question_type": "technical",
        "difficulty": "hard"
    }
    resp = requests.post(f"{BASE_URL}/campaigns/{campaign_id}/generate-questions", json=payload, headers=headers)
    if resp.status_code == 200:
        questions = resp.json()
        print(f"Success! Generated {len(questions)} questions.")
        for i, q in enumerate(questions):
            print(f"Q{i+1}: {q['question_text']} (Type: {q['question_type']})")
    else:
        print(f"Failed to generate questions. Status: {resp.status_code}, Resp: {resp.text}")

if __name__ == "__main__":
    token = login_org()
    campaign_id = create_campaign(token)
    test_generate_questions(token, campaign_id)
