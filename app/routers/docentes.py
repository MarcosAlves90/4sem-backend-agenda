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
	tags=["Docentes"],
	responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class DocenteNaoEncontrado(HTTPException):
	"""Docente não encontrado"""
	def __init__(self):
		super().__init__(status_code=404, detail="Docente não encontrado")


class EmailDuplicado(HTTPException):
	"""Email já cadastrado para outro docente"""
	def __init__(self):
		super().__init__(status_code=400, detail="Email já cadastrado para outro docente")


class ErroAoCriarDocente(HTTPException):
	"""Erro ao criar docente"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarDocente(HTTPException):
	"""Erro ao atualizar docente"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoDeletarDocente(HTTPException):
	"""Erro ao deletar docente"""
	def __init__(self):
		super().__init__(status_code=400, detail="Erro ao deletar docente")


class PermissaoNegada(HTTPException):
	"""Usuário não tem permissão para acessar este docente"""
	def __init__(self):
		super().__init__(status_code=403, detail="Você não tem permissão para acessar este docente")


# ============================================================================
# SCHEMAS PARA ATUALIZAÇÃO PARCIAL
# ============================================================================

class DocenteUpdate(BaseModel):
	nome: Optional[str] = Field(None, min_length=1, max_length=50)
	email: Optional[EmailStr] = None

	class Config:
		from_attributes = True

# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_docente_existe(db: Session, id_docente: int) -> models.Docente:
	"""Valida se docente existe. Retorna docente ou lança exceção."""
	docente = crud.obter_docente(db, id_docente)
	if not docente:
		raise DocenteNaoEncontrado()
	return docente


def _validar_docente_pertence_usuario(
	db: Session, 
	id_docente: int, 
	ra_usuario: str
) -> models.Docente:
	"""Valida se docente existe e pertence ao usuário. Retorna docente ou lança exceção."""
	docente = _validar_docente_existe(db, id_docente)
	
	# Verificar se o docente pertence ao usuário autenticado (comparar por RA)
	try:
		ra_docente = str(docente.ra) if hasattr(docente, 'ra') else None
		if ra_docente and ra_docente != ra_usuario:
			raise PermissaoNegada()
	except (ValueError, TypeError, AttributeError):
		# Se não conseguir comparar, verifica se tem ra
		if hasattr(docente, 'ra') and docente.ra is not None:
			raise PermissaoNegada()
	
	return docente


def _validar_email_unico(db: Session, email: str, id_docente_atual: int | None = None) -> None:
	"""Valida se email já está em uso por outro docente. Lança exceção se duplicado."""
	docente_existente = crud.obter_docente_por_email(db, email)
	
	if docente_existente is None:
		return
	
	# Se o email pertence ao mesmo docente, não é duplicação
	if id_docente_atual is not None:
		try:
			id_existente = int(str(docente_existente.id_docente))
			if id_existente == id_docente_atual:
				return
		except (ValueError, TypeError):
			pass
	
	raise EmailDuplicado()
