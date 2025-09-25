from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional, List

from bd_pcp.db.models.usuario import Usuario
from bd_pcp.schemas.auth_schema import UserCreate, UserUpdate


class UserService:
    """Serviço para operações com usuários"""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> Usuario:
        """Cria um novo usuário"""
        try:
            # Verificar se usuário já existe
            existing_user = db.query(Usuario).filter(
                (Usuario.USERNAME == user_data.username) |
                (Usuario.EMAIL == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.USERNAME == user_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Nome de usuário já existe"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email já está em uso"
                    )

            # Criar novo usuário
            db_user = Usuario(
                USERNAME=user_data.username,
                EMAIL=user_data.email,
                IS_ACTIVE=user_data.is_active
            )
            db_user.set_password(user_data.password)
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            return db_user
            
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao criar usuário - dados duplicados"
            )

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[Usuario]:
        """Busca usuário por nome de usuário"""
        return db.query(Usuario).filter(Usuario.USERNAME == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[Usuario]:
        """Busca usuário por ID"""
        return db.query(Usuario).filter(Usuario.ID == user_id).first()

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """Lista todos os usuários"""
        return db.query(Usuario).offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Usuario:
        """Atualiza um usuário"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Atualizar campos fornecidos
        update_data = user_data.dict(exclude_unset=True)
        
        if "password" in update_data:
            db_user.set_password(update_data.pop("password"))
        
        for field, value in update_data.items():
            if field == "username":
                setattr(db_user, "USERNAME", value)
            elif field == "email":
                setattr(db_user, "EMAIL", value)
            elif field == "is_active":
                setattr(db_user, "IS_ACTIVE", value)

        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao atualizar usuário - dados duplicados"
            )

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Remove um usuário"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        db.delete(db_user)
        db.commit()
        return True

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[Usuario]:
        """Autentica um usuário"""
        user = UserService.get_user_by_username(db, username)
        if not user or not user.verify_password(password):
            return None
        return user