from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from ..database import get_db
from .. import crud, models, schemas
from ..auth import verificar_token

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
	prefix="/anotacoes",
	tags=["Anotações"],
	responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class AnotacaoNaoEncontrada(HTTPException):
	"""Anotação não encontrada"""
	def __init__(self):
		super().__init__(status_code=404, detail="Anotação não encontrada")


class ErroAoCriarAnotacao(HTTPException):
	"""Erro ao criar anotação"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarAnotacao(HTTPException):
	"""Erro ao atualizar anotação"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoDeletarAnotacao(HTTPException):
	"""Erro ao deletar anotação"""
	def __init__(self):
		super().__init__(status_code=400, detail="Erro ao deletar anotação")


class PermissaoNegada(HTTPException):
	"""Usuário não tem permissão para acessar esta anotação"""
	def __init__(self):
		super().__init__(status_code=403, detail="Você não tem permissão para acessar esta anotação")


# ============================================================================
# SCHEMAS PARA ATUALIZAÇÃO PARCIAL
# ============================================================================

class AnotacaoUpdate(BaseModel):
	titulo: Optional[str] = Field(None, min_length=1, max_length=50)
	anotacao: Optional[str] = Field(None, min_length=1, max_length=255)

	class Config:
		from_attributes = True

# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_anotacao_existe(db: Session, id_anotacao: int) -> models.Anotacao:
	"""Valida se anotação existe. Retorna anotação ou lança exceção."""
	anotacao = crud.obter_anotacao(db, id_anotacao)
	if not anotacao:
		raise AnotacaoNaoEncontrada()
	return anotacao