@router.post("/", response_model=schemas.GenericResponse[schemas.Docente], status_code=201)
def criar_docente(
	docente: schemas.DocenteCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Criar novo docente.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Body:**
	- `nome` (string): Nome do docente (1-50 caracteres)
	- `email` (string): Email do docente (deve ser único)
	
	**Restrições:**
	- Email deve ser único na base de dados
	- Docente será associado ao RA do usuário autenticado
	
	**Respostas:**
	- 201: Docente criado com sucesso
	- 400: Erro de validação ou email duplicado
	- 401: Token ausente ou inválido
	"""
	try:
		_validar_email_unico(db, docente.email)
		
		# Obter RA do usuário autenticado
		ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
		
		# Criar docente diretamente com RA no banco de dados
		db_docente = models.Docente(
			nome=docente.nome,
			email=docente.email,
			ra=ra_usuario
		)
		db.add(db_docente)
		db.commit()
		db.refresh(db_docente)
		
		return schemas.GenericResponse(
			data=db_docente,
			success=True,
			message="Docente criado com sucesso"
		)
	except EmailDuplicado:
		raise
	except Exception as e:
		raise ErroAoCriarDocente(str(e))


@router.get("/", response_model=schemas.GenericListResponse[schemas.Docente])
def listar_docentes(
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
	db: Session = Depends(get_db)
):
	"""
	Listar todos os docentes do usuário autenticado com paginação.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Query Parameters:**
	- `skip` (int): Número de registros a saltar. Padrão: 0
	- `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
	
	**Restrições:**
	- Usuário só pode listar seus próprios docentes
	
	**Respostas:**
	- 200: Lista de docentes retornada com sucesso
	- 401: Token ausente ou inválido
	"""
	# Obter RA do usuário autenticado
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	
	# Listar apenas docentes do usuário autenticado
	docentes = db.query(models.Docente).filter(models.Docente.ra == ra_usuario).offset(skip).limit(limit).all()
	total = db.query(models.Docente).filter(models.Docente.ra == ra_usuario).count()
	
	return schemas.GenericListResponse(
		data=docentes,
		total=total,
		skip=skip,
		limit=limit,
		success=True
	)


@router.get("/{id_docente}", response_model=schemas.GenericResponse[schemas.Docente])
def obter_docente(
	id_docente: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Obter detalhes de um docente específico.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_docente` (int): ID único do docente
	
	**Restrições:**
	- Usuário só pode acessar seus próprios docentes
	
	**Respostas:**
	- 200: Docente retornado com sucesso
	- 403: Usuário não tem permissão para acessar este docente
	- 404: Docente não encontrado
	- 401: Token ausente ou inválido
	"""
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	docente = _validar_docente_pertence_usuario(db, id_docente, ra_usuario)
	return schemas.GenericResponse(data=docente, success=True)


@router.put("/{id_docente}", response_model=schemas.GenericResponse[schemas.Docente])
def atualizar_docente(
	id_docente: int,
	docente: schemas.DocenteCreate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Atualizar todos os campos de um docente (PUT).
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_docente` (int): ID único do docente a atualizar
	
	**Body:**
	- `nome` (string): Nome do docente (1-50 caracteres)
	- `email` (string): Email do docente (deve ser único)
	
	**Restrições:**
	- Docente deve existir e pertencer ao usuário autenticado
	- Email deve ser único (exceto o email atual do docente)
	- Todos os campos são obrigatórios
	
	**Respostas:**
	- 200: Docente atualizado com sucesso
	- 400: Erro de validação ou email duplicado
	- 403: Usuário não tem permissão para atualizar este docente
	- 404: Docente não encontrado
	- 401: Token ausente ou inválido
	"""
	try:
		ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
		_validar_docente_pertence_usuario(db, id_docente, ra_usuario)
		_validar_email_unico(db, docente.email, id_docente)
		
		db_atualizado = crud.atualizar_docente(db, id_docente, docente)
		return schemas.GenericResponse(
			data=db_atualizado,
			success=True,
			message="Docente atualizado com sucesso"
		)
	except (DocenteNaoEncontrado, EmailDuplicado, PermissaoNegada):
		raise
	except Exception as e:
		raise ErroAoAtualizarDocente(str(e))


@router.patch("/{id_docente}", response_model=schemas.GenericResponse[schemas.Docente])
def atualizar_parcial_docente(
	id_docente: int,
	docente_update: DocenteUpdate,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Atualizar parcialmente um docente (PATCH).
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_docente` (int): ID único do docente a atualizar
	
	**Body (todos os campos opcionais):**
	- `nome` (string, opcional): Nome do docente (1-50 caracteres)
	- `email` (string, opcional): Email do docente (deve ser único)
	
	**Restrições:**
	- Docente deve existir e pertencer ao usuário autenticado
	- Email deve ser único (exceto o email atual do docente)
	- Apenas campos fornecidos serão atualizados
	
	**Respostas:**
	- 200: Docente atualizado com sucesso
	- 400: Erro de validação, email duplicado ou nenhum dado fornecido
	- 403: Usuário não tem permissão para atualizar este docente
	- 404: Docente não encontrado
	- 401: Token ausente ou inválido
	"""
	try:
		ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
		docente_existente = _validar_docente_pertence_usuario(db, id_docente, ra_usuario)
		
		# Verificar se há dados para atualizar
		update_data = docente_update.model_dump(exclude_unset=True)
		if not update_data:
			raise ErroAoAtualizarDocente("Nenhum dado fornecido para atualização")
		
		# Validar email se fornecido
		if "email" in update_data:
			_validar_email_unico(db, update_data["email"], id_docente)
		
		# Preparar dados completos para atualização
		dados_atuais = {
			"nome": str(docente_existente.nome),
			"email": str(docente_existente.email)
		}
		dados_atuais.update(update_data)
		
		docente_completo = schemas.DocenteCreate(**dados_atuais)
		db_atualizado = crud.atualizar_docente(db, id_docente, docente_completo)
		
		return schemas.GenericResponse(
			data=db_atualizado,
			success=True,
			message="Docente atualizado parcialmente com sucesso"
		)
	except (DocenteNaoEncontrado, EmailDuplicado, ErroAoAtualizarDocente, PermissaoNegada):
		raise
	except Exception as e:
		raise ErroAoAtualizarDocente(str(e))


@router.delete("/{id_docente}", response_model=schemas.GenericResponse[dict])
def deletar_docente(
	id_docente: int,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Deletar um docente existente.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `id_docente` (int): ID único do docente a deletar
	
	**Restrições:**
	- Usuário só pode deletar seus próprios docentes
	
	**Respostas:**
	- 200: Docente deletado com sucesso
	- 400: Erro ao deletar docente
	- 403: Usuário não tem permissão para deletar este docente
	- 404: Docente não encontrado
	- 401: Token ausente ou inválido
	"""
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	_validar_docente_pertence_usuario(db, id_docente, ra_usuario)
	
	if crud.deletar_docente(db, id_docente):
		return schemas.GenericResponse(
			data={"id_deletado": id_docente},
			success=True,
			message="Docente deletado com sucesso"
		)
	
	raise ErroAoDeletarDocente()


@router.get("/email/{email}", response_model=schemas.GenericResponse[schemas.Docente])
def obter_docente_por_email(
	email: str,
	usuario_autenticado: models.Usuario = Depends(verificar_token),
	db: Session = Depends(get_db)
):
	"""
	Obter docente por email.
	
	**Autenticação:**
	- Requer token JWT no header `Authorization: Bearer <token>`
	
	**Path Parameters:**
	- `email` (string): Email do docente
	
	**Restrições:**
	- Usuário só pode acessar seus próprios docentes
	
	**Respostas:**
	- 200: Docente retornado com sucesso
	- 403: Usuário não tem permissão para acessar este docente
	- 404: Docente não encontrado
	- 401: Token ausente ou inválido
	"""
	ra_usuario = usuario_autenticado.ra if hasattr(usuario_autenticado, 'ra') else usuario_autenticado
	docente = crud.obter_docente_por_email(db, email)
	
	if not docente:
		raise DocenteNaoEncontrado()
	
	# Verificar se pertence ao usuário (comparar por RA)
	try:
		ra_docente = str(docente.ra) if hasattr(docente, 'ra') else None
		if ra_docente and ra_docente != ra_usuario:
			raise PermissaoNegada()
	except (ValueError, TypeError, AttributeError):
		if hasattr(docente, 'ra') and docente.ra is not None:
			raise PermissaoNegada()
	
	return schemas.GenericResponse(data=docente, success=True)