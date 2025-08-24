from datetime import datetime

from sqlalchemy import String, func, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from models.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID, 
        primary_key=True, 
        default=text("gen_random_uuid()")
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
    )

    display_name: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relaciones
