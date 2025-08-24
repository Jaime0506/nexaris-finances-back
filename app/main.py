from core.config import settings

from fastapi import FastAPI

from api.routes import router as api_router
from api.user.user_routes import router as user_router

app = FastAPI(title="Nexaris Finance Back", description="API for the Nexaris Finance Backend", prefix="/api/v1")

# Incluye el router de la API
app.include_router(api_router)

# Api de users
app.include_router(user_router)

# print(settings.model_dump())

# Endpoint de prueba inicial
@app.get("/")
def hello_world():
    return {"message": "Hello World"}