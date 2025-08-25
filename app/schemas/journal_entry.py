from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import List
from app.schemas.journal_line import JournalLineCreate, JournalLineRead

# Para lectura/escritura
class JournalEntryBase(BaseModel):
    occurred_at: datetime
    description: str | None = None

# Para crear
class JournalEntryCreate(JournalEntryBase):
    user_id: UUID

# Para crear asiento completo con líneas
class JournalEntryWithLinesCreate(JournalEntryBase):
    user_id: UUID
    lines: List[JournalLineCreate]

# Para actualizar
class JournalEntryUpdate(BaseModel):
    occurred_at: datetime | None = None
    description: str | None = None

# Para lectura (respuesta)
class JournalEntryRead(JournalEntryBase):
    id: UUID
    user_id: UUID
    occurred_at: datetime
    description: str | None
    created_at: datetime
    deleted_at: datetime | None

    class Config:
        from_attributes = True

# Para respuesta con líneas
class JournalEntryWithLinesRead(JournalEntryRead):
    lines: List[JournalLineRead]

    class Config:
        from_attributes = True
