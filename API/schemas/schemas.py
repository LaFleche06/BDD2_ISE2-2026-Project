"""
Schemas Pydantic

Ce module contient :
- Schémas de création
- Schémas de mise à jour
- Schémas de réponse

Les validations et les types permettent de sécuriser et de typer
les requêtes et les réponses de l'API.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


# =========================================================
# AUTH
# =========================================================

class LoginRequest(BaseModel):
    email: EmailStr
    mot_de_passe: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# =========================================================
# UTILISATEUR
# =========================================================

class UtilisateurBase(BaseModel):
    email: EmailStr
    role: str

class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str

class UtilisateurUpdate(BaseModel):
    """Pour activer / désactiver un compte."""
    actif: bool

class UtilisateurResponse(UtilisateurBase):
    id: int
    actif: bool

    model_config = {"from_attributes": True}


# =========================================================
# CLASSE
# =========================================================

class ClasseBase(BaseModel):
    libelle: str
    annee_scolaire: Optional[str] = None

class ClasseCreate(ClasseBase):
    pass

class ClasseUpdate(BaseModel):
    libelle: Optional[str] = None
    annee_scolaire: Optional[str] = None

class ClasseResponse(ClasseBase):
    id: int

    model_config = {"from_attributes": True}


# =========================================================
# MATIERE
# =========================================================

class MatiereBase(BaseModel):
    nom: str
    coefficient: Decimal = Decimal("1.00")
    volume_horaire: Optional[str] = None

class MatiereCreate(MatiereBase):
    pass

class MatiereUpdate(BaseModel):
    nom: Optional[str] = None
    coefficient: Optional[Decimal] = None
    volume_horaire: Optional[str] = None

class MatiereResponse(MatiereBase):
    id: int

    model_config = {"from_attributes": True}


# =========================================================
# ADMINISTRATEUR
# =========================================================

class AdministrateurBase(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None

class AdministrateurCreate(AdministrateurBase):
    email: EmailStr
    mot_de_passe: str

class AdministrateurUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None

class AdministrateurResponse(AdministrateurBase):
    id: int
    utilisateur_id: int
    utilisateur: UtilisateurResponse

    model_config = {"from_attributes": True}


# =========================================================
# PROFESSEUR
# =========================================================

class ProfesseurBase(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None

class ProfesseurCreate(ProfesseurBase):
    email: EmailStr
    mot_de_passe: str

class ProfesseurUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None

class ProfesseurResponse(ProfesseurBase):
    id: int
    utilisateur_id: int

    model_config = {"from_attributes": True}

class ProfesseurDetailResponse(ProfesseurBase):
    """Réponse enrichie incluant email et statut (pour l'admin)."""
    id: int
    utilisateur_id: int
    utilisateur: UtilisateurResponse

    model_config = {"from_attributes": True}


# =========================================================
# ETUDIANT
# =========================================================

class EtudiantBase(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None
    classe_id: int

class EtudiantCreate(EtudiantBase):
    email: EmailStr
    mot_de_passe: str

class EtudiantUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    classe_id: Optional[int] = None

class EtudiantResponse(EtudiantBase):
    matricule: int
    utilisateur_id: int
    classe: ClasseResponse

    model_config = {"from_attributes": True}

class EtudiantDetailResponse(EtudiantBase):
    """Réponse enrichie incluant email et statut (pour l'admin)."""
    matricule: int
    utilisateur_id: int
    classe: ClasseResponse
    utilisateur: UtilisateurResponse

    model_config = {"from_attributes": True}


# =========================================================
# NOTE
# =========================================================

class NoteBase(BaseModel):
    valeur: Decimal
    date_saisie: Optional[datetime] = None

    @field_validator("valeur")
    @classmethod
    def valeur_valide(cls, v):
        if v < 0 or v > 20:
            raise ValueError("La note doit être entre 0 et 20")
        return v

class NoteCreate(NoteBase):
    matiere_id: int
    etudiant_id: int

class NoteUpdate(BaseModel):
    valeur: Optional[Decimal] = None
    date_saisie: Optional[datetime] = None

    @field_validator("valeur")
    @classmethod
    def valeur_valide(cls, v):
        if v is not None and (v < 0 or v > 20):
            raise ValueError("La note doit être entre 0 et 20")
        return v

class NoteResponse(NoteBase):
    id: int
    matiere_id: int
    professeur_id: int
    etudiant_id: int
    matiere: MatiereResponse

    model_config = {"from_attributes": True}

class NoteCompleteResponse(NoteBase):
    """Note avec tous les détails imbriqués (vue admin)."""
    id: int
    matiere: MatiereResponse
    professeur: ProfesseurResponse
    etudiant: EtudiantResponse

    model_config = {"from_attributes": True}


# =========================================================
# INTERVENTION
# =========================================================

class InterventionCreate(BaseModel):
    professeur_id: int
    matiere_id: int
    classe_id: int

class InterventionResponse(BaseModel):
    professeur_id: int
    matiere_id: int
    classe_id: int
    professeur: ProfesseurResponse
    matiere: MatiereResponse
    classe: ClasseResponse

    model_config = {"from_attributes": True}


# =========================================================
# RESULTAT
# =========================================================

class ResultatResponse(BaseModel):
    id: int
    etudiant_id: int
    classe_id: int
    moyenne_generale: Optional[Decimal]
    decision: Optional[str]
    annee_scolaire: Optional[str]
    rang: Optional[int]
    etudiant: EtudiantResponse

    model_config = {"from_attributes": True}


# =========================================================
# DASHBOARD ETUDIANT
# =========================================================

class NoteDetaillee(BaseModel):
    matiere: str
    coefficient: Decimal
    valeur: Decimal

class DashboardEtudiant(BaseModel):
    matricule: int
    nom: str
    prenom: str
    classe: str
    annee_scolaire: Optional[str]
    moyenne_generale: Optional[Decimal]
    rang: Optional[int]
    decision: Optional[str]
    notes: list[NoteDetaillee]


# =========================================================
# DASHBOARD ADMIN
# =========================================================

class StatsGlobales(BaseModel):
    nb_etudiants: int
    nb_professeurs: int
    nb_classes: int
    nb_matieres: int
    nb_notes: int
    moyenne_etablissement: Optional[float]
    taux_reussite_pct: Optional[float]


# =========================================================
# CLASSEMENT
# =========================================================

class EntreeClassement(BaseModel):
    rang: int
    matricule: int
    nom: str
    prenom: str
    moyenne: Optional[float]
    decision: str

class ClassementClasse(BaseModel):
    classe: str
    annee_scolaire: Optional[str]
    classement: list[EntreeClassement]