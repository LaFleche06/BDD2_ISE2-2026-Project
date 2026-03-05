# ============================================================
# app.py - Application Flask EDE v3
# ============================================================
from flask import Flask, render_template, request, redirect, url_for, session, flash
import bcrypt, db
from config import SECRET_KEY
from datetime import date

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── HELPERS ───────────────────────────────────────────────────────────────────
def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('Veuillez vous connecter.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Acces non autorise.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

def note_color(val):
    if val is None: return 'grey'
    v = float(val)
    if v >= 14: return 'note-good'
    if v >= 10: return 'note-avg'
    return 'note-bad'

app.jinja_env.globals['note_color'] = note_color
app.jinja_env.globals['today'] = lambda: date.today().isoformat()

# ── PAGES PUBLIQUES ───────────────────────────────────────────────────────────
@app.route('/EDE/')
@app.route('/EDE/index')
def index():
    return render_template('index.html')

@app.route('/EDE/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        pwd   = request.form.get('password','').strip()
        user  = db.get_user_by_email(email)
        if user and bcrypt.checkpw(pwd.encode(), user['mot_de_passe'].encode()):
            session.clear()
            session['user_id'] = user['id_utilisateur']
            session['role']    = user['role_utilisateur']
            if user['role_utilisateur'] == 'etudiant':
                e = db.get_etudiant_by_user(user['id_utilisateur'])
                if e:
                    session['entity_id'] = e['matricule']
                    session['nom']       = f"{e['prenom']} {e['nom']}"
            elif user['role_utilisateur'] == 'professeur':
                p = db.get_professeur_by_user(user['id_utilisateur'])
                if p:
                    session['entity_id'] = p['id_prof']
                    session['nom']       = f"{p['prenom_prof']} {p['nom_prof']}"
            else:
                session['entity_id'] = user['id_utilisateur']
                session['nom']       = 'Administrateur'
            return redirect(url_for('dashboard'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('login.html')

@app.route('/EDE/logout')
def logout():
    session.clear()
    flash('Vous avez ete deconnecte. Entrez vos identifiants pour vous reconnecter.', 'success')
    return redirect(url_for('login'))

@app.route('/EDE/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    r = session.get('role')
    if r == 'etudiant':   return redirect(url_for('etudiant_dashboard'))
    if r == 'professeur': return redirect(url_for('prof_dashboard'))
    return redirect(url_for('admin_dashboard'))

@app.route('/EDE/test-db')
def test_db():
    try:
        conn = db.get_connection()
        conn.close()
        status = True
    except Exception as e:
        status = False
    return render_template('test_db.html', status=status)

# ── ETUDIANT ──────────────────────────────────────────────────────────────────
@app.route('/EDE/etudiant')
@login_required('etudiant')
def etudiant_dashboard():
    e = db.get_etudiant(session['entity_id'])
    notes, moy = db.get_moyennes_etudiant(session['entity_id'])
    classement  = db.get_classement_classe(e['Classe_id_classe']) if e else []
    rang = next((r['rang'] for r in classement if r['matricule'] == session['entity_id']), '-')
    return render_template('etudiant/dashboard.html', etudiant=e, moyenne=moy, rang=rang, nb_notes=len(notes))

@app.route('/EDE/etudiant/profil')
@login_required('etudiant')
def etudiant_profil():
    e = db.get_etudiant(session['entity_id'])
    return render_template('etudiant/profil.html', etudiant=e)

@app.route('/EDE/etudiant/notes')
@login_required('etudiant')
def etudiant_notes():
    notes, moy = db.get_moyennes_etudiant(session['entity_id'])
    decision = 'Admis' if moy >= 12 else 'Ajourne'
    return render_template('etudiant/notes.html', notes=notes, moyenne=moy, decision=decision)

# ── PROFESSEUR ────────────────────────────────────────────────────────────────
@app.route('/EDE/professeur')
@login_required('professeur')
def prof_dashboard():
    prof    = db.get_professeur(session['entity_id'])
    classes = db.get_classes_professeur(session['entity_id'])
    matieres= db.get_matieres_professeur(session['entity_id'])
    return render_template('prof/dashboard.html', prof=prof, classes=classes, matieres=matieres)

@app.route('/EDE/professeur/notes', methods=['GET','POST'])
@login_required('professeur')
def prof_notes():
    classes  = db.get_classes_professeur(session['entity_id'])
    classe_id= request.args.get('classe_id', type=int) or (classes[0]['id_classe'] if classes else None)
    etudiants= db.get_etudiants_by_classe(classe_id) if classe_id else []
    matieres = db.get_matieres_professeur(session['entity_id'])
    prof_id = session['entity_id']
    notes = db.query("""
                     SELECT *
                     FROM VUE_NOTES_COMPLETES
                     WHERE id_classe = ?
                       AND id_prof = ?
                     ORDER BY nom_etudiant, nom_matiere
                     """, classe_id, prof_id, fetchall=True) if classe_id else []

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'ajouter':
            ok, msg = db.add_note(
                request.form.get('matricule', type=int),
                request.form.get('matiere_id', type=int),
                session['entity_id'],
                request.form.get('valeur_note'),
                request.form.get('date_saisie') or date.today().isoformat())
            flash(msg, 'success' if ok else 'danger')
        elif action == 'modifier':
            ok, msg = db.update_note(
                request.form.get('note_id', type=int),
                request.form.get('valeur_note'),
                session['entity_id']
            )
            flash(msg, 'success' if ok else 'danger')
        elif action == 'supprimer':
            ok, msg = db.delete_note(
                request.form.get('note_id', type=int),
                session['entity_id']
            )
            flash(msg, 'success' if ok else 'danger')
        return redirect(url_for('prof_notes', classe_id=classe_id))

    return render_template('prof/notes.html',
        classes=classes, classe_id=classe_id,
        etudiants=etudiants, matieres=matieres, notes=notes)

@app.route('/EDE/professeur/moyennes')
@login_required('professeur')
def prof_moyennes():
    classes  = db.get_classes_professeur(session['entity_id'])
    classe_id= request.args.get('classe_id', type=int) or (classes[0]['id_classe'] if classes else None)
    classement = db.get_classement_classe(classe_id) if classe_id else []
    stats      = db.get_stats_classe(classe_id) if classe_id else {}
    return render_template('prof/moyennes.html',
        classes=classes, classe_id=classe_id, classement=classement, stats=stats)

@app.route('/EDE/professeur/classe')
@login_required('professeur')
def prof_classe():
    classes = db.get_classes_professeur(session['entity_id'])
    return render_template('prof/classe.html', classes=classes)

# ── ADMIN ─────────────────────────────────────────────────────────────────────
@app.route('/EDE/admin')
@login_required('admin')
def admin_dashboard():
    stats = db.get_stats_globales()
    return render_template('admin/dashboard.html', stats=stats)

# -- Etudiants
@app.route('/EDE/admin/etudiants')
@login_required('admin')
def admin_etudiants():
    etudiants = db.get_all_etudiants()
    classes   = db.get_all_classes()
    return render_template('admin/etudiants.html', etudiants=etudiants, classes=classes)

@app.route('/EDE/admin/etudiants/ajouter', methods=['GET','POST'])
@login_required('admin')
def admin_etudiant_ajouter():

    classes = db.get_all_classes()

    if request.method == 'POST':
        try:

            prenom = request.form['prenom'].strip().lower()
            nom = request.form['nom'].strip().lower()
            telephone = request.form.get('telephone','').strip()

            classe_id_raw = request.form.get('classe_id')
            if not classe_id_raw:
                raise ValueError("Veuillez sélectionner une classe.")

            classe_id = int(classe_id_raw)

            email = f"{prenom}.{nom}@ede.sn"

            password = bcrypt.hashpw(
                request.form['password'].encode(),
                bcrypt.gensalt()
            ).decode()

            db.add_etudiant(
                nom,
                prenom,
                email,
                telephone,
                classe_id,
                password
            )

            flash('Etudiant ajouté avec succès.', 'success')
            return redirect(url_for('admin_etudiants'))

        except Exception as e:
            flash(f'Erreur : {e}', 'danger')

    return render_template(
        'admin/form_etudiant.html',
        classes=classes,
        etudiant=None
    )
@app.route('/EDE/admin/etudiants/modifier/<int:matricule>', methods=['GET','POST'])
@login_required('admin')
def admin_etudiant_modifier(matricule):
    etudiant = db.get_etudiant(matricule)
    classes  = db.get_all_classes()
    if not etudiant:
        flash('Etudiant introuvable.','danger')
        return redirect(url_for('admin_etudiants'))
    if request.method == 'POST':
        db.update_etudiant(matricule,
            request.form['nom'].strip(),
            request.form['prenom'].strip(),
            request.form.get('telephone','').strip(),
            request.form.get('classe_id', type=int))
        flash('Etudiant modifie.', 'success')
        return redirect(url_for('admin_etudiants'))
    return render_template('admin/form_etudiant.html', etudiant=etudiant, classes=classes)

@app.route('/EDE/admin/etudiants/supprimer/<int:matricule>', methods=['POST'])
@login_required('admin')
def admin_etudiant_supprimer(matricule):
    db.delete_etudiant(matricule)
    flash('Etudiant supprime.', 'success')
    return redirect(url_for('admin_etudiants'))

# -- Professeurs
@app.route('/EDE/admin/professeurs')
@login_required('admin')
def admin_professeurs():
    return render_template('admin/professeurs.html', professeurs=db.get_all_professeurs())

@app.route('/EDE/admin/professeurs/ajouter', methods=['GET','POST'])
@login_required('admin')
def admin_prof_ajouter():

    matieres = db.get_all_matieres()
    classes = db.get_all_classes()

    if request.method == 'POST':
        try:

            prenom = request.form['prenom'].strip()
            nom = request.form['nom'].strip()
            telephone = request.form.get('telephone','').strip()

            email = f"{prenom.lower()}.{nom.lower()}@ede.sn"

            password = bcrypt.hashpw(
                request.form['password'].encode(),
                bcrypt.gensalt()
            ).decode()

            # création du professeur
            pid = db.add_professeur(
                nom,
                prenom,
                email,
                telephone,
                password
            )

            # récupération affectations
            matiere_ids = request.form.getlist("matieres")
            classe_ids = request.form.getlist("classes")

            for m in matiere_ids:
                for c in classe_ids:
                    db.affecter_professeur(pid, int(m), int(c))

            flash('Professeur ajouté et affecté.', 'success')
            return redirect(url_for('admin_professeurs'))

        except Exception as e:
            flash(f'Erreur : {e}', 'danger')

    return render_template(
        'admin/form_prof.html',
        prof=None,
        matieres=matieres,
        classes=classes
    )

@app.route('/EDE/admin/professeurs/modifier/<int:pid>', methods=['GET','POST'])
@login_required('admin')
def admin_prof_modifier(pid):
    prof     = db.get_professeur(pid)
    matieres = db.get_all_matieres()
    classes  = db.get_all_classes()
    if not prof:
        flash('Professeur introuvable.','danger')
        return redirect(url_for('admin_professeurs'))
    if request.method == 'POST':
        db.update_professeur(pid,
            request.form['nom'].strip(),
            request.form['prenom'].strip(),
            request.form.get('telephone','').strip())
        flash('Professeur modifie.', 'success')
        return redirect(url_for('admin_professeurs'))
    return render_template('admin/form_prof.html', prof=prof, matieres=matieres, classes=classes)

@app.route('/EDE/admin/professeurs/supprimer/<int:pid>', methods=['POST'])
@login_required('admin')
def admin_prof_supprimer(pid):
    db.delete_professeur(pid)
    flash('Professeur supprime.', 'success')
    return redirect(url_for('admin_professeurs'))

@app.route('/EDE/admin/professeurs/affecter/<int:pid>', methods=['POST'])
@login_required('admin')
def admin_affecter(pid):
    db.affecter_professeur(pid,
        request.form.get('matiere_id', type=int),
        request.form.get('classe_id', type=int))
    flash('Affectation ajoutee.', 'success')
    return redirect(url_for('admin_prof_modifier', pid=pid))

@app.route('/EDE/admin/professeurs/retirer/<int:pid>/<int:mid>/<int:cid>', methods=['POST'])
@login_required('admin')
def admin_retirer_affectation(pid, mid, cid):
    db.retirer_affectation(pid, mid, cid)
    flash('Affectation retiree.', 'success')
    return redirect(url_for('admin_prof_modifier', pid=pid))

# -- Matieres
@app.route('/EDE/admin/matieres')
@login_required('admin')
def admin_matieres():
    return render_template('admin/matieres.html', matieres=db.get_all_matieres())

@app.route('/EDE/admin/matieres/ajouter', methods=['GET','POST'])
@login_required('admin')
def admin_matiere_ajouter():
    if request.method == 'POST':
        db.add_matiere(
            request.form['nom'].strip(),
            request.form.get('coefficient', 1.0),
            request.form.get('volume_horaire','').strip())
        flash('Matiere ajoutee.', 'success')
        return redirect(url_for('admin_matieres'))
    return render_template('admin/form_matiere.html', matiere=None)

@app.route('/EDE/admin/matieres/modifier/<int:mid>', methods=['GET','POST'])
@login_required('admin')
def admin_matiere_modifier(mid):
    matiere = db.get_matiere(mid)
    if not matiere:
        flash('Matiere introuvable.','danger')
        return redirect(url_for('admin_matieres'))
    if request.method == 'POST':
        db.update_matiere(mid,
            request.form['nom'].strip(),
            request.form.get('coefficient', 1.0),
            request.form.get('volume_horaire','').strip())
        flash('Matiere modifiee.', 'success')
        return redirect(url_for('admin_matieres'))
    return render_template('admin/form_matiere.html', matiere=matiere)

@app.route('/EDE/admin/matieres/supprimer/<int:mid>', methods=['POST'])
@login_required('admin')
def admin_matiere_supprimer(mid):
    db.delete_matiere(mid)
    flash('Matiere supprimee.', 'success')
    return redirect(url_for('admin_matieres'))

# -- Classes
@app.route('/EDE/admin/classes')
@login_required('admin')
def admin_classes():
    classes = db.get_all_classes()
    for c in classes:
        s = db.get_stats_classe(c['id_classe'])
        c['nb_etudiants'] = s.get('nb_etudiants', 0)
        c['taux_reussite']= s.get('taux_reussite', 0)
    return render_template('admin/classes.html', classes=classes)

@app.route('/EDE/admin/classes/ajouter', methods=['POST'])
@login_required('admin')
def admin_classe_ajouter():
    db.add_classe(request.form['libelle'].strip(), request.form.get('annee','').strip())
    flash('Classe ajoutee.', 'success')
    return redirect(url_for('admin_classes'))

@app.route('/EDE/admin/classes/modifier/<int:cid>', methods=['POST'])
@login_required('admin')
def admin_classe_modifier(cid):
    db.update_classe(cid, request.form['libelle'].strip(), request.form.get('annee','').strip())
    flash('Classe modifiee.', 'success')
    return redirect(url_for('admin_classes'))

@app.route('/EDE/admin/classes/supprimer/<int:cid>', methods=['POST'])
@login_required('admin')
def admin_classe_supprimer(cid):
    db.delete_classe(cid)
    flash('Classe supprimee.', 'success')
    return redirect(url_for('admin_classes'))

# -- Notes admin
@app.route('/EDE/admin/notes', methods=['GET','POST'])
@login_required('admin')
def admin_notes():
    classes    = db.get_all_classes()
    matieres   = db.get_all_matieres()
    professeurs= db.get_all_professeurs()
    classe_id  = request.args.get('classe_id', type=int)
    etudiants  = db.get_etudiants_by_classe(classe_id) if classe_id else []
    notes      = db.get_notes_classe(classe_id) if classe_id else db.get_all_notes()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'ajouter':
            ok, msg = db.add_note(
                request.form.get('matricule', type=int),
                request.form.get('matiere_id', type=int),
                request.form.get('prof_id', type=int),
                request.form.get('valeur_note'),
                request.form.get('date_saisie') or date.today().isoformat())
            flash(msg, 'success' if ok else 'danger')
        elif action == 'modifier':
            ok, msg = db.update_note(
                request.form.get('note_id', type=int),
                request.form.get('valeur_note'),
                request.form.get('prof_id', type=int)
            )
            flash(msg, 'success' if ok else 'danger')
        elif action == 'supprimer':
            ok, msg = db.delete_note(
                request.form.get('note_id', type=int),
                request.form.get('prof_id', type=int)
            )
            flash(msg, 'success' if ok else 'danger')
        return redirect(url_for('admin_notes', classe_id=classe_id))

    return render_template('admin/notes.html',
        classes=classes, matieres=matieres, professeurs=professeurs,
        etudiants=etudiants, notes=notes, classe_id=classe_id)

# -- Classements
@app.route('/EDE/admin/classements')
@login_required('admin')
def admin_classements():
    classes   = db.get_all_classes()
    classe_id = request.args.get('classe_id', type=int) or (classes[0]['id_classe'] if classes else None)
    classement= db.get_classement_classe(classe_id) if classe_id else []
    stats     = db.get_stats_classe(classe_id) if classe_id else {}
    return render_template('admin/classements.html',
        classes=classes, classe_id=classe_id, classement=classement, stats=stats)

@app.route('/EDE/admin/classements/calculer/<int:classe_id>', methods=['POST'])
@login_required('admin')
def admin_calculer_resultats(classe_id):
    annee = request.form.get('annee_scolaire', '2024-2025')
    n = db.calculer_et_sauver_resultats(classe_id, annee)
    flash(f'{n} resultats sauvegardes pour {annee}.', 'success')
    return redirect(url_for('admin_classements', classe_id=classe_id))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
