import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# carrega variáveis de um arquivo .env na raiz do projeto (se existir)
root = Path(__file__).resolve().parents[1]
env_path = root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # tenta carregar do ambiente padrão (por exemplo quando o dev configurou manualmente)
    load_dotenv()

# Configure a DATABASE_URL via env var. Exemplo:
# postgresql://<user>:<password>@<host>:<port>/<database>
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/agenda_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency - retorna uma sessão do banco de dados e garante fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
