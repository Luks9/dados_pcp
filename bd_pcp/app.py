from fastapi import FastAPI
from bd_pcp.core.config import settings
from bd_pcp.core.session import get_db
from sqlalchemy import text
from bd_pcp.routers import gas_rotas, usuario_autenticacao

app = FastAPI(
    title="API PCP DADOS"
)


app.include_router(gas_rotas.router)
app.include_router(usuario_autenticacao.router)

@app.get("/")
def read_root():
    # Testa a conexão com o banco de dados
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        print("Conexão com o banco de dados bem-sucedida:")
    except Exception as e:
        print(settings.DATABASE_URL)
        print("Erro ao conectar ao banco de dados:", e)
    return {"Hello": "World" }