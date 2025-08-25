from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from core.db import get_db
from models.ledger_account import LedgerAccount, AccountKind
from models.user import User
from schemas.ledger_account import LedgerAccountBase, LedgerAccountCreate, LedgerAccountRead, LedgerAccountUpdate
from schemas.response import Response
from uuid import UUID

router = APIRouter(prefix="/ledger-account", tags=["ledger-account"])

# OBTENER TODAS LAS CUENTAS DE UN USUARIO
@router.get("/user/{user_id}", response_model=Response[list[LedgerAccountRead]])
async def get_user_accounts(user_id: UUID, db: AsyncSession = Depends(get_db)):
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Obtener cuentas del usuario (solo las no eliminadas)
    result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.user_id == user_id,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    accounts = result.scalars().all()

    return Response(
        status="200", 
        data=accounts, 
        message="User accounts fetched successfully"
    )

# OBTENER UNA CUENTA POR ID
@router.get("/{account_id}", response_model=Response[LedgerAccountRead])
async def get_account_by_id(account_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.id == account_id,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        
    return Response(
        status="200", 
        data=account, 
        message="Account fetched successfully"
    )

# CREAR UNA NUEVA CUENTA
@router.post("/create", response_model=Response[LedgerAccountRead])
async def create_account(payload: LedgerAccountCreate, db: AsyncSession = Depends(get_db)):
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verificar que no existe una cuenta con el mismo nombre para el usuario
    existing_account = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.user_id == payload.user_id,
            LedgerAccount.name == payload.name,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    
    if existing_account.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account with this name already exists for this user")
    
    new_account = LedgerAccount(
        user_id=payload.user_id,
        name=payload.name,
        kind=payload.kind,
        last4=payload.last4
    )

    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)

    return Response(
        status="201", 
        data=new_account, 
        message="Account created successfully"
    )

# ACTUALIZAR UNA CUENTA
@router.put("/{account_id}", response_model=Response[LedgerAccountRead])
async def update_account(account_id: UUID, payload: LedgerAccountUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.id == account_id,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    # Si se está actualizando el nombre, verificar que no exista otro con el mismo nombre
    if payload.name and payload.name != account.name:
        existing_account = await db.execute(
            select(LedgerAccount).where(
                LedgerAccount.user_id == account.user_id,
                LedgerAccount.name == payload.name,
                LedgerAccount.id != account_id,
                LedgerAccount.deleted_at.is_(None)
            )
        )
        
        if existing_account.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account with this name already exists for this user")
    
    # Actualizar campos
    if payload.name is not None:
        account.name = payload.name
    if payload.kind is not None:
        account.kind = payload.kind
    if payload.last4 is not None:
        account.last4 = payload.last4

    await db.commit()
    await db.refresh(account)

    return Response(status="200", data=account, message="Account updated successfully")

# ELIMINAR UNA CUENTA (soft delete)
@router.delete("/{account_id}", response_model=Response[dict])
async def delete_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.id == account_id,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    # Soft delete
    from datetime import datetime
    account.deleted_at = datetime.utcnow()

    await db.commit()

    return Response(status="200", data={"id": str(account_id)}, message="Account deleted successfully")

# OBTENER CUENTAS POR TIPO
@router.get("/user/{user_id}/kind/{kind}", response_model=Response[list[LedgerAccountRead]])
async def get_accounts_by_kind(user_id: UUID, kind: str, db: AsyncSession = Depends(get_db)):
    # Mapear valores de entrada a valores del enum
    kind_mapping = {
        "asset": AccountKind.asset,
        "liability": AccountKind.liability,
        "equity": AccountKind.equity,
        "income": AccountKind.income,
        "expense": AccountKind.expense
    }
    
    if kind.lower() not in kind_mapping:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account kind")
    
    account_kind = kind_mapping[kind.lower()]
    
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.user_id == user_id,
            LedgerAccount.kind == account_kind,
            LedgerAccount.deleted_at.is_(None)
        )
    )
    accounts = result.scalars().all()

    return Response(
        status="200", 
        data=accounts, 
        message=f"User {kind} accounts fetched successfully"
    )
