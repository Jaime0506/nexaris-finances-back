from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr

# Para lectura/escritura
class UserBase(BaseModel):
    email: EmailStr
    display_name: str | None = None

# Para crear
class UserCreate(UserBase):
    is_active: bool = True

class UserUpdate(UserBase):
    email: EmailStr | None = None
    display_name: str | None = None
    is_active: bool | None = None

# Para lectura (respuesta)
class UserRead(UserBase):
    id: UUID
    email: EmailStr
    display_name: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True  # permite mapear desde ORM
