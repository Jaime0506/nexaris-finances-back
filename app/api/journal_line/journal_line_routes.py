from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import get_db
from app.models.journal_line import JournalLine
from app.models.journal_entry import JournalEntry
from app.models.ledger_account import LedgerAccount
from app.schemas.journal_line import JournalLineBase, JournalLineCreate, JournalLineRead, JournalLineUpdate
from app.schemas.response import Response
from uuid import UUID
from decimal import Decimal

router = APIRouter(prefix="/journal-line", tags=["journal-line"])

# OBTENER TODAS LAS LÍNEAS DE UN ASIENTO
@router.get("/entry/{entry_id}", response_model=Response[list[JournalLineRead]])
async def get_entry_lines(entry_id: UUID, db: AsyncSession = Depends(get_db)):
    # Verificar que el asiento existe
    entry_result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.deleted_at.is_(None)
        )
    )
    entry = entry_result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    
    # Obtener las líneas del asiento
    result = await db.execute(
        select(JournalLine).where(JournalLine.entry_id == entry_id)
    )
    lines = result.scalars().all()

    return Response(
        status="200", 
        data=lines, 
        message="Journal lines fetched successfully"
    )

# OBTENER UNA LÍNEA POR ID
@router.get("/{line_id}", response_model=Response[JournalLineRead])
async def get_line_by_id(line_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JournalLine).where(JournalLine.id == line_id))
    line = result.scalar_one_or_none()

    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal line not found")
        
    return Response(
        status="200", 
        data=line, 
        message="Journal line fetched successfully"
    )

# CREAR UNA NUEVA LÍNEA
@router.post("/create", response_model=Response[JournalLineRead])
async def create_line(payload: JournalLineCreate, db: AsyncSession = Depends(get_db)):
    # Verificar que el asiento existe
    entry_result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == payload.entry_id,
            JournalEntry.deleted_at.is_(None)
        )
    )
    entry = entry_result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    
    # Verificar que la cuenta existe
    account_result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.id == payload.account_id,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    new_line = JournalLine(
        entry_id=payload.entry_id,
        account_id=payload.account_id,
        amount=payload.amount,
        side=payload.side
    )

    db.add(new_line)
    await db.commit()
    await db.refresh(new_line)

    return Response(
        status="201", 
        data=new_line, 
        message="Journal line created successfully"
    )

# ACTUALIZAR UNA LÍNEA
@router.put("/{line_id}", response_model=Response[JournalLineRead])
async def update_line(line_id: UUID, payload: JournalLineUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JournalLine).where(JournalLine.id == line_id))
    line = result.scalar_one_or_none()

    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal line not found")
    
    # Si se está actualizando la cuenta, verificar que existe
    if payload.account_id:
        account_result = await db.execute(
            select(LedgerAccount).where(
                LedgerAccount.id == payload.account_id,
                LedgerAccount.deleted_at.is_(None)
            )
        )
        account = account_result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    # Actualizar campos
    if payload.account_id is not None:
        line.account_id = payload.account_id
    if payload.amount is not None:
        line.amount = payload.amount
    if payload.side is not None:
        line.side = payload.side

    await db.commit()
    await db.refresh(line)

    return Response(status="200", data=line, message="Journal line updated successfully")

# ELIMINAR UNA LÍNEA
@router.delete("/{line_id}", response_model=Response[dict])
async def delete_line(line_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JournalLine).where(JournalLine.id == line_id))
    line = result.scalar_one_or_none()

    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal line not found")
    
    # Verificar que el asiento no esté eliminado
    entry_result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == line.entry_id,
            JournalEntry.deleted_at.is_(None)
        )
    )
    entry = entry_result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete line from deleted journal entry")
    
    await db.delete(line)
    await db.commit()

    return Response(status="200", data={"id": str(line_id)}, message="Journal line deleted successfully")

# OBTENER LÍNEAS DE UNA CUENTA
@router.get("/account/{account_id}", response_model=Response[list[JournalLineRead]])
async def get_account_lines(account_id: UUID, db: AsyncSession = Depends(get_db)):
    # Verificar que la cuenta existe
    account_result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.id == account_id,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    # Obtener las líneas de la cuenta (solo de asientos no eliminados)
    result = await db.execute(
        select(JournalLine)
        .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
        .where(
            JournalLine.account_id == account_id,
            JournalEntry.deleted_at.is_(None)
        )
        .order_by(JournalEntry.occurred_at.desc())
    )
    lines = result.scalars().all()

    return Response(
        status="200", 
        data=lines, 
        message="Account journal lines fetched successfully"
    )
