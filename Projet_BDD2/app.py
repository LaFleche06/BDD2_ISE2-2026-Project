# ============================================================
# app.py - Application Flask EDE — version API REST
# ============================================================
from flask import Flask, render_template, request, redirect, url_for, session, flash
import api_client as api
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True

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

# Generic breadcrumbs generator (called from jinja directly or context processors)
def generate_breadcrumbs(*crumbs):
    return [{'name': name, 'url': url} for name, url in crumbs if name]

app.jinja_env.globals['generate_breadcrumbs'] = generate_breadcrumbs


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
    import logging
    dash = api.get_dashboard_etudiant(_token())
    if not dash:
        # L'API n'a pas retourné de données — afficher une page d'erreur lisible
        flash("Impossible de charger le tableau de bord. Vérifiez la connexion à l'API.", "danger")
        return render_template('etudiant/dashboard.html', dash=None,
                               total_etudiants=0, rang_reel=None)
    # Pré-conversion des valeurs décimales string → float
    for n in dash.get('notes', []):
        v = n.get('valeur')
        if v is not None:
            try:
                n['valeur'] = float(v)
            except (ValueError, TypeError):
                n['valeur'] = None
        coef = n.get('coefficient')
        if coef is not None:
            try:
                n['coefficient'] = float(coef)
            except (ValueError, TypeError):
                pass
    moy = dash.get('moyenne_generale')
    if moy is not None:
        try:
            dash['moyenne_generale'] = float(moy)
        except (ValueError, TypeError):
            dash['moyenne_generale'] = None
    rang_reel = dash.get('rang')
    total_etudiants = dash.get('total_etudiants') or dash.get('nb_etudiants_classe') or 0
    return render_template('etudiant/dashboard.html', dash=dash,
                           total_etudiants=total_etudiants,
                           rang_reel=rang_reel)


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

    notes = api.get_mes_notes(_token())
    for i in interventions:
        etudiants = api.get_etudiants_by_classe(_token(), i['classe_id'])
        nb_etudiants = len(etudiants)
        etud_ids = {e['matricule'] for e in etudiants}
        nb_notes = sum(1 for n in notes if n['matiere_id'] == i['matiere_id'] and n['etudiant_id'] in etud_ids)
        
        i['nb_etudiants'] = nb_etudiants
        i['nb_notes'] = nb_notes
        i['remplissage'] = round((nb_notes / nb_etudiants * 100), 1) if nb_etudiants > 0 else 0

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


@app.route('/EDE/professeur/notes/batch')
@login_required('prof')
def prof_notes_batch():
    interventions = api.get_mes_interventions(_token())
    classes  = list({i['classe_id']: i['classe'] for i in interventions}.values())
    
    classe_id = request.args.get('classe_id', type=int)
    matiere_id = request.args.get('matiere_id', type=int)

    if not classe_id and classes:
        classe_id = classes[0]['id']

    # Filter matieres by the selected class
    matieres_for_class = [i['matiere'] for i in interventions if i['classe_id'] == classe_id]
    matieres = list({m['id']: m for m in matieres_for_class}.values())
    
    if not matiere_id and matieres:
        matiere_id = matieres[0]['id']

    etudiants = api.get_etudiants_by_classe(_token(), classe_id) if classe_id else []
    notes     = api.get_mes_notes(_token())
    # Ensure keys and comparison are robust against type changes
    existing_notes = {int(n['etudiant_id']): n for n in notes if str(n['matiere_id']) == str(matiere_id)}
    
    return render_template('prof/batch_notes.html',
                           classes=classes, classe_id=classe_id,
                           matieres=matieres, matiere_id=matiere_id,
                           etudiants=etudiants, existing_notes=existing_notes)


@app.route('/EDE/professeur/notes/batch_submit', methods=['POST'])
@login_required('prof')
def prof_notes_batch_submit():
    data = request.json
    r = api.saisir_note(
        _token(),
        data.get('etudiant_id'),
        data.get('matiere_id'),
        data.get('valeur')
    )
    if r.status_code == 201:
        return {"status": "success"}, 200
    return {"status": "error", "message": r.text}, 400


