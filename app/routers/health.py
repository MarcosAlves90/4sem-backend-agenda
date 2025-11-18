from fastapi import APIRouter

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
	  - `version` (string): Versão da API (ex: "1.0.1")
	
	**Exemplo de Resposta:**
	```json
	{
	  "status": "healthy",
	  "version": "1.0.1"
	}
	```
	"""
	return {"status": "healthy", "version": "1.0.1"}
