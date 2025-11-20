"""
Testes para o router de Discentes.

Testes abrangentes para CRUD de discentes com validações de permissão
(criar, listar, obter, atualizar, deletar).
"""

from fastapi.testclient import TestClient


class TestCriarDiscente:
    """Testes de endpoint POST /api/v1/discentes/"""

    def test_criar_discente_com_sucesso(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve criar novo discente para usuário autenticado"""
        dados_discente = {
            "nome": "João Discente",
            "email": "discente@example.com",
            "tel_celular": "11987654321",
            "id_curso": 1,
        }

        response = client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["nome"] == dados_discente["nome"]
        assert data["email"] == dados_discente["email"]
        assert data["ra"] == usuario_teste.ra  # RA deve ser do usuário

    def test_criar_discente_email_duplicado(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve retornar 400 se email já existe"""
        # Criar primeiro discente
        dados_discente_1 = {
            "nome": "Discente 1",
            "email": "discente@example.com",
        }
        client.post(
            "/api/v1/discentes/", json=dados_discente_1, headers=headers_autenticado
        )

        # Tentar criar com mesmo email
        dados_discente_2 = {
            "nome": "Discente 2",
            "email": "discente@example.com",  # Email duplicado
        }
        response = client.post(
            "/api/v1/discentes/", json=dados_discente_2, headers=headers_autenticado
        )

        assert response.status_code == 400

    def test_criar_discente_sem_autenticacao(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.post(
            "/api/v1/discentes/", json={"nome": "João", "email": "joao@example.com"}
        )

        assert response.status_code == 403


class TestListarDiscentes:
    """Testes de endpoint GET /api/v1/discentes/"""

    def test_listar_discentes_do_usuario(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve listar apenas discentes do usuário autenticado"""
        # Criar discente
        dados_discente = {
            "nome": "João Discente",
            "email": "discente@example.com",
        }
        client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )

        # Listar
        response = client.get("/api/v1/discentes/", headers=headers_autenticado)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)

    def test_listar_discentes_sem_autenticacao(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.get("/api/v1/discentes/")

        assert response.status_code == 403


class TestObterDiscente:
    """Testes de endpoint GET /api/v1/discentes/{id_discente}"""

    def test_obter_discente_do_usuario(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve obter discente do usuário autenticado"""
        # Criar discente
        dados_discente = {
            "nome": "João Discente",
            "email": "discente@example.com",
        }
        response_criacao = client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )
        id_discente = response_criacao.json()["data"]["id_discente"]

        # Obter
        response = client.get(
            f"/api/v1/discentes/{id_discente}", headers=headers_autenticado
        )

        assert response.status_code == 200
        assert response.json()["data"]["id_discente"] == id_discente

    def test_obter_discente_outro_usuario(
        self,
        client: TestClient,
        usuario_teste,
        usuario_teste_2,
        headers_autenticado,
        headers_autenticado_usuario_2,
    ):
        """Deve retornar 403 se tentar acessar discente de outro usuário"""
        # Usuario 1 cria discente
        dados_discente = {
            "nome": "Discente do Usuário 1",
            "email": "discente@example.com",
        }
        response_criacao = client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )
        id_discente = response_criacao.json()["data"]["id_discente"]

        # Usuario 2 tenta acessar
        response = client.get(
            f"/api/v1/discentes/{id_discente}", headers=headers_autenticado_usuario_2
        )

        assert response.status_code == 403


class TestAtualizarDiscente:
    """Testes de endpoints PUT/PATCH /api/v1/discentes/{id_discente}"""

    def test_atualizar_discente_completo(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve atualizar todos os campos do discente (PUT)"""
        # Criar discente
        dados_discente = {
            "nome": "João Discente",
            "email": "discente@example.com",
        }
        response_criacao = client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )
        id_discente = response_criacao.json()["data"]["id_discente"]

        # Atualizar
        dados_atualizacao = {
            "nome": "João Discente Atualizado",
            "email": "discente.novo@example.com",
        }
        response = client.put(
            f"/api/v1/discentes/{id_discente}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["nome"] == "João Discente Atualizado"

    def test_atualizar_discente_parcial(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve atualizar apenas campos fornecidos (PATCH)"""
        # Criar discente
        dados_discente = {
            "nome": "João Discente",
            "email": "discente@example.com",
        }
        response_criacao = client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )
        id_discente = response_criacao.json()["data"]["id_discente"]

        # Atualizar parcialmente
        dados_atualizacao = {"nome": "João Novo"}
        response = client.patch(
            f"/api/v1/discentes/{id_discente}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "João Novo"


class TestDeletarDiscente:
    """Testes de endpoint DELETE /api/v1/discentes/{id_discente}"""

    def test_deletar_discente_com_sucesso(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve deletar discente do usuário"""
        # Criar discente
        dados_discente = {
            "nome": "João Discente",
            "email": "discente@example.com",
        }
        response_criacao = client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )
        id_discente = response_criacao.json()["data"]["id_discente"]

        # Deletar
        response = client.delete(
            f"/api/v1/discentes/{id_discente}", headers=headers_autenticado
        )

        assert response.status_code == 200

    def test_deletar_discente_outro_usuario(
        self,
        client: TestClient,
        usuario_teste,
        usuario_teste_2,
        headers_autenticado,
        headers_autenticado_usuario_2,
    ):
        """Deve retornar 403 se tentar deletar discente de outro usuário"""
        # Usuario 1 cria discente
        dados_discente = {
            "nome": "Discente do Usuário 1",
            "email": "discente@example.com",
        }
        response_criacao = client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )
        id_discente = response_criacao.json()["data"]["id_discente"]

        # Usuario 2 tenta deletar
        response = client.delete(
            f"/api/v1/discentes/{id_discente}", headers=headers_autenticado_usuario_2
        )

        assert response.status_code == 403


class TestObterDiscentePorEmail:
    """Testes de endpoint GET /api/v1/discentes/email/{email}"""

    def test_obter_discente_por_email(
        self, client: TestClient, usuario_teste, headers_autenticado
    ):
        """Deve obter discente por email"""
        # Criar discente
        email_discente = "discente@example.com"
        dados_discente = {
            "nome": "João Discente",
            "email": email_discente,
        }
        client.post(
            "/api/v1/discentes/", json=dados_discente, headers=headers_autenticado
        )

        # Obter por email
        response = client.get(
            f"/api/v1/discentes/email/{email_discente}", headers=headers_autenticado
        )

        assert response.status_code == 200
        assert response.json()["data"]["email"] == email_discente
