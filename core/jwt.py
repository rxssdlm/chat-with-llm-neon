"""
Manejo de creación y validación de JWT.

El servidor:
- Crea el token al hacer login
- Lo firma con una clave secreta
- No guarda el token en base de datos (stateless)
"""

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from core.config import settings


def create_access_token(subject: str) -> str:
    """
    Crea un JWT firmado.

    subject normalmente será el user.id
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,  # identificador del usuario
        "exp": expire    # fecha de expiración
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )


def decode_token(token: str) -> dict:
    """
    Valida y decodifica un JWT.
    Lanza excepción si es inválido o expiró.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=["HS256"]
    )