@app.route('/EDE/professeur/moyennes')
@login_required('prof')
def prof_moyennes():
    interventions = api.get_mes_interventions(_token())
    classes  = list({i['classe_id']: i['classe'] for i in interventions}.values())
    classe_id = request.args.get('classe_id', type=int)
    matiere_id = request.args.get('matiere_id', type=int)
    if not classe_id and classes:
        classe_id = classes[0]['id']

    # Matières pour la classe sélectionnée
    matieres_classe = list({i['matiere_id']: i['matiere'] for i in interventions if i['classe_id'] == classe_id}.values())
    if not matiere_id and matieres_classe:
        matiere_id = matieres_classe[0]['id']

    # Classement général de la classe (toutes matières)
    c_data = api.get_classement_prof(_token(), classe_id) if classe_id else []
    classement_general = c_data.get('classement', []) if isinstance(c_data, dict) else (c_data or [])

    # Classement par matière : notes de la matière sélectionnée, triées par valeur desc
    notes_prof = api.get_mes_notes(_token())
    notes_matiere = [n for n in notes_prof if n['matiere_id'] == matiere_id]

    # Utiliser l'endpoint professeur pour avoir les matricules cohérents
    etudiants_classe = api.get_etudiants_by_classe(_token(), classe_id) if classe_id else []
    # Les notes ont etudiant_id = matricule, on construit un dict matricule → étudiant
    etud_by_matricule = {str(e['matricule']): e for e in etudiants_classe}

    classement_matiere = []
    for n in notes_matiere:
        etud = etud_by_matricule.get(str(n['etudiant_id']))
        if not etud:
            # Fallback : essayer en cherchant dans les notes imbriquées si disponible
            etud = n.get('etudiant') or {}
        try:
            val = float(n['valeur'])
        except (ValueError, TypeError):
            val = None
        classement_matiere.append({
            'nom': etud.get('nom', '?') if isinstance(etud, dict) else '?',
            'prenom': etud.get('prenom', '?') if isinstance(etud, dict) else '?',
            'matricule': n['etudiant_id'],
            'note': val,
        })
    classement_matiere.sort(key=lambda x: (x['note'] is None, -(x['note'] or 0)))
    for idx, e in enumerate(classement_matiere):
        e['rang'] = idx + 1

    # Convert note values
    for e in classement_general:
        try:
            e['moyenne'] = float(e.get('moyenne', 0) or 0)
        except (ValueError, TypeError):
            e['moyenne'] = None

    return render_template('prof/moyennes.html',
                           classes=classes, classe_id=classe_id,
                           matieres_classe=matieres_classe, matiere_id=matiere_id,
                           classement=classement_general,
                           classement_matiere=classement_matiere)


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
    interventions = api.get_all_interventions(_token())
    classes = api.get_all_classes(_token())
    notes = api.get_all_notes_admin(_token())
    annees = api.get_annees_scolaires(_token())
    annee_filtre = request.args.get('annee_scolaire')
    
    # Filter stats based on year
    if annee_filtre:
        classes = [c for c in classes if c.get('annee_scolaire') == annee_filtre]
        stats['nb_classes'] = len(classes)
        # simplistic recalculation for alerts
        
    alerts = []
    
    classes_ids = {c['id']: c for c in classes}
    for c in classes:
        # Check if intervention exists
        c_intervs = [i for i in interventions if i['classe_id'] == c['id']]
        if not c_intervs:
             alerts.append({"type": "warning", "msg": f"La classe {c['libelle']} n'a aucune intervention."})
             
        for i in c_intervs:
            etudiants = api.get_etudiants_by_classe(_token(), i['classe_id'])
            etud_ids = {e['matricule'] for e in etudiants}
            nb_notes = sum(1 for n in notes if n['matiere_id'] == i['matiere_id'] and n['etudiant_id'] in etud_ids)
            nb_etudiants = len(etud_ids)
            if nb_etudiants > 0 and nb_notes == 0:
                 alerts.append({"type": "danger", "msg": f"La matière {i['matiere']['nom']} pour {c['libelle']} a un taux de remplissage de 0%."})

    return render_template('admin/dashboard.html', stats=stats, alerts=alerts, annees=annees, annee_filtre=annee_filtre)


