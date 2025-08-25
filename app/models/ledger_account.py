from datetime import datetime
from enum import Enum
from sqlalchemy import String, ForeignKey, func, text, CHAR
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

from enum import Enum

class AccountKind(str, Enum):
    asset = "asset"
    liability = "liability"
    equity = "equity"
    income = "income"
    expense = "expense"

pg_account_kind = ENUM(AccountKind, name="account_kind", create_type=False)

class LedgerAccount(Base):
    __tablename__ = "ledger_account"

    id: Mapped[str] = mapped_column(
        UUID, primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[str] = mapped_column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[AccountKind] = mapped_column(pg_account_kind, nullable=False)
    last4: Mapped[str | None] = mapped_column(CHAR(4))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    user = relationship("User", back_populates="accounts")
    lines = relationship("JournalLine", back_populates="account")