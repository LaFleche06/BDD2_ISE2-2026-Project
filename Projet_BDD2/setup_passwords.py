# ============================================================
# setup_passwords.py - A lancer UNE SEULE FOIS apres create_db.sql
# python setup_passwords.py
# ============================================================

import bcrypt, pyodbc
from config import get_conn_string

comptes = [

    # ADMIN
    ('barry.thierno@ede.sn', 'admin123'),

    # PROFESSEURS
    ('thiaw@ede.sn', 'prof123'),
    ('ndiaye.moussa@ede.sn', 'prof123'),
    ('ba.aissatou@ede.sn', 'prof123'),
    ('sarr.abdou@ede.sn', 'prof123'),

    # ETUDIANTS
    ('ousmane.ndiaye@ede.sn', 'etudiant123'),
    ('fatou.diop@ede.sn', 'etudiant123'),
    ('mamadou.fall@ede.sn', 'etudiant123'),
    ('awa.sarr@ede.sn', 'etudiant123'),
    ('cheikh.kane@ede.sn', 'etudiant123'),
    ('ibrahima.sy@ede.sn', 'etudiant123'),
]

conn   = pyodbc.connect(get_conn_string())
cursor = conn.cursor()

ok = 0

for email, pwd in comptes:
    h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        "UPDATE UTILISATEUR SET mot_de_passe=? WHERE email_utilisateur=?",
        h,
        email
    )

    if cursor.rowcount:
        print(f"[OK] {email}")
        ok += 1
    else:
        print(f"[--] {email} introuvable")

conn.commit()
conn.close()

print(f"\n{ok}/{len(comptes)} mots de passe mis a jour.")
print("Vous pouvez maintenant lancer : python app.py")