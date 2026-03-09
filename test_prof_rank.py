import os
import requests
import json

app_url = "http://127.0.0.1:8000"

def login(email, mdp):
    r = requests.post(f"{app_url}/auth/login", data={"username":email, "password":mdp})
    return r.json()["access_token"]

tok = login("prof1@ecole.com", "profpass")
print("prof1 token:", tok)

notes = requests.get(f"{app_url}/prof/notes", headers={"Authorization": f"Bearer {tok}"})
print("mes notes:", len(notes.json()))
print("mes notes 1:", notes.json()[0] if len(notes.json()) > 0 else "None")

c_etu = requests.get(f"{app_url}/prof/classes/1/etudiants", headers={"Authorization": f"Bearer {tok}"})
print("etudiants in class 1:", c_etu.json())

c_etu2 = requests.get(f"{app_url}/prof/classes/2/etudiants", headers={"Authorization": f"Bearer {tok}"})
print("etudiants in class 2:", c_etu2.json())

c_inter = requests.get(f"{app_url}/prof/interventions", headers={"Authorization": f"Bearer {tok}"})
print("mes interventions:", c_inter.json())
