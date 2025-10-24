from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import List

from bd_pcp.db.models.mercado_gas import MercadoGas
from bd_pcp.schemas.mercado_gas_schema import MercadoGasCriacao


class MercadoGasRepository:
    """Repositorio para operacoes CRUD do MercadoGas."""

    def __init__(self, db: Session):
        self.db = db
        self.model = MercadoGas

    def criar(self, dados: MercadoGasCriacao) -> MercadoGas:
        """Cria um novo registro de MercadoGas."""
        return self.criar_em_lote([dados])[0]

    def criar_em_lote(self, dados_lista: List[MercadoGasCriacao]) -> List[MercadoGas]:
        """Cria vários registros de MercadoGas em uma única operação."""
        if not dados_lista:
            return []

        objetos = [
            self.model(
                DATA=dados.DATA,
                PLANILHA=dados.PLANILHA,
                ABA=dados.ABA,
                PRODUTO=dados.PRODUTO,
                LOCAL=dados.LOCAL,
                UNIDADE=dados.UNIDADE,
                VALOR=dados.VALOR,
                EMPRESA=dados.EMPRESA,
            )
            for dados in dados_lista
        ]

        try:
            self.db.add_all(objetos)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        for objeto in objetos:
            self.db.refresh(objeto)

        return objetos

    def atualizar_atualizado_em_por_planilha_aba_data(
        self,
        data: date,
        planilha: str,
        aba: str,
    ) -> None:
        """Atualiza ATUALIZADO_EM para registros existentes combinando data/planilha/aba."""
        
        fuso_fortaleza = ZoneInfo("America/Fortaleza")
        
        count = (
            self.db.query(self.model)
            .filter(
                self.model.DATA == data,
                self.model.PLANILHA == planilha,
                self.model.ABA == aba,
                self.model.ATUALIZADO_EM.is_(None),
            )
            .update({self.model.ATUALIZADO_EM: datetime.now(fuso_fortaleza)}, synchronize_session=False)
        )

        if count:
            # Garante que a atualizacao seja enviada antes de inserir novos registros.
            self.db.flush()

    def listar(
        self,
        apenas_sem_atualizacao: bool = False,
    ) -> List[MercadoGas]:
        """Retorna registros, opcionalmente filtrando os sem ATUALIZADO_EM."""
        consulta = self.db.query(self.model)

        if apenas_sem_atualizacao:
            consulta = consulta.filter(self.model.ATUALIZADO_EM.is_(None))

        return consulta.order_by(self.model.DATA.desc()).all()

    def filtro_mes(self, mes: int, ano: int) -> List[MercadoGas]:
        """Retorna registros filtrando por mês e ano."""
        consulta = self.db.query(self.model).filter(
            extract('month', self.model.DATA) == mes,
            extract('year', self.model.DATA) == ano
        )
        return consulta.order_by(self.model.DATA.desc()).all()
