# ============================================================
# db.py - Couche acces donnees (schema MCD v3)
# ============================================================
import pyodbc
from config import get_conn_string

def get_connection():
    return pyodbc.connect(get_conn_string())

def query(sql, *params, fetchone=False, fetchall=False, commit=False):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, list(params)) if params else cursor.execute(sql)
    result = None
    if fetchone:
        row    = cursor.fetchone()
        cols   = [c[0] for c in cursor.description] if cursor.description else []
        result = dict(zip(cols, row)) if row else None
    elif fetchall:
        cols   = [c[0] for c in cursor.description] if cursor.description else []
        result = [dict(zip(cols, r)) for r in cursor.fetchall()]
    if commit:
        conn.commit()
    conn.close()
    return result

# ── AUTH ──────────────────────────────────────────────────────────────────────
def get_user_by_email(email):
    return query(
        "SELECT * FROM UTILISATEUR WHERE email_utilisateur=? AND actif=1",
        email, fetchone=True)

# ── ETUDIANTS ─────────────────────────────────────────────────────────────────
def get_all_etudiants():
    return query("""
        SELECT e.*, c.libelle_classe, c.annee_scolaire
        FROM ETUDIANT e
        LEFT JOIN Classe c ON e.Classe_id_classe = c.id_classe
        ORDER BY e.nom, e.prenom
    """, fetchall=True)

def get_etudiant(matricule):
    return query("""
        SELECT e.*, c.libelle_classe, c.annee_scolaire
        FROM ETUDIANT e
        LEFT JOIN Classe c ON e.Classe_id_classe = c.id_classe
        WHERE e.matricule=?
    """, matricule, fetchone=True)

def get_etudiant_by_user(user_id):
    return query("""
        SELECT e.*, c.libelle_classe, c.annee_scolaire
        FROM ETUDIANT e
        LEFT JOIN Classe c ON e.Classe_id_classe = c.id_classe
        WHERE e.UTILISATEUR_id_utilisateur=?
    """, user_id, fetchone=True)

def add_etudiant(nom, prenom, email, telephone, classe_id, hpwd):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO UTILISATEUR (email_utilisateur,mot_de_passe,role_utilisateur) VALUES (?,?,'etudiant')",
        email, hpwd)
    cursor.execute("SELECT SCOPE_IDENTITY()")
    uid = int(cursor.fetchone()[0])
    cursor.execute(
        "INSERT INTO ETUDIANT (Classe_id_classe,UTILISATEUR_id_utilisateur,nom,prenom,telephone_etudiant) VALUES (?,?,?,?,?)",
        classe_id or None, uid, nom, prenom, telephone)
    conn.commit(); conn.close()

def update_etudiant(matricule, nom, prenom, telephone, classe_id):
    query("UPDATE ETUDIANT SET nom=?,prenom=?,telephone_etudiant=?,Classe_id_classe=? WHERE matricule=?",
          nom, prenom, telephone, classe_id or None, matricule, commit=True)

def delete_etudiant(matricule):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT UTILISATEUR_id_utilisateur FROM ETUDIANT WHERE matricule=?", matricule)
    row = cursor.fetchone()
    cursor.execute("DELETE FROM NOTES    WHERE ETUDIANT_matricule=?", matricule)
    cursor.execute("DELETE FROM RESULTAT WHERE ETUDIANT_matricule=?", matricule)
    cursor.execute("DELETE FROM ETUDIANT WHERE matricule=?", matricule)
    if row:
        cursor.execute("DELETE FROM UTILISATEUR WHERE id_utilisateur=?", row[0])
    conn.commit(); conn.close()

def get_etudiants_by_classe(classe_id):
    return query("""
        SELECT e.*, c.libelle_classe
        FROM ETUDIANT e
        LEFT JOIN Classe c ON e.Classe_id_classe = c.id_classe
        WHERE e.Classe_id_classe=? ORDER BY e.nom
    """, classe_id, fetchall=True)

# ── PROFESSEURS ───────────────────────────────────────────────────────────────
def get_all_professeurs():
    return query("SELECT * FROM PROFESSEUR ORDER BY nom_prof", fetchall=True)

def get_professeur(pid):
    return query("SELECT * FROM PROFESSEUR WHERE id_prof=?", pid, fetchone=True)

def get_professeur_by_user(user_id):
    return query("SELECT * FROM PROFESSEUR WHERE UTILISATEUR_id_utilisateur=?", user_id, fetchone=True)

def add_professeur(nom, prenom, email, telephone, hpwd):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO UTILISATEUR (email_utilisateur,mot_de_passe,role_utilisateur) VALUES (?,?,'professeur')",
        email, hpwd)
    cursor.execute("SELECT SCOPE_IDENTITY()")
    uid = int(cursor.fetchone()[0])
    cursor.execute(
        "INSERT INTO PROFESSEUR (UTILISATEUR_id_utilisateur,nom_prof,prenom_prof,telephone_prof) VALUES (?,?,?,?)",
        uid, nom, prenom, telephone)
    conn.commit(); conn.close()