# -- Administrateurs -------------------------------------------------------------
@app.route('/EDE/admin/administrateurs')
@login_required('admin')
def admin_administrateurs():
    administrateurs = api.get_all_administrateurs(_token())
    return render_template('admin/administrateurs.html', administrateurs=administrateurs)


@app.route('/EDE/admin/administrateurs/ajouter', methods=['GET', 'POST'])
@login_required('admin')
def admin_administrateur_ajouter():
    if request.method == 'POST':
        try:
            nom    = request.form['nom'].strip()
            prenom = request.form['prenom'].strip()
            telephone = request.form.get('telephone', '').strip() or None
            email  = request.form.get('email', '').strip()
            mdp    = request.form['password'].strip()
            r = api.create_administrateur(_token(), {
                "nom": nom, "prenom": prenom, "telephone": telephone,
                "email": email, "mot_de_passe": mdp,
            })
            if r.status_code == 201:
                flash('Administrateur ajouté avec succès.', 'success')
                return redirect(url_for('admin_administrateurs'))
            else:
                detail = r.json().get('detail', r.text) if r.content else r.text
                flash(f'Erreur : {detail}', 'danger')
        except Exception as e:
            flash(f'Erreur : {e}', 'danger')
    return render_template('admin/form_admin.html')



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


@app.route('/EDE/admin/etudiants/<int:matricule>')
@login_required('admin')
def admin_etudiant_detail(matricule):
    etudiant = api.get_etudiant(_token(), matricule)
    if not etudiant:
        flash('Étudiant introuvable.', 'danger')
        return redirect(url_for('admin_etudiants'))
    
    notes = api.get_notes_etudiant_admin(_token(), matricule)
    # Pre-convert string decimals to float
    for n in notes:
        try:
            n['valeur'] = float(n['valeur'])
        except (ValueError, TypeError, KeyError):
            n['valeur'] = None
        # Also fix coefficient in nested matiere
        mat = n.get('matiere') or {}
        try:
            mat['coefficient'] = float(mat.get('coefficient', 1))
        except (ValueError, TypeError):
            pass
    # Get all subjects for student's class to show missing grades
    interventions = api.get_all_interventions(_token())
    classe_id = etudiant.get('classe_id')
    if classe_id:
        matieres_classe = list({i['matiere_id']: i['matiere'] for i in interventions if i.get('classe_id') == classe_id}.values())
    else:
        matieres_classe = []
    
    return render_template('admin/etudiant_detail.html', 
                           etudiant=etudiant, 
                           notes=notes,
                           matieres_classe=matieres_classe)


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

@app.route('/EDE/admin/professeurs/<int:pid>')
@login_required('admin')
def admin_prof_detail(pid):
    prof = api.get_professeur(_token(), pid)
    if not prof:
        flash('Professeur introuvable.', 'danger')
        return redirect(url_for('admin_professeurs'))

    interventions = [i for i in api.get_all_interventions(_token()) if i['professeur_id'] == pid]
    # Utilise l'endpoint admin pour avoir des matricules cohérents avec les notes admin
    notes = api.get_all_notes_admin(_token())

    for i in interventions:
        # get_etudiants_admin_by_classe filtre depuis /admin/etudiants → matricules cohérents
        etudiants = api.get_etudiants_admin_by_classe(_token(), i['classe_id'])
        etud_ids = {e['matricule'] for e in etudiants}
        nb_notes = sum(
            1 for n in notes
            if n['professeur_id'] == pid
            and n['matiere_id'] == i['matiere_id']
            and n['etudiant_id'] in etud_ids
        )
        nb_etudiants = len(etud_ids)

        i['nb_etudiants'] = nb_etudiants
        i['nb_notes'] = nb_notes
        i['remplissage'] = round((nb_notes / nb_etudiants * 100), 1) if nb_etudiants > 0 else 0

    return render_template('admin/prof_detail.html', prof=prof, interventions=interventions)

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


