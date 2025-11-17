from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, models, schemas
from ..auth import criar_access_token, criar_refresh_token, verificar_token, verificar_refresh_token


# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
	tags=["Usuário"],
	responses={404: {"description": "Não encontrado"}},
)


# ============================================================================
# ENDPOINTS - USUÁRIOS
# ============================================================================


@router.post("/login", response_model=schemas.Token, tags=["Autenticação"])
def login(
	credenciais: schemas.Login,
	response: Response,
	db: Session = Depends(get_db),
):
	"""
	Realizar login e obter token JWT.
	
	**Campos Obrigatórios:**
	- `username`: Username do usuário
	- `senha_hash`: Senha do usuário
	
	**Response:**
	- `access_token`: Token JWT para usar nas requisições autenticadas
	- `refresh_token`: Token para renovar o access_token (válido por 7 dias)
	- `token_type`: Tipo do token (sempre "bearer")
	- Refresh token também será enviado em cookie HttpOnly
	"""
	# Procura usuário por username
	db_usuario = db.query(models.Usuario).filter(models.Usuario.username == credenciais.username).first()
	
	if not db_usuario:
		raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
	
	# Verifica a senha com bcrypt
	if not crud.verificar_senha(credenciais.senha_hash, db_usuario.senha_hash):
		raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
	
	# Cria tokens JWT
	access_token = criar_access_token(data={"id_usuario": db_usuario.id_usuario})
	refresh_token = criar_refresh_token(data={"id_usuario": db_usuario.id_usuario})
	
	# Setar refresh token em cookie HttpOnly
	response.set_cookie(
		key="refresh_token",
		value=refresh_token,
		httponly=True,
		secure=False,
		samesite="lax",
		max_age=7 * 24 * 60 * 60,
		path="/",
	)
	
	return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=schemas.Token, tags=["Autenticação"])
def refresh_token(
	request: schemas.RefreshTokenRequest,
	response: Response,
	db: Session = Depends(get_db),
):
	"""
	Renovar access_token usando refresh_token.
	
	**Body:**
	- `refresh_token`: Seu refresh_token obtido no login (ou use o cookie automaticamente)
	
	**Response:**
	- `access_token`: Novo token JWT válido por 30 minutos
	- `refresh_token`: Novo refresh_token válido por 7 dias
	- `token_type`: Tipo do token (sempre "bearer")
	- Novo refresh token também será enviado em cookie HttpOnly
	"""
	id_usuario = verificar_refresh_token(request.refresh_token)
	
	# Verifica se o usuário ainda existe
	db_usuario = crud.obter_usuario(db, id_usuario)
	if not db_usuario:
		raise HTTPException(status_code=401, detail="Usuário não encontrado")
	
	# Gera novos tokens
	access_token = criar_access_token(data={"id_usuario": id_usuario})
	new_refresh_token = criar_refresh_token(data={"id_usuario": id_usuario})
	
	# Atualizar cookie de refresh
	response.set_cookie(
		key="refresh_token",
		value=new_refresh_token,
		httponly=True,
		secure=False,
		samesite="lax",
		max_age=7 * 24 * 60 * 60,
		path="/",
	)
	
	return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post("/", response_model=schemas.GenericResponse[schemas.Usuario], status_code=201)
def criar_usuario(
	usuario: schemas.UsuarioCreate,
	db: Session = Depends(get_db),
):
	"""
	Criar novo usuário (aluno).
	
	**Campos Obrigatórios:**
	- `ra`: Registro Acadêmico (exatamente 13 dígitos)
	- `nome`: Nome do usuário (1-50 caracteres)
	- `email`: Email único (máx. 40 caracteres)
	- `username`: Username único (1-20 caracteres)
	- `nome_instituicao`: Nome da instituição (1-80 caracteres) - será criada automaticamente se não existir
	- `senha_hash`: Senha hash (mínimo 6 caracteres)
	
	**Campos Opcionais:**
	- `dt_nascimento`: Data de nascimento (formato: YYYY-MM-DD)
	- `tel_celular`: Telefone celular (formato internacional com '+' ou mínimo 10 dígitos, máx. 15 caracteres)
	- `id_curso`: ID do curso
	- `modulo`: Módulo (1-12, padrão: 1)
	- `bimestre`: Bimestre
	"""
	try:
		db_usuario = crud.criar_usuario(db, usuario)
		return schemas.GenericResponse(
			data=db_usuario,
			success=True,
			message="Usuário criado com sucesso",
		)
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=schemas.GenericResponse[schemas.Usuario], tags=["Autenticação"])
def obter_perfil_autenticado(
	usuario_autenticado: models.Usuario = Depends(verificar_token),
):
	"""
	Obter dados do usuário autenticado.
	
	**Requer token JWT no header:**
	```
	Authorization: Bearer <seu_token_jwt>
	```
	"""
	return schemas.GenericResponse(data=usuario_autenticado, success=True)


@router.get("/", response_model=schemas.GenericListResponse[schemas.Usuario])
def listar_usuarios(
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
	db: Session = Depends(get_db),
):
	"""
	Listar todos os usuários com paginação.
	"""
	usuarios = crud.obter_usuarios(db, skip, limit)
	total = db.query(models.Usuario).count()

	return schemas.GenericListResponse(
		data=usuarios,
		success=True,
		total=total,
		skip=skip,
		limit=limit,
	)


