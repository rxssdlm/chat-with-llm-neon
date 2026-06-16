"""
Configuración del proyecto.

Este módulo maneja la configuración de la aplicación, incluyendo:
- Variables de entorno
- Configuración de GROQ API
- Configuración de FastAPI
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Configuración de la aplicación.
    
    Las variables se pueden definir en un archivo .env o como variables de entorno.
    """
    # Configuración de GROQ
    groq_api_key: str = Field(
        ...,
        description="API Key de GROQ. Obtén una en https://console.groq.com/"
    )

    # OpenRouter (alternativa gratuita - openrouter.ai)
    openrouter_api_key: str = Field(
        default="",
        description="API Key de OpenRouter. Obtén una en https://openrouter.ai/"
    )
    
        # 🔐 Clave secreta para firmar JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    # 🔐 Clave secreta para firmar JWT
    JWT_SECRET_KEY: str = Field(
    default="dev-secret-change-me",
    description="Clave secreta para firmar JWT"
)

    # ⏳ Minutos de expiración del token
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
    default=60,
    description="Minutos de expiración del JWT"
)

    # Configuración de la aplicación
    app_name: str = Field(
        default="Chat with LLM",
        description="Nombre de la aplicación"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Versión de la aplicación"
    )
    debug: bool = Field(
        default=False,
        description="Modo debug (muestra más información en errores)"
    )
    
    # Configuración por defecto del modelo
    default_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Modelo por defecto de GROQ"
    )
    default_temperature: float = Field(
        default=0.7,
        description="Temperatura por defecto"
    )
    default_max_tokens: int = Field(
        default=1024,
        description="Máximo de tokens por defecto"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignorar variables extra en .env que no están definidas en esta clase


# Instancia global de configuración
settings = Settings()

