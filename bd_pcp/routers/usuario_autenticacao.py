from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBasic
from sqlalchemy.orm import Session
from typing import List

from bd_pcp.core.session import get_db
from bd_pcp.core.security import SecurityManager, get_current_user
from bd_pcp.core.config import settings
from bd_pcp.schemas.auth_schema import LoginRequest, TokenResponse, UserCreate, UserResponse, UserUpdate
from bd_pcp.services.user_service import UserService

router = APIRouter(tags=["Authentication"], prefix="/api/auth")

# Autenticação básica temporária (remova quando tiver modelo User)
security_basic = HTTPBasic()

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de login que retorna um token JWT
    """
    # Autenticar usuário no banco de dados
    user = UserService.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.IS_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = SecurityManager.create_access_token(
        data={"sub": str(user.ID), "username": user.USERNAME},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Retorna informações do usuário autenticado
    """
    return current_user

@router.post("/refresh")
async def refresh_token(current_user = Depends(get_current_user)):
    """
    Renova o token de acesso
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = SecurityManager.create_access_token(
        data={"sub": current_user.get("user_id"), "username": current_user.get("username")},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

# Endpoints para gerenciamento de usuários
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Apenas usuários autenticados podem criar outros usuários
):
    """
    Cria um novo usuário
    """
    return UserService.create_user(db, user_data)

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Lista todos os usuários
    """
    return UserService.get_all_users(db, skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Busca usuário por ID
    """
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Atualiza um usuário
    """
    return UserService.update_user(db, user_id, user_data)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Remove um usuário
    """
    UserService.delete_user(db, user_id)
    return {"message": "Usuário removido com sucesso"}