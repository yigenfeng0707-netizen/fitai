import requests

base_url = "http://localhost:8000"

def test_login(username, password):
    print(f"\n=== Testing login: {username}/{password} ===")
    try:
        r = requests.post(f"{base_url}/api/v1/auth/login", 
                        data={"username": username, "password": password})
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print("Success!")
            print(f"  Access Token: {data.get('access_token')[:20]}...")
            print(f"  User: {data.get('username')}, Role: {data.get('role_id')}")
            return data.get('access_token')
        else:
            print(f"Error: {r.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_get_members(token):
    print("\n=== Testing members API ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{base_url}/api/v1/members", headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Found {len(data)} members")
            for m in data[:3]:
                print(f"  - {m.get('name')}, Phone: {m.get('phone')}")
    except Exception as e:
        print(f"Exception: {e}")

def test_get_courses(token):
    print("\n=== Testing courses API ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{base_url}/api/v1/courses", headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Found {len(data)} courses")
            for c in data[:3]:
                print(f"  - {c.get('name')}, Price: {c.get('price')}")
    except Exception as e:
        print(f"Exception: {e}")

def test_get_schedules(token):
    print("\n=== Testing schedules API ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{base_url}/api/v1/courses/schedules", headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Found {len(data)} schedules")
            for s in data[:3]:
                print(f"  - {s.get('date')} {s.get('start_time')}-{s.get('end_time')}")
    except Exception as e:
        print(f"Exception: {e}")

def test_get_coaches(token):
    print("\n=== Testing coaches API ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{base_url}/api/v1/coaches", headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Found {len(data)} coaches")
            for c in data[:3]:
                print(f"  - {c.get('name')}, Specialty: {c.get('specialty')}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("="*60)
    print("     FitAI API Demo Test")
    print("="*60)
    
    token = test_login("admin", "admin123")
    
    if token:
        test_get_members(token)
        test_get_courses(token)
        test_get_schedules(token)
        test_get_coaches(token)
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)