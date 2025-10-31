from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
from datetime import datetime
import pandas as pd
import time


from bd_pcp.core.security import get_current_user
from bd_pcp.core.session import get_db
from bd_pcp.db.repositories.gas_repositorios import MercadoGasRepository
from bd_pcp.schemas.mercado_gas_schema import (
    MercadoGasCriacao,
    MercadoGasSaida
)
from bd_pcp.services.gas_txt_parser import GasTxtParserError, parse_mercado_gas_upload

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
        start = time.perf_counter()
        repositorio = MercadoGasRepository(db)
        registros = repositorio.listar(apenas_sem_atualizacao=apenas_sem_atualizacao)
        end = time.perf_counter()
        print(f"Tempo total da query: {(end - start)*1000:.2f} ms")
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


@router.post(
    "/upload-txt",
    status_code=status.HTTP_201_CREATED,
)
async def importar_mercado_gas_txt(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Importa registros de MercadoGas a partir de um arquivo texto delimitado."""
    if not arquivo.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ter a extensão .txt.",
        )

    conteudo_bruto = await arquivo.read()

    try:
        registros = parse_mercado_gas_upload(conteudo_bruto)
    except GasTxtParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        )

    validar_payload(registros)

    try:
        repositorio = MercadoGasRepository(db)
        combos_atualizados = set()

        for item in registros:
            chave = (item.DATA, item.PLANILHA, item.ABA)
            if chave not in combos_atualizados:
                repositorio.atualizar_atualizado_em_por_planilha_aba_data(
                    data=item.DATA,
                    planilha=item.PLANILHA,
                    aba=item.ABA,
                )
                combos_atualizados.add(chave)
        criados = repositorio.criar_em_lote(registros)
        return {"total_processados": len(criados), "arquivo": arquivo.filename}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao importar arquivo: {str(e)}"
        )

@router.get("/exportar-excel", response_model=bytes)
async def exportar_excel(
    mes: int = Query(..., ge=1, le=12, description="Mês para filtrar os registros."),
    ano: int = Query(..., ge=2000, le=datetime.now().year, description="Ano para filtrar os registros."),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Exporta os registros filtrados por mês e ano para um arquivo Excel."""
    try:
        repositorio = MercadoGasRepository(db)
        registros = repositorio.filtro_mes(mes=mes, ano=ano)

        if not registros:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum registro encontrado para o mês e ano especificados."
            )

        dados_lista = [
            {
                "ID": item.ID,
                "DATA": item.DATA,
                "PLANILHA": item.PLANILHA,
                "ABA": item.ABA,
                "PRODUTO": item.PRODUTO,
                "LOCAL": item.LOCAL,
                "EMPRESA": item.EMPRESA,
                "UNIDADE": item.UNIDADE,
                "VALOR": item.VALOR,
                "CRIADO_EM": item.CRIADO_EM,
                "ATUALIZADO_EM": item.ATUALIZADO_EM,
            }
            for item in registros
        ]

        df = pd.DataFrame(dados_lista)

        output = BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='MercadoGas')
            
        output.seek(0)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao exportar dados: {str(e)}"
        )
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': f'attachment; filename="mercado_gas_{mes}_{ano}.xlsx"'
        }
    )