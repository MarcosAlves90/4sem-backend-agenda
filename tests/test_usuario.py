"""
Testes para o router de Usuários.

Testes abrangentes para autenticação (login, refresh) e CRUD de usuários
(criar, listar, obter, atualizar, deletar).
"""

from fastapi.testclient import TestClient


class TestLogin:
    """Testes de endpoint POST /api/v1/usuario/login"""

    def test_login_com_sucesso(self, client: TestClient, usuario_teste):
        """Deve fazer login com credentials válidas e retornar access_token"""
        response = client.post(
            "/api/v1/usuario/login",
            json={"username": "joao", "senha_hash": "SenhaForte@123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "refresh_token" in response.cookies

    def test_login_username_invalido(self, client: TestClient):
        """Deve retornar 401 se username não existe"""
        response = client.post(
            "/api/v1/usuario/login",
            json={"username": "inexistente", "senha_hash": "SenhaQualquer"},
        )

        assert response.status_code == 401
        assert "inválidos" in response.json()["detail"]

    def test_login_senha_incorreta(self, client: TestClient, usuario_teste):
        """Deve retornar 401 se senha está errada"""
        response = client.post(
            "/api/v1/usuario/login",
            json={"username": "joao", "senha_hash": "SenhaErrada"},
        )

        assert response.status_code == 401
        assert "inválidos" in response.json()["detail"]


class TestRefreshToken:
    """Testes de endpoint POST /api/v1/usuario/refresh"""

    def test_refresh_token_com_sucesso(
        self, client: TestClient, refresh_token_usuario_teste
    ):
        """Deve renovar access_token com refresh_token válido"""
        response = client.post(
            "/api/v1/usuario/refresh",
            json={"refresh_token": refresh_token_usuario_teste},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalido(self, client: TestClient):
        """Deve retornar 401 se refresh_token é inválido"""
        response = client.post(
            "/api/v1/usuario/refresh", json={"refresh_token": "token_invalido"}
        )

        assert response.status_code == 401


class TestCriarUsuario:
    """Testes de endpoint POST /api/v1/usuario/"""

    def test_criar_usuario_com_sucesso(self, client: TestClient, usuario_teste_data):
        """Deve criar novo usuário com dados válidos"""
        response = client.post("/api/v1/usuario/", json=usuario_teste_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["ra"] == usuario_teste_data["ra"]
        assert data["email"] == usuario_teste_data["email"]
        assert data["username"] == usuario_teste_data["username"]

    def test_criar_usuario_email_duplicado(
        self, client: TestClient, usuario_teste, usuario_teste_data
    ):
        """Deve retornar 400 se email já existe"""
        usuario_teste_data["email"] = "joao@example.com"  # Email do usuario_teste
        usuario_teste_data["ra"] = "9999999999999"
        usuario_teste_data["username"] = "novo_username"

        response = client.post("/api/v1/usuario/", json=usuario_teste_data)

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "unique" in detail or "constraint" in detail or "email" in detail

    def test_criar_usuario_username_duplicado(
        self, client: TestClient, usuario_teste, usuario_teste_data
    ):
        """Deve retornar 400 se username já existe"""
        usuario_teste_data["username"] = "joao"  # Username do usuario_teste
        usuario_teste_data["ra"] = "8888888888888"
        usuario_teste_data["email"] = "novo@example.com"

        response = client.post("/api/v1/usuario/", json=usuario_teste_data)

        assert response.status_code == 400


class TestListarUsuarios:
    """Testes de endpoint GET /api/v1/usuario/"""

    def test_listar_usuarios_com_sucesso(self, client: TestClient, usuario_teste):
        """Deve listar todos os usuários com paginação"""
        response = client.get("/api/v1/usuario/")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert data["total"] >= 1
        assert data["skip"] == 0
        assert data["limit"] == 100

    def test_listar_usuarios_com_paginacao(self, client: TestClient, usuario_teste):
        """Deve respeitar parâmetros skip e limit"""
        response = client.get("/api/v1/usuario/?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10


class TestObterUsuario:
    """Testes de endpoint GET /api/v1/usuario/{id_usuario}"""

    def test_obter_usuario_por_id(self, client: TestClient, usuario_teste):
        """Deve retornar usuário por ID"""
        response = client.get(f"/api/v1/usuario/{usuario_teste.id_usuario}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id_usuario"] == usuario_teste.id_usuario
        assert data["email"] == usuario_teste.email

    def test_obter_usuario_inexistente(self, client: TestClient):
        """Deve retornar 404 se usuário não existe"""
        response = client.get("/api/v1/usuario/9999")

        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()


class TestObterUsuarioPorRA:
    """Testes de endpoint GET /api/v1/usuario/ra/{ra}"""

    def test_obter_usuario_por_ra(self, client: TestClient, usuario_teste):
        """Deve retornar usuário por RA"""
        response = client.get(f"/api/v1/usuario/ra/{usuario_teste.ra}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["ra"] == usuario_teste.ra

    def test_obter_usuario_ra_inexistente(self, client: TestClient):
        """Deve retornar 404 se RA não existe"""
        response = client.get("/api/v1/usuario/ra/0000000000000")

        assert response.status_code == 404


class TestObterPerfil:
    """Testes de endpoint GET /api/v1/usuario/me"""

    def test_obter_perfil_autenticado(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve retornar perfil do usuário autenticado"""
        response = client.get("/api/v1/usuario/me", headers=headers_autenticado)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id_usuario"] == usuario_teste.id_usuario
        assert data["ra"] == usuario_teste.ra

    def test_obter_perfil_sem_autenticacao(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.get("/api/v1/usuario/me")

        assert response.status_code == 403


class TestAtualizarUsuario:
    """Testes de endpoints PUT/PATCH /api/v1/usuario/"""

    def test_atualizar_usuario_completo(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve atualizar todos os campos do usuário (PUT)"""
        dados_atualizacao = {
            "nome": "João Silva Atualizado",
            "email": "joao.novo@example.com",
            "username": "joao_novo",
            "senha_hash": "NovaSenha@123",
            "tel_celular": "11987654321",
        }

        response = client.put(
            "/api/v1/usuario/", json=dados_atualizacao, headers=headers_autenticado
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["nome"] == "João Silva Atualizado"

    def test_atualizar_usuario_parcial(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve atualizar apenas campos fornecidos (PATCH)"""
        dados_atualizacao = {"nome": "João Novo Nome"}

        response = client.patch(
            "/api/v1/usuario/", json=dados_atualizacao, headers=headers_autenticado
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["nome"] == "João Novo Nome"

    def test_atualizar_usuario_sem_autenticacao(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.put("/api/v1/usuario/", json={"nome": "Novo Nome"})

        assert response.status_code == 403


class TestDeletarUsuario:
    """Testes de endpoint DELETE /api/v1/usuario/"""

    def test_deletar_usuario_com_sucesso(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve deletar usuário autenticado"""
        response = client.delete("/api/v1/usuario/", headers=headers_autenticado)

        assert response.status_code == 200
        assert "deletado" in response.json()["message"].lower()

    def test_deletar_usuario_sem_autenticacao(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.delete("/api/v1/usuario/")

        assert response.status_code == 403


class TestListarPorInstituicao:
    """Testes de endpoint GET /api/v1/usuario/instituicao/{id_instituicao}"""

    def test_listar_usuarios_por_instituicao(
        self, client: TestClient, usuario_teste, instituicao_teste
    ):
        """Deve listar usuários de uma instituição"""
        response = client.get(
            f"/api/v1/usuario/instituicao/{instituicao_teste.id_instituicao}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["total"] >= 1


class TestListarPorCurso:
    """Testes de endpoint GET /api/v1/usuario/curso/{id_curso}"""

    def test_listar_usuarios_por_curso(
        self, client: TestClient, usuario_teste, curso_teste
    ):
        """Deve listar usuários de um curso"""
        response = client.get(f"/api/v1/usuario/curso/{curso_teste.id_curso}")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
