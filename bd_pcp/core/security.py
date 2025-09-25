from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from bd_pcp.core.config import settings
from bd_pcp.core.session import get_db

# Configuração do contexto de hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do esquema de autenticação
security = HTTPBearer()

class SecurityManager:
    """Gerenciador de segurança para autenticação e autorização"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Gera hash da senha"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Cria token JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verifica e decodifica o token JWT"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependência para obter o token atual
async def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Obtém e valida o token atual"""
    return SecurityManager.verify_token(credentials.credentials)

# Dependência para obter o usuário atual (se você tiver modelo de usuário)
async def get_current_user(
    token_data: dict = Depends(get_current_token),
    db: Session = Depends(get_db)
):
    """Obtém o usuário atual baseado no token"""
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    # Aqui você pode buscar o usuário no banco se tiver um modelo User
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="Usuário não encontrado")
    # return user
    
    return {"user_id": user_id}

# Middleware de autenticação opcional
def require_auth(func):
    """Decorator para endpoints que requerem autenticação"""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper