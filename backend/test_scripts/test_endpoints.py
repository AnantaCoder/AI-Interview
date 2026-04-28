import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_flow():
    # 1. Register candidate
    cand_data = {
        "email": "cand_test@example.com",
        "password": "password123",
        "user_type": "candidate",
        "full_name": "Test Candidate"
    }
    # ignore if already exists
    requests.post(f"{BASE_URL}/auth/signup", json=cand_data)
    
    # Login candidate
    cand_login = requests.post(f"{BASE_URL}/auth/signin", json={
        "email": cand_data["email"],
        "password": cand_data["password"]
    }).json()
    cand_token = cand_login.get("session", {}).get("access_token")
    if not cand_token:
        print("Candidate login failed:", cand_login)
        return

    # 2. Candidate Profile GET
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    r = requests.get(f"{BASE_URL}/candidate/profile", headers=cand_headers)
    print("Candidate Profile GET:", r.status_code)

    # 3. Register Organization
    org_data = {
        "email": "org_test@example.com",
        "password": "password123",
        "user_type": "organization",
        "full_name": "Test Org"
    }
    requests.post(f"{BASE_URL}/auth/signup", json=org_data)
    
    # Login organization
    org_login = requests.post(f"{BASE_URL}/auth/signin", json={
        "email": org_data["email"],
        "password": org_data["password"]
    }).json()
    org_token = org_login.get("session", {}).get("access_token")
    if not org_token:
        print("Organization login failed:", org_login)
        return
        
    org_headers = {"Authorization": f"Bearer {org_token}"}

    # 4. Org Profile GET
    r = requests.get(f"{BASE_URL}/organization/profile", headers=org_headers)
    print("Org Profile GET:", r.status_code)
    
    # 5. Org creates campaign
    campaign_data = {
        "title": "Software Engineer",
        "description": "Looking for a python dev",
    }
    r = requests.post(f"{BASE_URL}/campaigns/", json=campaign_data, headers=org_headers)
    print("Create Campaign:", r.status_code)
    campaign_id = r.json().get("id")

    if not campaign_id:
        print("Campaign creation failed:", r.json())
        return

    # 6. Candidate applies
    r = requests.post(f"{BASE_URL}/campaigns/{campaign_id}/apply", headers=cand_headers)
    print("Candidate Apply:", r.status_code)
    if r.status_code != 200:
        print(r.json())

    # 7. Org fetches applicants
    r = requests.get(f"{BASE_URL}/campaigns/{campaign_id}/applicants", headers=org_headers)
    print("Org Fetch Applicants:", r.status_code)
    applicants = r.json()
    print("Applicants:", len(applicants))

    if applicants:
        cand_id = applicants[0]["candidate"]["id"]
        # 8. Org updates status
        r = requests.patch(f"{BASE_URL}/campaigns/{campaign_id}/applicants/{cand_id}/status", 
                          json={"status": "in_progress", "is_shortlisted": True}, 
                          headers=org_headers)
        print("Org Update Applicant:", r.status_code)
        if r.status_code != 200:
            print(r.json())

    # 9. Candidate fetches applications
    r = requests.get(f"{BASE_URL}/candidate/applications", headers=cand_headers)
    print("Candidate Fetch Applications:", r.status_code)
    if r.status_code == 200:
        print("Applications found:", len(r.json()))
    else:
        print(r.json())

if __name__ == "__main__":
    test_flow()
