from core.config import settings

from fastapi import FastAPI
import os

from api.routes import router as api_router

app = FastAPI(title="Nexaris Finance Back", description="API for the Nexaris Finance Backend")

# Incluye el router de la API (que ya incluye todas las rutas)
app.include_router(api_router, prefix="/api/v1")

# print(settings.model_dump())

# Endpoint de prueba inicial
@app.get("/")
def hello_world():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)