# ============================================================
# config.py - Modifier avec vos paramètres SQL Server
# ============================================================

DB_SERVER   = 'DESKTOP-XXXX\\SQLEXPRESS'
DB_NAME     = 'EtudiantDB'
DB_USER     = 'sa'
DB_PASSWORD = 'VotreMotDePasse'

DB_DRIVER   = 'ODBC Driver 17 for SQL Server'
SECRET_KEY  = 'ede-secret-key-2024'

def get_conn_string():
    return (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=5;"
    )
