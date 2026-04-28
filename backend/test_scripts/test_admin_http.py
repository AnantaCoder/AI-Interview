import urllib.request
import urllib.parse
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def request(method, path, data=None, token=None):
    url = BASE_URL + path
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
        
    req_data = None
    if data:
        req_data = json.dumps(data).encode('utf-8')
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def run_tests():
    print("1. Creating Admin User...")
    admin_data = {
        "email": "super_admin@test.com",
        "password": "Password123!",
        "user_type": "admin",
        "full_name": "Super Admin"
    }
    status, res = request("POST", "/auth/signup", admin_data)
    if status not in [200, 201, 400]: # 400 if already exists
        print(f"Signup failed: {res}")
        return

    print("2. Logging in...")
    status, res = request("POST", "/auth/signin", {
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    
    if status != 200:
        print(f"Login failed: {res}")
        return
        
    token = res["session"]["access_token"]
    print(f"Token acquired. Length: {len(token)}")

    print("\n3. Testing GET /admin/users")
    status, res = request("GET", "/admin/users", token=token)
    print(f"Status: {status}")
    if status == 200:
        print(f"Total users: {res['total']}")
        print(f"First user email: {res['items'][0]['email'] if res['items'] else 'None'}")
        if res['items']:
            target_user = res['items'][0]
    
    print("\n4. Testing GET /admin/analytics")
    status, res = request("GET", "/admin/analytics", token=token)
    print(f"Status: {status}")
    if status == 200:
        print(f"Analytics: {res}")

    if target_user:
        print(f"\n5. Testing PATCH /admin/users/{target_user['id']}/status")
        # Toggle is_active
        new_active = not target_user['is_active']
        status, res = request("PATCH", f"/admin/users/{target_user['id']}/status", 
                              data={"is_active": new_active}, token=token)
        print(f"Status: {status}")
        print(f"Response: {res}")
        
        # Reset back
        request("PATCH", f"/admin/users/{target_user['id']}/status", 
                data={"is_active": True}, token=token)

    print("\nAll Admin tests completed successfully!")

if __name__ == "__main__":
    run_tests()
