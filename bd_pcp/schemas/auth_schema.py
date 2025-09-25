from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """Schema para requisição de login"""
    username: str = Field(..., description="Nome de usuário")
    password: str = Field(..., description="Senha")

class TokenResponse(BaseModel):
    """Schema para resposta do token"""
    access_token: str = Field(..., description="Token de acesso")
    token_type: str = Field(default="bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")

class UserCreate(BaseModel):
    """Schema para criação de usuário"""
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário único")
    password: str = Field(..., min_length=6, max_length=100, description="Senha do usuário")
    email: Optional[str] = Field(None, description="Email do usuário")
    is_active: bool = Field(default=True, description="Status ativo do usuário")

class UserResponse(BaseModel):
    """Schema para resposta de usuário"""
    ID: int
    USERNAME: str
    EMAIL: Optional[str]
    IS_ACTIVE: bool
    CRIADO_EM: datetime
    ATUALIZADO_EM: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, description="Email do usuário")
    is_active: Optional[bool] = Field(None, description="Status ativo do usuário")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="Nova senha")