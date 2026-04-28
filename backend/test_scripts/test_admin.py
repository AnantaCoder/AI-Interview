from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_session_maker
from app.db.models.user import User

client = TestClient(app)

def test_admin_endpoints():
    print("Testing Admin Endpoints...")
    
    # 1. Create an admin user via signup endpoint
    admin_data = {
        "email": "admin_test@example.com",
        "password": "adminpassword",
        "user_type": "admin",
        "full_name": "Super Admin"
    }
    
    res = client.post("/api/v1/auth/signup", json=admin_data)
    # Ignore if already exists
    
    login_res = client.post("/api/v1/auth/signin", json={
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    
    if login_res.status_code != 200:
        print("Failed to login as admin:", login_res.json())
        return
        
    token = login_res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test GET /admin/users
    print("\n--- Testing GET /admin/users ---")
    users_res = client.get("/api/v1/admin/users", headers=headers)
    print("Status:", users_res.status_code)
    if users_res.status_code == 200:
        data = users_res.json()
        print(f"Total Users: {data['total']}")
        print(f"First User: {data['items'][0]['email'] if data['items'] else 'None'}")
    else:
        print("Error:", users_res.json())

    # 3. Test GET /admin/analytics
    print("\n--- Testing GET /admin/analytics ---")
    analytics_res = client.get("/api/v1/admin/analytics", headers=headers)
    print("Status:", analytics_res.status_code)
    if analytics_res.status_code == 200:
        print("Analytics Data:", analytics_res.json())
    else:
        print("Error:", analytics_res.json())
        
    # 4. Test PATCH /admin/users/{user_id}/status
    print("\n--- Testing PATCH /admin/users/{user_id}/status ---")
    if users_res.status_code == 200 and users_res.json()['items']:
        target_user_id = users_res.json()['items'][0]['id']
        patch_res = client.patch(f"/api/v1/admin/users/{target_user_id}/status", 
                               json={"is_active": False, "email_verified": "Y"}, 
                               headers=headers)
        print("Status:", patch_res.status_code)
        print("Response:", patch_res.json())
        
        # Reset it back to active so we don't break the user
        client.patch(f"/api/v1/admin/users/{target_user_id}/status", 
                    json={"is_active": True}, 
                    headers=headers)
    
    print("\nAdmin tests completed.")

if __name__ == "__main__":
    test_admin_endpoints()
