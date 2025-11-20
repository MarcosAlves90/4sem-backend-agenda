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
	prefix="/curso-disciplina",
	tags=["Curso-Disciplina"],
	responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class CursoDisciplinaJaExiste(HTTPException):
	"""Associação Curso-Disciplina já existe"""
	def __init__(self):
		super().__init__(
			status_code=400,
			detail="Esta associação Curso-Disciplina já existe"
		)


class CursoDisciplinaNaoEncontrada(HTTPException):
	"""Associação Curso-Disciplina não encontrada"""
	def __init__(self):
		super().__init__(status_code=404, detail="Associação Curso-Disciplina não encontrada")


class CursoNaoEncontrado(HTTPException):
	"""Curso não encontrado"""
	def __init__(self):
		super().__init__(status_code=404, detail="Curso não encontrado")


class DisciplinaNaoEncontrada(HTTPException):
	"""Disciplina não encontrada"""
	def __init__(self):
		super().__init__(status_code=404, detail="Disciplina não encontrada")


class ErroAoCriarAssociacao(HTTPException):
	"""Erro ao criar associação"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarAssociacao(HTTPException):
	"""Erro ao atualizar associação"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoDeletarAssociacao(HTTPException):
	"""Erro ao deletar associação"""
	def __init__(self):
		super().__init__(status_code=400, detail="Erro ao deletar associação")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_curso_existe(db: Session, id_curso: int) -> models.Curso:
	"""Valida se curso existe. Retorna curso ou lança exceção."""
	curso = db.query(models.Curso).filter(models.Curso.id_curso == id_curso).first()
	if not curso:
		raise CursoNaoEncontrado()
	return curso


def _validar_disciplina_existe(db: Session, id_disciplina: int) -> models.Disciplina:
	"""Valida se disciplina existe. Retorna disciplina ou lança exceção."""
	disciplina = db.query(models.Disciplina).filter(
		models.Disciplina.id_disciplina == id_disciplina
	).first()
	if not disciplina:
		raise DisciplinaNaoEncontrada()
	return disciplina


def _validar_associacao_existe(
	db: Session,
	id_curso: int,
	id_disciplina: int
) -> models.CursoDisciplina:
	"""Valida se associação existe. Retorna associação ou lança exceção."""
	associacao = db.query(models.CursoDisciplina).filter(
		(models.CursoDisciplina.id_curso == id_curso) &
		(models.CursoDisciplina.id_disciplina == id_disciplina)
	).first()
	if not associacao:
		raise CursoDisciplinaNaoEncontrada()
	return associacao


def _contar_associacoes(
	db: Session,
	id_curso: Optional[int] = None,
	id_disciplina: Optional[int] = None
) -> int:
	"""Conta associações com filtros opcionais."""
	query = db.query(models.CursoDisciplina)

	if id_curso is not None:
		query = query.filter(models.CursoDisciplina.id_curso == id_curso)

	if id_disciplina is not None:
		query = query.filter(models.CursoDisciplina.id_disciplina == id_disciplina)

	return query.count()


# ============================================================================
# ENDPOINTS - CREATE
# ============================================================================

