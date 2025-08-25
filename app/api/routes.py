from fastapi import APIRouter
from api.user.user_routes import router as user_router
from api.ledger_account.ledger_account_routes import router as ledger_account_router
from api.journal_entry.journal_entry_routes import router as journal_entry_router
from api.journal_line.journal_line_routes import router as journal_line_router
from api.reports.reports_routes import router as reports_router

router = APIRouter()

# Incluir todas las rutas
router.include_router(user_router)
router.include_router(ledger_account_router)
router.include_router(journal_entry_router)
router.include_router(journal_line_router)
router.include_router(reports_router)

@router.get("/")
def get_():
    return {"status": "ok" }