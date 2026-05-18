import requests

try:
    r = requests.get('http://localhost:8000/')
    print('Root:', r.status_code)
except:
    print('Root failed')

try:
    r = requests.post('http://localhost:8000/api/v1/auth/login', data={'username':'admin','password':'admin123'})
    print('Login:', r.status_code)
    if r.status_code == 200:
        data = r.json()
        token = data.get('access_token')
        print('Token received')
        
        headers = {'Authorization': 'Bearer ' + token}
        r2 = requests.get('http://localhost:8000/api/v1/members', headers=headers)
        print('Members:', r2.status_code, len(r2.json()) if r2.status_code == 200 else 'error')
        
        r3 = requests.get('http://localhost:8000/api/v1/courses', headers=headers)
        print('Courses:', r3.status_code, len(r3.json()) if r3.status_code == 200 else 'error')
except Exception as e:
    print('Error:', str(e))

print('Done')