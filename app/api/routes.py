from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_():
    return {"status": "ok" }