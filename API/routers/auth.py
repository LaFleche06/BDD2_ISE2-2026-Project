"""
Router d'authentification 

Endpoints :
    POST /auth/login  : vérifie les credentials et retourne un token JWT.


"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.session import get_db
from models.models import Utilisateur
from schemas.schemas import LoginRequest, TokenResponse
from core.security import verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authentifie un utilisateur et retourne un token JWT.

    Args:
        credentials (LoginRequest): email et mot de passe fournis par l'utilisateur
        db (Session): session SQLAlchemy injectée automatiquement

    Raises:
        HTTPException: si l'email ou le mot de passe est incorrect
        HTTPException: si le compte est désactivé

    Returns:
        TokenResponse: token JWT et rôle de l'utilisateur
    """

    # Recherche de l'utilisateur dans la base par email
    user = db.query(Utilisateur).filter(
        Utilisateur.email == credentials.email
    ).first()

    # Vérifie que l'utilisateur existe et que le mot de passe est correct
    
    if not user or not verify_password(credentials.mot_de_passe, user.mot_de_passe):
        # Même message pour email inconnu ou mot de passe incorrect
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    # Vérifie que le compte est actif
    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )

    # Création du token JWT avec l'identifiant et le rôle de l'utilisateur
    token = create_token({"sub": str(user.id), "role": user.role})

    # Retourne la réponse au front
    return TokenResponse(access_token=token, role=user.role)
