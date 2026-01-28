"""
Schemas para las peticiones y respuestas del chat.

Este módulo define los modelos de datos (schemas) que se utilizan para:
- Validar las peticiones entrantes del usuario
- Estructurar las respuestas del modelo LLM
"""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Schema para un mensaje individual del chat.
    
    Representa un mensaje que puede ser enviado por el usuario o recibido del modelo.
    """
    role: str = Field(
        ...,
        description="Rol del mensaje: 'user' para el usuario, 'assistant' para el modelo",
        examples=["user", "assistant"]
    )
    content: str = Field(
        ...,
        description="Contenido del mensaje",
        min_length=1,
        examples=["Hola, ¿cómo estás?"]
    )


class ChatRequest(BaseModel):
    """
    Schema para la petición de chat.
    
    Esta es la estructura que el cliente debe enviar al endpoint /chat.
    Contiene el mensaje del usuario y opcionalmente el historial de conversación.
    """
    message: str = Field(
        ...,
        description="Mensaje del usuario que se enviará al modelo LLM",
        min_length=1,
        examples=["Explícame qué es la inteligencia artificial"]
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Historial opcional de la conversación para mantener contexto"
    )
    model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Modelo de GROQ a utilizar. Opciones comunes: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperatura del modelo (0.0 = determinista, 2.0 = muy creativo)"
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=8192,
        description="Número máximo de tokens en la respuesta"
    )


class ChatResponse(BaseModel):
    """
    Schema para la respuesta del chat.
    
    Esta es la estructura que el servidor devuelve al cliente después de procesar
    el mensaje con el modelo LLM de GROQ.
    """
    response: str = Field(
        ...,
        description="Respuesta generada por el modelo LLM"
    )
    model_used: str = Field(
        ...,
        description="Modelo de GROQ que se utilizó para generar la respuesta"
    )
    tokens_used: int = Field(
        ...,
        description="Número de tokens utilizados en la generación"
    )
    prompt_tokens: int = Field(
        ...,
        description="Número de tokens en el prompt enviado"
    )
    completion_tokens: int = Field(
        ...,
        description="Número de tokens en la respuesta generada"
    )
    conversation_history: list[ChatMessage] = Field(
        ...,
        description="Historial actualizado de la conversación incluyendo la nueva respuesta"
    )


class ErrorResponse(BaseModel):
    """
    Schema para respuestas de error.
    
    Se utiliza cuando ocurre un error al procesar la petición.
    """
    error: str = Field(
        ...,
        description="Mensaje de error descriptivo"
    )
    detail: str = Field(
        default="",
        description="Detalles adicionales del error (opcional)"
    )
