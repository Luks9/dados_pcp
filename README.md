# API PCP Dados

Esta aplicacao FastAPI expoe um endpoint protegido para cadastrar ou atualizar informacoes do mercado de gas em um banco SQL Server. O projeto ja inclui servicos de autenticacao via JWT, gerenciamento basico de usuarios e integracao com SQLAlchemy para persistencia dos dados.

## Visao geral da arquitetura
- `bd_pcp/app.py`: ponto de entrada da aplicacao FastAPI.
- `bd_pcp/routers/usuario_autenticacao.py`: endpoints de login, refresh de token e CRUD de usuarios.
- `bd_pcp/routers/gas_rotas.py`: endpoint autenticado `POST /api/gas/upsert` para inserir ou atualizar registros do mercado de gas.
- `bd_pcp/db/models`: modelos SQLAlchemy para as tabelas `USUARIO` e `MERCADO_GAS`.
- `bd_pcp/core`: configuracoes, gerenciamento de seguranca (JWT) e sessao de banco de dados.

## Requisitos
- Python 3.11+
- SQL Server acessivel com o driver "ODBC Driver 17 for SQL Server" instalado na maquina que executara a API
- Poetry (opcional, mas recomendado para gerenciar dependencias)

## Configuracao do ambiente
1. Crie um arquivo `.env` na raiz do projeto com as configuracoes sensiveis:
   ```env
   DB_DRIVER=mssql+pyodbc
   DB_HOST=SEU_SERVIDOR\INSTANCIA
   DB_PORT=1433
   DB_NAME=NOME_DO_BANCO
   DB_USER=USUARIO
   DB_PASSWORD=SENHA
   DB_ODBC_DRIVER=ODBC Driver 17 for SQL Server

   SECRET_KEY=sua_chave_ultra_secreta
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=300
   ```
   Substitua os valores por credenciais validas para o seu ambiente.

2. Instale as dependencias:
   - Com Poetry:
     ```bash
     poetry install
     ```
   - Sem Poetry:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     pip install -r requirements.txt  # gere o arquivo com `poetry export` se necessario
     ```

3. Garanta que voce possui acesso ao SQL Server configurado no `.env`. O modulo `bd_pcp/core/session.py` pode ser executado diretamente para criar as tabelas basicas caso elas ainda nao existam:
   ```bash
   poetry run python -m bd_pcp.core.session
   ```

## Executando a API
Utilize o `task` definido no `pyproject.toml`:
```bash
poetry run task run
```
Ou execute o Uvicorn manualmente:
```bash
poetry run uvicorn bd_pcp.app:app --reload
```
A API ficara disponivel em `http://localhost:8000` por padrao. Caso deseje usar outra porta, ajuste o comando do Uvicorn conforme necessario.

## Autenticacao
1. Crie um usuario (requer token valido):
   - `POST /api/auth/users`
2. Realize login para obter o token JWT:
   - `POST /api/auth/login`
   - Corpo de exemplo:
     ```json
     {
       "username": "usuario",
       "password": "senha"
     }
     ```
   - Resposta:
     ```json
     {
       "access_token": "<jwt>",
       "token_type": "bearer",
       "expires_in": 18000
     }
     ```
3. Envie o token no cabecalho `Authorization: Bearer <token>` para acessar os demais endpoints protegidos, como `/api/gas/upsert`, `/api/auth/me`, `/api/auth/users`, etc.

## Endpoint de mercado de gas
- **Metodo**: `POST`
- **Rota**: `/api/gas/upsert`
- **Requer autenticacao**: Sim
- **Descricao**: Recebe uma lista de registros e faz o upsert com base na combinacao (`DATA`, `PLANILHA`, `ABA`, `PRODUTO`). Se o registro existir, os campos variaveis sao atualizados; caso contrario, um novo registro e criado.
- **Exemplo de requisicao**:
  ```json
  [
    {
      "DATA": "2024-09-24",
      "PLANILHA": "PLANILHA.xlsx",
      "ABA": "HISTORICO",
      "PRODUTO": "GLP",
      "LOCAL": "Unidade X",
      "DESCRICAO": "Descricao opcional",
      "UNIDADE": "ton",
      "VALOR": 2.44,
      "DENSIDADE": 0.55
    }
  ]
  ```
- **Resposta**: `200 OK` (sem corpo). Em caso de erro, a API retorna detalhes no campo `detail`.

## Testes
O diretorio `tests/` esta pronto para receber suites de testes. Execute-os conforme sua ferramenta preferida (por exemplo, `pytest`).

## Proximos passos sugeridos
- Adicionar documentacao Swagger personalizada (disponivel por padrao em `/docs`).
- Criar scripts Alembic para versionar o schema do banco.
- Expandir a cobertura de testes automatizados.
