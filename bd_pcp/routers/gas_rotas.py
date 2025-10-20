from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from bd_pcp.core.security import get_current_user
from bd_pcp.core.session import get_db
from bd_pcp.db.repositories.gas_repositorios import MercadoGasRepository
from bd_pcp.schemas.mercado_gas_schema import (
    MercadoGasCriacao,
    MercadoGasSaida
)

router = APIRouter(tags=["Gas"], prefix="/api/gas")


def validar_payload(dados: List[MercadoGasCriacao]) -> None:
    """Valida a lista completa antes de persistir no banco."""
    if not dados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lista de registros vazia."
        )

    for indice, item in enumerate(dados, start=1):
        planilha = item.PLANILHA.strip()
        aba = item.ABA.strip()
        produto = item.PRODUTO.strip()
        unidade = item.UNIDADE.strip()

        if not all([planilha, aba, produto, unidade]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {indice}: campos PLANILHA, ABA, PRODUTO e UNIDADE nao podem ser vazios."
            )


@router.post("/upsert", status_code=status.HTTP_200_OK)
async def criar_ou_atualizar_mercado_gas(
    dados: List[MercadoGasCriacao],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Atualiza ATUALIZADO_EM dos registros existentes com a mesma combinacao
    data/planilha/aba antes de adicionar novos registros do payload.
    """
    validar_payload(dados)

    try:
        repositorio = MercadoGasRepository(db)
        resultados = []
        combos_atualizados = set()

        for item in dados:
            chave = (item.DATA, item.PLANILHA, item.ABA)
            if chave not in combos_atualizados:
                repositorio.atualizar_atualizado_em_por_planilha_aba_data(
                    data=item.DATA,
                    planilha=item.PLANILHA,
                    aba=item.ABA,
                )
                combos_atualizados.add(chave)

            resultado = repositorio.criar(item)
            resultados.append(MercadoGasSaida.model_validate(resultado))

        return {"total_processados": len(resultados)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dados: {str(e)}"
        )
