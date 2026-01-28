"""
Aplicación principal FastAPI para el chat con LLM.

Este es el punto de entrada de la aplicación. Configura FastAPI y registra las rutas.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routes.chat import router as chat_router

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    API para chat con modelos LLM usando GROQ.
    
    Esta aplicación está diseñada para enseñar a estudiantes cómo:
    - Enviar mensajes a un modelo LLM
    - Entender cómo funcionan los prompts
    - Ver cómo responde el modelo
    
    **Endpoints principales:**
    - `POST /chat/`: Enviar un mensaje y recibir una respuesta del modelo
    - `GET /chat/models`: Listar modelos disponibles
    - `GET /chat/health`: Verificar el estado del servicio
    - `GET /`: Interfaz web para probar el chat
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar las rutas
app.include_router(chat_router)

# Servir archivos estáticos (para la interfaz web)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Endpoint raíz que sirve la interfaz web del chat.
    """
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head><title>Chat with LLM</title></head>
            <body>
                <h1>Chat with LLM</h1>
                <p>La interfaz web no está disponible. Por favor, usa la documentación en <a href="/docs">/docs</a></p>
            </body>
        </html>
        """


@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación.
    """
    print(f"🚀 {settings.app_name} v{settings.app_version} iniciado")
    print(f"📚 Documentación disponible en: http://localhost:8000/docs")
    print(f"🌐 Interfaz web disponible en: http://localhost:8000/")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Recarga automática en desarrollo
        log_level="info"
    )
