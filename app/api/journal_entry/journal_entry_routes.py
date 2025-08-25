from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.db import get_db
from app.models.journal_entry import JournalEntry
from app.models.journal_line import JournalLine
from app.models.ledger_account import LedgerAccount
from app.models.user import User
from app.schemas.journal_entry import JournalEntryBase, JournalEntryCreate, JournalEntryRead, JournalEntryUpdate, JournalEntryWithLinesCreate, JournalEntryWithLinesRead
from app.schemas.journal_line import JournalLineRead
from app.schemas.response import Response
from uuid import UUID
from decimal import Decimal
from typing import List

router = APIRouter(prefix="/journal-entry", tags=["journal-entry"])

# OBTENER TODOS LOS ASIENTOS DE UN USUARIO
@router.get("/user/{user_id}", response_model=Response[list[JournalEntryRead]])
async def get_user_entries(user_id: UUID, db: AsyncSession = Depends(get_db)):
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Obtener asientos del usuario (solo los no eliminados)
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.user_id == user_id,
            JournalEntry.deleted_at.is_(None)
        ).order_by(JournalEntry.occurred_at.desc())
    )
    entries = result.scalars().all()

    return Response(
        status="200", 
        data=entries, 
        message="User journal entries fetched successfully"
    )

# OBTENER UN ASIENTO POR ID CON SUS LÍNEAS
@router.get("/{entry_id}", response_model=Response[JournalEntryWithLinesRead])
async def get_entry_by_id(entry_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))       # <- carga las líneas
        .where(
            JournalEntry.id == entry_id,
            JournalEntry.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")

    # No hagas: entry.lines = lines
    # Devuélvelo directo o mapea a DTO
    return Response(status="200", data=entry, message="Journal entry fetched successfully")

# CREAR UN ASIENTO COMPLETO CON LÍNEAS
@router.post("/create-with-lines", response_model=Response[JournalEntryWithLinesRead])
async def create_entry_with_lines(payload: JournalEntryWithLinesCreate, db: AsyncSession = Depends(get_db)):
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Validar que hay al menos 2 líneas
    if len(payload.lines) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Journal entry must have at least 2 lines")
    
    # Validar que las cuentas existen y pertenecen al usuario
    account_ids = [line.account_id for line in payload.lines]
    accounts_result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.id.in_(account_ids),
            LedgerAccount.user_id == payload.user_id,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    accounts = accounts_result.scalars().all()
    
    if len(accounts) != len(account_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more accounts not found or do not belong to user")
    
    # Validar balance (débitos = créditos)
    total_debits = Decimal('0')
    total_credits = Decimal('0')
    
    for line in payload.lines:
        if line.side == 'D':
            total_debits += line.amount
        else:
            total_credits += line.amount
    
    if total_debits != total_credits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Journal entry is not balanced. Debits: {total_debits}, Credits: {total_credits}"
        )
    
    # Crear el asiento
    new_entry = JournalEntry(
        user_id=payload.user_id,
        occurred_at=payload.occurred_at,
        description=payload.description
    )
    
    db.add(new_entry)
    await db.flush()  # Para obtener el ID del asiento
    
    # Crear las líneas
    for line_data in payload.lines:
        new_line = JournalLine(
            entry_id=new_entry.id,
            account_id=line_data.account_id,
            amount=line_data.amount,
            side=line_data.side
        )
        db.add(new_line)
    
    await db.commit()
    await db.refresh(new_entry)
    
    # Obtener las líneas creadas
    lines_result = await db.execute(
        select(JournalLine).where(JournalLine.entry_id == new_entry.id)
    )
    lines = lines_result.scalars().all()
    
    # Asignar las líneas al asiento
    new_entry.lines = lines

    return Response(
        status="201", 
        data=new_entry, 
        message="Journal entry created successfully"
    )

# CREAR UN ASIENTO SIMPLE
@router.post("/create", response_model=Response[JournalEntryRead])
async def create_entry(payload: JournalEntryCreate, db: AsyncSession = Depends(get_db)):
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    new_entry = JournalEntry(
        user_id=payload.user_id,
        occurred_at=payload.occurred_at,
        description=payload.description
    )

    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)

    return Response(
        status="201", 
        data=new_entry, 
        message="Journal entry created successfully"
    )

# ACTUALIZAR UN ASIENTO
@router.put("/{entry_id}", response_model=Response[JournalEntryRead])
async def update_entry(entry_id: UUID, payload: JournalEntryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.deleted_at.is_(None)
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    
    # Actualizar campos
    if payload.occurred_at is not None:
        entry.occurred_at = payload.occurred_at
    if payload.description is not None:
        entry.description = payload.description

    await db.commit()
    await db.refresh(entry)

    return Response(status="200", data=entry, message="Journal entry updated successfully")

# ELIMINAR UN ASIENTO (soft delete)
@router.delete("/{entry_id}", response_model=Response[dict])
async def delete_entry(entry_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.deleted_at.is_(None)
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    
    # Soft delete
    from datetime import datetime
    entry.deleted_at = datetime.utcnow()

    await db.commit()

    return Response(status="200", data={"id": str(entry_id)}, message="Journal entry deleted successfully")

# OBTENER ASIENTOS POR RANGO DE FECHAS
@router.get("/user/{user_id}/date-range", response_model=Response[list[JournalEntryRead]])
async def get_entries_by_date_range(
    user_id: UUID, 
    start_date: str, 
    end_date: str, 
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
    
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.user_id == user_id,
            JournalEntry.occurred_at >= start_dt,
            JournalEntry.occurred_at <= end_dt,
            JournalEntry.deleted_at.is_(None)
        ).order_by(JournalEntry.occurred_at.desc())
    )
    entries = result.scalars().all()

    return Response(
        status="200", 
        data=entries, 
        message="Journal entries fetched successfully"
    )
