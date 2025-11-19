from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

from ..database import get_db
from .. import crud, models, schemas
from ..auth import verificar_token

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
	prefix="/discentes",
	tags=["Discentes"],
	responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class DiscenteNaoEncontrado(HTTPException):
	"""Discente não encontrado"""
	def __init__(self):
		super().__init__(status_code=404, detail="Discente não encontrado")


class EmailDuplicado(HTTPException):
	"""Email já cadastrado para outro discente"""
	def __init__(self):
		super().__init__(status_code=400, detail="Email já cadastrado para outro discente")


class ErroAoCriarDiscente(HTTPException):
	"""Erro ao criar discente"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarDiscente(HTTPException):
	"""Erro ao atualizar discente"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoDeletarDiscente(HTTPException):
	"""Erro ao deletar discente"""
	def __init__(self):
		super().__init__(status_code=400, detail="Erro ao deletar discente")


class PermissaoNegada(HTTPException):
	"""Usuário não tem permissão para acessar este discente"""
	def __init__(self):
		super().__init__(status_code=403, detail="Você não tem permissão para acessar este discente")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_discente_existe(db: Session, id_discente: int) -> models.Discente:
	"""Valida se discente existe. Retorna discente ou lança exceção."""
	discente = crud.obter_discente(db, id_discente)
	if not discente:
		raise DiscenteNaoEncontrado()
	return discente


def _validar_discente_pertence_usuario(
	db: Session,
	id_discente: int,
	ra_usuario: str
) -> models.Discente:
	"""Valida se discente existe e pertence ao usuário. Retorna discente ou lança exceção."""
	discente = _validar_discente_existe(db, id_discente)

	# Verificar se o discente pertence ao usuário autenticado (comparar por RA)
	try:
		ra_discente = str(discente.ra) if hasattr(discente, 'ra') else None
		if ra_discente and ra_discente != ra_usuario:
			raise PermissaoNegada()
	except (ValueError, TypeError, AttributeError):
		# Se não conseguir comparar, verifica se tem ra
		if hasattr(discente, 'ra') and discente.ra is not None:
			raise PermissaoNegada()

	return discente


def _validar_email_unico(db: Session, email: str, id_discente_atual: int | None = None) -> None:
	"""Valida se email já está em uso por outro discente. Lança exceção se duplicado."""
	discente_existente = crud.obter_discente_por_email(db, email)

	if discente_existente is None:
		return

	# Se o email pertence ao mesmo discente, não é duplicação
	if id_discente_atual is not None:
		try:
			id_existente = int(str(discente_existente.id_discente))
			if id_existente == id_discente_atual:
				return
		except (ValueError, TypeError):
			pass

	raise EmailDuplicado()


# ============================================================================
# ENDPOINTS (CRUD)
# ============================================================================

