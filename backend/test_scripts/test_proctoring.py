import asyncio
import websockets
import requests
import json
import base64
import cv2
import numpy as np
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"
WS_URL = "ws://127.0.0.1:8000/api/v1/ws"

def login_cand():
    print("Logging in as candidate...")
    payload = {
        "email": "cand_test@example.com",
        "password": "password123"
    }
    resp = requests.post(f"{BASE_URL}/auth/signin", json=payload)
    if resp.status_code == 200:
        return resp.json().get("session", {}).get("access_token")
    elif resp.status_code == 404:
        print("Candidate not found. Signing up...")
        signup_payload = {
            "email": "cand_test@example.com",
            "password": "password123",
            "full_name": "Test Candidate",
            "user_type": "candidate"
        }
        resp = requests.post(f"{BASE_URL}/auth/signup", json=signup_payload)
        resp.raise_for_status()
        return login_cand()
    else:
        resp.raise_for_status()

def create_org_campaign_and_apply(cand_token):
    # Org login/signup
    print("Setting up interview...")
    org_payload = {"email": "org_test2@example.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/signin", json=org_payload)
    if resp.status_code == 404:
        requests.post(f"{BASE_URL}/auth/signup", json={**org_payload, "full_name": "Org 2", "user_type": "organization"}).raise_for_status()
        resp = requests.post(f"{BASE_URL}/auth/signin", json=org_payload)
    org_token = resp.json().get("session", {}).get("access_token")
    
    # Create campaign
    camp_payload = {
        "title": "Software Engineer",
        "description": "Desc",
        "required_skills": ["Python"],
        "min_experience_years": 2,
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/campaigns/", json=camp_payload, headers={"Authorization": f"Bearer {org_token}"})
    resp.raise_for_status()
    campaign_id = resp.json().get("id")
    
    # Apply as candidate
    headers = {"Authorization": f"Bearer {cand_token}"}
    resp = requests.post(f"{BASE_URL}/campaigns/{campaign_id}/apply", headers=headers)
    if resp.status_code == 400 and "Already applied" in resp.text:
        # Get existing applications
        resp = requests.get(f"{BASE_URL}/candidates/me/applications", headers=headers)
        interviews = resp.json()
        return interviews[0]["id"]
    
    resp.raise_for_status()
    return resp.json().get("id")

async def test_websocket_proctoring(cand_token, interview_id):
    print("Connecting to proctoring websocket...")
    uri = f"{WS_URL}/proctoring/{interview_id}?token={cand_token}"
    
    # Create a dummy image (e.g. solid color) which will trigger "face not detected"
    # To test actual face detection, we could download a sample face image, but this is enough to test pipeline execution
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (200, 200, 200) # light gray
    
    # Encode to JPEG base64
    _, buffer = cv2.imencode('.jpg', img)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send frame 1
            print("Sending frame 1...")
            await websocket.send(img_b64)
            resp_str = await websocket.recv()
            resp = json.loads(resp_str)
            print("Response 1:", resp)
            
            # Send frame 2
            print("Sending frame 2...")
            await websocket.send(img_b64)
            resp_str = await websocket.recv()
            resp = json.loads(resp_str)
            print("Response 2:", resp)
            
            print("Proctoring WebSocket test completed successfully.")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    cand_token = login_cand()
    interview_id = create_org_campaign_and_apply(cand_token)
    
    # Ensure interview is "IN_PROGRESS"
    resp = requests.post(f"{BASE_URL}/interviews/{interview_id}/start", headers={"Authorization": f"Bearer {cand_token}"})
    # Ignore error if already started
    
    asyncio.run(test_websocket_proctoring(cand_token, interview_id))
