from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401 - Necessário para registrar os modelos no SQLAlchemy
from . import constants
from .routers import (
    health,
    calendario,
    usuario,
    docentes,
    anotacao,
    discentes,
    notas,
    horario,
)

# ============================================================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================================================

# Base.metadata.create_all(bind=engine)  # Usar migrations (alembic) em produção

# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================================

app = FastAPI(
    title="API Agenda Acadêmica",
    version=constants.API_VERSION,
    description="API para gerenciamento de agenda acadêmica de alunos",
)

# CORS - Configurado com domínios específicos em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=constants.CORS_ORIGINS,
    allow_credentials=constants.CORS_ALLOW_CREDENTIALS,
    allow_methods=constants.CORS_ALLOW_METHODS,
    allow_headers=constants.CORS_ALLOW_HEADERS,
)


# ============================================================================
# TEMPLATES
# ============================================================================

templates = Jinja2Templates(directory="templates")

# ============================================================================
# ROUTERS
# ============================================================================

app.include_router(health.router, prefix="/api/v1/health")
app.include_router(usuario.router, prefix="/api/v1/usuario")
app.include_router(notas.router, prefix="/api/v1/notas")
app.include_router(discentes.router, prefix="/api/v1/discentes")
app.include_router(anotacao.router, prefix="/api/v1/anotacao")
app.include_router(docentes.router, prefix="/api/v1/docentes")
app.include_router(horario.router, prefix="/api/v1/horario")
app.include_router(calendario.router, prefix="/api/v1/calendario")

# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================


@app.get("/", tags=["Health"])
def homepage(request: Request):
    """Página inicial - links para documentação."""
    return templates.TemplateResponse("index.html", {"request": request})
