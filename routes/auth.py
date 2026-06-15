"""
Endpoints para registro y login con JWT.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import hash_password, verify_password
from core.jwt import create_access_token
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(email: str, password: str, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario.
    """

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    new_user = User(
        email=email,
        hashed_password=hash_password(password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generamos token automáticamente al registrarse
    access_token = create_access_token(subject=str(new_user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login con email + password.
    """

    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    access_token = create_access_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
