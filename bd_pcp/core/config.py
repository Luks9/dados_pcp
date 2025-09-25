from pydantic_settings import BaseSettings
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    """
    Configurações globais da aplicação.

    As variáveis de ambiente são carregadas automaticamente de um arquivo .env.
    """
        
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database Configuration
    DB_DRIVER: str = "mssql+pyodbc"
    DB_HOST: str
    DB_PORT: int = 1433
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_ODBC_DRIVER: str = "ODBC Driver 17 for SQL Server"

    @property
    def DATABASE_URL(self) -> str:
        """Constrói a URL do banco de dados a partir das variáveis separadas."""
        #return "mssql+pyodbc://acesso.pcp.dados:!QAZ@werBrava@10.117.201.110\ssis/BD_DADOS?driver=ODBC+Driver+17+for+SQL+Server"
        return f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?driver={self.DB_ODBC_DRIVER.replace(' ', '+')}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()