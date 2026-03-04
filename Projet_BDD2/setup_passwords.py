# ============================================================
# setup_passwords.py - A lancer UNE SEULE FOIS apres create_db.sql
# python setup_passwords.py
# ============================================================
import bcrypt, pyodbc
from config import get_conn_string

comptes = [
    ('admin@ede.ca',   'admin123'),
    ('dupont@ede.ca',  'prof123'),
    ('martin@ede.ca',  'prof123'),
    ('leblanc@ede.ca', 'prof123'),
    ('alice@ede.ca',   'etudiant123'),
    ('marc@ede.ca',    'etudiant123'),
    ('sophie@ede.ca',  'etudiant123'),
    ('karim@ede.ca',   'etudiant123'),
]

conn   = pyodbc.connect(get_conn_string())
cursor = conn.cursor()
ok = 0
for email, pwd in comptes:
    h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    cursor.execute("UPDATE UTILISATEUR SET mot_de_passe=? WHERE email_utilisateur=?", h, email)
    if cursor.rowcount:
        print(f"  [OK] {email}")
        ok += 1
    else:
        print(f"  [--] {email} introuvable")
conn.commit()
conn.close()
print(f"\n{ok}/{len(comptes)} mots de passe mis a jour.")
print("Vous pouvez maintenant lancer : python app.py")
