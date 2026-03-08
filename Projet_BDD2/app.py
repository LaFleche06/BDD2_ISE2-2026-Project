# ============================================================
# app.py - Application Flask EDE — version API REST
# ============================================================
from flask import Flask, render_template, request, redirect, url_for, session, flash
import api_client as api
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── HELPERS ───────────────────────────────────────────────────────────────────
def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'token' not in session:
                flash('Veuillez vous connecter.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Accès non autorisé.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def note_color(val):
    if val is None:
        return 'grey'
    try:
        v = float(val)
    except (ValueError, TypeError):
        return 'grey'
    if v >= 14:
        return 'note-good'
    if v >= 10:
        return 'note-avg'
    return 'note-bad'


app.jinja_env.globals['note_color'] = note_color


def _token():
    return session.get('token', '')


# ── PAGES PUBLIQUES ───────────────────────────────────────────────────────────
@app.route("/")
def root():
    return redirect(url_for("index"))


@app.route('/EDE/')
@app.route('/EDE/index')
def index():
    return render_template('index.html')


@app.route('/EDE/login', methods=['GET', 'POST'])
def login():
    if 'token' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        pwd   = request.form.get('password', '').strip()
        token, role = api.login(email, pwd)
        if token:
            session.clear()
            session['token'] = token
            session['role']  = role
            # Récupérer le nom selon le rôle
            if role == 'etudiant':
                profil = api.get_profil_etudiant(token)
                if profil:
                    session['entity_id'] = profil['matricule']
                    session['nom'] = f"{profil['prenom']} {profil['nom']}"
            elif role == 'prof':
                # L'API retourne le rôle 'prof' pour les professeurs
                intervs = api.get_mes_interventions(token)
                # On devine l'ID prof depuis la première intervention
                if intervs:
                    session['entity_id'] = intervs[0]['professeur_id']
                    p = intervs[0]['professeur']
                    session['nom'] = f"{p['prenom']} {p['nom']}"
                else:
                    session['entity_id'] = None
                    session['nom'] = 'Professeur'
            else:
                # admin
                profil = api.get_profil_admin(token)
                if profil:
                    session['entity_id'] = profil['id']
                    prenom = profil.get('prenom') or ''
                    nom    = profil.get('nom') or ''
                    session['nom'] = f"{prenom} {nom}".strip() or 'Administrateur'
                else:
                    session['entity_id'] = None
                    session['nom'] = 'Administrateur'
            return redirect(url_for('dashboard'))
        error = 'Email ou mot de passe incorrect, ou compte désactivé.'
    return render_template('login.html', error=error)


@app.route('/EDE/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'success')
    return redirect(url_for('login'))


@app.route('/EDE/dashboard')
def dashboard():
    if 'token' not in session:
        return redirect(url_for('login'))
    r = session.get('role')
    if r == 'etudiant':
        return redirect(url_for('etudiant_dashboard'))
    if r == 'prof':
        return redirect(url_for('prof_dashboard'))
    return redirect(url_for('admin_dashboard'))


@app.route('/EDE/test-api')
def test_api():
    ok, data = api.health_check()
    return render_template('test_api.html', status=ok, data=data)


# ── ÉTUDIANT ──────────────────────────────────────────────────────────────────
@app.route('/EDE/etudiant')
@login_required('etudiant')
def etudiant_dashboard():
    dash = api.get_dashboard_etudiant(_token())
    return render_template('etudiant/dashboard.html', dash=dash)


@app.route('/EDE/etudiant/profil')
@login_required('etudiant')
def etudiant_profil():
    profil = api.get_profil_etudiant(_token())
    return render_template('etudiant/profil.html', etudiant=profil)


@app.route('/EDE/etudiant/notes')
@login_required('etudiant')
def etudiant_notes():
    notes = api.get_mes_notes_etudiant(_token())
    return render_template('etudiant/notes.html', notes=notes)


# ── PROFESSEUR ────────────────────────────────────────────────────────────────
@app.route('/EDE/professeur')
@login_required('prof')
def prof_dashboard():
    interventions = api.get_mes_interventions(_token())
    # regrouper matières et classes distinctes
    matieres = {i['matiere_id']: i['matiere'] for i in interventions}.values()
    classes  = {i['classe_id']:  i['classe']  for i in interventions}.values()
    return render_template('prof/dashboard.html',
                           interventions=interventions,
                           matieres=list(matieres),
                           classes=list(classes))


@app.route('/EDE/professeur/notes', methods=['GET', 'POST'])
@login_required('prof')
def prof_notes():
    interventions = api.get_mes_interventions(_token())
    classes  = list({i['classe_id']: i['classe']  for i in interventions}.values())
    matieres = list({i['matiere_id']:i['matiere'] for i in interventions}.values())

    classe_id = request.args.get('classe_id', type=int)
    if not classe_id and classes:
        classe_id = classes[0]['id']

    etudiants = api.get_etudiants_by_classe(_token(), classe_id) if classe_id else []
    notes     = api.get_mes_notes(_token())
    # filtrer les notes sur la classe choisie
    mat_ids_classe = {i['matiere_id'] for i in interventions if i['classe_id'] == classe_id}
    notes_affichees = [n for n in notes if n['matiere_id'] in mat_ids_classe] if classe_id else notes

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'ajouter':
            r = api.saisir_note(
                _token(),
                request.form.get('etudiant_id', type=int),
                request.form.get('matiere_id', type=int),
                request.form.get('valeur_note'),
            )
            if r.status_code == 201:
                flash('Note ajoutée avec succès.', 'success')
            else:
                try:
                    detail = r.json().get('detail', r.text)
                except Exception:
                    detail = r.text
                flash(f'Erreur : {detail}', 'danger')
        elif action == 'modifier':
            r = api.modifier_note(
                _token(),
                request.form.get('note_id', type=int),
                request.form.get('valeur_note'),
            )
            flash('Note modifiée.' if r.status_code == 200 else f'Erreur : {r.text}',
                  'success' if r.status_code == 200 else 'danger')
        elif action == 'supprimer':
            r = api.supprimer_note(_token(), request.form.get('note_id', type=int))
            flash('Note supprimée.' if r.status_code == 204 else f'Erreur : {r.text}',
                  'success' if r.status_code == 204 else 'danger')
        return redirect(url_for('prof_notes', classe_id=classe_id))

    return render_template('prof/notes.html',
                           classes=classes, classe_id=classe_id,
                           etudiants=etudiants, matieres=matieres,
                           notes=notes_affichees, interventions=interventions)


@app.route('/EDE/professeur/moyennes')
@login_required('prof')
def prof_moyennes():
    interventions = api.get_mes_interventions(_token())
    classes  = list({i['classe_id']: i['classe'] for i in interventions}.values())
    classe_id = request.args.get('classe_id', type=int)
    if not classe_id and classes:
        classe_id = classes[0]['id']
    c_data = api.get_classement_prof(_token(), classe_id) if classe_id else []
    classement = c_data.get('classement', []) if isinstance(c_data, dict) else c_data
    return render_template('prof/moyennes.html',
                           classes=classes, classe_id=classe_id, classement=classement)


@app.route('/EDE/professeur/classe')
@login_required('prof')
def prof_classe():
    interventions = api.get_mes_interventions(_token())
    classes = list({i['classe_id']: i['classe'] for i in interventions}.values())
    return render_template('prof/classe.html', classes=classes)


# ── ADMIN ─────────────────────────────────────────────────────────────────────
@app.route('/EDE/admin')
@login_required('admin')
def admin_dashboard():
    stats = api.get_stats_globales(_token())
    return render_template('admin/dashboard.html', stats=stats)


# -- Étudiants -----------------------------------------------------------------
@app.route('/EDE/admin/etudiants')
@login_required('admin')
def admin_etudiants():
    etudiants = api.get_all_etudiants(_token())
    classes   = api.get_all_classes(_token())
    return render_template('admin/etudiants.html', etudiants=etudiants, classes=classes)


@app.route('/EDE/admin/etudiants/ajouter', methods=['GET', 'POST'])
@login_required('admin')
def admin_etudiant_ajouter():
    classes = api.get_all_classes(_token())
    if request.method == 'POST':
        try:
            classe_id_raw = request.form.get('classe_id')
            if not classe_id_raw:
                raise ValueError("Veuillez sélectionner une classe.")
            nom    = request.form['nom'].strip()
            prenom = request.form['prenom'].strip()
            telephone = request.form.get('telephone', '').strip() or None
            email  = request.form.get('email', '').strip()
            mdp    = request.form['password'].strip()
            r = api.create_etudiant(_token(), {
                "nom": nom, "prenom": prenom, "telephone": telephone,
                "classe_id": int(classe_id_raw),
                "email": email, "mot_de_passe": mdp,
            })
            if r.status_code == 201:
                flash('Étudiant ajouté avec succès.', 'success')
                return redirect(url_for('admin_etudiants'))
            else:
                detail = r.json().get('detail', r.text) if r.content else r.text
                flash(f'Erreur : {detail}', 'danger')
        except Exception as e:
            flash(f'Erreur : {e}', 'danger')
    return render_template('admin/form_etudiant.html', classes=classes, etudiant=None)


@app.route('/EDE/admin/etudiants/modifier/<int:matricule>', methods=['GET', 'POST'])
@login_required('admin')
def admin_etudiant_modifier(matricule):
    etudiant = api.get_etudiant(_token(), matricule)
    classes  = api.get_all_classes(_token())
    if not etudiant:
        flash('Étudiant introuvable.', 'danger')
        return redirect(url_for('admin_etudiants'))
    if request.method == 'POST':
        payload = {
            "nom":      request.form['nom'].strip(),
            "prenom":   request.form['prenom'].strip(),
            "telephone":request.form.get('telephone', '').strip() or None,
            "classe_id":request.form.get('classe_id', type=int),
        }
        r = api.update_etudiant(_token(), matricule, payload)
        if r.status_code == 200:
            flash('Étudiant modifié.', 'success')
            return redirect(url_for('admin_etudiants'))
        flash(f'Erreur : {r.text}', 'danger')
    return render_template('admin/form_etudiant.html', etudiant=etudiant, classes=classes)


@app.route('/EDE/admin/etudiants/supprimer/<int:matricule>', methods=['POST'])
@login_required('admin')
def admin_etudiant_supprimer(matricule):
    r = api.delete_etudiant(_token(), matricule)
    flash('Étudiant supprimé.' if r.status_code == 204 else f'Erreur : {r.text}',
          'success' if r.status_code == 204 else 'danger')
    return redirect(url_for('admin_etudiants'))


# -- Professeurs ---------------------------------------------------------------
@app.route('/EDE/admin/professeurs')
@login_required('admin')
def admin_professeurs():
    professeurs   = api.get_all_professeurs(_token())
    interventions = api.get_all_interventions(_token())
    return render_template('admin/professeurs.html', professeurs=professeurs, interventions=interventions)


@app.route('/EDE/admin/professeurs/ajouter', methods=['GET', 'POST'])
@login_required('admin')
def admin_prof_ajouter():
    matieres = api.get_all_matieres(_token())
    classes  = api.get_all_classes(_token())
    if request.method == 'POST':
        try:
            nom      = request.form['nom'].strip()
            prenom   = request.form['prenom'].strip()
            telephone= request.form.get('telephone', '').strip() or None
            email    = request.form.get('email', '').strip()
            mdp      = request.form['password'].strip()
            r = api.create_professeur(_token(), {
                "nom": nom, "prenom": prenom, "telephone": telephone,
                "email": email, "mot_de_passe": mdp,
            })
            if r.status_code == 201:
                pid = r.json()['id']
                # Interventions
                for m in request.form.getlist('matieres'):
                    for c in request.form.getlist('classes'):
                        api.create_intervention(_token(), pid, int(m), int(c))
                flash('Professeur ajouté et affecté.', 'success')
                return redirect(url_for('admin_professeurs'))
            detail = r.json().get('detail', r.text) if r.content else r.text
            flash(f'Erreur : {detail}', 'danger')
        except Exception as e:
            flash(f'Erreur : {e}', 'danger')
    return render_template('admin/form_prof.html', prof=None, matieres=matieres, classes=classes)


@app.route('/EDE/admin/professeurs/modifier/<int:pid>', methods=['GET', 'POST'])
@login_required('admin')
def admin_prof_modifier(pid):
    prof          = api.get_professeur(_token(), pid)
    matieres      = api.get_all_matieres(_token())
    classes       = api.get_all_classes(_token())
    interventions = [i for i in api.get_all_interventions(_token()) if i['professeur_id'] == pid]
    if not prof:
        flash('Professeur introuvable.', 'danger')
        return redirect(url_for('admin_professeurs'))
    if request.method == 'POST':
        payload = {
            "nom":      request.form['nom'].strip(),
            "prenom":   request.form['prenom'].strip(),
            "telephone":request.form.get('telephone', '').strip() or None,
        }
        r = api.update_professeur(_token(), pid, payload)
        if r.status_code == 200:
            flash('Professeur modifié.', 'success')
            return redirect(url_for('admin_professeurs'))
        flash(f'Erreur : {r.text}', 'danger')
    return render_template('admin/form_prof.html',
                           prof=prof, matieres=matieres, classes=classes,
                           interventions=interventions)


@app.route('/EDE/admin/professeurs/supprimer/<int:pid>', methods=['POST'])
@login_required('admin')
def admin_prof_supprimer(pid):
    r = api.delete_professeur(_token(), pid)
    flash('Professeur supprimé.' if r.status_code == 204 else f'Erreur : {r.text}',
          'success' if r.status_code == 204 else 'danger')
    return redirect(url_for('admin_professeurs'))


@app.route('/EDE/admin/professeurs/affecter/<int:pid>', methods=['POST'])
@login_required('admin')
def admin_affecter(pid):
    mid = request.form.get('matiere_id', type=int)
    cid = request.form.get('classe_id', type=int)
    api.create_intervention(_token(), pid, mid, cid)
    flash('Affectation ajoutée.', 'success')
    return redirect(url_for('admin_prof_modifier', pid=pid))


@app.route('/EDE/admin/professeurs/retirer/<int:pid>/<int:mid>/<int:cid>', methods=['POST'])
@login_required('admin')
def admin_retirer_affectation(pid, mid, cid):
    api.delete_intervention(_token(), pid, mid, cid)
    flash('Affectation retirée.', 'success')
    return redirect(url_for('admin_prof_modifier', pid=pid))


# -- Matières ------------------------------------------------------------------
@app.route('/EDE/admin/matieres')
@login_required('admin')
def admin_matieres():
    return render_template('admin/matieres.html', matieres=api.get_all_matieres(_token()))


@app.route('/EDE/admin/matieres/ajouter', methods=['GET', 'POST'])
@login_required('admin')
def admin_matiere_ajouter():
    if request.method == 'POST':
        r = api.create_matiere(
            _token(),
            request.form['nom'].strip(),
            request.form.get('coefficient') or None,
            request.form.get('volume_horaire', '').strip() or None,
        )
        if r.status_code == 201:
            flash('Matière ajoutée.', 'success')
            return redirect(url_for('admin_matieres'))
        flash(f'Erreur : {r.text}', 'danger')
    return render_template('admin/form_matiere.html', matiere=None)


@app.route('/EDE/admin/matieres/modifier/<int:mid>', methods=['GET', 'POST'])
@login_required('admin')
def admin_matiere_modifier(mid):
    matiere = api.get_all_matieres(_token())
    matiere = next((m for m in matiere if m['id'] == mid), None)
    if not matiere:
        flash('Matière introuvable.', 'danger')
        return redirect(url_for('admin_matieres'))
    if request.method == 'POST':
        r = api.update_matiere(
            _token(), mid,
            request.form['nom'].strip(),
            request.form.get('coefficient') or None,
            request.form.get('volume_horaire', '').strip() or None,
        )
        if r.status_code == 200:
            flash('Matière modifiée.', 'success')
            return redirect(url_for('admin_matieres'))
        flash(f'Erreur : {r.text}', 'danger')
    return render_template('admin/form_matiere.html', matiere=matiere)


@app.route('/EDE/admin/matieres/supprimer/<int:mid>', methods=['POST'])
@login_required('admin')
def admin_matiere_supprimer(mid):
    r = api.delete_matiere(_token(), mid)
    flash('Matière supprimée.' if r.status_code == 204 else f'Erreur : {r.text}',
          'success' if r.status_code == 204 else 'danger')
    return redirect(url_for('admin_matieres'))


# -- Classes -------------------------------------------------------------------
@app.route('/EDE/admin/classes')
@login_required('admin')
def admin_classes():
    classes = api.get_all_classes(_token())
    for c in classes:
        s = api.get_stats_classe(_token(), c['id'])
        c['nb_etudiants']  = s.get('nb_etudiants', 0)
        c['taux_reussite'] = s.get('taux_reussite', 0)
    return render_template('admin/classes.html', classes=classes)


@app.route('/EDE/admin/classes/ajouter', methods=['POST'])
@login_required('admin')
def admin_classe_ajouter():
    r = api.create_classe(
        _token(),
        request.form['libelle'].strip(),
        request.form.get('annee', '').strip() or None,
    )
    flash('Classe ajoutée.' if r.status_code == 201 else f'Erreur : {r.text}',
          'success' if r.status_code == 201 else 'danger')
    return redirect(url_for('admin_classes'))


@app.route('/EDE/admin/classes/modifier/<int:cid>', methods=['POST'])
@login_required('admin')
def admin_classe_modifier(cid):
    r = api.update_classe(
        _token(), cid,
        request.form['libelle'].strip(),
        request.form.get('annee', '').strip() or None,
    )
    flash('Classe modifiée.' if r.status_code == 200 else f'Erreur : {r.text}',
          'success' if r.status_code == 200 else 'danger')
    return redirect(url_for('admin_classes'))


@app.route('/EDE/admin/classes/supprimer/<int:cid>', methods=['POST'])
@login_required('admin')
def admin_classe_supprimer(cid):
    r = api.delete_classe(_token(), cid)
    flash('Classe supprimée.' if r.status_code == 204 else f'Erreur : {r.text}',
          'success' if r.status_code == 204 else 'danger')
    return redirect(url_for('admin_classes'))


# -- Notes admin ---------------------------------------------------------------
@app.route('/EDE/admin/notes', methods=['GET', 'POST'])
@login_required('admin')
def admin_notes():
    classes     = api.get_all_classes(_token())
    matieres    = api.get_all_matieres(_token())
    professeurs = api.get_all_professeurs(_token())
    classe_id   = request.args.get('classe_id', type=int)
    etudiants   = api.get_etudiants_by_classe(_token(), classe_id) if classe_id else []
    notes       = api.get_all_notes_admin(_token(), classe_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'supprimer':
            r = api.supprimer_note(_token(), request.form.get('note_id', type=int))
            flash('Note supprimée.' if r.status_code == 204 else f'Erreur : {r.text}',
                  'success' if r.status_code == 204 else 'danger')
        elif action == 'modifier':
            r = api.modifier_note(
                _token(),
                request.form.get('note_id', type=int),
                request.form.get('valeur_note'),
            )
            flash('Note modifiée.' if r.status_code == 200 else f'Erreur : {r.text}',
                  'success' if r.status_code == 200 else 'danger')
        return redirect(url_for('admin_notes', classe_id=classe_id))

    return render_template('admin/notes.html',
                           classes=classes, matieres=matieres, professeurs=professeurs,
                           etudiants=etudiants, notes=notes, classe_id=classe_id)


# -- Classements ---------------------------------------------------------------
@app.route('/EDE/admin/classements')
@login_required('admin')
def admin_classements():
    classes   = api.get_all_classes(_token())
    classe_id = request.args.get('classe_id', type=int) or (classes[0]['id'] if classes else None)
    c_data = api.get_classement_classe(_token(), classe_id) if classe_id else []
    classement = c_data.get('classement', []) if isinstance(c_data, dict) else c_data
    stats      = api.get_stats_classe(_token(), classe_id) if classe_id else {}
    resultats  = api.get_resultats_classe(_token(), classe_id) if classe_id else []
    return render_template('admin/classements.html',
                           classes=classes, classe_id=classe_id,
                           classement=classement, stats=stats, resultats=resultats)


@app.route('/EDE/admin/classements/sauvegarder/<int:classe_id>', methods=['POST'])
@login_required('admin')
def admin_sauvegarder_classement(classe_id):
    r = api.sauvegarder_classement(_token(), classe_id)
    flash('Résultats officiels sauvegardés !' if r.status_code == 201 else f'Erreur : {r.text}',
          'success' if r.status_code == 201 else 'danger')
    return redirect(url_for('admin_classements', classe_id=classe_id))


# -- Gestion comptes -----------------------------------------------------------
@app.route('/EDE/admin/utilisateurs/<int:user_id>/activer', methods=['POST'])
@login_required('admin')
def admin_activer(user_id):
    r = api.activer_compte(_token(), user_id)
    flash('Compte activé.' if r.status_code == 200 else f'Erreur : {r.text}',
          'success' if r.status_code == 200 else 'danger')
    return redirect(request.referrer or url_for('admin_etudiants'))


@app.route('/EDE/admin/utilisateurs/<int:user_id>/desactiver', methods=['POST'])
@login_required('admin')
def admin_desactiver(user_id):
    r = api.desactiver_compte(_token(), user_id)
    flash('Compte désactivé.' if r.status_code == 200 else f'Erreur : {r.text}',
          'success' if r.status_code == 200 else 'danger')
    return redirect(request.referrer or url_for('admin_etudiants'))


@app.route('/EDE/admin/utilisateurs/<int:user_id>/reset-password', methods=['POST'])
@login_required('admin')
def admin_reset_password(user_id):
    nouveau = request.form.get('nouveau_mot_de_passe', '').strip()
    if not nouveau:
        flash('Le nouveau mot de passe ne peut pas être vide.', 'danger')
        return redirect(request.referrer or url_for('admin_etudiants'))
    r = api.reset_password(_token(), user_id, nouveau)
    flash('Mot de passe réinitialisé.' if r.status_code == 200 else f'Erreur : {r.text}',
          'success' if r.status_code == 200 else 'danger')
    return redirect(request.referrer or url_for('admin_etudiants'))


import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