@app.route('/EDE/admin/matieres/<int:mid>')
@login_required('admin')
def admin_matiere_detail(mid):
    matieres = api.get_all_matieres(_token())
    matiere = next((m for m in matieres if m['id'] == mid), None)
    if not matiere:
        flash('Matière introuvable.', 'danger')
        return redirect(url_for('admin_matieres'))
    
    interventions = [i for i in api.get_all_interventions(_token()) if i['matiere_id'] == mid]
    notes = api.get_all_notes_admin(_token(), matiere_id=mid)
    # Pre-convert note values
    for n in notes:
        try:
            n['valeur'] = float(n['valeur'])
        except (ValueError, TypeError):
            n['valeur'] = None

    for i in interventions:
        etudiants = api.get_etudiants_admin_by_classe(_token(), i['classe_id'])
        etud_ids = {e['matricule'] for e in etudiants}
        # NoteCompleteResponse has no classe_id — filter only by matiere_id and etudiant_id
        nb_notes = sum(1 for n in notes if n['matiere_id'] == i['matiere_id'] and n['etudiant_id'] in etud_ids)
        nb_etudiants = len(etud_ids)
        
        i['nb_etudiants'] = nb_etudiants
        i['nb_notes'] = nb_notes
        i['remplissage'] = round((nb_notes / nb_etudiants * 100), 1) if nb_etudiants > 0 else 0

    return render_template('admin/matiere_detail.html', matiere=matiere, interventions=interventions, notes=notes)

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
        c['taux_reussite'] = s.get('taux_reussite_pct', 0)
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


@app.route('/EDE/admin/classes/<int:cid>')
@login_required('admin')
def admin_classe_detail(cid):
    classes = api.get_all_classes(_token())
    classe = next((c for c in classes if c['id'] == cid), None)
    if not classe:
        flash('Classe introuvable.', 'danger')
        return redirect(url_for('admin_classes'))

    stats      = api.get_stats_classe(_token(), cid)
    etudiants  = api.get_etudiants_admin_by_classe(_token(), cid)
    
    c_data = api.get_classement_classe(_token(), cid)
    classement = c_data.get('classement', []) if isinstance(c_data, dict) else c_data

    # Retrieve missing fill rate for that given class subjects
    interventions = [i for i in api.get_all_interventions(_token()) if i['classe_id'] == cid]
    notes = api.get_all_notes_admin(_token(), cid)
    
    for i in interventions:
        etud_ids = {e['matricule'] for e in etudiants}
        nb_notes = sum(1 for n in notes if n['matiere_id'] == i['matiere_id'] and n['etudiant_id'] in etud_ids)
        nb_etudiants = len(etud_ids)
        
        i['nb_etudiants'] = nb_etudiants
        i['nb_notes'] = nb_notes
        i['remplissage'] = round((nb_notes / nb_etudiants * 100), 1) if nb_etudiants > 0 else 0

    return render_template('admin/classe_detail.html', 
                           classe=classe,
                           stats=stats,
                           etudiants=etudiants,
                           classement=classement,
                           interventions=interventions)

