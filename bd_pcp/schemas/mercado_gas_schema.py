from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

class MercadoGasBase(BaseModel):
    """Schema base para MercadoGas"""
    DATA: date = Field(..., example="2025-09-24")
    PLANILHA: str = Field(..., max_length=100, example="ATI GUAMARÉ - HISTÓRICO MOVIMENTAÇÃO E ESTOQUE.xlsx")
    ABA: str = Field(..., max_length=100, example="HISTÓRICO CONSOLIDAÇÃO - GLP")
    PRODUTO: str = Field(..., max_length=100, example="GLP")
    LOCAL: Optional[str] = Field(None, max_length=100, example="3R Petroleum-EF-470.006")
    DESCRICAO: Optional[str] = Field(None, max_length=255, example="Potiguar E&P - EF-470.004 - Volume de Retirada Carreta")
    UNIDADE: str = Field(..., max_length=20, example="ton")
    VALOR: float = Field(..., example="2.44")
    DENSIDADE: Optional[float] = Field(None, example="0.55")

class MercadoGasCriacao(MercadoGasBase):
    """Schema para criação de MercadoGas"""
    pass

class MercadoGasAtualizacao(MercadoGasBase):
    """Schema para atualização de MercadoGas"""
    DATA: Optional[date] = Field(None, description="Data do registro")
    PLANILHA: Optional[str] = Field(None, max_length=100, description="Nome da planilha")
    ABA: Optional[str] = Field(None, max_length=100, description="Nome da aba")
    PRODUTO: Optional[str] = Field(None, max_length=100, description="Nome do produto")
    LOCAL: Optional[str] = Field(None, max_length=100, description="Local do produto")
    DESCRICAO: Optional[str] = Field(None, max_length=255, description="Descrição")
    UNIDADE: Optional[str] = Field(None, max_length=20, description="Unidade de medida")
    VALOR: Optional[float] = Field(None, description="Valor do produto")
    DENSIDADE: Optional[float] = Field(None, description="Densidade do produto")

class MercadoGasSaida(MercadoGasBase):
    """Schema para resposta de MercadoGas"""
    ID: int = Field(..., description="ID único do registro")
    CRIADO_EM: datetime = Field(..., description="Data de criação")
    ATUALIZADO_EM: Optional[datetime] = Field(None, description="Data da última atualização")

    model_config = {"from_attributes": True}