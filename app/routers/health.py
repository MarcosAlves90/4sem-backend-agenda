from fastapi import APIRouter

from .. import constants

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(tags=["Health"])

# ============================================================================
# ENDPOINTS - HEALTH
# ============================================================================


@router.get("/", tags=["Health"])
def health_check():
    """
    Verificar status da API.

    **Propósito:**
    - Endpoint de monitoramento para verificar se a aplicação está online
    - Usado por probes de health check, load balancers e monitoramento

    **Respostas:**
    - 200: API está saudável e online
      - `status` (string): Estado da API ("healthy")
      - `version` (string): Versão da API (ex: "1.1.0")

    **Exemplo de Resposta:**
    ```json
    {
      "status": "healthy",
      "version": "1.1.0"
    }
    ```
    """
    return {"status": "healthy", "version": constants.API_VERSION}
