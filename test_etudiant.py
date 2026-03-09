import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'API'))
from database.session import SessionLocal
from models.models import Etudiant, Utilisateur

db = SessionLocal()
e = db.query(Etudiant).first()
if e:
    print(f"Testing for etudiant {e.matricule} - {e.prenom} {e.nom}")
    import requests
    app_url = "http://127.0.0.1:8000"
    
    # Get token for etudiant
    user = e.utilisateur
    print(f"Login with {user.email}")
    r = requests.post(f"{app_url}/auth/login", data={"username": user.email, "password": "password123"})
    if r.status_code == 200:
        tok = r.json()["access_token"]
        dash = requests.get(f"{app_url}/etudiant/dashboard", headers={"Authorization": f"Bearer {tok}"})
        if dash.status_code == 200:
            d = dash.json()
            print("Dashboard moy:", d.get('moyenne_generale'))
            print("Dashboard rang:", d.get('rang'))
            for n in d.get('notes', []):
                print(f"Matiere: {n.get('matiere')} - Note: {n.get('valeur')} - Rang: {n.get('rang_matiere')}/{n.get('total_etudiants')}")
        else:
            print("Dash error:", dash.text)
    else:
        print("Login failed, status:", r.status_code, r.text)
else:
    print("No etudiant found")
db.close()
