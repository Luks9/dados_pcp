from fastapi import status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from bd_pcp.db.models.mercado_gas import MercadoGas
from bd_pcp.schemas.mercado_gas_schema import MercadoGasCriacao


class MercadoGasRepository:
    """Repositório para operações CRUD do MercadoGas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = MercadoGas
    
    def criar(self, dados: MercadoGasCriacao) -> MercadoGas:
        """Cria um novo registro de MercadoGas"""
        db_obj = self.model(
            DATA=dados.DATA,
            PLANILHA=dados.PLANILHA,
            ABA=dados.ABA,
            PRODUTO=dados.PRODUTO,
            LOCAL=dados.LOCAL,
            UNIDADE=dados.UNIDADE,
            VALOR=dados.VALOR,
            EMPRESA=dados.EMPRESA
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def buscar_por_criterios_unicos(
        self,
        data: date,
        planilha: str,
        aba: str,
        produto: str
    ) -> Optional[MercadoGas]:
        """Busca um registro pelos critérios únicos: data, planilha, aba e produto"""
        return self.db.query(self.model).filter(
            self.model.DATA == data,
            self.model.PLANILHA == planilha,
            self.model.ABA == aba,
            self.model.PRODUTO == produto
        ).first()
    
    def upsert(self, dados: MercadoGasCriacao) -> MercadoGas:
        """Cria um novo registro ou atualiza um existente baseado nos critérios únicos"""
        registro_existente = self.buscar_por_criterios_unicos(
            data=dados.DATA,
            planilha=dados.PLANILHA,
            aba=dados.ABA,
            produto=dados.PRODUTO
        )
        
        if registro_existente:
            # Atualizar apenas os campos que podem mudar
            registro_existente.LOCAL = dados.LOCAL
            registro_existente.UNIDADE = dados.UNIDADE
            registro_existente.VALOR = dados.VALOR
            registro_existente.EMPRESA = dados.EMPRESA

            self.db.commit()
            self.db.refresh(registro_existente)
            return registro_existente
        else:
            # Criar novo registro
            try:
                return self.criar(dados)
            except Exception as e:
                raise Exception(f"Erro ao criar registro: {str(e)}")