from fastapi import APIRouter, Depends, HTTPException, Query, status
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


@router.get("/", response_model=List[MercadoGasSaida])
async def listar_mercado_gas(
    apenas_sem_atualizacao: bool = Query(
        False,
        description="Quando verdadeiro, retorna somente registros sem data de atualizacao.",
    ),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Retorna registros de MercadoGas, com filtro opcional por ATUALIZADO_EM."""
    try:
        repositorio = MercadoGasRepository(db)
        registros = repositorio.listar(apenas_sem_atualizacao=apenas_sem_atualizacao)
        return [MercadoGasSaida.model_validate(item) for item in registros]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados: {str(e)}",
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
        combos_atualizados = set()
        registros_para_criacao: List[MercadoGasCriacao] = []

        for item in dados:
            chave = (item.DATA, item.PLANILHA, item.ABA)
            if chave not in combos_atualizados:
                repositorio.atualizar_atualizado_em_por_planilha_aba_data(
                    data=item.DATA,
                    planilha=item.PLANILHA,
                    aba=item.ABA,
                )
                combos_atualizados.add(chave)

            registros_para_criacao.append(item)

        criados = repositorio.criar_em_lote(registros_para_criacao)
        resultados = [MercadoGasSaida.model_validate(resultado) for resultado in criados]

        return {"total_processados": len(resultados)}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dados: {str(e)}"
        )
