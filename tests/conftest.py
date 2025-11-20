"""
Configuração central de fixtures para testes da API.

Este arquivo contém todas as fixtures compartilhadas entre os testes,
incluindo: cliente de teste, banco de dados, usuários de teste, e tokens JWT.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime

from app.database import Base, get_db
from app.main import app
from app.models import Usuario, Instituicao, Curso, TipoData
from app.auth import criar_access_token, criar_refresh_token
from app.crud import hash_senha
from fastapi.testclient import TestClient

# ============================================================================
# CONFIGURAÇÃO DE BANCO DE DADOS
# ============================================================================


@pytest.fixture(scope="session")
def db_engine():
    """
    Criar engine de BD em memória para testes (escopo: sessão).
    Usa SQLite em memória para velocidade máxima.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine


@pytest.fixture
def db_session(db_engine):
    """
    Criar nova sessão de BD para cada teste (escopo: função).
    Auto-rollback após teste para isolamento completo.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    Cliente de teste FastAPI com BD mockado (escopo: função).
    Injeta sessão de teste no dependency override.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ============================================================================
# DADOS DE TESTE - INSTITUIÇÕES
# ============================================================================


@pytest.fixture
def instituicao_teste(db_session: Session) -> Instituicao:
    """
    Criar instituição de teste padrão.
    Usada como padrão para criar usuários.
    """
    instituicao = Instituicao(nome="Universidade Teste")
    db_session.add(instituicao)
    db_session.commit()
    db_session.refresh(instituicao)
    return instituicao


@pytest.fixture
def tipo_data_teste(db_session: Session) -> TipoData:
    """
    Criar tipos de data padrão para testes.
    Necessário para testes de calendário.
    """
    tipos = [
        TipoData(id_tipo_data=1, nome="Falta"),
        TipoData(id_tipo_data=2, nome="Não letivo"),
        TipoData(id_tipo_data=3, nome="Letivo"),
    ]
    for tipo in tipos:
        db_session.add(tipo)
    db_session.commit()
    return tipos[0]


@pytest.fixture
def curso_teste(db_session: Session, instituicao_teste: Instituicao) -> Curso:
    """
    Criar curso de teste padrão.
    Associado à instituição de teste.
    """
    curso = Curso(
        nome="Engenharia de Software", id_instituicao=instituicao_teste.id_instituicao
    )
    db_session.add(curso)
    db_session.commit()
    db_session.refresh(curso)
    return curso


# ============================================================================
# DADOS DE TESTE - USUÁRIOS
# ============================================================================


@pytest.fixture
def usuario_teste_data() -> dict:
    """
    Dados de usuario para testes (sem criar no BD).
    Usado para testes de criação de usuários.
    """
    return {
        "ra": "1234567890123",
        "nome": "João Silva",
        "email": "joao@example.com",
        "username": "joao",
        "nome_instituicao": "Universidade Teste",
        "nome_curso": "Engenharia de Software",
        "senha_hash": "SenhaForte@123",
        "dt_nascimento": "1990-05-15",
        "tel_celular": "11979592191",
    }


@pytest.fixture
def usuario_teste(
    db_session: Session,
    instituicao_teste: Instituicao,
    curso_teste: Curso,
    tipo_data_teste,
) -> Usuario:
    """
    Criar usuário de teste padrão no BD (escopo: função).
    Usado para testes de endpoints autenticados.
    """
    usuario = Usuario(
        ra="1234567890123",
        nome="João Silva",
        email="joao@example.com",
        username="joao",
        id_instituicao=instituicao_teste.id_instituicao,
        id_curso=curso_teste.id_curso,
        senha_hash=hash_senha("SenhaForte@123"),
        dt_nascimento=datetime(1990, 5, 15).date(),
        tel_celular="11979592191",
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture
def usuario_teste_2(
    db_session: Session,
    instituicao_teste: Instituicao,
    curso_teste: Curso,
    tipo_data_teste,
) -> Usuario:
    """
    Criar segundo usuário de teste (para testes de isolamento).
    """
    usuario = Usuario(
        ra="9876543210987",
        nome="Maria Santos",
        email="maria@example.com",
        username="maria",
        id_instituicao=instituicao_teste.id_instituicao,
        id_curso=curso_teste.id_curso,
        senha_hash=hash_senha("OutraSenha@456"),
        dt_nascimento=datetime(1992, 8, 20).date(),
        tel_celular="11987654321",
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


# ============================================================================
# AUTENTICAÇÃO - TOKENS
# ============================================================================


@pytest.fixture
def access_token_usuario_teste(usuario_teste: Usuario) -> str:
    """
    Gerar access token JWT para usuario_teste.
    Válido por 30 minutos (padrão da aplicação).
    """
    return criar_access_token(data={"id_usuario": usuario_teste.id_usuario})


@pytest.fixture
def refresh_token_usuario_teste(usuario_teste: Usuario) -> str:
    """
    Gerar refresh token JWT para usuario_teste.
    Válido por 7 dias (padrão da aplicação).
    """
    return criar_refresh_token(data={"id_usuario": usuario_teste.id_usuario})


@pytest.fixture
def headers_autenticado(access_token_usuario_teste: str) -> dict:
    """
    Headers HTTP com Bearer token para requisições autenticadas.
    """
    return {"Authorization": f"Bearer {access_token_usuario_teste}"}


@pytest.fixture
def headers_autenticado_usuario_2(usuario_teste_2: Usuario) -> dict:
    """
    Headers para segundo usuário (teste de isolamento de dados).
    """
    token = criar_access_token(data={"id_usuario": usuario_teste_2.id_usuario})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# MARCADORES CUSTOMIZADOS
# ============================================================================


def pytest_configure(config):
    """
    Registrar marcadores customizados para categorizar testes.
    """
    config.addinivalue_line(
        "markers", "integration: testes de integração com múltiplos endpoints"
    )
    config.addinivalue_line("markers", "unit: testes unitários de endpoints isolados")
    config.addinivalue_line("markers", "auth: testes de autenticação e autorização")
    config.addinivalue_line(
        "markers", "crud: testes de criação, leitura, atualização, deleção"
    )
    config.addinivalue_line(
        "markers", "permission: testes de verificação de permissões"
    )
