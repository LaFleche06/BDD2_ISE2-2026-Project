# ============================================================
# config.py - Configuration SQL Server
# ============================================================

import os


# ------------------------------------------------------------
# Paramètres base de données
# ------------------------------------------------------------

# Si variables d'environnement existent → on les utilise
# sinon on prend les valeurs par défaut pour le développement

DB_SERVER   = os.getenv("DB_SERVER", r"SARAH-LAURE\IS2_DB")
DB_NAME     = os.getenv("DB_NAME", "EtudiantDB")
DB_USER     = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ensae")

DB_DRIVER = "ODBC Driver 17 for SQL Server"


# ------------------------------------------------------------
# Flask
# ------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "ede-secret-key-2024")


# ------------------------------------------------------------
# Connection string SQL Server
# ------------------------------------------------------------

def get_conn_string():
    return (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )