"""
Dépendances FastAPI pour l'authentification et l'autorisation.

Contient :
- get_current_user  : extrait et valide le token JWT, retourne l'utilisateur connecté
- require_role      : factory de guards qui vérifie le rôle de l'utilisateur

Usage dans un router :
    @router.get("/admin/only")
    def admin_route(user = Depends(require_role("admin"))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from typing import Callable

from database.session import get_db
from models.models import Utilisateur
from core.security import decode_token


# Indique à FastAPI où chercher le token (header Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Utilisateur:
    """
    Dépendance principale d'authentification.

    Décode le JWT, vérifie sa validité, et retourne l'objet Utilisateur
    correspondant depuis la base de données.

    Raises:
        HTTPException 401 : token invalide ou expiré
        HTTPException 401 : utilisateur introuvable
        HTTPException 403 : compte désactivé
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(Utilisateur).filter(Utilisateur.id == user_id_int).first()

    if user is None:
        raise credentials_exception

    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )

    return user


def require_role(*roles: str) -> Callable:
    """
    Factory de guard par rôle.

    Retourne une dépendance FastAPI qui vérifie que l'utilisateur connecté
    possède l'un des rôles autorisés.

    Args:
        *roles: rôles autorisés, ex: require_role("admin"), require_role("admin", "prof")

    Returns:
        Callable : dépendance FastAPI injectable via Depends()

    Raises:
        HTTPException 403 : si le rôle de l'utilisateur n'est pas dans la liste

    Example:
        @router.get("/notes")
        def get_notes(user = Depends(require_role("prof", "admin"))):
            ...
    """

    def _guard(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès réservé aux rôles : {', '.join(roles)}"
            )
        return current_user

    return _guard