# -- Notes admin ---------------------------------------------------------------
@app.route('/EDE/admin/notes', methods=['GET', 'POST'])
@login_required('admin')
def admin_notes():
    classes     = api.get_all_classes(_token())
    matieres    = api.get_all_matieres(_token())
    professeurs = api.get_all_professeurs(_token())
    classe_id   = request.args.get('classe_id', type=int)
    matiere_id  = request.args.get('matiere_id', type=int)
    prof_id     = request.args.get('prof_id', type=int)
    etudiants   = api.get_etudiants_by_classe(_token(), classe_id) if classe_id else []
    notes       = api.get_all_notes_admin(_token(), classe_id=classe_id, matiere_id=matiere_id)

    # Filtre par professeur côté client (l'API ne supporte pas ce filtre)
    if prof_id:
        notes = [n for n in notes if n.get('professeur_id') == prof_id]

    # Pré-conversion des valeurs de notes
    for n in notes:
        try:
            n['valeur'] = float(n['valeur'])
        except (ValueError, TypeError):
            n['valeur'] = None

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
        return redirect(url_for('admin_notes', classe_id=classe_id, matiere_id=matiere_id, prof_id=prof_id))

    return render_template('admin/notes.html',
                           classes=classes, matieres=matieres, professeurs=professeurs,
                           etudiants=etudiants, notes=notes,
                           classe_id=classe_id, matiere_id=matiere_id, prof_id=prof_id)


# -- Classements ---------------------------------------------------------------
@app.route('/EDE/admin/classements')
@login_required('admin')
def admin_classements():
    classes    = api.get_all_classes(_token())
    classe_id  = request.args.get('classe_id', type=int) or (classes[0]['id'] if classes else None)
    matiere_id = request.args.get('matiere_id', type=int)
    c_data = api.get_classement_classe(_token(), classe_id) if classe_id else []
    classement = c_data.get('classement', []) if isinstance(c_data, dict) else (c_data or [])
    stats      = api.get_stats_classe(_token(), classe_id) if classe_id else {}
    resultats  = api.get_resultats_classe(_token(), classe_id) if classe_id else []

    # Récupérer toutes les matières de la classe pour le filtre
    interventions = api.get_all_interventions(_token())
    matieres_classe = list({i['matiere_id']: i['matiere'] for i in interventions if i['classe_id'] == classe_id}.values()) if classe_id else []
    if not matiere_id and matieres_classe:
        matiere_id = matieres_classe[0]['id']

    # Classement par matière (calculé côté client depuis les notes admin)
    classement_matiere = []
    if classe_id and matiere_id:
        notes_classe = api.get_all_notes_admin(_token(), classe_id=classe_id, matiere_id=matiere_id)
        etudiants_classe = api.get_etudiants_admin_by_classe(_token(), classe_id)
        etud_by_id = {e['matricule']: e for e in etudiants_classe}
        for n in notes_classe:
            etud = etud_by_id.get(n['etudiant_id']) or n.get('etudiant') or {}
            try:
                val = float(n['valeur'])
            except (ValueError, TypeError):
                val = None
            classement_matiere.append({
                'nom': etud.get('nom', '?'),
                'prenom': etud.get('prenom', '?'),
                'matricule': n['etudiant_id'],
                'note': val,
            })
        classement_matiere.sort(key=lambda x: (x['note'] is None, -(x['note'] or 0)))
        for idx, e in enumerate(classement_matiere):
            e['rang'] = idx + 1

    return render_template('admin/classements.html',
                           classes=classes, classe_id=classe_id,
                           classement=classement, stats=stats, resultats=resultats,
                           matieres_classe=matieres_classe, matiere_id=matiere_id,
                           classement_matiere=classement_matiere)


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


@app.route('/EDE/admin/interventions')
@login_required('admin')
def admin_interventions():
    interventions = api.get_all_interventions(_token())
    notes = api.get_all_notes_admin(_token())
    
    for i in interventions:
        etudiants = api.get_etudiants_by_classe(_token(), i['classe_id'])
        nb_etudiants = len(etudiants)
        etud_ids = {e['matricule'] for e in etudiants}
        nb_notes = sum(1 for n in notes if n['matiere_id'] == i['matiere_id'] and n['etudiant_id'] in etud_ids)
        
        i['nb_etudiants'] = nb_etudiants
        i['nb_notes'] = nb_notes
        i['remplissage'] = round((nb_notes / nb_etudiants * 100), 1) if nb_etudiants > 0 else 0

    return render_template('admin/interventions.html', interventions=interventions)