@router.get("/{id_usuario}", response_model=schemas.GenericResponse[schemas.Usuario])
def obter_usuario(
	id_usuario: int,
	db: Session = Depends(get_db),
):
	"""
	Obter usuário por ID.
	"""
	db_usuario = crud.obter_usuario(db, id_usuario)
	if not db_usuario:
		raise HTTPException(status_code=404, detail="Usuário não encontrado")

	return schemas.GenericResponse(data=db_usuario, success=True)


@router.get("/ra/{ra}", response_model=schemas.GenericResponse[schemas.Usuario])
def obter_usuario_por_ra(
	ra: str,
	db: Session = Depends(get_db),
):
	"""
	Obter usuário por RA.
	"""
	db_usuario = crud.obter_usuario_por_ra(db, ra)
	if not db_usuario:
		raise HTTPException(status_code=404, detail="Usuário não encontrado")

	return schemas.GenericResponse(data=db_usuario, success=True)


@router.get("/instituicao/{id_instituicao}", response_model=schemas.GenericListResponse[schemas.Usuario])
def listar_usuarios_por_instituicao(
	id_instituicao: int,
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
	db: Session = Depends(get_db),
):
	"""
	Listar usuários de uma instituição.
	"""
	usuarios = crud.obter_usuarios_por_instituicao(db, id_instituicao, skip, limit)
	total = db.query(models.Usuario).filter(models.Usuario.id_instituicao == id_instituicao).count()

	return schemas.GenericListResponse(
		data=usuarios,
		success=True,
		total=total,
		skip=skip,
		limit=limit,
	)


@router.get("/curso/{id_curso}", response_model=schemas.GenericListResponse[schemas.Usuario])
def listar_usuarios_por_curso(
	id_curso: int,
	skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
	limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
	db: Session = Depends(get_db),
):
	"""
	Listar usuários de um curso.
	"""
	usuarios = crud.obter_usuarios_por_curso(db, id_curso, skip, limit)
	total = db.query(models.Usuario).filter(models.Usuario.id_curso == id_curso).count()

	return schemas.GenericListResponse(
		data=usuarios,
		success=True,
		total=total,
		skip=skip,
		limit=limit,
	)


@router.put("/{id_usuario}", response_model=schemas.GenericResponse[schemas.Usuario])
def atualizar_usuario(
	id_usuario: int,
	usuario: schemas.UsuarioUpdate,
	db: Session = Depends(get_db),
):
	"""
	Atualizar usuário (apenas campos fornecidos no body).
	
	**Campos Atualizáveis:**
	- `nome`: Nome do usuário (1-50 caracteres)
	- `email`: Email único (máx. 40 caracteres)
	- `username`: Username único (1-20 caracteres)
	- `senha_hash`: Senha (será hasheada automaticamente)
	- `dt_nascimento`: Data de nascimento (formato: YYYY-MM-DD)
	- `tel_celular`: Telefone celular (formato internacional com '+' ou mínimo 10 dígitos)
	- `nome_curso`: Nome do curso (será criado automaticamente se não existir)
	- `modulo`: Módulo (1-12)
	- `bimestre`: Bimestre
	"""
	db_usuario = crud.obter_usuario(db, id_usuario)
	if not db_usuario:
		raise HTTPException(status_code=404, detail="Usuário não encontrado")

	try:
		db_atualizado = crud.atualizar_usuario(db, id_usuario, usuario)
		return schemas.GenericResponse(
			data=db_atualizado,
			success=True,
			message="Usuário atualizado com sucesso",
		)
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{id_usuario}", response_model=schemas.GenericResponse[schemas.Usuario])
def atualizar_usuario_parcial(
	id_usuario: int,
	usuario: schemas.UsuarioUpdate,
	db: Session = Depends(get_db),
):
	"""
	Atualizar usuário parcialmente (apenas campos fornecidos no body).
	
	**Campos Atualizáveis:**
	- `nome`: Nome do usuário (1-50 caracteres)
	- `email`: Email único (máx. 40 caracteres)
	- `username`: Username único (1-20 caracteres)
	- `senha_hash`: Senha (será hasheada automaticamente)
	- `dt_nascimento`: Data de nascimento (formato: YYYY-MM-DD)
	- `tel_celular`: Telefone celular (formato internacional com '+' ou mínimo 10 dígitos)
	- `nome_curso`: Nome do curso (será criado automaticamente se não existir)
	- `modulo`: Módulo (1-12)
	- `bimestre`: Bimestre
	"""
	db_usuario = crud.obter_usuario(db, id_usuario)
	if not db_usuario:
		raise HTTPException(status_code=404, detail="Usuário não encontrado")

	try:
		db_atualizado = crud.atualizar_usuario(db, id_usuario, usuario)
		return schemas.GenericResponse(
			data=db_atualizado,
			success=True,
			message="Usuário atualizado com sucesso",
		)
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_usuario}", response_model=schemas.GenericResponse[dict])
def deletar_usuario(
	id_usuario: int,
	db: Session = Depends(get_db),
):
	"""
	Deletar um usuário por ID.
	"""
	db_usuario = crud.obter_usuario(db, id_usuario)
	if not db_usuario:
		raise HTTPException(status_code=404, detail="Usuário não encontrado")

	if crud.deletar_usuario(db, id_usuario):
		return schemas.GenericResponse(
			data={"id_deletado": id_usuario},
			success=True,
			message="Usuário deletado com sucesso",
		)

	raise HTTPException(status_code=400, detail="Erro ao deletar usuário")