@router.post(
	"/",
	response_model=schemas.GenericResponse[schemas.CursoDisciplinaDetail],
	status_code=201
)
def criar_associacao_curso_disciplina(
	associacao: schemas.CursoDisciplinaCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db),
):
	"""
	Criar nova associação Curso-Disciplina.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Body:**
	- `id_curso` (int): ID do curso
	- `id_disciplina` (int): ID da disciplina
	- `modulo` (int): Número do módulo (1-12)

	**Restrições:**
	- Curso e disciplina devem existir
	- Associação não deve existir previamente

	**Respostas:**
	- 201: Associação criada com sucesso
	- 400: Erro de validação, curso/disciplina não encontrados ou associação já existe
	- 401: Token ausente ou inválido
	"""
	try:
		# Validações
		_validar_curso_existe(db, associacao.id_curso)
		_validar_disciplina_existe(db, associacao.id_disciplina)

		# Verificar se já existe
		try:
			_validar_associacao_existe(db, associacao.id_curso, associacao.id_disciplina)
			raise CursoDisciplinaJaExiste()
		except CursoDisciplinaNaoEncontrada:
			pass

		# Criar associação
		nova_associacao = models.CursoDisciplina(
			id_curso=associacao.id_curso,
			id_disciplina=associacao.id_disciplina,
			modulo=associacao.modulo,
		)

		db.add(nova_associacao)
		db.commit()
		db.refresh(nova_associacao)

		return schemas.GenericResponse(
			data=schemas.CursoDisciplinaDetail.model_validate(nova_associacao),
			success=True,
			message="Associação Curso-Disciplina criada com sucesso",
		)
	except (CursoNaoEncontrado, DisciplinaNaoEncontrada, CursoDisciplinaJaExiste):
		raise
	except Exception as e:
		raise ErroAoCriarAssociacao(str(e))


# ============================================================================
# ENDPOINTS - READ
# ============================================================================

@router.get(
	"/",
	response_model=schemas.GenericListResponse[schemas.CursoDisciplinaDetail]
)
def listar_associacoes_curso_disciplina(
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	id_curso: int = Query(None, description="Filtrar por ID do curso"),
	id_disciplina: int = Query(None, description="Filtrar por ID da disciplina"),
	db: Session = Depends(get_db),
):
	"""
	Listar associações Curso-Disciplina com paginação e filtros.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
	- `id_curso` (int, opcional): Filtrar por ID do curso
	- `id_disciplina` (int, opcional): Filtrar por ID da disciplina

	**Respostas:**
	- 200: Lista de associações retornada com sucesso
	- 401: Token ausente ou inválido
	"""
	query = db.query(models.CursoDisciplina)

	if id_curso is not None:
		query = query.filter(models.CursoDisciplina.id_curso == id_curso)

	if id_disciplina is not None:
		query = query.filter(models.CursoDisciplina.id_disciplina == id_disciplina)

	associacoes = query.offset(skip).limit(limit).all()
	total = _contar_associacoes(db, id_curso, id_disciplina)

	return schemas.GenericListResponse(
		data=[schemas.CursoDisciplinaDetail.model_validate(a) for a in associacoes],
		total=total,
		skip=skip,
		limit=limit,
		success=True,
		message="Associações retornadas com sucesso",
	)


@router.get(
	"/{id_curso}/{id_disciplina}",
	response_model=schemas.GenericResponse[schemas.CursoDisciplinaDetail]
)
def obter_associacao_curso_disciplina(
	id_curso: int,
	id_disciplina: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db),
):
	"""
	Obter associação Curso-Disciplina específica.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_curso` (int): ID do curso
	- `id_disciplina` (int): ID da disciplina

	**Respostas:**
	- 200: Associação retornada com sucesso
	- 404: Associação não encontrada
	- 401: Token ausente ou inválido
	"""
	associacao = _validar_associacao_existe(db, id_curso, id_disciplina)

	return schemas.GenericResponse(
		data=schemas.CursoDisciplinaDetail.model_validate(associacao),
		success=True,
		message="Associação retornada com sucesso",
	)


@router.get(
	"/curso/{id_curso}",
	response_model=schemas.GenericListResponse[schemas.CursoDisciplinaDetail]
)
def listar_disciplinas_por_curso(
	id_curso: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	db: Session = Depends(get_db),
):
	"""
	Listar todas as disciplinas de um curso específico.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_curso` (int): ID do curso

	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

	**Restrições:**
	- Curso deve existir

	**Respostas:**
	- 200: Lista de disciplinas retornada com sucesso
	- 404: Curso não encontrado
	- 401: Token ausente ou inválido
	"""
	_validar_curso_existe(db, id_curso)

	associacoes = db.query(models.CursoDisciplina).filter(
		models.CursoDisciplina.id_curso == id_curso
	).offset(skip).limit(limit).all()

	total = _contar_associacoes(db, id_curso=id_curso)

	return schemas.GenericListResponse(
		data=[schemas.CursoDisciplinaDetail.model_validate(a) for a in associacoes],
		total=total,
		skip=skip,
		limit=limit,
		success=True,
		message="Disciplinas do curso retornadas com sucesso",
	)


