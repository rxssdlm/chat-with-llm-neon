"""
Rutas para el chat con LLM.

Este módulo contiene los endpoints de la API para interactuar con el modelo LLM de GROQ.
Incluye documentación detallada para ayudar a los estudiantes a entender:
- Cómo se envían los mensajes
- Cómo funciona el prompt
- Cómo responde el modelo
"""

from fastapi import APIRouter, HTTPException, status
from groq import Groq
from typing import List

from schemas.chat import ChatRequest, ChatResponse, ChatMessage, ErrorResponse
from core.config import settings

# Crear el router para las rutas de chat
router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Inicializar el cliente de GROQ
groq_client = Groq(api_key=settings.groq_api_key)


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar mensaje al chat",
    description="""
    Este endpoint permite enviar un mensaje al modelo LLM de GROQ y recibir una respuesta.
    
    **Cómo funciona:**
    
    1. **Envío del mensaje**: El cliente envía un mensaje en formato JSON con la estructura definida en `ChatRequest`.
    
    2. **Construcción del prompt**: El sistema construye un prompt que incluye:
       - El historial de conversación (si existe)
       - El nuevo mensaje del usuario
       - Instrucciones del sistema (opcional)
    
    3. **Llamada a GROQ**: Se envía el prompt al modelo LLM de GROQ usando la API.
    
    4. **Procesamiento de la respuesta**: GROQ procesa el prompt y genera una respuesta.
    
    5. **Retorno de la respuesta**: El servidor devuelve la respuesta junto con metadatos útiles
       (tokens usados, modelo utilizado, etc.)
    
    **Parámetros importantes:**
    - `message`: El mensaje del usuario
    - `model`: El modelo de GROQ a utilizar (por defecto: llama-3.3-70b-versatile)
    - `temperature`: Controla la creatividad (0.0 = determinista, 2.0 = muy creativo)
    - `max_tokens`: Límite de tokens en la respuesta
    - `conversation_history`: Historial opcional para mantener contexto
    
    **Ejemplo de uso:**
    ```json
    {
        "message": "¿Qué es Python?",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    ```
    """
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal para el chat.
    
    Procesa el mensaje del usuario y genera una respuesta usando GROQ.
    """
    try:
        # Construir el historial de mensajes para GROQ
        # GROQ espera una lista de mensajes con formato específico
        messages: List[dict] = []
        
        # Si hay historial de conversación, agregarlo
        if request.conversation_history:
            for msg in request.conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Agregar el nuevo mensaje del usuario
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Llamar a la API de GROQ
        # Esta es la parte clave donde se envía el prompt al modelo
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # Extraer la respuesta del modelo
        # La respuesta viene en chat_completion.choices[0].message.content
        response_content = chat_completion.choices[0].message.content
        
        # Actualizar el historial de conversación
        updated_history = request.conversation_history.copy()
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=response_content))
        
        # Construir y retornar la respuesta
        return ChatResponse(
            response=response_content,
            model_used=chat_completion.model,
            tokens_used=chat_completion.usage.total_tokens,
            prompt_tokens=chat_completion.usage.prompt_tokens,
            completion_tokens=chat_completion.usage.completion_tokens,
            conversation_history=updated_history
        )
        
    except Exception as e:
        # Manejo de errores
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el mensaje: {str(e)}"
        )


@router.get(
    "/models",
    summary="Listar modelos disponibles",
    description="""
    Este endpoint devuelve una lista de los modelos disponibles en GROQ.
    
    **Modelos comunes:**
    - `llama-3.3-70b-versatile`: Modelo versátil y potente (recomendado)
    - `mixtral-8x7b-32768`: Modelo con contexto largo
    - `gemma2-9b-it`: Modelo más rápido y eficiente
    
    **Nota**: Los modelos disponibles pueden cambiar. Consulta la documentación
    oficial de GROQ para la lista más actualizada.
    """
)
async def get_models():
    """
    Devuelve información sobre los modelos disponibles.
    
    Nota: GROQ no tiene un endpoint directo para listar modelos,
    así que retornamos una lista estática de modelos conocidos.
    """
    return {
        "models": [
            {
                "id": "llama-3.3-70b-versatile",
                "name": "Llama 3.3 70B Versatile",
                "description": "Modelo versátil y potente, ideal para la mayoría de tareas"
            },
            {
                "id": "mixtral-8x7b-32768",
                "name": "Mixtral 8x7B",
                "description": "Modelo con contexto largo (hasta 32K tokens)"
            },
            {
                "id": "gemma2-9b-it",
                "name": "Gemma 2 9B IT",
                "description": "Modelo rápido y eficiente, ideal para respuestas rápidas"
            }
        ],
        "default": settings.default_model
    }


@router.get(
    "/health",
    summary="Verificar salud del servicio",
    description="Endpoint simple para verificar que el servicio está funcionando correctamente."
)
async def health_check():
    """
    Verifica que el servicio está funcionando.
    """
    return {
        "status": "healthy",
        "service": "chat-with-llm",
        "groq_configured": bool(settings.groq_api_key)
    }
