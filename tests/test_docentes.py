"""
Testes para o router de Docentes.

Testes abrangentes para CRUD de docentes com validações de permissão.
"""


class TestCriarDocente:
    """Testes de endpoint POST /api/v1/docentes/"""

    def test_criar_docente_com_sucesso(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve criar novo docente para usuário autenticado"""
        dados_docente = {
            "nome": "Prof. João",
            "email": "prof.joao@example.com",
            "disciplina": "Matemática",
        }

        response = client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["nome"] == dados_docente["nome"]
        assert data["ra"] == usuario_teste.ra

    def test_criar_docente_email_duplicado(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve retornar 400 se email já existe"""
        dados_docente_1 = {
            "nome": "Prof. 1",
            "email": "prof@example.com",
        }
        client.post(
            "/api/v1/docentes/", json=dados_docente_1, headers=headers_autenticado
        )

        dados_docente_2 = {
            "nome": "Prof. 2",
            "email": "prof@example.com",  # Email duplicado
        }
        response = client.post(
            "/api/v1/docentes/", json=dados_docente_2, headers=headers_autenticado
        )

        assert response.status_code == 400


class TestListarDocentes:
    """Testes de endpoint GET /api/v1/docentes/"""

    def test_listar_docentes_do_usuario(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve listar apenas docentes do usuário autenticado"""
        dados_docente = {
            "nome": "Prof. João",
            "email": "prof.joao@example.com",
        }
        client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )

        response = client.get("/api/v1/docentes/", headers=headers_autenticado)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)


class TestObterDocente:
    """Testes de endpoint GET /api/v1/docentes/{id_docente}"""

    def test_obter_docente_do_usuario(self, client, usuario_teste, headers_autenticado):
        """Deve obter docente do usuário autenticado"""
        dados_docente = {
            "nome": "Prof. João",
            "email": "prof.joao@example.com",
        }
        response_criacao = client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )
        id_docente = response_criacao.json()["data"]["id_docente"]

        response = client.get(
            f"/api/v1/docentes/{id_docente}", headers=headers_autenticado
        )

        assert response.status_code == 200
        assert response.json()["data"]["id_docente"] == id_docente

    def test_obter_docente_outro_usuario(
        self,
        client,
        usuario_teste,
        usuario_teste_2,
        headers_autenticado,
        headers_autenticado_usuario_2,
    ):
        """Deve retornar 403 se tentar acessar docente de outro usuário"""
        dados_docente = {
            "nome": "Prof. do Usuário 1",
            "email": "prof@example.com",
        }
        response_criacao = client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )
        id_docente = response_criacao.json()["data"]["id_docente"]

        response = client.get(
            f"/api/v1/docentes/{id_docente}", headers=headers_autenticado_usuario_2
        )

        assert response.status_code == 403


class TestAtualizarDocente:
    """Testes de endpoints PUT/PATCH /api/v1/docentes/{id_docente}"""

    def test_atualizar_docente_completo(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve atualizar todos os campos do docente (PUT)"""
        dados_docente = {
            "nome": "Prof. João",
            "email": "prof.joao@example.com",
        }
        response_criacao = client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )
        id_docente = response_criacao.json()["data"]["id_docente"]

        dados_atualizacao = {
            "nome": "Prof. João Atualizado",
            "email": "prof.joao.novo@example.com",
        }
        response = client.put(
            f"/api/v1/docentes/{id_docente}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Prof. João Atualizado"

    def test_atualizar_docente_parcial(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve atualizar apenas campos fornecidos (PATCH)"""
        dados_docente = {
            "nome": "Prof. João",
            "email": "prof.joao@example.com",
        }
        response_criacao = client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )
        id_docente = response_criacao.json()["data"]["id_docente"]

        dados_atualizacao = {"nome": "Prof. Novo"}
        response = client.patch(
            f"/api/v1/docentes/{id_docente}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Prof. Novo"


class TestDeletarDocente:
    """Testes de endpoint DELETE /api/v1/docentes/{id_docente}"""

    def test_deletar_docente_com_sucesso(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve deletar docente do usuário"""
        dados_docente = {
            "nome": "Prof. João",
            "email": "prof.joao@example.com",
        }
        response_criacao = client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )
        id_docente = response_criacao.json()["data"]["id_docente"]

        response = client.delete(
            f"/api/v1/docentes/{id_docente}", headers=headers_autenticado
        )

        assert response.status_code == 200


class TestObterDocentePorEmail:
    """Testes de endpoint GET /api/v1/docentes/email/{email}"""

    def test_obter_docente_por_email(self, client, usuario_teste, headers_autenticado):
        """Deve obter docente por email"""
        email_docente = "prof@example.com"
        dados_docente = {
            "nome": "Prof. João",
            "email": email_docente,
        }
        client.post(
            "/api/v1/docentes/", json=dados_docente, headers=headers_autenticado
        )

        response = client.get(
            f"/api/v1/docentes/email/{email_docente}", headers=headers_autenticado
        )

        assert response.status_code == 200
        assert response.json()["data"]["email"] == email_docente
