from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bd_pcp.core.config import settings
from urllib.parse import quote_plus
from bd_pcp.db.models.model_base import Base


connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=10.117.201.110\ssis;"
    "PORT=1433;"
    "DATABASE=BD_DADOS;"
    "UID=acesso.pcp.dados;"
    "PWD=!QAZ@werBrava;")

DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"


# Criação da engine para o banco de dados
engine = create_engine(
    DATABASE_URL,
    fast_executemany=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Função para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    '''
    Criando todas as tabelas no banco de dados
    Importe a(s) tabela(s) que deseja criar
    '''
    #from bd_pcp.db.models.usuario import Usuario  # Importe suas tabelas aqui
    from bd_pcp.db.models.mercado_gas import MercadoGas 
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")


if __name__ == "__main__":
    # Chama a função para criar as tabelas 
    create_tables()