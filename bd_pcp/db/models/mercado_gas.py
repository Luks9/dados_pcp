from bd_pcp.db.models.model_base import Base
from sqlalchemy import Column, Integer, String, Float, Date, func, DateTime


class MercadoGas(Base):
    __tablename__ = "MERCADO_GAS"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    DATA = Column(Date, nullable=False)
    PLANILHA = Column(String(100), nullable=False)
    ABA = Column(String(100), nullable=False)
    PRODUTO = Column(String(100), nullable=False)
    LOCAL = Column(String(100), nullable=True)
    DESCRICAO = Column(String(255), nullable=True)
    UNIDADE = Column(String(20), nullable=False)
    VALOR = Column(Float, nullable=False)
    DENSIDADE = Column(Float, nullable=True)
    CRIADO_EM = Column(DateTime, server_default=func.now())
    ATUALIZADO_EM = Column(DateTime, onupdate=func.now())