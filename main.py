"""
Aplicación principal FastAPI del CRM AI Agent (NexusCRM).

Este es el punto de entrada de la aplicación. Configura FastAPI y registra las rutas.
"""
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routes.auth import router as auth_router
from routes.crm import router as crm_router

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    API del agente CRM NexusCRM, basado en GROQ + Agno.

    **Endpoints principales:**
    - `POST /auth/login`: Obtener un token JWT
    - `POST /crm/chat`: Conversar con el agente CRM
    - `GET /static/crm.html`: Interfaz web del CRM
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
app.include_router(auth_router)
app.include_router(crm_router)

# Servir archivos estáticos (para la interfaz web)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    """
    Redirige a la interfaz web del CRM.
    """
    return RedirectResponse(url="/static/crm.html")


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