# ============================================================================
# ENDPOINTS - UPDATE
# ============================================================================

@router.put(
	"/{id_curso}/{id_disciplina}",
	response_model=schemas.GenericResponse[schemas.CursoDisciplinaDetail]
)
def atualizar_associacao_curso_disciplina(
	id_curso: int,
	id_disciplina: int,
	associacao_update: schemas.CursoDisciplinaCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db),
):
	"""
	Atualizar associação Curso-Disciplina (módulo).

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_curso` (int): ID do curso
	- `id_disciplina` (int): ID da disciplina

	**Body:**
	- `id_curso` (int): Novo ID do curso (opcional, se diferente do path)
	- `id_disciplina` (int): Novo ID da disciplina (opcional, se diferente do path)
	- `modulo` (int): Novo número do módulo (1-12)

	**Restrições:**
	- Associação deve existir
	- Novo curso e disciplina devem existir

	**Respostas:**
	- 200: Associação atualizada com sucesso
	- 400: Erro de validação
	- 404: Associação ou curso/disciplina não encontrados
	- 401: Token ausente ou inválido
	"""
	try:
		associacao_existente = _validar_associacao_existe(db, id_curso, id_disciplina)

		# Validações para novos valores
		_validar_curso_existe(db, associacao_update.id_curso)
		_validar_disciplina_existe(db, associacao_update.id_disciplina)

		# Se alterando a associação (curso ou disciplina)
		if (associacao_update.id_curso != id_curso or
			associacao_update.id_disciplina != id_disciplina):
			try:
				_validar_associacao_existe(
					db,
					associacao_update.id_curso,
					associacao_update.id_disciplina
				)
				raise CursoDisciplinaJaExiste()
			except CursoDisciplinaNaoEncontrada:
				pass

		# Deletar antiga e criar nova (chave composta)
		db.delete(associacao_existente)

		nova_associacao = models.CursoDisciplina(
			id_curso=associacao_update.id_curso,
			id_disciplina=associacao_update.id_disciplina,
			modulo=associacao_update.modulo,
		)

		db.add(nova_associacao)
		db.commit()
		db.refresh(nova_associacao)

		return schemas.GenericResponse(
			data=schemas.CursoDisciplinaDetail.model_validate(nova_associacao),
			success=True,
			message="Associação atualizada com sucesso",
		)
	except (
		CursoDisciplinaNaoEncontrada,
		CursoNaoEncontrado,
		DisciplinaNaoEncontrada,
		CursoDisciplinaJaExiste
	):
		raise
	except Exception as e:
		raise ErroAoAtualizarAssociacao(str(e))


# ============================================================================
# ENDPOINTS - DELETE
# ============================================================================

@router.delete(
	"/{id_curso}/{id_disciplina}",
	response_model=schemas.GenericResponse[dict]
)
def deletar_associacao_curso_disciplina(
	id_curso: int,
	id_disciplina: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db),
):
	"""
	Deletar associação Curso-Disciplina.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_curso` (int): ID do curso
	- `id_disciplina` (int): ID da disciplina

	**Respostas:**
	- 200: Associação deletada com sucesso
	- 400: Erro ao deletar associação
	- 404: Associação não encontrada
	- 401: Token ausente ou inválido
	"""
	associacao_existente = _validar_associacao_existe(db, id_curso, id_disciplina)

	try:
		db.delete(associacao_existente)
		db.commit()

		return schemas.GenericResponse(
			data={"id_curso": id_curso, "id_disciplina": id_disciplina},
			success=True,
			message="Associação deletada com sucesso",
		)
	except Exception as e:
		raise ErroAoDeletarAssociacao()
