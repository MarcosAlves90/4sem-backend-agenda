"""
Testes para o router de Anotações.
"""


class TestCriarAnotacao:
    """Testes de endpoint POST /api/v1/anotacao/"""

    def test_criar_anotacao_com_sucesso(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve criar nova anotação para usuário autenticado"""
        dados_anotacao = {
            "titulo": "Minha Anotação",
            "anotacao": "Conteúdo da anotação",
        }

        response = client.post(
            "/api/v1/anotacao/", json=dados_anotacao, headers=headers_autenticado
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["titulo"] == dados_anotacao["titulo"]
        assert data["anotacao"] == dados_anotacao["anotacao"]
        assert data["ra"] == usuario_teste.ra


class TestListarAnotacoes:
    """Testes de endpoint GET /api/v1/anotacao/"""

    def test_listar_anotacoes_do_usuario(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve listar apenas anotações do usuário autenticado"""
        dados_anotacao = {"titulo": "Anotação 1", "anotacao": "Conteúdo 1"}
        client.post(
            "/api/v1/anotacao/", json=dados_anotacao, headers=headers_autenticado
        )

        response = client.get("/api/v1/anotacao/", headers=headers_autenticado)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)


class TestObterAnotacao:
    """Testes de endpoint GET /api/v1/anotacao/{id_anotacao}"""

    def test_obter_anotacao_do_usuario(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve obter anotação do usuário autenticado"""
        dados_anotacao = {"titulo": "Anotação 1", "anotacao": "Conteúdo 1"}
        response_criacao = client.post(
            "/api/v1/anotacao/", json=dados_anotacao, headers=headers_autenticado
        )
        id_anotacao = response_criacao.json()["data"]["id_anotacao"]

        response = client.get(
            f"/api/v1/anotacao/{id_anotacao}", headers=headers_autenticado
        )

        assert response.status_code == 200
        assert response.json()["data"]["id_anotacao"] == id_anotacao

    def test_obter_anotacao_outro_usuario(
        self,
        client,
        usuario_teste,
        usuario_teste_2,
        headers_autenticado,
        headers_autenticado_usuario_2,
    ):
        """Deve retornar 403 se tentar acessar anotação de outro usuário"""
        dados_anotacao = {"titulo": "Anotação do Usuário 1", "anotacao": "Conteúdo"}
        response_criacao = client.post(
            "/api/v1/anotacao/", json=dados_anotacao, headers=headers_autenticado
        )
        id_anotacao = response_criacao.json()["data"]["id_anotacao"]

        response = client.get(
            f"/api/v1/anotacao/{id_anotacao}", headers=headers_autenticado_usuario_2
        )

        assert response.status_code == 403


class TestAtualizarAnotacao:
    """Testes de endpoints PUT/PATCH /api/v1/anotacao/{id_anotacao}"""

    def test_atualizar_anotacao_completa(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve atualizar todos os campos da anotação (PUT)"""
        dados_anotacao = {"titulo": "Anotação 1", "anotacao": "Conteúdo 1"}
        response_criacao = client.post(
            "/api/v1/anotacao/", json=dados_anotacao, headers=headers_autenticado
        )
        id_anotacao = response_criacao.json()["data"]["id_anotacao"]

        dados_atualizacao = {
            "titulo": "Anotação Atualizada",
            "anotacao": "Novo conteúdo",
        }
        response = client.put(
            f"/api/v1/anotacao/{id_anotacao}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["titulo"] == "Anotação Atualizada"

    def test_atualizar_anotacao_parcial(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve atualizar apenas campos fornecidos (PATCH)"""
        dados_anotacao = {"titulo": "Anotação 1", "anotacao": "Conteúdo 1"}
        response_criacao = client.post(
            "/api/v1/anotacao/", json=dados_anotacao, headers=headers_autenticado
        )
        id_anotacao = response_criacao.json()["data"]["id_anotacao"]

        dados_atualizacao = {"titulo": "Novo Título"}
        response = client.patch(
            f"/api/v1/anotacao/{id_anotacao}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["titulo"] == "Novo Título"


class TestDeletarAnotacao:
    """Testes de endpoint DELETE /api/v1/anotacao/{id_anotacao}"""

    def test_deletar_anotacao_com_sucesso(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve deletar anotação do usuário"""
        dados_anotacao = {"titulo": "Anotação 1", "anotacao": "Conteúdo 1"}
        response_criacao = client.post(
            "/api/v1/anotacao/", json=dados_anotacao, headers=headers_autenticado
        )
        id_anotacao = response_criacao.json()["data"]["id_anotacao"]

        response = client.delete(
            f"/api/v1/anotacao/{id_anotacao}", headers=headers_autenticado
        )

        assert response.status_code == 200
