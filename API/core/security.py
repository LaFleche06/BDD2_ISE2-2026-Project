"""
Module de sécurité pour l'application.

Contient :
- Gestion des mots de passe (hash + vérification)
- Création et décodage de tokens JWT pour l'authentification

Basé sur bcrypt pour le hashage et jose pour JWT.
"""

import bcrypt
from datetime import datetime, timedelta,timezone
from jose import jwt
import os
from dotenv import load_dotenv



load_dotenv()

# Clé secrète pour signer les JWT
SECRET_KEY = os.getenv("SECRET_KEY")

# Algorithme de signature des JWT
ALGORITHM = "HS256"

# Durée de validité du token
TOKEN_EXPIRE_MINUTES = 60 * 8


# ─── Gestion des mots de passe ───────────────────────────

def hash_password(plain: str) -> str:
    """
    Hash un mot de passe en clair pour le stocker en base de manière sécurisée.

    Args:
        plain (str): mot de passe en clair

    Returns:
        str: mot de passe hashé (bcrypt)
    """
    hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt())
    return hashed.decode()


def verify_password(plain: str, hashed: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond à un hash stocké.

    Args:
        plain (str): mot de passe en clair fourni par l'utilisateur
        hashed (str): mot de passe hashé stocké en base

    Returns:
        bool: True si le mot de passe correspond, False sinon
    """
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ─── Gestion des tokens JWT ─────────────────────────────

def create_token(data: dict) -> str:
    """
    Crée un token JWT signé contenant les informations du payload.

    Args:
        data (dict): données à inclure dans le token (ex: {"sub": user_id, "role": "prof"})

    Returns:
        str: token JWT encodé
    """
    # Copie du payload pour ne pas modifier l'original
    payload = data.copy()
    
    # Ajoute une date d'expiration
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload["exp"] = int(expire.timestamp())  # exp doit être un entier Epoch


    # Encode et signe le token
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """
    Décode un token JWT et vérifie sa validité.

    Args:
        token (str): token JWT fourni par le client

    Returns:
        dict: payload décodé

    Raises:
        JWTError: si le token est invalide ou expiré
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])