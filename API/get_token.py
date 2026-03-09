import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.security import create_access_token
from database.session import SessionLocal
from models.models import Utilisateur
db = SessionLocal()
admin = db.query(Utilisateur).filter(Utilisateur.role == 'admin').first()
if admin:
    token = create_access_token(data={"sub": admin.email, "role": admin.role})
    print(token)
