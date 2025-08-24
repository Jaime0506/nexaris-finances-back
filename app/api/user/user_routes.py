from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.db import get_db
from models.user import User
from schemas.user import UserBase, UserCreate, UserRead, UserUpdate
from schemas.response import Response

from uuid import UUID

router = APIRouter(prefix="/user", tags=["user"])

# OBTENGO TODOS LOS USUARIOS
@router.get("/get-all-users", response_model=Response[list[UserRead]])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()

    return Response(
        status="200", 
        data=users, 
        message="Users fetched successfully"
    )

# OBTENGO UN USUARIO POR ID
@router.get("/get-user-by-id/{user_id}", response_model=Response[UserRead])
async def get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return Response(
        status="200", 
        data=user, 
        message="User fetched successfully"
    )

@router.post("/create-user", response_model=Response[UserCreate])
async def create_user(payload: UserBase, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))

    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User email already exists")
    
    new_user = User(email=payload.email, display_name=payload.display_name)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return Response(
        status="201", 
        data=new_user, 
        message="User created successfully"
    )

@router.put("/update-user/{user_id}", response_model=Response[UserUpdate])
async def update_user(user_id: UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if payload.email:
        user.email = payload.email

    if payload.display_name:
        user.display_name = payload.display_name

    await db.commit()
    await db.refresh(user)

    return Response(status="200", data=user, message="User updated successfully")