from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, models, schemas
from ..auth import (
    criar_access_token,
    criar_refresh_token,
    verificar_token,
    verificar_refresh_token,
)

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    tags=["Usuário"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================


class UsuarioNaoEncontrado(HTTPException):
    """Usuário não encontrado"""

    def __init__(self):
        super().__init__(status_code=404, detail="Usuário não encontrado")


class CredenciaisInvalidas(HTTPException):
    """Credenciais de login inválidas"""

    def __init__(self):
        super().__init__(status_code=401, detail="Usuário ou senha inválidos")


class ErroAoCriarUsuario(HTTPException):
    """Erro ao criar usuário (ex: email/username duplicado)"""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoAtualizar(HTTPException):
    """Erro ao atualizar usuário"""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoDeletar(HTTPException):
    """Erro ao deletar usuário"""

    def __init__(self):
        super().__init__(status_code=400, detail="Erro ao deletar usuário")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================


def _anexar_nomes_usuario(usuario: models.Usuario) -> models.Usuario:
    """Anexa nomes de instituição e curso ao objeto usuário."""
    try:
        usuario.nome_instituicao = (
            usuario.instituicao.nome if usuario.instituicao else None
        )
        usuario.nome_curso = usuario.curso.nome if usuario.curso else None
    except Exception:
        usuario.nome_instituicao = None
        usuario.nome_curso = None
    return usuario


def _anexar_nomes_usuarios_lista(usuarios: list) -> list:
    """Anexa nomes a uma lista de usuários."""
    return [_anexar_nomes_usuario(u) for u in usuarios]


def _validar_usuario_existe(db: Session, id_usuario: int) -> models.Usuario:
    """Valida se usuário existe. Retorna usuário ou lança exceção."""
    usuario = crud.obter_usuario(db, id_usuario)
    if not usuario:
        raise UsuarioNaoEncontrado()
    return usuario


def _validar_credenciais(db: Session, username: str, senha: str) -> models.Usuario:
    """Valida credenciais de login. Retorna usuário ou lança exceção."""
    usuario = (
        db.query(models.Usuario).filter(models.Usuario.username == username).first()
    )

    if not usuario or not crud.verificar_senha(
        senha, str(usuario.senha_hash) if usuario else ""
    ):
        raise CredenciaisInvalidas()

    return usuario


# ============================================================================
# ENDPOINTS - AUTENTICAÇÃO
# ============================================================================


@router.post("/login", response_model=schemas.Token)
def login(
    credenciais: schemas.Login,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Realizar login e obter token JWT.

    **Body:**
    - `username` (string): Username do usuário
    - `senha_hash` (string): Senha do usuário (mínimo 6 caracteres)

    **Cookies Definidos:**
    - `refresh_token` (HttpOnly): Token para renovar access_token (válido por 7 dias)

    **Response Body:**
    - `access_token` (string): Token JWT para usar em requisições autenticadas (válido por 30 minutos)
    - `token_type` (string): Tipo do token (sempre "bearer")

    **Respostas:**
    - 200: Login bem-sucedido, access_token retornado no body
    - 401: Username ou senha inválidos
    """
    # Validação de credenciais
    usuario = _validar_credenciais(db, credenciais.username, credenciais.senha_hash)

    # Criar tokens
    access_token = criar_access_token(data={"id_usuario": usuario.id_usuario})
    refresh_token = criar_refresh_token(data={"id_usuario": usuario.id_usuario})

    # Setar refresh token em cookie HttpOnly
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    request: schemas.RefreshTokenRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Renovar access_token usando refresh_token.

    **Autenticação:**
    - Requer refresh_token no body OU no cookie HttpOnly

    **Body:**
    - `refresh_token` (string): Seu refresh_token obtido no login

    **Cookies Definidos:**
    - `refresh_token` (HttpOnly): Novo token válido por 7 dias

    **Response Body:**
    - `access_token` (string): Novo token JWT válido por 30 minutos
    - `token_type` (string): Tipo do token (sempre "bearer")

    **Respostas:**
    - 200: Token renovado com sucesso
    - 401: Refresh token inválido ou usuário não encontrado
    """
    # Validar refresh token
    id_usuario = verificar_refresh_token(request.refresh_token)

    # Verificar se usuário ainda existe
    usuario = _validar_usuario_existe(db, id_usuario)

    # Gerar novos tokens
    access_token = criar_access_token(data={"id_usuario": usuario.id_usuario})
    novo_refresh_token = criar_refresh_token(data={"id_usuario": usuario.id_usuario})

    # Atualizar cookie
    response.set_cookie(
        key="refresh_token",
        value=novo_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================================
# ENDPOINTS - CREATE
# ============================================================================


@router.post(
    "/", response_model=schemas.GenericResponse[schemas.Usuario], status_code=201
)
def criar_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
):
    """
    Criar novo usuário (aluno).

    **Body:**
    - `ra` (string): Registro Acadêmico - exatamente 13 dígitos
    - `nome` (string): Nome do usuário (1-50 caracteres)
    - `email` (string): Email único (máx. 40 caracteres)
    - `username` (string): Username único (1-20 caracteres)
    - `nome_instituicao` (string): Nome da instituição (1-80 caracteres) - será criada automaticamente se não existir
    - `senha_hash` (string): Senha (mínimo 6 caracteres) - será criptografada automaticamente
    - `dt_nascimento` (date, opcional): Data de nascimento no formato YYYY-MM-DD
    - `tel_celular` (string, opcional): Telefone celular (formato internacional com '+' ou mínimo 10 dígitos, máx. 15)
    - `id_curso` (int, opcional): ID do curso
    - `modulo` (int, opcional): Módulo (1-12, padrão: 1)
    - `bimestre` (int, opcional): Bimestre

    **Restrições:**
    - RA, email e username devem ser únicos
    - Email e RA já registrados resultam em erro 400

    **Respostas:**
    - 201: Usuário criado com sucesso
    - 400: Erro de validação ou duplicação
    """
    try:
        usuario_criado = crud.criar_usuario(db, usuario)
        _anexar_nomes_usuario(usuario_criado)
        return schemas.GenericResponse(
            data=usuario_criado,
            success=True,
            message="Usuário criado com sucesso",
        )
    except Exception as e:
        raise ErroAoCriarUsuario(str(e))


# ============================================================================
# ENDPOINTS - READ
# ============================================================================


@router.get("/me", response_model=schemas.GenericResponse[schemas.Usuario])
def obter_perfil_autenticado(
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Obter dados do perfil do usuário autenticado.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Respostas:**
    - 200: Dados do perfil retornados com sucesso
    - 404: Usuário não encontrado
    - 401: Token ausente ou inválido
    """
    id_usuario = (
        usuario_autenticado.id_usuario
        if hasattr(usuario_autenticado, "id_usuario")
        else usuario_autenticado
    )
    usuario = _validar_usuario_existe(db, id_usuario)
    _anexar_nomes_usuario(usuario)
    return schemas.GenericResponse(data=usuario, success=True)


@router.get("/", response_model=schemas.GenericListResponse[schemas.Usuario])
def listar_usuarios(
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar todos os usuários com paginação.

    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

    **Respostas:**
    - 200: Lista de usuários retornada com sucesso
    """
    usuarios = crud.obter_usuarios(db, skip, limit)
    usuarios = _anexar_nomes_usuarios_lista(usuarios)
    total = db.query(models.Usuario).count()

    return schemas.GenericListResponse(
        data=usuarios,
        success=True,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{id_usuario}", response_model=schemas.GenericResponse[schemas.Usuario])
def obter_usuario_por_id(
    id_usuario: int,
    db: Session = Depends(get_db),
):
    """
    Obter usuário por ID.

    **Path Parameters:**
    - `id_usuario` (int): ID único do usuário

    **Respostas:**
    - 200: Usuário retornado com sucesso
    - 404: Usuário não encontrado
    """
    usuario = _validar_usuario_existe(db, id_usuario)
    _anexar_nomes_usuario(usuario)
    return schemas.GenericResponse(data=usuario, success=True)


@router.get("/ra/{ra}", response_model=schemas.GenericResponse[schemas.Usuario])
def obter_usuario_por_ra(
    ra: str,
    db: Session = Depends(get_db),
):
    """
    Obter usuário por RA (Registro Acadêmico).

    **Path Parameters:**
    - `ra` (string): RA do usuário (exatamente 13 dígitos)

    **Respostas:**
    - 200: Usuário retornado com sucesso
    - 404: Usuário não encontrado
    """
    usuario = crud.obter_usuario_por_ra(db, ra)
    if not usuario:
        raise UsuarioNaoEncontrado()
    _anexar_nomes_usuario(usuario)
    return schemas.GenericResponse(data=usuario, success=True)


@router.get(
    "/instituicao/{id_instituicao}",
    response_model=schemas.GenericListResponse[schemas.Usuario],
)
def listar_usuarios_por_instituicao(
    id_instituicao: int,
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar usuários de uma instituição específica com paginação.

    **Path Parameters:**
    - `id_instituicao` (int): ID único da instituição

    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

    **Respostas:**
    - 200: Lista de usuários retornada com sucesso
    """
    usuarios = crud.obter_usuarios_por_instituicao(db, id_instituicao, skip, limit)
    usuarios = _anexar_nomes_usuarios_lista(usuarios)
    total = (
        db.query(models.Usuario)
        .filter(models.Usuario.id_instituicao == id_instituicao)
        .count()
    )

    return schemas.GenericListResponse(
        data=usuarios,
        success=True,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/curso/{id_curso}", response_model=schemas.GenericListResponse[schemas.Usuario]
)
def listar_usuarios_por_curso(
    id_curso: int,
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar usuários de um curso específico com paginação.

    **Path Parameters:**
    - `id_curso` (int): ID único do curso

    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

    **Respostas:**
    - 200: Lista de usuários retornada com sucesso
    """
    usuarios = crud.obter_usuarios_por_curso(db, id_curso, skip, limit)
    usuarios = _anexar_nomes_usuarios_lista(usuarios)
    total = db.query(models.Usuario).filter(models.Usuario.id_curso == id_curso).count()

    return schemas.GenericListResponse(
        data=usuarios,
        success=True,
        total=total,
        skip=skip,
        limit=limit,
    )


# ============================================================================
# ENDPOINTS - UPDATE
# ============================================================================


@router.put("/", response_model=schemas.GenericResponse[schemas.Usuario])
def atualizar_usuario(
    usuario: schemas.UsuarioUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar todos os campos do perfil do usuário autenticado (PUT).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Body:**
    - `nome` (string): Nome do usuário (1-50 caracteres)
    - `email` (string): Email único (máx. 40 caracteres)
    - `username` (string): Username único (1-20 caracteres)
    - `senha_hash` (string): Senha (mínimo 6 caracteres) - será criptografada automaticamente
    - `dt_nascimento` (date, opcional): Data de nascimento no formato YYYY-MM-DD
    - `tel_celular` (string, opcional): Telefone (formato internacional com '+' ou mínimo 10 dígitos)
    - `nome_curso` (string, opcional): Nome do curso - será criado automaticamente se não existir
    - `modulo` (int, opcional): Módulo (1-12)
    - `bimestre` (int, opcional): Bimestre

    **Restrições:**
    - Usuário só pode atualizar seu próprio perfil
    - Todos os campos são opcionais (use PUT ou PATCH indistintamente)

    **Respostas:**
    - 200: Usuário atualizado com sucesso
    - 400: Erro de validação
    - 401: Token ausente ou inválido
    """
    try:
        id_usuario = (
            usuario_autenticado.id_usuario
            if hasattr(usuario_autenticado, "id_usuario")
            else usuario_autenticado
        )
        usuario_atualizado = crud.atualizar_usuario(db, id_usuario, usuario)
        if usuario_atualizado:
            _anexar_nomes_usuario(usuario_atualizado)
        return schemas.GenericResponse(
            data=usuario_atualizado,
            success=True,
            message="Usuário atualizado com sucesso",
        )
    except Exception as e:
        raise ErroAoAtualizar(str(e))


@router.patch("/", response_model=schemas.GenericResponse[schemas.Usuario])
def atualizar_usuario_parcial(
    usuario: schemas.UsuarioUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar parcialmente o perfil do usuário autenticado (PATCH).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Body (todos os campos opcionais):**
    - `nome` (string, opcional): Nome do usuário (1-50 caracteres)
    - `email` (string, opcional): Email único (máx. 40 caracteres)
    - `username` (string, opcional): Username único (1-20 caracteres)
    - `senha_hash` (string, opcional): Senha (mínimo 6 caracteres) - será criptografada automaticamente
    - `dt_nascimento` (date, opcional): Data de nascimento no formato YYYY-MM-DD
    - `tel_celular` (string, opcional): Telefone (formato internacional com '+' ou mínimo 10 dígitos)
    - `nome_curso` (string, opcional): Nome do curso - será criado automaticamente se não existir
    - `modulo` (int, opcional): Módulo (1-12)
    - `bimestre` (int, opcional): Bimestre

    **Restrições:**
    - Usuário só pode atualizar seu próprio perfil
    - Apenas campos fornecidos serão atualizados

    **Respostas:**
    - 200: Usuário atualizado com sucesso
    - 400: Erro de validação
    - 401: Token ausente ou inválido
    """
    try:
        id_usuario = (
            usuario_autenticado.id_usuario
            if hasattr(usuario_autenticado, "id_usuario")
            else usuario_autenticado
        )
        usuario_atualizado = crud.atualizar_usuario(db, id_usuario, usuario)
        if usuario_atualizado:
            _anexar_nomes_usuario(usuario_atualizado)
        return schemas.GenericResponse(
            data=usuario_atualizado,
            success=True,
            message="Usuário atualizado com sucesso",
        )
    except Exception as e:
        raise ErroAoAtualizar(str(e))


# ============================================================================
# ENDPOINTS - DELETE
# ============================================================================


@router.delete("/", response_model=schemas.GenericResponse[dict])
def deletar_usuario(
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Deletar a conta do usuário autenticado.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Restrições:**
    - Usuário só pode deletar sua própria conta
    - Ação irreversível

    **Respostas:**
    - 200: Usuário deletado com sucesso
    - 400: Erro ao deletar usuário
    - 401: Token ausente ou inválido
    """
    id_usuario = (
        usuario_autenticado.id_usuario
        if hasattr(usuario_autenticado, "id_usuario")
        else usuario_autenticado
    )
    if crud.deletar_usuario(db, id_usuario):
        return schemas.GenericResponse(
            data={"id_deletado": id_usuario},
            success=True,
            message="Usuário deletado com sucesso",
        )

    raise ErroAoDeletar()
