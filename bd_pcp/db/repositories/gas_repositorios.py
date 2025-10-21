from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from bd_pcp.db.models.mercado_gas import MercadoGas
from bd_pcp.schemas.mercado_gas_schema import MercadoGasCriacao


class MercadoGasRepository:
    """Repositorio para operacoes CRUD do MercadoGas."""

    def __init__(self, db: Session):
        self.db = db
        self.model = MercadoGas

    def criar(self, dados: MercadoGasCriacao) -> MercadoGas:
        """Cria um novo registro de MercadoGas."""
        db_obj = self.model(
            DATA=dados.DATA,
            PLANILHA=dados.PLANILHA,
            ABA=dados.ABA,
            PRODUTO=dados.PRODUTO,
            LOCAL=dados.LOCAL,
            UNIDADE=dados.UNIDADE,
            VALOR=dados.VALOR,
            EMPRESA=dados.EMPRESA,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

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
