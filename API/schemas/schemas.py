# Définition du format de donnée de l'API en input et output
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
    token_type: str = "bearer" # token_type : par défaut "bearer", utilisé dans l'en-tête Authorization
    role: str


# =========================================================
# UTILISATEUR
# =========================================================

class UtilisateurBase(BaseModel):
    email: EmailStr
    role: str

class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str

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
# PROFESSEUR
# =========================================================

class ProfesseurBase(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None

class ProfesseurCreate(ProfesseurBase):
    # Pour créer un prof, on crée aussi son compte utilisateur
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
    classe: ClasseResponse         # objet classe embarqué dans la réponse

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
    etudiant_id: int   # le prof saisit pour quel étudiant

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
    matiere: MatiereResponse     # détail matière embarqué

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
# DASHBOARD ETUDIANT  (réponse enrichie pour le front)
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