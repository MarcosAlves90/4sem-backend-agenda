"""
Testes para o router de Health.
"""


class TestHealthCheck:
    """Testes de endpoint GET /health/"""

    def test_health_check_sucesso(self, client):
        """Deve retornar status healthy da API"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
