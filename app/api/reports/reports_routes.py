from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, text
from app.core.db import get_db
from app.models.journal_line import JournalLine
from app.models.journal_entry import JournalEntry
from app.models.ledger_account import LedgerAccount, AccountKind
from app.models.user import User
from app.schemas.response import Response
from uuid import UUID
from decimal import Decimal
from typing import Dict, List
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["reports"])

# BALANCE GENERAL
@router.get("/balance-sheet/{user_id}", response_model=Response[dict])
async def get_balance_sheet(user_id: UUID, as_of_date: str | None = None, db: AsyncSession = Depends(get_db)):
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Parsear fecha si se proporciona
    filter_date = None
    if as_of_date:
        try:
            filter_date = datetime.fromisoformat(as_of_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
    
    # Construir la consulta base
    base_query = select(
        LedgerAccount.id,
        LedgerAccount.name,
        LedgerAccount.kind,
        func.sum(
            case(
                (JournalLine.side == 'D', JournalLine.amount),
                else_=0
            )
        ).label('debits'),
        func.sum(
            case(
                (JournalLine.side == 'C', JournalLine.amount),
                else_=0
            )
        ).label('credits')
    ).select_from(
        LedgerAccount
    ).outerjoin(
        JournalLine, LedgerAccount.id == JournalLine.account_id
    ).outerjoin(
        JournalEntry, JournalLine.entry_id == JournalEntry.id
    ).where(
        LedgerAccount.user_id == user_id,
        LedgerAccount.deleted_at.is_(None),
        JournalEntry.deleted_at.is_(None) if JournalEntry.id is not None else True
    )
    
    # Agregar filtro de fecha si se proporciona
    if filter_date:
        base_query = base_query.where(
            (JournalEntry.occurred_at <= filter_date) | (JournalEntry.occurred_at.is_(None))
        )
    
    base_query = base_query.group_by(
        LedgerAccount.id,
        LedgerAccount.name,
        LedgerAccount.kind
    )
    
    result = await db.execute(base_query)
    accounts_data = result.all()
    
    # Organizar por tipo de cuenta
    balance_sheet = {
        "assets": [],
        "liabilities": [],
        "equity": []
    }
    
    total_assets = Decimal('0')
    total_liabilities = Decimal('0')
    total_equity = Decimal('0')
    
    for account in accounts_data:
        balance = account.debits - account.credits
        
        account_data = {
            "id": str(account.id),
            "name": account.name,
            "balance": float(balance)
        }
        
        if account.kind == AccountKind.asset:
            balance_sheet["assets"].append(account_data)
            total_assets += balance
        elif account.kind == AccountKind.liability:
            balance_sheet["liabilities"].append(account_data)
            total_liabilities += balance
        elif account.kind == AccountKind.equity:
            balance_sheet["equity"].append(account_data)
            total_equity += balance
    
    # Calcular equity total (Assets - Liabilities)
    calculated_equity = total_assets - total_liabilities
    
    return Response(
        status="200",
        data={
            "as_of_date": as_of_date or datetime.utcnow().isoformat(),
            "accounts": balance_sheet,
            "totals": {
                "total_assets": float(total_assets),
                "total_liabilities": float(total_liabilities),
                "total_equity": float(total_equity),
                "calculated_equity": float(calculated_equity)
            }
        },
        message="Balance sheet generated successfully"
    )

# ESTADO DE RESULTADOS (INCOME STATEMENT)
@router.get("/income-statement/{user_id}", response_model=Response[dict])
async def get_income_statement(
    user_id: UUID, 
    start_date: str, 
    end_date: str, 
    db: AsyncSession = Depends(get_db)
):
    # Verificar que el usuario existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Parsear fechas
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
    
    # Consultar ingresos y gastos
    result = await db.execute(
        select(
            LedgerAccount.id,
            LedgerAccount.name,
            LedgerAccount.kind,
            func.sum(
                case(
                    (JournalLine.side == 'C', JournalLine.amount),
                    else_=0
                )
            ).label('credits'),
            func.sum(
                case(
                    (JournalLine.side == 'D', JournalLine.amount),
                    else_=0
                )
            ).label('debits')
        ).select_from(
            LedgerAccount
        ).join(
            JournalLine, LedgerAccount.id == JournalLine.account_id
        ).join(
            JournalEntry, JournalLine.entry_id == JournalEntry.id
        ).where(
            LedgerAccount.user_id == user_id,
            LedgerAccount.kind.in_([AccountKind.INCOME, AccountKind.EXPENSE]),
            LedgerAccount.deleted_at.is_(None),
            JournalEntry.deleted_at.is_(None),
            JournalEntry.occurred_at >= start_dt,
            JournalEntry.occurred_at <= end_dt
        ).group_by(
            LedgerAccount.id,
            LedgerAccount.name,
            LedgerAccount.kind
        )
    )
    
    accounts_data = result.all()
    
    # Organizar por tipo
    income_statement = {
        "income": [],
        "expenses": []
    }
    
    total_income = Decimal('0')
    total_expenses = Decimal('0')
    
    for account in accounts_data:
        if account.kind == AccountKind.INCOME:
            # Para ingresos: créditos - débitos
            net_amount = account.credits - account.debits
            income_statement["income"].append({
                "id": str(account.id),
                "name": account.name,
                "amount": float(net_amount)
            })
            total_income += net_amount
        elif account.kind == AccountKind.EXPENSE:
            # Para gastos: débitos - créditos
            net_amount = account.debits - account.credits
            income_statement["expenses"].append({
                "id": str(account.id),
                "name": account.name,
                "amount": float(net_amount)
            })
            total_expenses += net_amount
    
    net_income = total_income - total_expenses
    
    return Response(
        status="200",
        data={
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "accounts": income_statement,
            "totals": {
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "net_income": float(net_income)
            }
        },
        message="Income statement generated successfully"
    )

# MOVIMIENTOS DE UNA CUENTA
@router.get("/account-movements/{account_id}", response_model=Response[dict])
async def get_account_movements(
    account_id: UUID,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db)
):
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
    
    # Construir consulta base
    base_query = select(
        JournalEntry.occurred_at,
        JournalEntry.description,
        JournalLine.amount,
        JournalLine.side
    ).select_from(
        JournalLine
    ).join(
        JournalEntry, JournalLine.entry_id == JournalEntry.id
    ).where(
        JournalLine.account_id == account_id,
        JournalEntry.deleted_at.is_(None)
    )
    
    # Agregar filtros de fecha si se proporcionan
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            base_query = base_query.where(JournalEntry.occurred_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid start date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            base_query = base_query.where(JournalEntry.occurred_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid end date format")
    
    base_query = base_query.order_by(JournalEntry.occurred_at.desc())
    
    result = await db.execute(base_query)
    movements = result.all()
    
    # Calcular balance
    balance = Decimal('0')
    movements_list = []
    
    for movement in movements:
        if movement.side == 'D':
            balance += movement.amount
        else:
            balance -= movement.amount
        
        movements_list.append({
            "date": movement.occurred_at.isoformat(),
            "description": movement.description,
            "debit": float(movement.amount) if movement.side == 'D' else 0,
            "credit": float(movement.amount) if movement.side == 'C' else 0,
            "balance": float(balance)
        })
    
    return Response(
        status="200",
        data={
            "account": {
                "id": str(account.id),
                "name": account.name,
                "kind": account.kind.value
            },
            "movements": movements_list,
            "final_balance": float(balance)
        },
        message="Account movements fetched successfully"
    )