# -- Import en lot -----------------------------------------------------------
@app.route('/EDE/admin/import-lot/<string:type>', methods=['GET', 'POST'])
@login_required('admin')
def admin_import_lot(type):
    if type not in ('etudiant', 'prof'):
        return redirect(url_for('admin_dashboard'))

    classes = api.get_all_classes(_token())
    import json
    classes_json = json.dumps([{'id': c['id'], 'libelle': c['libelle']} for c in classes])
    resultats = []

    if request.method == 'POST':
        rows_raw = {}
        for key, val in request.form.items():
            # key format: rows[0][nom], rows[0][email], ...
            import re
            m = re.match(r'rows\[(\d+)\]\[(\w+)\]', key)
            if m:
                idx, field = m.group(1), m.group(2)
                if idx not in rows_raw:
                    rows_raw[idx] = {}
                rows_raw[idx][field] = val.strip()

        for idx in sorted(rows_raw.keys(), key=int):
            row = rows_raw[idx]
            nom    = row.get('nom', '').strip()
            prenom = row.get('prenom', '').strip()
            email  = row.get('email', '').strip()
            mdp    = row.get('mot_de_passe', '').strip()
            tel    = row.get('telephone', '').strip() or None

            if not nom or not prenom or not email or not mdp:
                resultats.append({'ok': False, 'nom': nom, 'prenom': prenom, 'email': email,
                                  'message': 'Champs obligatoires manquants'})
                continue

            if type == 'etudiant':
                classe_id = row.get('classe_id', '')
                if not classe_id:
                    resultats.append({'ok': False, 'nom': nom, 'prenom': prenom, 'email': email,
                                      'message': 'Classe manquante'})
                    continue
                payload = {'nom': nom, 'prenom': prenom, 'email': email,
                           'mot_de_passe': mdp, 'telephone': tel,
                           'classe_id': int(classe_id)}
                r = api.create_etudiant(_token(), payload)
            else:
                payload = {'nom': nom, 'prenom': prenom, 'email': email,
                           'mot_de_passe': mdp, 'telephone': tel}
                r = api.create_professeur(_token(), payload)

            if r.status_code in (200, 201):
                resultats.append({'ok': True, 'nom': nom, 'prenom': prenom, 'email': email,
                                  'message': ''})
            else:
                try:
                    msg = r.json().get('detail', r.text)
                except Exception:
                    msg = r.text
                resultats.append({'ok': False, 'nom': nom, 'prenom': prenom, 'email': email,
                                  'message': msg})

        nb_ok = sum(1 for r in resultats if r['ok'])
        flash(f'{nb_ok}/{len(resultats)} importation(s) réussie(s).', 'success' if nb_ok == len(resultats) else 'warning')

    return render_template('admin/import_lot.html', type=type, classes_json=classes_json, resultats=resultats)


@app.route('/EDE/admin/professeurs/import-lot')
@login_required('admin')
def admin_profs_import_lot():
    return redirect(url_for('admin_import_lot', type='prof'))


@app.route('/EDE/admin/etudiants/import-lot')
@login_required('admin')
def admin_etudiants_import_lot():
    return redirect(url_for('admin_import_lot', type='etudiant'))


@app.route('/EDE/profil/mot_de_passe', methods=['GET', 'POST'])
def modifier_mot_de_passe():
    if 'token' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        ancien = request.form.get('ancien_mdp', '').strip()
        nouveau = request.form.get('nouveau_mdp', '').strip()
        confirmer = request.form.get('confirmer_mdp', '').strip()
        
        if not ancien or not nouveau or not confirmer:
            flash("Veuillez remplir tous les champs.", "warning")
        elif nouveau != confirmer:
            flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
        else:
            r = api.change_password(_token(), ancien, nouveau)
            if r.status_code == 200:
                flash("Mot de passe modifié avec succès. Veuillez vous reconnecter.", "success")
                session.clear()
                return redirect(url_for('login'))
            else:
                try:
                    detail = r.json().get('detail', r.text)
                except Exception:
                    detail = r.text
                flash(f"Erreur : {detail}", "danger")

    return render_template('modifier_mdp.html')


import os

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

