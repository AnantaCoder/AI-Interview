import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(method, path, data=None, headers=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, headers=headers, timeout=10)
        elif method == "POST":
            r = httpx.post(url, json=data, headers=headers, timeout=10)
        
        status = "PASS" if r.status_code < 400 else "FAIL"
        print(f"{status} | {method} {path} -> {r.status_code}")
        if r.status_code >= 400:
            print(f"     Error: {r.json().get('message', r.text)[:100]}")
        return r
    except Exception as e:
        print(f"ERROR | {method} {path} -> {e}")
        return None

print("=" * 60)
print("AUTH ENDPOINT TESTS")
print("=" * 60)

# Test 1: Signup
r = test_endpoint("POST", "/auth/signup", {
    "email": "test_candidate_001@test.com",
    "password": "TestPass123!",
    "user_type": "candidate",
    "full_name": "Test Candidate"
})

# Test 2: Signin
r = test_endpoint("POST", "/auth/signin", {
    "email": "test_candidate_001@test.com",
    "password": "TestPass123!"
})

# Test 3: Google Auth URL
r = test_endpoint("GET", "/auth/google?user_type=candidate")
if r and r.status_code == 200:
    print(f"     Google URL starts with: {r.json().get('url', '')[:50]}...")

# Test 4: Get Me (no token - expected 401)
r = test_endpoint("GET", "/auth/me")

# Test 5: Refresh Token (invalid - expected 401)
r = test_endpoint("POST", "/auth/refresh", {"refresh_token": "invalid"})

# Test 6: Password Reset
r = test_endpoint("POST", "/auth/password/reset", {"email": "test@test.com"})

print("=" * 60)
print("TESTS COMPLETE")
