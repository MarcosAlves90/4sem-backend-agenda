# 🧪 Testes - API Agenda Acadêmica

**Status:** ✅ 82/82 testes passando (100%)

## 📊 Cobertura

| Router | Testes | Status |
|--------|--------|--------|
| Usuario | 23 | ✅ Auth, CRUD, Tokens |
| Discentes | 12 | ✅ CRUD + Permissões |
| Docentes | 9 | ✅ CRUD |
| Notas | 9 | ✅ CRUD + RA Filter |
| Horários | 9 | ✅ CRUD + Validações |
| Calendário | 12 | ✅ CRUD + Duplicação |
| Anotações | 7 | ✅ CRUD |
| Health | 1 | ✅ Status Check |

## 🚀 Quickstart

```bash
# Instalar dependências
pip install -r requirements-dev.txt

# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Teste específico
pytest tests/test_usuario.py::TestLogin -v
```

## 📁 Estrutura

```text
tests/
├── conftest.py          # Fixtures compartilhadas
├── test_usuario.py      # Autenticação + CRUD
├── test_discentes.py    # Alunos
├── test_docentes.py     # Professores
├── test_notas.py        # Avaliações
├── test_horarios.py     # Aulas
├── test_calendario.py   # Eventos acadêmicos
├── test_anotacoes.py    # Anotações
└── test_health.py       # Health check
```

## 🔐 Segurança Testada

✅ **Autenticação:** Login, Refresh Token, JWT validation  
✅ **Autorização:** Isolamento de dados, verificação de propriedade  
✅ **Validação:** Email/username duplicado, valores inválidos  
✅ **Permissões:** Endpoints protegidos, acesso restrito

## 🔧 Fixtures Principais

```python
db_session          # Banco SQLite em memória (isolado por teste)
client              # TestClient FastAPI
usuario_teste       # Usuário padrão
usuario_teste_2     # Segundo usuário (testes de isolamento)
headers_autenticado # JWT headers
tipo_data_teste     # Tipos de calendário (Falta, Não letivo, Letivo)
```

## 📊 Padrão de Teste

```python
class TestCriar:
    def test_criar_com_sucesso(self, client, usuario_teste):
        """Arrange, Act, Assert"""
        response = client.post("/endpoint", json=dados)
        
        assert response.status_code == 201
        assert response.json()["data"]["campo"] == valor
```

## 🔄 CI/CD

GitHub Actions (`.github/workflows/tests.yml`):

- ✅ Testes (pytest + coverage)
- ✅ Lint (ruff, black, mypy)
- ✅ Security (bandit)

Execute localmente:

```bash
pytest --cov=app
ruff check app/
black --check app/
mypy app/ --ignore-missing-imports
```

## 🐛 Debug

```bash
# Verbose output
pytest -vv

# Com debugger
pytest --pdb

# Teste específico
pytest tests/test_usuario.py::TestLogin::test_login_com_sucesso -vv
```

## ✅ Checklist - Novo Endpoint

- [ ] Criar `test_novo_router.py`
- [ ] Testar sucesso (2xx)
- [ ] Testar erros (4xx, 5xx)
- [ ] Testar validações
- [ ] Testar permissões (se autenticado)
- [ ] Rodar: `pytest --cov=app`
- [ ] Cobertura > 80%

## 📚 Recursos

- [pytest docs](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
