"""
Testes para o router de Calendário.
"""


class TestCriarEvento:
    """Testes de endpoint POST /api/v1/calendario/"""

    def test_criar_evento_com_sucesso(self, client, usuario_teste, headers_autenticado):
        """Deve criar novo evento de calendário para usuário autenticado"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}

        response = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["data_evento"] == "2024-12-25"
        assert data["ra"] == usuario_teste.ra

    def test_criar_evento_tipo_invalido(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve retornar 422 se tipo_data inválido"""
        dados_evento = {
            "data_evento": "2024-12-25",
            "id_tipo_data": 999,  # Tipo inválido
        }

        response = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )

        assert response.status_code == 422

    def test_criar_evento_duplicado(self, client, usuario_teste, headers_autenticado):
        """Deve retornar 409 se já existe evento para mesma data e RA"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}

        # Criar primeiro evento
        client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )

        # Tentar criar evento duplicado
        response = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )

        assert response.status_code == 409


class TestListarEventos:
    """Testes de endpoint GET /api/v1/calendario/"""

    def test_listar_eventos_do_usuario(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve listar apenas eventos do usuário autenticado"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )

        response = client.get("/api/v1/calendario/", headers=headers_autenticado)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)
        assert data["total"] >= 1


class TestObterEvento:
    """Testes de endpoint GET /api/v1/calendario/{id_data_evento}"""

    def test_obter_evento_do_usuario(self, client, usuario_teste, headers_autenticado):
        """Deve obter evento do usuário autenticado"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        response_criacao = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )
        id_evento = response_criacao.json()["data"]["id_data_evento"]

        response = client.get(
            f"/api/v1/calendario/{id_evento}", headers=headers_autenticado
        )

        assert response.status_code == 200

    def test_obter_evento_outro_usuario(
        self,
        client,
        usuario_teste,
        usuario_teste_2,
        headers_autenticado,
        headers_autenticado_usuario_2,
    ):
        """Deve retornar 403 se tentar acessar evento de outro usuário"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        response_criacao = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )
        id_evento = response_criacao.json()["data"]["id_data_evento"]

        response = client.get(
            f"/api/v1/calendario/{id_evento}", headers=headers_autenticado_usuario_2
        )

        assert response.status_code == 403


class TestObterEventoPorData:
    """Testes de endpoint GET /api/v1/calendario/data/{data_evento}"""

    def test_obter_evento_por_data(self, client, usuario_teste, headers_autenticado):
        """Deve obter evento por data"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )

        response = client.get(
            "/api/v1/calendario/data/2024-12-25", headers=headers_autenticado
        )

        assert response.status_code == 200

    def test_obter_evento_data_invalida(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve retornar 400 se formato de data inválido"""
        response = client.get(
            "/api/v1/calendario/data/25-12-2024",  # Formato errado
            headers=headers_autenticado,
        )

        assert response.status_code == 400


class TestListarEventosPorTipo:
    """Testes de endpoint GET /api/v1/calendario/tipo/{id_tipo_data}"""

    def test_listar_eventos_por_tipo(self, client, usuario_teste, headers_autenticado):
        """Deve listar eventos filtrados por tipo"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )

        response = client.get("/api/v1/calendario/tipo/1", headers=headers_autenticado)

        assert response.status_code == 200


class TestAtualizarEvento:
    """Testes de endpoints PUT/PATCH /api/v1/calendario/{id_data_evento}"""

    def test_atualizar_evento_completo(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve atualizar todos os campos do evento (PUT)"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        response_criacao = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )
        id_evento = response_criacao.json()["data"]["id_data_evento"]

        dados_atualizacao = {"data_evento": "2024-12-26", "id_tipo_data": 2}
        response = client.put(
            f"/api/v1/calendario/{id_evento}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200

    def test_atualizar_evento_parcial(self, client, usuario_teste, headers_autenticado):
        """Deve atualizar apenas campos fornecidos (PATCH)"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        response_criacao = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )
        id_evento = response_criacao.json()["data"]["id_data_evento"]

        dados_atualizacao = {"id_tipo_data": 2}
        response = client.patch(
            f"/api/v1/calendario/{id_evento}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200


class TestDeletarEvento:
    """Testes de endpoint DELETE /api/v1/calendario/{id_data_evento}"""

    def test_deletar_evento_com_sucesso(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve deletar evento do usuário"""
        dados_evento = {"data_evento": "2024-12-25", "id_tipo_data": 1}
        response_criacao = client.post(
            "/api/v1/calendario/", json=dados_evento, headers=headers_autenticado
        )
        id_evento = response_criacao.json()["data"]["id_data_evento"]

        response = client.delete(
            f"/api/v1/calendario/{id_evento}", headers=headers_autenticado
        )

        assert response.status_code == 200
