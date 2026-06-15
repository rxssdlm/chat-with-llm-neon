"""
Manejo de hashing de passwords.

Nunca guardamos passwords en texto plano.
Siempre se guardan hasheados usando bcrypt.
"""

from passlib.context import CryptContext

# bcrypt es el estándar actual seguro
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Convierte una password en su versión hasheada.
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifica si la password ingresada coincide con el hash guardado.
    """
    return pwd_context.verify(password, hashed_password)
