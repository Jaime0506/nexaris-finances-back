from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal

# Para lectura/escritura
class JournalLineBase(BaseModel):
    account_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    side: str = Field(..., pattern="^[DC]$")  # Solo D o C

# Para crear
class JournalLineCreate(JournalLineBase):
    entry_id: UUID

# Para actualizar
class JournalLineUpdate(BaseModel):
    account_id: UUID | None = None
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    side: str | None = Field(None, pattern="^[DC]$")

# Para lectura (respuesta)
class JournalLineRead(JournalLineBase):
    id: UUID
    entry_id: UUID
    account_id: UUID
    amount: Decimal
    side: str

    class Config:
        from_attributes = True
