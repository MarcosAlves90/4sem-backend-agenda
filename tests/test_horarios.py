"""
Testes para o router de Horários.
"""


class TestCriarHorario:
    """Testes de endpoint POST /api/v1/horario/"""

    def test_criar_horario_com_sucesso(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve criar novo horário para usuário autenticado"""
        dados_horario = {"dia_semana": 1, "numero_aula": 1, "disciplina": "Matemática"}

        response = client.post(
            "/api/v1/horario/", json=dados_horario, headers=headers_autenticado
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["dia_semana"] == 1
        assert data["ra"] == usuario_teste.ra

    def test_criar_horario_dia_invalido(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve retornar 422 se dia_semana inválido (não é 1-6)"""
        dados_horario = {
            "dia_semana": 7,  # Inválido
            "numero_aula": 1,
        }

        response = client.post(
            "/api/v1/horario/", json=dados_horario, headers=headers_autenticado
        )

        assert response.status_code == 422

    def test_criar_horario_numero_aula_invalido(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve retornar 422 se numero_aula inválido (não é 1-4)"""
        dados_horario = {
            "dia_semana": 1,
            "numero_aula": 5,  # Inválido
        }

        response = client.post(
            "/api/v1/horario/", json=dados_horario, headers=headers_autenticado
        )

        assert response.status_code == 422


class TestListarHorarios:
    """Testes de endpoint GET /api/v1/horario/"""

    def test_listar_horarios_do_usuario(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve listar apenas horários do usuário autenticado"""
        dados_horario = {
            "dia_semana": 1,
            "numero_aula": 1,
        }
        client.post("/api/v1/horario/", json=dados_horario, headers=headers_autenticado)

        response = client.get("/api/v1/horario/", headers=headers_autenticado)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)


class TestObterHorario:
    """Testes de endpoint GET /api/v1/horario/{id_horario}"""

    def test_obter_horario_do_usuario(self, client, usuario_teste, headers_autenticado):
        """Deve obter horário do usuário autenticado"""
        dados_horario = {
            "dia_semana": 1,
            "numero_aula": 1,
        }
        response_criacao = client.post(
            "/api/v1/horario/", json=dados_horario, headers=headers_autenticado
        )
        id_horario = response_criacao.json()["data"]["id_horario"]

        response = client.get(
            f"/api/v1/horario/{id_horario}", headers=headers_autenticado
        )

        assert response.status_code == 200
        assert response.json()["data"]["id_horario"] == id_horario


class TestListarHorariosPorDia:
    """Testes de endpoint GET /api/v1/horario/dia/{dia_semana}"""

    def test_listar_horarios_por_dia(self, client, usuario_teste, headers_autenticado):
        """Deve listar horários de um dia específico"""
        dados_horario = {
            "dia_semana": 2,
            "numero_aula": 1,
        }
        client.post("/api/v1/horario/", json=dados_horario, headers=headers_autenticado)

        response = client.get("/api/v1/horario/dia/2", headers=headers_autenticado)

        assert response.status_code == 200


class TestAtualizarHorario:
    """Testes de endpoints PUT/PATCH /api/v1/horario/{id_horario}"""

    def test_atualizar_horario_completo(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve atualizar todos os campos do horário (PUT)"""
        dados_horario = {
            "dia_semana": 1,
            "numero_aula": 1,
        }
        response_criacao = client.post(
            "/api/v1/horario/", json=dados_horario, headers=headers_autenticado
        )
        id_horario = response_criacao.json()["data"]["id_horario"]

        dados_atualizacao = {
            "dia_semana": 2,
            "numero_aula": 2,
        }
        response = client.put(
            f"/api/v1/horario/{id_horario}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["dia_semana"] == 2

    def test_atualizar_horario_parcial(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve atualizar apenas campos fornecidos (PATCH)"""
        dados_horario = {
            "dia_semana": 1,
            "numero_aula": 1,
        }
        response_criacao = client.post(
            "/api/v1/horario/", json=dados_horario, headers=headers_autenticado
        )
        id_horario = response_criacao.json()["data"]["id_horario"]

        dados_atualizacao = {"dia_semana": 3}
        response = client.patch(
            f"/api/v1/horario/{id_horario}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["dia_semana"] == 3


class TestDeletarHorario:
    """Testes de endpoint DELETE /api/v1/horario/{id_horario}"""

    def test_deletar_horario_com_sucesso(
        self, client, usuario_teste, headers_autenticado
    ):
        """Deve deletar horário do usuário"""
        dados_horario = {
            "dia_semana": 1,
            "numero_aula": 1,
        }
        response_criacao = client.post(
            "/api/v1/horario/", json=dados_horario, headers=headers_autenticado
        )
        id_horario = response_criacao.json()["data"]["id_horario"]

        response = client.delete(
            f"/api/v1/horario/{id_horario}", headers=headers_autenticado
        )

        assert response.status_code == 200
