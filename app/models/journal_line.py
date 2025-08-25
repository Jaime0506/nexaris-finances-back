# app/models/journal_line.py
from sqlalchemy import ForeignKey, CheckConstraint, text, CHAR, NUMERIC
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

class JournalLine(Base):
    __tablename__ = "journal_line"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_journal_line_amount_positive"),
        CheckConstraint("side IN ('D','C')", name="ck_journal_line_side_dc"),
    )

    id: Mapped[str] = mapped_column(
        UUID, primary_key=True, server_default=text("gen_random_uuid()")
    )
    entry_id: Mapped[str] = mapped_column(UUID, ForeignKey("journal_entry.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[str] = mapped_column(UUID, ForeignKey("ledger_account.id"), nullable=False)
    amount: Mapped[str] = mapped_column(NUMERIC(18, 2), nullable=False)
    side: Mapped[str] = mapped_column(CHAR(1), nullable=False)

    entry = relationship("JournalEntry", back_populates="lines", lazy="selectin")
    account = relationship("LedgerAccount", back_populates="lines", lazy="selectin")
