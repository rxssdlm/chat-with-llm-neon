"""
Dependencies relacionadas con autenticación.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.jwt import decode_token
from models.user import User

# Indica dónde está el endpoint de login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extrae el usuario actual a partir del JWT enviado
    en el header Authorization: Bearer <token>
    """

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Token sin subject")

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    return user
