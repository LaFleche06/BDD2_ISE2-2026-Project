import sys
import os

# Add the project directory to sys.path to import api_client and config
sys.path.append(os.path.abspath('c:/Users/HP/Desktop/temp/TODO/SEMESTRE_1/BDD2/projet/Projet_BDD2'))

import api_client as api
from config import SECRET_KEY

# Simulate a session token. In a real scenario, we'd need a valid one.
# I'll try to find one from the terminal logs if possible, or just assume we might need to login.
# For now, I'll just try to simulate the logic and see if it fails on data structure.

def debug_etudiant(matricule, token):
    print(f"DEBUG: Fetching etudiant {matricule}")
    try:
        etudiant = api.get_etudiant(token, matricule)
        print(f"DEBUG: Etudiant: {etudiant}")
        if not etudiant:
            print("ERROR: Etudiant not found")
            return
            
        notes = api.get_notes_etudiant_admin(token, matricule) or []
        print(f"DEBUG: Found {len(notes)} notes")
        for n in notes:
            print(f"DEBUG: Processing note ID {n.get('id')}")
            try:
                n['valeur'] = float(n['valeur'])
            except Exception as e:
                print(f"DEBUG: Value conversion failed for note {n.get('id')}: {e}")
            
            mat = n.get('matiere') or {}
            try:
                mat['coefficient'] = float(mat.get('coefficient', 1))
            except Exception as e:
                print(f"DEBUG: Coef conversion failed for note {n.get('id')}: {e}")

        interventions = api.get_all_interventions(token) or []
        print(f"DEBUG: Found {len(interventions)} interventions")
        classe_id = etudiant.get('classe_id')
        if classe_id:
            try:
                matieres_classe = list({i['matiere_id']: i['matiere'] for i in interventions if i.get('classe_id') == classe_id}.values())
                print(f"DEBUG: Matieres in class: {len(matieres_classe)}")
            except Exception as e:
                print(f"DEBUG: Matieres extraction failed: {e}")
        else:
            print("DEBUG: No classe_id for student")

        print("DEBUG: All data processing finished successfully")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    # We need a token. I'll print instructions to the user or try to "guess" if there's a test account.
    # Actually, I can't easily get a token without login.
    # I'll check if I can find a token in the terminal logs from previous runs.
    # The user's uvicorn logs showed some activity.
    print("This script needs a valid token and matricule to run.")
    print("Example: python debug_student.py <token> <matricule>")
    if len(sys.argv) > 2:
        debug_etudiant(int(sys.argv[2]), sys.argv[1])
    else:
        print("Missing arguments.")
