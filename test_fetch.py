import requests

s = requests.Session()
r = s.post("http://127.0.0.1:5000/EDE/login", data={"email": "etudiant@ensae.sn", "password": "etu123"})
r2 = s.get("http://127.0.0.1:5000/EDE/etudiant")
print("STUDENT DASHBOARD:", r2.status_code)
if r2.status_code == 500:
    print(r2.text)

r = s.post("http://127.0.0.1:5000/EDE/login", data={"email": "admin@ensae.sn", "password": "admin123"})
r3 = s.get("http://127.0.0.1:5000/EDE/admin/etudiants/1")
print("ADMIN ETUDIANT 1:", r3.status_code)
if r3.status_code == 500:
    print(r3.text)

r4 = s.get("http://127.0.0.1:5000/EDE/admin/dashboard")
print("ADMIN DASHBOARD:", r4.status_code)

