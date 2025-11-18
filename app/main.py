from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# import os

from .database import engine, Base
from . import models  # noqa: F401 - Necessário para registrar os modelos no SQLAlchemy
from .routers import health, calendario, tipo_data, usuario, docentes, anotacao

# ============================================================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================================================

# [PERIGO] Criar tabelas automaticamente (descomentar uma única vez para inicializar)
# Base.metadata.create_all(bind=engine)

# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================================

app = FastAPI(
    title="API Agenda Acadêmica",
    version="1.0.1",
    description="API para gerenciamento de agenda acadêmica de alunos",
)

# CORS - Necessário para permitir credenciais (cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Substituir por domínios específicos em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# TEMPLATES E RECURSOS ESTÁTICOS
# ============================================================================

templates = Jinja2Templates(directory="templates")

# [EXEMPLO] Servir arquivos estáticos (CSS, JS, imagens)
# if os.path.exists("static"):
#     app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# ROUTERS
# ============================================================================

app.include_router(health.router, prefix="/api/v1/health")
app.include_router(anotacao.router, prefix="/app/v1/anotacao")
app.include_router(docentes.router, prefix="/api/v1") 
app.include_router(usuario.router, prefix="/api/v1/usuario")
app.include_router(tipo_data.router, prefix="/api/v1/tipo-data")
app.include_router(calendario.router, prefix="/api/v1/calendario")

# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

@app.get("/", tags=["Health"])
def homepage(request: Request):
    """Página inicial - links para documentação."""
    return templates.TemplateResponse("index.html", {"request": request})