def update_professeur(pid, nom, prenom, telephone):
    query("UPDATE PROFESSEUR SET nom_prof=?,prenom_prof=?,telephone_prof=? WHERE id_prof=?",
          nom, prenom, telephone, pid, commit=True)

def delete_professeur(pid):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT UTILISATEUR_id_utilisateur FROM PROFESSEUR WHERE id_prof=?", pid)
    row = cursor.fetchone()
    cursor.execute("DELETE FROM INTERVIENT WHERE PROFESSEUR_id_prof=?", pid)
    cursor.execute("DELETE FROM NOTES      WHERE PROFESSEUR_id_prof=?", pid)
    cursor.execute("DELETE FROM PROFESSEUR WHERE id_prof=?", pid)
    if row:
        cursor.execute("DELETE FROM UTILISATEUR WHERE id_utilisateur=?", row[0])
    conn.commit(); conn.close()

def get_matieres_professeur(prof_id):
    return query("""
        SELECT m.*, c.libelle_classe, c.id_classe
        FROM INTERVIENT i
        JOIN MATIERES m ON i.MATIERES_id_matiere = m.id_matiere
        JOIN Classe   c ON i.Classe_id_classe    = c.id_classe
        WHERE i.PROFESSEUR_id_prof=?
    """, prof_id, fetchall=True)

def get_classes_professeur(prof_id):
    return query("""
        SELECT DISTINCT c.*
        FROM Classe c
        JOIN INTERVIENT i ON i.Classe_id_classe = c.id_classe
        WHERE i.PROFESSEUR_id_prof=?
    """, prof_id, fetchall=True)

def affecter_professeur(prof_id, matiere_id, classe_id):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM INTERVIENT
            WHERE PROFESSEUR_id_prof=? AND MATIERES_id_matiere=? AND Classe_id_classe=?)
        INSERT INTO INTERVIENT (PROFESSEUR_id_prof,MATIERES_id_matiere,Classe_id_classe)
        VALUES (?,?,?)
    """, prof_id, matiere_id, classe_id, prof_id, matiere_id, classe_id)
    conn.commit(); conn.close()

def retirer_affectation(prof_id, matiere_id, classe_id):
    query("DELETE FROM INTERVIENT WHERE PROFESSEUR_id_prof=? AND MATIERES_id_matiere=? AND Classe_id_classe=?",
          prof_id, matiere_id, classe_id, commit=True)

# ── CLASSES ───────────────────────────────────────────────────────────────────
def get_all_classes():
    return query("SELECT * FROM Classe ORDER BY libelle_classe", fetchall=True)

def get_classe(cid):
    return query("SELECT * FROM Classe WHERE id_classe=?", cid, fetchone=True)

def add_classe(libelle, annee):
    query("INSERT INTO Classe (libelle_classe,annee_scolaire) VALUES (?,?)", libelle, annee, commit=True)

def update_classe(cid, libelle, annee):
    query("UPDATE Classe SET libelle_classe=?,annee_scolaire=? WHERE id_classe=?", libelle, annee, cid, commit=True)

def delete_classe(cid):
    query("DELETE FROM Classe WHERE id_classe=?", cid, commit=True)

# ── MATIERES ──────────────────────────────────────────────────────────────────
def get_all_matieres():
    return query("SELECT * FROM MATIERES ORDER BY nom_matiere", fetchall=True)

def get_matiere(mid):
    return query("SELECT * FROM MATIERES WHERE id_matiere=?", mid, fetchone=True)

def add_matiere(nom, coefficient, volume_horaire):
    query("INSERT INTO MATIERES (nom_matiere,coefficient_matiere,volume_horaire) VALUES (?,?,?)",
          nom, coefficient, volume_horaire, commit=True)

def update_matiere(mid, nom, coefficient, volume_horaire):
    query("UPDATE MATIERES SET nom_matiere=?,coefficient_matiere=?,volume_horaire=? WHERE id_matiere=?",
          nom, coefficient, volume_horaire, mid, commit=True)

def delete_matiere(mid):
    query("DELETE FROM MATIERES WHERE id_matiere=?", mid, commit=True)

# ── NOTES ─────────────────────────────────────────────────────────────────────
def get_notes_etudiant(matricule):
    return query(
        "SELECT * FROM VUE_NOTES_COMPLETES WHERE matricule=? ORDER BY nom_matiere",
        matricule, fetchall=True)

def get_notes_classe(classe_id):
    return query(
        "SELECT * FROM VUE_NOTES_COMPLETES WHERE id_classe=? ORDER BY nom_etudiant, nom_matiere",
        classe_id, fetchall=True)

def get_all_notes():
    return query(
        "SELECT * FROM VUE_NOTES_COMPLETES ORDER BY nom_etudiant, nom_matiere",
        fetchall=True)

def add_note(matricule, matiere_id, prof_id, valeur, date_saisie):

    try:
        val = float(valeur)
    except Exception:
        return False, "Note invalide."

    if not (0 <= val <= 20):
        return False, "La note doit etre entre 0 et 20."

    val = round(val, 2)

    conn = get_connection()
    cursor = conn.cursor()

    # VERIFIER que le professeur enseigne cette matiere dans la classe de l'etudiant
    cursor.execute("""
        SELECT COUNT(*)
        FROM INTERVIENT i
        JOIN ETUDIANT e ON e.Classe_id_classe = i.Classe_id_classe
        WHERE i.PROFESSEUR_id_prof = ?
        AND i.MATIERES_id_matiere = ?
        AND e.matricule = ?
    """, prof_id, matiere_id, matricule)

    if cursor.fetchone()[0] == 0:
        conn.close()
        return False, "Vous n'enseignez pas cette matiere pour cet etudiant."

    # verifier si une note existe deja
    cursor.execute("""
        SELECT COUNT(*)
        FROM NOTES
        WHERE ETUDIANT_matricule=? AND MATIERES_id_matiere=?
    """, matricule, matiere_id)

    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "Une note existe deja pour cet etudiant dans cette matiere."

    # insertion
    cursor.execute("""
        INSERT INTO NOTES
        (MATIERES_id_matiere, PROFESSEUR_id_prof, ETUDIANT_matricule, valeur_note, date_saisie)
        VALUES (?,?,?,?,?)
    """, matiere_id, prof_id, matricule, val, date_saisie)

    conn.commit()
    conn.close()

    return True, "Note ajoutee avec succes."

def update_note(note_id, valeur, prof_id):

    try:
        val = float(valeur)
    except Exception:
        return False, "Note invalide."

    if not (0 <= val <= 20):
        return False, "La note doit etre entre 0 et 20."

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE NOTES
        SET valeur_note = ?
        WHERE id_notes = ?
        AND PROFESSEUR_id_prof = ?
    """, val, note_id, prof_id)

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return False, "Modification non autorisee."

    conn.close()

    return True, "Note modifiee."

