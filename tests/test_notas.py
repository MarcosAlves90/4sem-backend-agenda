"""
Testes para o router de Notas.
"""


class TestCriarNota:
    """Testes de endpoint POST /api/v1/notas/"""

    def test_criar_nota_com_sucesso(self, client, usuario_teste, headers_autenticado):
        """Deve criar nova nota para usuário autenticado"""
        dados_nota = {"nota": "8.5", "bimestre": 1, "disciplina": "Matemática"}

        response = client.post(
            "/api/v1/notas/", json=dados_nota, headers=headers_autenticado
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["nota"] == dados_nota["nota"]
        assert data["ra"] == usuario_teste.ra


class TestListarNotas:
    """Testes de endpoint GET /api/v1/notas/"""

    def test_listar_notas_do_usuario(self, client, usuario_teste, headers_autenticado):
        """Deve listar apenas notas do usuário autenticado"""
        dados_nota = {"nota": "8.5", "bimestre": 1, "disciplina": "Matemática"}
        client.post("/api/v1/notas/", json=dados_nota, headers=headers_autenticado)

        response = client.get("/api/v1/notas/", headers=headers_autenticado)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)


class TestObterNota:
    """Testes de endpoint GET /api/v1/notas/{id_nota}"""

    def test_obter_nota_do_usuario(self, client, usuario_teste, headers_autenticado):
        """Deve obter nota do usuário autenticado"""
        dados_nota = {"nota": "8.5", "bimestre": 1, "disciplina": "Matemática"}
        response_criacao = client.post(
            "/api/v1/notas/", json=dados_nota, headers=headers_autenticado
        )
        id_nota = response_criacao.json()["data"]["id_nota"]

        response = client.get(f"/api/v1/notas/{id_nota}", headers=headers_autenticado)

        assert response.status_code == 200
        assert response.json()["data"]["id_nota"] == id_nota

    def test_obter_nota_outro_usuario(
        self,
        client,
        usuario_teste,
        usuario_teste_2,
        headers_autenticado,
        headers_autenticado_usuario_2,
    ):
        """Deve retornar 403 se tentar acessar nota de outro usuário"""
        dados_nota = {
            "nota": "9.0",
            "bimestre": 1,
        }
        response_criacao = client.post(
            "/api/v1/notas/", json=dados_nota, headers=headers_autenticado
        )
        id_nota = response_criacao.json()["data"]["id_nota"]

        response = client.get(
            f"/api/v1/notas/{id_nota}", headers=headers_autenticado_usuario_2
        )

        assert response.status_code == 403


class TestAtualizarNota:
    """Testes de endpoints PUT/PATCH /api/v1/notas/{id_nota}"""

    def test_atualizar_nota_completa(self, client, usuario_teste, headers_autenticado):
        """Deve atualizar todos os campos da nota (PUT)"""
        dados_nota = {
            "nota": "8.5",
            "bimestre": 1,
        }
        response_criacao = client.post(
            "/api/v1/notas/", json=dados_nota, headers=headers_autenticado
        )
        id_nota = response_criacao.json()["data"]["id_nota"]

        dados_atualizacao = {
            "nota": "9.0",
            "bimestre": 1,
        }
        response = client.put(
            f"/api/v1/notas/{id_nota}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["nota"] == "9.0"

    def test_atualizar_nota_parcial(self, client, usuario_teste, headers_autenticado):
        """Deve atualizar apenas campos fornecidos (PATCH)"""
        dados_nota = {
            "nota": "8.5",
            "bimestre": 1,
        }
        response_criacao = client.post(
            "/api/v1/notas/", json=dados_nota, headers=headers_autenticado
        )
        id_nota = response_criacao.json()["data"]["id_nota"]

        dados_atualizacao = {"nota": "9.5"}
        response = client.patch(
            f"/api/v1/notas/{id_nota}",
            json=dados_atualizacao,
            headers=headers_autenticado,
        )

        assert response.status_code == 200
        assert response.json()["data"]["nota"] == "9.5"


class TestDeletarNota:
    """Testes de endpoint DELETE /api/v1/notas/{id_nota}"""

    def test_deletar_nota_com_sucesso(self, client, usuario_teste, headers_autenticado):
        """Deve deletar nota do usuário"""
        dados_nota = {
            "nota": "8.5",
            "bimestre": 1,
        }
        response_criacao = client.post(
            "/api/v1/notas/", json=dados_nota, headers=headers_autenticado
        )
        id_nota = response_criacao.json()["data"]["id_nota"]

        response = client.delete(
            f"/api/v1/notas/{id_nota}", headers=headers_autenticado
        )

        assert response.status_code == 200
