"""
Définition des modèles ORM à l'aide de SQLAlchemy.

Ce module décrit la structure logique de la base de données en utilisant
le système ORM de SQLAlchemy. Chaque classe Python correspond à une table
de la base relationnelle, et chaque attribut de classe correspond à une
colonne de cette table.

Objectif
--------
Permettre à l'application de manipuler les données de la base SQL Server
sous forme d'objets Python plutôt que d'écrire directement des requêtes SQL.

Remarque
--------
Ce module ne crée pas automatiquement les tables dans la base de données.
La création effective des tables dépend d'un appel explicite à :

    Base.metadata.create_all(engine)

"""

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean,
    ForeignKey, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
from database.session import Base


# =========================================================
# UTILISATEUR
# =========================================================

class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False, unique=True)
    mot_de_passe = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    actif = Column(Boolean, nullable=False, default=True)

    # Relations (un utilisateur peut être lié à un seul rôle)
    etudiant = relationship("Etudiant", back_populates="utilisateur", uselist=False)
    professeur = relationship("Professeur", back_populates="utilisateur", uselist=False)
    administrateur = relationship("Administrateur", back_populates="utilisateur", uselist=False)


# =========================================================
# CLASSE
# =========================================================

class Classe(Base):
    __tablename__ = "classe"

    id = Column(Integer, primary_key=True, autoincrement=True)
    libelle = Column(String(30), nullable=False)
    annee_scolaire = Column(String(20), nullable=True)

    etudiants = relationship("Etudiant", back_populates="classe")
    interventions = relationship("Intervention", back_populates="classe")
    resultats = relationship("Resultat", back_populates="classe")


# =========================================================
# MATIERE
# =========================================================

class Matiere(Base):
    __tablename__ = "matiere"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    coefficient = Column(Numeric(4, 2), nullable=False, default=1.00)
    volume_horaire = Column(String(10), nullable=True)

    notes = relationship("Note", back_populates="matiere")
    interventions = relationship("Intervention", back_populates="matiere")


# =========================================================
# PROFESSEUR
# =========================================================

class Professeur(Base):
    __tablename__ = "professeur"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)

    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=True)

    utilisateur = relationship("Utilisateur", back_populates="professeur")
    notes = relationship("Note", back_populates="professeur")
    interventions = relationship("Intervention", back_populates="professeur")


# =========================================================
# ADMINISTRATEUR
# =========================================================

class Administrateur(Base):
    __tablename__ = "administrateur"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)

    nom = Column(String(50), nullable=True)
    prenom = Column(String(50), nullable=True)
    telephone = Column(String(20), nullable=True)

    utilisateur = relationship("Utilisateur", back_populates="administrateur")


# =========================================================
# ETUDIANT
# =========================================================

class Etudiant(Base):
    __tablename__ = "etudiant"

    matricule = Column(Integer, primary_key=True, autoincrement=True)
    classe_id = Column(Integer, ForeignKey("classe.id"), nullable=False)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)

    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=True)

    utilisateur = relationship("Utilisateur", back_populates="etudiant")
    classe = relationship("Classe", back_populates="etudiants")
    notes = relationship("Note", back_populates="etudiant")
    resultats = relationship("Resultat", back_populates="etudiant")


# =========================================================
# INTERVENTION (professeur enseigne une matière dans une classe)
# =========================================================

class Intervention(Base):
    __tablename__ = "intervention"

    professeur_id = Column(Integer, ForeignKey("professeur.id"), primary_key=True)
    matiere_id = Column(Integer, ForeignKey("matiere.id"), primary_key=True)
    classe_id = Column(Integer, ForeignKey("classe.id"), primary_key=True)

    professeur = relationship("Professeur", back_populates="interventions")
    matiere = relationship("Matiere", back_populates="interventions")
    classe = relationship("Classe", back_populates="interventions")


# =========================================================
# NOTE
# =========================================================

class Note(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, autoincrement=True)

    matiere_id = Column(Integer, ForeignKey("matiere.id"), nullable=False)
    professeur_id = Column(Integer, ForeignKey("professeur.id"), nullable=False)
    etudiant_id = Column(Integer, ForeignKey("etudiant.matricule"), nullable=False)

    valeur = Column(Numeric(5, 2), nullable=False)
    date_saisie = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "etudiant_id",
            "matiere_id",
            name="uq_note_etudiant_matiere"
        ),
    )

    matiere = relationship("Matiere", back_populates="notes")
    professeur = relationship("Professeur", back_populates="notes")
    etudiant = relationship("Etudiant", back_populates="notes")


# =========================================================
# RESULTAT
# =========================================================

class Resultat(Base):
    __tablename__ = "resultat"

    id = Column(Integer, primary_key=True, autoincrement=True)

    classe_id = Column(Integer, ForeignKey("classe.id"), nullable=False)
    etudiant_id = Column(Integer, ForeignKey("etudiant.matricule"), nullable=False)

    moyenne_generale = Column(Numeric(5, 2), nullable=True)
    decision = Column(String(20), nullable=True)
    annee_scolaire = Column(String(20), nullable=True)
    rang = Column(Integer, nullable=True)

    classe = relationship("Classe", back_populates="resultats")
    etudiant = relationship("Etudiant", back_populates="resultats")
