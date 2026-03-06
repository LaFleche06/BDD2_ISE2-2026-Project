"""
API exposant un endpoint de test
permettant de vérifier la connexion à une base de données AWS RDS.

L’endpoint /test-aws :
- Injecte une session SQLAlchemy
- Exécute une requête SQL simple
- Retourne la version du serveur si la connexion réussit
- Retourne un message d’erreur en cas d’échec

"""

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.session import get_db,engine

from models.models import Base                 
from routers import auth

app = FastAPI(title="version en dev : API BDD2")

# Crée les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)         

app.include_router(auth.router) 

@app.get("/test-aws")
def test_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT @@VERSION")).fetchone()
        if result is None:
            return {
                "status": "Error",
                "message": "Aucun résultat retourné"
            }
        return {
            "status": "Success",
            "message": "Connexion à AWS RDS réussie !",
            "sql_server_version": result[0]
        }
    except Exception as e:
        return {
            "status": "Error",
            "message": str(e)
        }             