def delete_note(note_id, prof_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM NOTES
        WHERE id_notes = ?
        AND PROFESSEUR_id_prof = ?
    """, note_id, prof_id)

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return False, "Suppression non autorisee."

    conn.close()

    return True, "Note supprimee."

# ── STATISTIQUES & VUES ───────────────────────────────────────────────────────
def get_classement_classe(classe_id):
    return query(
        "SELECT * FROM VUE_CLASSEMENT_CLASSE WHERE id_classe=? ORDER BY rang",
        classe_id, fetchall=True)

def get_stats_classe(classe_id):
    r = query("SELECT * FROM VUE_STATS_CLASSE WHERE id_classe=?", classe_id, fetchone=True)
    return r or {
        'nb_etudiants':0,'moyenne_classe':0,'note_max':0,
        'note_min':0,'nb_admis':0,'nb_ajournes':0,'taux_reussite':0}

def get_stats_globales():
    r = query("SELECT * FROM VUE_STATS_GLOBALES", fetchone=True)
    return r or {
        'nb_etudiants':0,'nb_professeurs':0,'nb_classes':0,
        'nb_matieres':0,'nb_notes':0,'moyenne_globale':0}

def get_moyennes_etudiant(matricule):
    notes = get_notes_etudiant(matricule)
    if not notes:
        return [], 0.0
    tc  = sum(float(n['coefficient_matiere']) for n in notes)
    if tc == 0:
        return notes, 0.0
    moy = sum(float(n['valeur_note']) * float(n['coefficient_matiere']) for n in notes) / tc
    return notes, round(moy, 2)

def calculer_et_sauver_resultats(classe_id, annee_scolaire):
    classement = get_classement_classe(classe_id)
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM RESULTAT WHERE Classe_id_classe=? AND annee_scolaire=?",
        classe_id, annee_scolaire)
    for r in classement:
        cursor.execute("""
            INSERT INTO RESULTAT
              (Classe_id_classe,ETUDIANT_matricule,moyenne_generale,decision,annee_scolaire,rang)
            VALUES (?,?,?,?,?,?)
        """, classe_id, r['matricule'], r['moyenne_generale'],
             r['decision'], annee_scolaire, r['rang'])
    conn.commit(); conn.close()
    return len(classement)

def get_resultats_classe(classe_id):
    return query(
        "SELECT * FROM VUE_RESULTATS_COMPLETS WHERE id_classe=? ORDER BY rang",
        classe_id, fetchall=True)