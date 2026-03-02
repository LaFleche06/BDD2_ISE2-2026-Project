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

from .database import get_db 

app = FastAPI()

@app.get("/test-aws")
def test_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT @@VERSION")).fetchone()
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