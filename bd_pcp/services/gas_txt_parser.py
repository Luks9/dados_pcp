from __future__ import annotations

import csv
import json
from datetime import date, datetime
from io import StringIO
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from bd_pcp.schemas.mercado_gas_schema import MercadoGasCriacao

ENCODINGS: Sequence[str] = ("utf-8-sig", "latin-1", "cp1258")
REQUIRED_COLUMNS = {"DATA", "PLANILHA", "ABA", "PRODUTO", "UNIDADE", "VALOR"}


class GasTxtParserError(ValueError):
    """Erro de validacao ao processar upload TXT."""

    def __init__(self, detail: Any):
        super().__init__(str(detail))
        self.detail = detail


def parse_mercado_gas_upload(conteudo_bruto: bytes) -> List[MercadoGasCriacao]:
    """Converte bytes de upload em registros MercadoGasCriacao."""
    texto = _decode_upload(conteudo_bruto)
    registros = _parse_texto_para_registros(texto)
    return registros


def _decode_upload(conteudo_bruto: bytes) -> str:
    if not conteudo_bruto:
        raise GasTxtParserError("Arquivo vazio.")

    for encoding in ENCODINGS:
        try:
            return conteudo_bruto.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise GasTxtParserError(
        "Nao foi possivel decodificar o arquivo. Utilize UTF-8 ou Latin-1."
    )


def _parse_texto_para_registros(texto: str) -> List[MercadoGasCriacao]:
    texto_limpo = texto.strip()
    if not texto_limpo:
        raise GasTxtParserError("Arquivo vazio.")

    registros_json, erros_json = _tentar_parse_json(texto_limpo)
    if registros_json is not None:
        if erros_json:
            raise GasTxtParserError(erros_json)
        return registros_json

    registros_csv, erros_csv = _parse_csv(texto)
    if erros_csv:
        raise GasTxtParserError(erros_csv)
    return registros_csv


def _tentar_parse_json(texto_limpo: str) -> Tuple[Optional[List[MercadoGasCriacao]], List[str]]:
    if not texto_limpo.startswith(("[", "{")):
        return None, []

    try:
        conteudo_json = json.loads(texto_limpo)
    except json.JSONDecodeError:
        return None, []

    linhas_json = _extrair_dicts_json(conteudo_json)
    if linhas_json is None:
        return None, []

    try:
        registros, erros = _converter_dicts_para_registros(
            linhas=linhas_json,
            colunas_obrigatorias=REQUIRED_COLUMNS,
            indice_inicio=1,
        )
    except ValueError as exc:
        raise GasTxtParserError(str(exc)) from exc

    return registros, erros


def _parse_csv(texto: str) -> Tuple[List[MercadoGasCriacao], List[str]]:
    delimitador = _detectar_delimitador(texto)
    leitor = csv.DictReader(StringIO(texto), delimiter=delimitador)
    if not leitor.fieldnames:
        raise GasTxtParserError("Cabecalho nao identificado no arquivo.")

    mapeamento_cabecalho = _normalizar_cabecalho(leitor.fieldnames)
    ausentes = REQUIRED_COLUMNS.difference(mapeamento_cabecalho.keys())
    if ausentes:
        print(texto)
        cabecalho_original = [nome or "<vazio>" for nome in leitor.fieldnames or []]
        raise GasTxtParserError(
            f"Colunas obrigatorias ausentes: {', '.join(sorted(ausentes))}."
             f"Cabecalho encontrado: {cabecalho_original}"
             f"{mapeamento_cabecalho}"
        )

    try:
        registros, erros = _converter_dicts_para_registros(
            linhas=list(leitor),
            colunas_obrigatorias=REQUIRED_COLUMNS,
            indice_inicio=2,
        )
    except ValueError as exc:
        raise GasTxtParserError(str(exc)) from exc

    return registros, erros


def _detectar_delimitador(conteudo: str) -> str:
    candidatos = [";", "\t", "|", ","]
    contagens = {sep: conteudo.count(sep) for sep in candidatos}
    if any(contagens.values()):
        return max(contagens, key=contagens.get)
    return ";"


