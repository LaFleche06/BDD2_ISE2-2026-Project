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