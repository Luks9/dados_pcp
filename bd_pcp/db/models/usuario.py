from bd_pcp.db.models.model_base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Usuario(Base):
    __tablename__ = "USUARIO"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    USERNAME = Column(String(50), unique=True, nullable=False, index=True)
    PASSWORD_HASH = Column(String(255), nullable=False)
    EMAIL = Column(String(100), unique=True, nullable=True, index=True)
    IS_ACTIVE = Column(Boolean, default=True, nullable=False)
    CRIADO_EM = Column(DateTime, server_default=func.now())
    ATUALIZADO_EM = Column(DateTime, onupdate=func.now())

    def verify_password(self, password: str) -> bool:
        """Verifica se a senha fornecida é válida"""
        return pwd_context.verify(password, self.PASSWORD_HASH)

    @staticmethod
    def hash_password(password: str) -> str:
        """Gera hash da senha"""
        return pwd_context.hash(password)

    def set_password(self, password: str):
        """Define a senha do usuário"""
        self.PASSWORD_HASH = self.hash_password(password)