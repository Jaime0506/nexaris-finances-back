from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.ledger_account import AccountKind

# Para lectura/escritura
class LedgerAccountBase(BaseModel):
    name: str
    kind: AccountKind
    last4: str | None = None

# Para crear
class LedgerAccountCreate(LedgerAccountBase):
    user_id: UUID

# Para actualizar
class LedgerAccountUpdate(BaseModel):
    name: str | None = None
    kind: AccountKind | None = None
    last4: str | None = None

# Para lectura (respuesta)
class LedgerAccountRead(LedgerAccountBase):
    id: UUID
    user_id: UUID
    name: str
    kind: AccountKind
    last4: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    class Config:
        from_attributes = True
