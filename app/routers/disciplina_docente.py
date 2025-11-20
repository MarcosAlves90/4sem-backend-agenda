from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..auth import verificar_token
from .. import crud, models, schemas

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
	prefix="/disciplina-docente",
	tags=["Disciplina-Docente"],
	responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class DisciplinaDocenteJaExiste(HTTPException):
	"""Associação Disciplina-Docente já existe"""
	def __init__(self):
		super().__init__(
			status_code=400,
			detail="Este docente já está associado a esta disciplina"
		)


class DisciplinaDocenteNaoEncontrada(HTTPException):
	"""Associação Disciplina-Docente não encontrada"""
	def __init__(self):
		super().__init__(
			status_code=404,
			detail="Associação Disciplina-Docente não encontrada"
		)


class DisciplinaNaoEncontrada(HTTPException):
	"""Disciplina não encontrada"""
	def __init__(self):
		super().__init__(status_code=404, detail="Disciplina não encontrada")


class DocenteNaoEncontrado(HTTPException):
	"""Docente não encontrado"""
	def __init__(self):
		super().__init__(status_code=404, detail="Docente não encontrado")


class ErroAoCriarAssociacao(HTTPException):
	"""Erro ao criar associação"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoDeletarAssociacao(HTTPException):
	"""Erro ao deletar associação"""
	def __init__(self):
		super().__init__(status_code=400, detail="Erro ao deletar associação")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_disciplina_existe(db: Session, id_disciplina: int) -> models.Disciplina:
	"""Valida se disciplina existe. Retorna disciplina ou lança exceção."""
	disciplina = db.query(models.Disciplina).filter(
		models.Disciplina.id_disciplina == id_disciplina
	).first()
	if not disciplina:
		raise DisciplinaNaoEncontrada()
	return disciplina


def _validar_docente_existe(db: Session, id_docente: int) -> models.Docente:
	"""Valida se docente existe. Retorna docente ou lança exceção."""
	docente = db.query(models.Docente).filter(
		models.Docente.id_docente == id_docente
	).first()
	if not docente:
		raise DocenteNaoEncontrado()
	return docente


def _validar_associacao_existe(
	db: Session,
	id_disciplina: int,
	id_docente: int
) -> models.DisciplinaDocente:
	"""Valida se associação existe. Retorna associação ou lança exceção."""
	associacao = db.query(models.DisciplinaDocente).filter(
		(models.DisciplinaDocente.id_disciplina == id_disciplina) &
		(models.DisciplinaDocente.id_docente == id_docente)
	).first()
	if not associacao:
		raise DisciplinaDocenteNaoEncontrada()
	return associacao


def _contar_associacoes(
	db: Session,
	id_disciplina: Optional[int] = None,
	id_docente: Optional[int] = None
) -> int:
	"""Conta associações com filtros opcionais."""
	query = db.query(models.DisciplinaDocente)

	if id_disciplina is not None:
		query = query.filter(models.DisciplinaDocente.id_disciplina == id_disciplina)

	if id_docente is not None:
		query = query.filter(models.DisciplinaDocente.id_docente == id_docente)

	return query.count()


# ============================================================================
# ENDPOINTS - CREATE
# ============================================================================

@router.post(
	"/",
	response_model=schemas.GenericResponse[schemas.DisciplinaDocenteDetail],
	status_code=201
)
def criar_associacao_disciplina_docente(
	associacao: schemas.DisciplinaDocenteCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db),
):
	"""
	Criar nova associação Disciplina-Docente.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Body:**
	- `id_disciplina` (int): ID da disciplina
	- `id_docente` (int): ID do docente

	**Restrições:**
	- Disciplina e docente devem existir
	- Associação não deve existir previamente

	**Respostas:**
	- 201: Associação criada com sucesso
	- 400: Erro de validação, disciplina/docente não encontrados ou associação já existe
	- 401: Token ausente ou inválido
	"""
	try:
		# Validações
		_validar_disciplina_existe(db, associacao.id_disciplina)
		_validar_docente_existe(db, associacao.id_docente)

		# Verificar se já existe
		try:
			_validar_associacao_existe(db, associacao.id_disciplina, associacao.id_docente)
			raise DisciplinaDocenteJaExiste()
		except DisciplinaDocenteNaoEncontrada:
			pass

		# Criar associação
		nova_associacao = models.DisciplinaDocente(
			id_disciplina=associacao.id_disciplina,
			id_docente=associacao.id_docente,
		)

		db.add(nova_associacao)
		db.commit()
		db.refresh(nova_associacao)

		return schemas.GenericResponse(
			data=schemas.DisciplinaDocenteDetail.model_validate(nova_associacao),
			success=True,
			message="Associação Disciplina-Docente criada com sucesso",
		)
	except (DisciplinaNaoEncontrada, DocenteNaoEncontrado, DisciplinaDocenteJaExiste):
		raise
	except Exception as e:
		raise ErroAoCriarAssociacao(str(e))


# ============================================================================
# ENDPOINTS - READ
# ============================================================================

@router.get(
	"/",
	response_model=schemas.GenericListResponse[schemas.DisciplinaDocenteDetail]
)
def listar_associacoes_disciplina_docente(
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	id_disciplina: int = Query(None, description="Filtrar por ID da disciplina"),
	id_docente: int = Query(None, description="Filtrar por ID do docente"),
	db: Session = Depends(get_db),
):
	"""
	Listar associações Disciplina-Docente com paginação e filtros.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
	- `id_disciplina` (int, opcional): Filtrar por ID da disciplina
	- `id_docente` (int, opcional): Filtrar por ID do docente

	**Respostas:**
	- 200: Lista de associações retornada com sucesso
	- 401: Token ausente ou inválido
	"""
	query = db.query(models.DisciplinaDocente)

	if id_disciplina is not None:
		query = query.filter(models.DisciplinaDocente.id_disciplina == id_disciplina)

	if id_docente is not None:
		query = query.filter(models.DisciplinaDocente.id_docente == id_docente)

	associacoes = query.offset(skip).limit(limit).all()
	total = _contar_associacoes(db, id_disciplina, id_docente)

	return schemas.GenericListResponse(
		data=[schemas.DisciplinaDocenteDetail.model_validate(a) for a in associacoes],
		total=total,
		skip=skip,
		limit=limit,
		success=True,
		message="Associações retornadas com sucesso",
	)


@router.get(
	"/{id_disciplina}/{id_docente}",
	response_model=schemas.GenericResponse[schemas.DisciplinaDocenteDetail]
)
def obter_associacao_disciplina_docente(
	id_disciplina: int,
	id_docente: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db),
):
	"""
	Obter associação Disciplina-Docente específica.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_disciplina` (int): ID da disciplina
	- `id_docente` (int): ID do docente

	**Respostas:**
	- 200: Associação retornada com sucesso
	- 404: Associação não encontrada
	- 401: Token ausente ou inválido
	"""
	associacao = _validar_associacao_existe(db, id_disciplina, id_docente)

	return schemas.GenericResponse(
		data=schemas.DisciplinaDocenteDetail.model_validate(associacao),
		success=True,
		message="Associação retornada com sucesso",
	)


@router.get(
	"/disciplina/{id_disciplina}",
	response_model=schemas.GenericListResponse[schemas.DisciplinaDocenteDetail]
)
def listar_docentes_por_disciplina(
	id_disciplina: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	db: Session = Depends(get_db),
):
	"""
	Listar todos os docentes de uma disciplina específica.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_disciplina` (int): ID da disciplina

	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

	**Restrições:**
	- Disciplina deve existir

	**Respostas:**
	- 200: Lista de docentes retornada com sucesso
	- 404: Disciplina não encontrada
	- 401: Token ausente ou inválido
	"""
	_validar_disciplina_existe(db, id_disciplina)

	associacoes = db.query(models.DisciplinaDocente).filter(
		models.DisciplinaDocente.id_disciplina == id_disciplina
	).offset(skip).limit(limit).all()

	total = _contar_associacoes(db, id_disciplina=id_disciplina)

	return schemas.GenericListResponse(
		data=[schemas.DisciplinaDocenteDetail.model_validate(a) for a in associacoes],
		total=total,
		skip=skip,
		limit=limit,
		success=True,
		message="Docentes da disciplina retornados com sucesso",
	)


@router.get(
	"/docente/{id_docente}",
	response_model=schemas.GenericListResponse[schemas.DisciplinaDocenteDetail]
)
def listar_disciplinas_por_docente(
	id_docente: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	db: Session = Depends(get_db),
):
	"""
	Listar todas as disciplinas de um docente específico.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_docente` (int): ID do docente

	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

	**Restrições:**
	- Docente deve existir

	**Respostas:**
	- 200: Lista de disciplinas retornada com sucesso
	- 404: Docente não encontrado
	- 401: Token ausente ou inválido
	"""
	_validar_docente_existe(db, id_docente)

	associacoes = db.query(models.DisciplinaDocente).filter(
		models.DisciplinaDocente.id_docente == id_docente
	).offset(skip).limit(limit).all()

	total = _contar_associacoes(db, id_docente=id_docente)

	return schemas.GenericListResponse(
		data=[schemas.DisciplinaDocenteDetail.model_validate(a) for a in associacoes],
		total=total,
		skip=skip,
		limit=limit,
		success=True,
		message="Disciplinas do docente retornadas com sucesso",
	)


# ============================================================================
# ENDPOINTS - DELETE
# ============================================================================

@router.delete(
	"/{id_disciplina}/{id_docente}",
	response_model=schemas.GenericResponse[dict]
)
def deletar_associacao_disciplina_docente(
	id_disciplina: int,
	id_docente: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db),
):
	"""
	Deletar associação Disciplina-Docente.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_disciplina` (int): ID da disciplina
	- `id_docente` (int): ID do docente

	**Respostas:**
	- 200: Associação deletada com sucesso
	- 400: Erro ao deletar associação
	- 404: Associação não encontrada
	- 401: Token ausente ou inválido
	"""
	associacao_existente = _validar_associacao_existe(db, id_disciplina, id_docente)

	try:
		db.delete(associacao_existente)
		db.commit()

		return schemas.GenericResponse(
			data={"id_disciplina": id_disciplina, "id_docente": id_docente},
			success=True,
			message="Associação deletada com sucesso",
		)
	except Exception as e:
		raise ErroAoDeletarAssociacao()
