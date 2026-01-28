# 💬 Chat with LLM

Este proyecto forma parte del diplomado de desarrollo de agentes AI.

Una aplicación FastAPI educativa que demuestra cómo interactuar con modelos LLM usando GROQ. Diseñado para enseñar a estudiantes cómo funcionan los prompts, el envío de mensajes y las respuestas de los modelos.

## 📚 Objetivos Educativos

Este proyecto está diseñado para que los estudiantes aprendan:

1. **Cómo se envían mensajes a un LLM**: Entender la estructura de las peticiones HTTP y el formato de mensajes
2. **Cómo funciona el prompt**: Ver cómo se construye el prompt y cómo afecta la respuesta del modelo
3. **Cómo responde el modelo**: Analizar las respuestas, tokens utilizados y metadatos

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.8 o superior
- Una API Key de GROQ (obtén una en [https://console.groq.com/](https://console.groq.com/))

### Instalación

1. **Clonar el repositorio** (si aplica):
   ```bash
   git clone <url-del-repositorio>
   cd chat-with-llm
   ```

2. **Crear un entorno virtual** (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   
   Crea un archivo `.env` en la raíz del proyecto:
   ```bash
   cp .env.example .env
   ```
   
   Edita el archivo `.env` y agrega tu API Key de GROQ:
   ```
   GROQ_API_KEY=tu_api_key_aqui
   ```

5. **Ejecutar la aplicación**:
   ```bash
   python main.py
   ```
   
   O usando uvicorn directamente:
   ```bash
   uvicorn main:app --reload
   ```

6. **Abrir en el navegador**:
   - Interfaz web: [http://localhost:8000/](http://localhost:8000/)
   - Documentación API: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📖 Estructura del Proyecto

```
chat-with-llm/
├── main.py                 # Aplicación principal FastAPI
├── requirements.txt        # Dependencias del proyecto
├── .env                   # Variables de entorno (no versionado)
├── .env.example           # Ejemplo de variables de entorno
├── core/
│   ├── __init__.py
│   └── config.py          # Configuración de la aplicación
├── routes/
│   └── chat.py            # Rutas del chat
├── schemas/
│   └── chat.py            # Modelos de datos (Pydantic)
└── static/
    └── index.html         # Interfaz web del chat
```

## 🔧 Componentes Principales

### 1. Schemas (`schemas/chat.py`)

Define los modelos de datos que se usan para validar peticiones y respuestas:

- **`ChatMessage`**: Representa un mensaje individual (usuario o asistente)
- **`ChatRequest`**: Estructura de la petición del cliente
- **`ChatResponse`**: Estructura de la respuesta del servidor
- **`ErrorResponse`**: Estructura para respuestas de error

### 2. Configuración (`core/config.py`)

Maneja la configuración de la aplicación usando `pydantic-settings`:

- Carga variables de entorno desde `.env`
- Configuración de GROQ API
- Valores por defecto del modelo

### 3. Rutas (`routes/chat.py`)

Endpoints de la API:

- **`POST /chat/`**: Endpoint principal para enviar mensajes
- **`GET /chat/models`**: Lista modelos disponibles
- **`GET /chat/health`**: Verifica el estado del servicio

### 4. Interfaz Web (`static/index.html`)

Interfaz HTML simple y moderna para probar el chat sin necesidad de Postman.

## 📡 Uso de la API

### Endpoint Principal: POST /chat/

**Petición:**
```json
{
    "message": "¿Qué es Python?",
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.7,
    "max_tokens": 1024,
    "conversation_history": []
}
```

**Respuesta:**
```json
{
    "response": "Python es un lenguaje de programación...",
    "model_used": "llama-3.3-70b-versatile",
    "tokens_used": 150,
    "prompt_tokens": 20,
    "completion_tokens": 130,
    "conversation_history": [
        {
            "role": "user",
            "content": "¿Qué es Python?"
        },
        {
            "role": "assistant",
            "content": "Python es un lenguaje de programación..."
        }
    ]
}
```

### Parámetros Importantes

- **`message`** (requerido): El mensaje del usuario
- **`model`** (opcional): Modelo de GROQ a usar. Por defecto: `llama-3.3-70b-versatile`
- **`temperature`** (opcional): Controla la creatividad (0.0 = determinista, 2.0 = muy creativo). Por defecto: 0.7
- **`max_tokens`** (opcional): Límite de tokens en la respuesta. Por defecto: 1024
- **`conversation_history`** (opcional): Historial de conversación para mantener contexto

### Modelos Disponibles

- **`llama-3.3-70b-versatile`**: Modelo versátil y potente (recomendado)
- **`mixtral-8x7b-32768`**: Modelo con contexto largo (hasta 32K tokens)
- **`gemma2-9b-it`**: Modelo rápido y eficiente

## 🎓 Conceptos Educativos

### 1. ¿Cómo se envía el mensaje?

El flujo es el siguiente:

1. El cliente (navegador, Postman, etc.) envía una petición HTTP POST a `/chat/`
2. FastAPI valida la petición usando los schemas de Pydantic
3. Se construye el prompt con el historial y el nuevo mensaje
4. Se envía el prompt a GROQ usando su SDK
5. GROQ procesa el prompt y genera una respuesta
6. El servidor devuelve la respuesta al cliente

### 2. ¿Cómo funciona el prompt?

El prompt se construye como una lista de mensajes:

```python
messages = [
    {"role": "user", "content": "Mensaje 1"},
    {"role": "assistant", "content": "Respuesta 1"},
    {"role": "user", "content": "Mensaje 2"}
]
```

El modelo usa este historial para mantener contexto en la conversación.

### 3. ¿Cómo responde el modelo?

GROQ devuelve:
- **`response`**: El texto generado por el modelo
- **`tokens_used`**: Total de tokens utilizados
- **`prompt_tokens`**: Tokens en el prompt
- **`completion_tokens`**: Tokens en la respuesta

## 🧪 Pruebas

### Usando la Interfaz Web

1. Abre [http://localhost:8000/](http://localhost:8000/)
2. Ajusta los parámetros (modelo, temperatura, max_tokens)
3. Escribe un mensaje y envía
4. Observa la respuesta y los metadatos

### Usando la Documentación Interactiva

1. Abre [http://localhost:8000/docs](http://localhost:8000/docs)
2. Expande el endpoint `POST /chat/`
3. Haz clic en "Try it out"
4. Completa el JSON de ejemplo
5. Haz clic en "Execute"

### Usando cURL

```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, ¿cómo estás?",
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.7
  }'
```

## 🔍 Debugging

Si encuentras errores:

1. **Verifica tu API Key**: Asegúrate de que `GROQ_API_KEY` esté correctamente configurada en `.env`
2. **Revisa los logs**: Los errores se muestran en la consola
3. **Consulta la documentación**: Usa `/docs` para ver los detalles de cada endpoint
4. **Verifica la conexión**: Usa `/chat/health` para verificar el estado

## 📝 Notas para Instructores

- Este proyecto está diseñado para ser educativo y fácil de entender
- Todos los archivos tienen comentarios explicativos
- La interfaz web permite probar sin necesidad de herramientas externas
- Los estudiantes pueden experimentar con diferentes modelos y parámetros

## 🤝 Contribuciones

Este es un proyecto educativo. Las contribuciones son bienvenidas, especialmente:
- Mejoras en la documentación
- Ejemplos adicionales
- Mejoras en la interfaz web

## 📄 Licencia

[Especificar licencia si aplica]

## 🔗 Enlaces Útiles

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de GROQ](https://console.groq.com/docs)
- [Documentación de Pydantic](https://docs.pydantic.dev/)