def _normalizar_cabecalho(fieldnames: Sequence[Optional[str]]) -> Dict[str, str]:
    mapeamento: Dict[str, str] = {}
    for nome in fieldnames:
        if not nome:
            continue
        normalizado = nome.strip().strip('"').strip("'")
        if not normalizado:
            continue
        mapeamento.setdefault(normalizado.upper(), nome)
    return mapeamento


def _normalizar_linha(dados: Dict[Optional[str], Any]) -> Dict[str, Any]:
    resultado: Dict[str, Any] = {}
    for chave, valor in (dados or {}).items():
        if not chave:
            continue
        normalizado = chave.strip().strip('"').strip("'").upper()
        if normalizado:
            resultado[normalizado] = valor
    return resultado


def _linha_para_schema(linha: Dict[str, Any]) -> MercadoGasCriacao:
    return MercadoGasCriacao(
        DATA=_converter_data(linha.get("DATA")),
        PLANILHA=(linha.get("PLANILHA") or "").strip(),
        ABA=(linha.get("ABA") or "").strip(),
        PRODUTO=(linha.get("PRODUTO") or "").strip(),
        LOCAL=_normalizar_campo_texto(linha.get("LOCAL")),
        EMPRESA=_normalizar_campo_texto(linha.get("EMPRESA")),
        UNIDADE=(linha.get("UNIDADE") or "").strip(),
        VALOR=_converter_valor(linha.get("VALOR")),
    )


def _extrair_dicts_json(payload: Any) -> Optional[List[Dict[str, Any]]]:
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for chave in ("registros", "dados", "items", "itens", "data", "result"):
            valor = payload.get(chave)
            if isinstance(valor, list):
                return valor
        return [payload]

    return None


def _converter_dicts_para_registros(
    linhas: Iterable[Dict[str, Any]],
    colunas_obrigatorias: set[str],
    indice_inicio: int,
) -> Tuple[List[MercadoGasCriacao], List[str]]:
    linhas_lista = list(linhas)
    if not linhas_lista:
        raise ValueError("Arquivo sem registros de dados.")

    erros: List[str] = []
    normalizados: List[Dict[str, Any]] = []

    for offset, linha in enumerate(linhas_lista):
        if not isinstance(linha, dict):
            erros.append(f"Linha {indice_inicio + offset}: Formato de registro invalido.")
            continue
        normalizados.append(_normalizar_linha(linha))

    if not normalizados:
        mensagem = "; ".join(erros) if erros else "Nenhum registro valido encontrado."
        raise ValueError(mensagem)

    colunas_presentes: set[str] = set()
    for linha in normalizados:
        colunas_presentes.update(linha.keys())

    ausentes = colunas_obrigatorias - colunas_presentes
    if ausentes:
        raise ValueError(
            f"Colunas obrigatorias ausentes: {', '.join(sorted(ausentes))}."
        )

    registros: List[MercadoGasCriacao] = []

    for offset, linha in enumerate(normalizados):
        try:
            registros.append(_linha_para_schema(linha))
        except Exception as exc:
            erros.append(f"Linha {indice_inicio + offset}: {exc}")

    return registros, erros


def _normalizar_campo_texto(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    texto = valor.strip()
    return texto or None


def _converter_data(data_str: Optional[str]) -> date:
    if not data_str:
        raise ValueError("Campo DATA nao pode ser vazio.")

    texto = str(data_str).strip()
    formatos = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue

    raise ValueError(f"Formato de data invalido: '{texto}'.")


def _converter_valor(valor_bruto: Optional[Any]) -> float:
    if valor_bruto is None:
        return 0

    if isinstance(valor_bruto, (int, float)):
        return float(valor_bruto)

    texto = str(valor_bruto).strip().replace(" ", "")
    if not texto:
        return 0

    tem_ponto = "." in texto
    tem_virgula = "," in texto

    if tem_ponto and tem_virgula:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif tem_virgula:
        texto = texto.replace(",", ".")

    return float(texto)
