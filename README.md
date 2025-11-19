# API Agenda Acadêmica

API REST para gerenciamento de agenda acadêmica de alunos com autenticação JWT e migrations automáticas.

## Quick Start

### 1. Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configuração

Crie arquivo `.env`:

```env
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=sua-chave-secreta-gerada
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Inicializar BD

Descomente em `app/main.py`:

```python
Base.metadata.create_all(bind=engine)
```

Execute uma vez e recomente.

### 4. Executar

```bash
uvicorn app.main:app --reload
```

API: [`http://localhost:8000`](http://localhost:8000)  
Docs: [`http://localhost:8000/docs`](http://localhost:8000/docs)

## Rotas

- `GET /api/v1/health` - Health check
- `GET /` - Página inicial
- `/api/v1/usuario` - Gerenciamento de usuários
- `/api/v1/docentes` - Gerenciamento de docentes
- `/api/v1/discentes` - Gerenciamento de discentes
- `/api/v1/tipo-data` - Tipos de datas
- `/api/v1/calendario` - Calendário acadêmico
- `/app/v1/anotacao` - Gerenciamento de anotações

## Stack

- **FastAPI** - Framework web moderno
- **SQLAlchemy** - ORM
- **PostgreSQL** - Banco de dados
- **Pydantic** - Validação de dados
- **JWT** - Autenticação
- **Alembic** - Migrations

## Estrutura

```txt
app/
├── main.py          # App e rotas principais
├── database.py      # Conexão BD
├── models.py        # Modelos ORM
├── crud.py          # Operações
├── schemas.py       # Validators Pydantic
├── auth.py          # Autenticação JWT
└── routers/         # Endpoints
    ├── anotacao.py
    ├── calendario.py
    ├── discentes.py
    ├── docentes.py
    ├── health.py
    ├── tipo_data.py
    └── usuario.py
```

## Licença

MIT