@router.post("/", response_model=schemas.GenericResponse[schemas.Discente], status_code=201)
def criar_discente(
	discente: schemas.DiscenteCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Criar novo discente.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Body:**
	- `nome` (string): Nome do discente (1-50 caracteres)
	- `email` (string): Email do discente (deve ser único)
	- `tel_celular` (string, opcional): Telefone (máx. 15 caracteres)
	- `id_curso` (int, opcional): ID do curso

	**Restrições:**
	- Email deve ser único na base de dados
	- Discente será associado ao RA do usuário autenticado

	**Respostas:**
	- 201: Discente criado com sucesso
	- 400: Erro de validação ou email duplicado
	- 401: Token ausente ou inválido
	"""
	try:
		_validar_email_unico(db, discente.email)

		# Obter RA do usuário autenticado
		ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado

		# Criar discente diretamente com RA no banco de dados
		db_discente = models.Discente(
			nome=discente.nome,
			email=discente.email,
			tel_celular=discente.tel_celular,
			id_curso=discente.id_curso,
			ra=ra_usuario
		)
		db.add(db_discente)
		db.commit()
		db.refresh(db_discente)

		return schemas.GenericResponse(
			data=db_discente,
			success=True,
			message="Discente criado com sucesso"
		)
	except EmailDuplicado:
		raise
	except Exception as e:
		raise ErroAoCriarDiscente(str(e))


@router.get("/", response_model=schemas.GenericListResponse[schemas.Discente])
def listar_discentes(
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	db: Session = Depends(get_db)
):
	"""
	Listar todos os discentes do usuário autenticado com paginação.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

	**Restrições:**
	- Usuário só pode listar seus próprios discentes

	**Respostas:**
	- 200: Lista de discentes retornada com sucesso
	- 401: Token ausente ou inválido
	"""
	# Obter RA do usuário autenticado
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado

	# Listar apenas discentes do usuário autenticado
	discentes = db.query(models.Discente).filter(models.Discente.ra == ra_usuario).offset(skip).limit(limit).all()
	total = db.query(models.Discente).filter(models.Discente.ra == ra_usuario).count()

	return schemas.GenericListResponse(
		data=discentes,
		total=total,
		skip=skip,
		limit=limit,
		success=True
	)


@router.get("/{id_discente}", response_model=schemas.GenericResponse[schemas.Discente])
def obter_discente(
	id_discente: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Obter detalhes de um discente específico.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `id_discente` (int): ID único do discente

	**Restrições:**
	- Usuário só pode acessar seus próprios discentes

	**Respostas:**
	- 200: Discente retornado com sucesso
	- 403: Usuário não tem permissão para acessar este discente
	- 404: Discente não encontrado
	- 401: Token ausente ou inválido
	"""
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	discente = _validar_discente_pertence_usuario(db, id_discente, ra_usuario)
	return schemas.GenericResponse(data=discente, success=True)


@router.get("/email/{email}", response_model=schemas.GenericResponse[schemas.Discente])
def obter_discente_por_email(
	email: str,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Obter discente por email.

	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`

	**Path Parameters:**
	- `email` (string): Email do discente

	**Restrições:**
	- Usuário só pode acessar seus próprios discentes

	**Respostas:**
	- 200: Discente retornado com sucesso
	- 403: Usuário não tem permissão para acessar este discente
	- 404: Discente não encontrado
	- 401: Token ausente ou inválido
	"""
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	discente = crud.obter_discente_por_email(db, email)

	if not discente:
		raise DiscenteNaoEncontrado()

	# Verificar se pertence ao usuário (comparar por RA)
	try:
		ra_discente = str(discente.ra) if hasattr(discente, 'ra') else None
		if ra_discente and ra_discente != ra_usuario:
			raise PermissaoNegada()
	except (ValueError, TypeError, AttributeError):
		if hasattr(discente, 'ra') and discente.ra is not None:
			raise PermissaoNegada()

	return schemas.GenericResponse(data=discente, success=True)


@router.put(
    "/{id_discente}",
    response_model=schemas.GenericResponse[schemas.Discente],
    summary="Atualizar um discente (PUT)"
)
def update_discente(
    id_discente: int,
    discente: schemas.DiscenteCreate, 
    db: Session = Depends(get_db)
):
    """
    Atualiza completamente um discente pelo seu ID (operação PUT).

    Substitui todos os dados do discente existente pelos dados fornecidos.
    """
    db_discente = crud.obter_discente(db, id_discente=id_discente)
    if db_discente is None:
        raise HTTPException(status_code=404, detail="Discente não encontrado")

    try:
        updated_discente = crud.atualizar_discente(db, id_discente=id_discente, discente=discente)
        return schemas.GenericResponse(
            data=updated_discente,
            success=True,
            message="Discente atualizado com sucesso"
        )
    except crud.IntegrityError:
       
        raise HTTPException(status_code=400, detail="Email já cadastrado")


@router.patch(
    "/{id_discente}",
    response_model=schemas.GenericResponse[schemas.Discente],
    summary="Atualizar um discente parcialmente (PATCH)"
)
def patch_discente(
    id_discente: int,
    discente: schemas.DiscenteUpdate,  
    db: Session = Depends(get_db)
):
    """
    Atualiza parcialmente um discente pelo seu ID (operação PATCH).

    Atualiza apenas os campos fornecidos no corpo da requisição.
    """
    db_discente = crud.obter_discente(db, id_discente=id_discente)
    if db_discente is None:
        raise HTTPException(status_code=404, detail="Discente não encontrado")

    try:
       
        patched_discente = crud.atualizar_discente_parcial(db, id_discente=id_discente, discente=discente)
        return schemas.GenericResponse(
            data=patched_discente,
            success=True,
            message="Discente atualizado parcialmente com sucesso"
        )
    except crud.IntegrityError:
        raise HTTPException(status_code=400, detail="Email já cadastrado")


@router.delete(
    "/{id_discente}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar um discente"
)
def delete_discente(
    id_discente: int,
    db: Session = Depends(get_db)
):
    """
    Deleta um discente pelo seu ID.
    """
    db_discente = crud.obter_discente(db, id_discente=id_discente)
    if db_discente is None:
        raise HTTPException(status_code=404, detail="Discente não encontrado")

    success = crud.deletar_discente(db, id_discente=id_discente)
    if not success:
        
        raise HTTPException(status_code=500, detail="Erro ao deletar discente")

    return  