def _validar_anotacao_pertence_usuario(
	db: Session, 
	id_anotacao: int, 
	ra_usuario: str
) -> models.Anotacao:
	"""Valida se anotação existe e pertence ao usuário. Retorna anotação ou lança exceção."""
	anotacao = _validar_anotacao_existe(db, id_anotacao)
	
	# Verificar se a anotação pertence ao usuário autenticado (comparar por RA)
	try:
		ra_anotacao = str(anotacao.ra) if hasattr(anotacao, 'ra') else None
		if ra_anotacao and ra_anotacao != ra_usuario:
			raise PermissaoNegada()
	except (ValueError, TypeError, AttributeError):
		# Se não conseguir comparar, verifica se tem ra
		if hasattr(anotacao, 'ra') and anotacao.ra is not None:
			raise PermissaoNegada()
	
	return anotacao


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=schemas.GenericResponse[schemas.Anotacao], status_code=201)
def criar_anotacao(
	anotacao: schemas.AnotacaoCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Criar nova anotação.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Body:**
	- `titulo` (string): Título da anotação (1-50 caracteres)
	- `anotacao` (string): Conteúdo da anotação (1-255 caracteres)
	
	**Restrições:**
	- Anotação será associada ao RA do usuário autenticado
	
	**Respostas:**
	- 201: Anotação criada com sucesso
	- 400: Erro de validação
	- 401: Token ausente ou inválido
	"""
	try:
		# Obter RA do usuário autenticado
		ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
		
		# Criar anotação com RA do usuário
		db_anotacao = models.Anotacao(
			ra=ra_usuario,
			titulo=anotacao.titulo,
			anotacao=anotacao.anotacao
		)
		db.add(db_anotacao)
		db.commit()
		db.refresh(db_anotacao)
		
		return schemas.GenericResponse(
			data=db_anotacao,
			success=True,
			message="Anotação criada com sucesso"
		)
	except Exception as e:
		raise ErroAoCriarAnotacao(str(e))


@router.get("/", response_model=schemas.GenericListResponse[schemas.Anotacao])
def listar_anotacoes(
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	db: Session = Depends(get_db)
):
	"""
	Listar todas as anotações do usuário autenticado com paginação.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
	
	**Restrições:**
	- Usuário só pode listar suas próprias anotações
	
	**Respostas:**
	- 200: Lista de anotações retornada com sucesso
	- 401: Token ausente ou inválido
	"""
	# Obter RA do usuário autenticado
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	
	# Listar apenas anotações do usuário autenticado
	anotacoes = crud.obter_anotacoes_por_usuario(db, ra_usuario, skip, limit)
	total = db.query(models.Anotacao).filter(models.Anotacao.ra == ra_usuario).count()
	
	return schemas.GenericListResponse(
		data=anotacoes,
		total=total,
		skip=skip,
		limit=limit,
		success=True
	)


@router.get("/{id_anotacao}", response_model=schemas.GenericResponse[schemas.Anotacao])
def obter_anotacao(
	id_anotacao: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Obter detalhes de uma anotação específica.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_anotacao` (int): ID único da anotação
	
	**Restrições:**
	- Usuário só pode acessar suas próprias anotações
	
	**Respostas:**
	- 200: Anotação retornada com sucesso
	- 403: Usuário não tem permissão para acessar esta anotação
	- 404: Anotação não encontrada
	- 401: Token ausente ou inválido
	"""
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	anotacao = _validar_anotacao_pertence_usuario(db, id_anotacao, ra_usuario)
	
	return schemas.GenericResponse(data=anotacao, success=True)


@router.put("/{id_anotacao}", response_model=schemas.GenericResponse[schemas.Anotacao])
def atualizar_anotacao(
	id_anotacao: int,
	anotacao: schemas.AnotacaoCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Atualizar todos os campos de uma anotação (PUT).
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_anotacao` (int): ID único da anotação a atualizar
	
	**Body:**
	- `titulo` (string): Título da anotação (1-50 caracteres)
	- `anotacao` (string): Conteúdo da anotação (1-255 caracteres)
	
	**Restrições:**
	- Anotação deve existir e pertencer ao usuário autenticado
	- Todos os campos são obrigatórios
	
	**Respostas:**
	- 200: Anotação atualizada com sucesso
	- 400: Erro de validação
	- 403: Usuário não tem permissão para atualizar esta anotação
	- 404: Anotação não encontrada
	- 401: Token ausente ou inválido
	"""
	try:
		ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
		_validar_anotacao_pertence_usuario(db, id_anotacao, ra_usuario)
		
		db_atualizado = crud.atualizar_anotacao(db, id_anotacao, anotacao)
		return schemas.GenericResponse(
			data=db_atualizado,
			success=True,
			message="Anotação atualizada com sucesso"
		)
	except (AnotacaoNaoEncontrada, PermissaoNegada):
		raise
	except Exception as e:
		raise ErroAoAtualizarAnotacao(str(e))


@router.patch("/{id_anotacao}", response_model=schemas.GenericResponse[schemas.Anotacao])
def atualizar_parcial_anotacao(
	id_anotacao: int,
	anotacao_update: AnotacaoUpdate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Atualizar parcialmente uma anotação (PATCH).
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_anotacao` (int): ID único da anotação a atualizar
	
	**Body (todos os campos opcionais):**
	- `titulo` (string, opcional): Título da anotação (1-50 caracteres)
	- `anotacao` (string, opcional): Conteúdo da anotação (1-255 caracteres)
	
	**Restrições:**
	- Anotação deve existir e pertencer ao usuário autenticado
	- Apenas campos fornecidos serão atualizados
	
	**Respostas:**
	- 200: Anotação atualizada com sucesso
	- 400: Erro de validação ou nenhum dado fornecido
	- 403: Usuário não tem permissão para atualizar esta anotação
	- 404: Anotação não encontrada
	- 401: Token ausente ou inválido
	"""
	try:
		ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
		anotacao_existente = _validar_anotacao_pertence_usuario(db, id_anotacao, ra_usuario)
		
		# Verificar se há dados para atualizar
		update_data = anotacao_update.model_dump(exclude_unset=True)
		if not update_data:
			raise ErroAoAtualizarAnotacao("Nenhum dado fornecido para atualização")
		
		# Preparar dados completos para atualização
		dados_atuais = {
			"titulo": str(anotacao_existente.titulo),
			"anotacao": str(anotacao_existente.anotacao)
		}
		dados_atuais.update(update_data)
		
		anotacao_completa = schemas.AnotacaoCreate(**dados_atuais)
		db_atualizado = crud.atualizar_anotacao(db, id_anotacao, anotacao_completa)
		
		return schemas.GenericResponse(
			data=db_atualizado,
			success=True,
			message="Anotação atualizada parcialmente com sucesso"
		)
	except (AnotacaoNaoEncontrada, ErroAoAtualizarAnotacao, PermissaoNegada):
		raise
	except Exception as e:
		raise ErroAoAtualizarAnotacao(str(e))


@router.delete("/{id_anotacao}", response_model=schemas.GenericResponse[dict])
def deletar_anotacao(
	id_anotacao: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Deletar uma anotação existente.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_anotacao` (int): ID único da anotação a deletar
	
	**Restrições:**
	- Usuário só pode deletar suas próprias anotações
	
	**Respostas:**
	- 200: Anotação deletada com sucesso
	- 400: Erro ao deletar anotação
	- 403: Usuário não tem permissão para deletar esta anotação
	- 404: Anotação não encontrada
	- 401: Token ausente ou inválido
	"""
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	_validar_anotacao_pertence_usuario(db, id_anotacao, ra_usuario)
	
	if crud.deletar_anotacao(db, id_anotacao):
		return schemas.GenericResponse(
			data={"id_deletado": id_anotacao},
			success=True,
			message="Anotação deletada com sucesso"
		)
	
	raise ErroAoDeletarAnotacao()
