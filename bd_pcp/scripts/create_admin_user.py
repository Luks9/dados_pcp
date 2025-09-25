"""
Script para criar usuário administrador inicial
Execute este script após configurar o banco de dados
"""
from sqlalchemy.orm import Session
from bd_pcp.core.session import SessionLocal
from bd_pcp.db.models.usuario import Usuario


def create_admin_user():
    """Cria um usuário administrador inicial"""
    db: Session = SessionLocal()
    
    try:
        # Verificar se já existe um usuário admin
        admin_user = db.query(Usuario).filter(Usuario.USERNAME == "admin").first()
        
        if admin_user:
            print("Usuário admin já existe!")
            return
        
        # Criar usuário admin
        admin = Usuario(
            USERNAME="admin",
            EMAIL="admin@empresa.com",
            IS_ACTIVE=True
        )
        admin.set_password("admin123")  # Lembre-se de alterar esta senha!
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"Usuário admin criado com sucesso! ID: {admin.ID}")
        print("IMPORTANTE: Altere a senha padrão após o primeiro login!")
        
    except Exception as e:
        print(f"Erro ao criar usuário admin: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()