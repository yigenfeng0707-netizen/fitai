import requests

def test_login():
    try:
        r = requests.post('http://localhost:8000/api/v1/auth/login', json={'username': 'admin', 'password': 'admin123'})
        print(f"Login - Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Login - Response: {data}")
            return data.get('access_token')
        else:
            print(f"Login - Error: {r.text}")
            return None
    except Exception as e:
        print(f"Login - Exception: {e}")
        return None

def test_members(token):
    if not token:
        print("No token, skipping members test")
        return
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get('http://localhost:8000/api/v1/members', headers=headers)
        print(f"\nMembers - Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Members - Count: {len(data)}")
        else:
            print(f"Members - Error: {r.text}")
    except Exception as e:
        print(f"Members - Exception: {e}")

def test_courses(token):
    if not token:
        print("No token, skipping courses test")
        return
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get('http://localhost:8000/api/v1/courses', headers=headers)
        print(f"\nCourses - Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Courses - Count: {len(data)}")
        else:
            print(f"Courses - Error: {r.text}")
    except Exception as e:
        print(f"Courses - Exception: {e}")

def test_coaches(token):
    if not token:
        print("No token, skipping coaches test")
        return
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get('http://localhost:8000/api/v1/coaches', headers=headers)
        print(f"\nCoaches - Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Coaches - Count: {len(data)}")
        else:
            print(f"Coaches - Error: {r.text}")
    except Exception as e:
        print(f"Coaches - Exception: {e}")

if __name__ == "__main__":
    print("="*50)
    print("Testing FitAI API")
    print("="*50)
    
    token = test_login()
    test_members(token)
    test_courses(token)
    test_coaches(token)
    
    print("\n" + "="*50)
    print("Test completed!")
    print("="*50)