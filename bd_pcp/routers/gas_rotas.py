from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Set, Tuple

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

    combinacoes: Set[Tuple[str, str, str, str]] = set()

    for indice, item in enumerate(dados, start=1):
        planilha = item.PLANILHA.strip()
        aba = item.ABA.strip()
        produto = item.PRODUTO.strip()
        unidade = item.UNIDADE.strip()
        chave = (str(item.DATA), planilha.lower(), aba.lower(), produto.lower())

        if not all([planilha, aba, produto, unidade]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {indice}: campos PLANILHA, ABA, PRODUTO e UNIDADE nao podem ser vazios."
            )

        if chave in combinacoes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {indice}: registro duplicado para a combinacao DATA/PLANILHA/ABA/PRODUTO."
            )
        combinacoes.add(chave)


@router.post("/upsert", status_code=status.HTTP_200_OK)
async def criar_ou_atualizar_mercado_gas(
    dados: List[MercadoGasCriacao],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cria novos registros ou atualiza existentes baseado em:
    - Data
    - Planilha
    - Aba
    - Produto

    Se ja existir um registro com essas caracteristicas, ele sera atualizado.
    Caso contrario, um novo registro sera criado.
    """
    validar_payload(dados)

    try:
        repositorio = MercadoGasRepository(db)
        resultados = []

        for item in dados:
            resultado = repositorio.upsert(item)
            resultados.append(MercadoGasSaida.model_validate(resultado))

        return {"total_processados": len(resultados)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dados: {str(e)}"
        )

