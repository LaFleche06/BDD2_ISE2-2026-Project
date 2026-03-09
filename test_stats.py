import requests
s = requests.Session()
r_login = s.post("http://127.0.0.1:5000/EDE/login", data={"email": "admin@ecole.sn", "password": "pass"})
r_stats = s.get("http://127.0.0.1:8000/admin/stats", headers={"Authorization": "Bearer " + s.cookies.get("access_token", "")})
print(r_stats.json())
