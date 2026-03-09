import requests

s = requests.Session()
r = s.post("http://127.0.0.1:5000/EDE/login", data={"email": "admin@ensae.sn", "password": "admin123"})
r2 = s.get("http://127.0.0.1:5000/EDE/dashboard")
print("ADMIN DASHBOARD:", r2.status_code)
if r2.status_code == 500:
    print(r2.text[:1000])

