from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, models, schemas
from ..auth import verificar_token

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
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
        super().__init__(
            status_code=400, detail="Email já cadastrado para outro discente"
        )


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
        super().__init__(
            status_code=403, detail="Você não tem permissão para acessar este discente"
        )


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
    db: Session, id_discente: int, ra_usuario: str
) -> models.Discente:
    """Valida se discente existe e pertence ao usuário. Retorna discente ou lança exceção."""
    discente = _validar_discente_existe(db, id_discente)

    # Verificar se o discente pertence ao usuário autenticado (comparar por RA)
    try:
        ra_discente = str(discente.ra) if hasattr(discente, "ra") else None
        if ra_discente and ra_discente != ra_usuario:
            raise PermissaoNegada()
    except (ValueError, TypeError, AttributeError):
        # Se não conseguir comparar, verifica se tem ra
        if hasattr(discente, "ra") and discente.ra is not None:
            raise PermissaoNegada()

    return discente


def _validar_email_unico(
    db: Session, email: str, id_discente_atual: int | None = None
) -> None:
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


@router.post(
    "/", response_model=schemas.GenericResponse[schemas.Discente], status_code=201
)
def criar_discente(
    discente: schemas.DiscenteCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
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
        ra_usuario = (
            usuario_autenticado.ra
            if hasattr(usuario_autenticado, "ra")
            else usuario_autenticado
        )

        # Criar discente diretamente com RA no banco de dados
        db_discente = models.Discente(
            nome=discente.nome,
            email=discente.email,
            tel_celular=discente.tel_celular,
            id_curso=discente.id_curso,
            ra=ra_usuario,
        )
        db.add(db_discente)
        db.commit()
        db.refresh(db_discente)

        return schemas.GenericResponse(
            data=db_discente, success=True, message="Discente criado com sucesso"
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
    db: Session = Depends(get_db),
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
    ra_usuario = (
        usuario_autenticado.ra
        if hasattr(usuario_autenticado, "ra")
        else usuario_autenticado
    )

    # Listar apenas discentes do usuário autenticado
    discentes = (
        db.query(models.Discente)
        .filter(models.Discente.ra == ra_usuario)
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(models.Discente).filter(models.Discente.ra == ra_usuario).count()

    return schemas.GenericListResponse(
        data=discentes, total=total, skip=skip, limit=limit, success=True
    )


@router.get("/{id_discente}", response_model=schemas.GenericResponse[schemas.Discente])
def obter_discente(
    id_discente: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
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
    ra_usuario = (
        usuario_autenticado.ra
        if hasattr(usuario_autenticado, "ra")
        else usuario_autenticado
    )
    discente = _validar_discente_pertence_usuario(db, id_discente, ra_usuario)
    return schemas.GenericResponse(data=discente, success=True)


@router.get("/email/{email}", response_model=schemas.GenericResponse[schemas.Discente])
def obter_discente_por_email(
    email: str,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
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
    ra_usuario = (
        usuario_autenticado.ra
        if hasattr(usuario_autenticado, "ra")
        else usuario_autenticado
    )
    discente = crud.obter_discente_por_email(db, email)

    if not discente:
        raise DiscenteNaoEncontrado()

    # Verificar se pertence ao usuário (comparar por RA)
    try:
        ra_discente = str(discente.ra) if hasattr(discente, "ra") else None
        if ra_discente and ra_discente != ra_usuario:
            raise PermissaoNegada()
    except (ValueError, TypeError, AttributeError):
        if hasattr(discente, "ra") and discente.ra is not None:
            raise PermissaoNegada()

    return schemas.GenericResponse(data=discente, success=True)


@router.put("/{id_discente}", response_model=schemas.GenericResponse[schemas.Discente])
def atualizar_discente_completo(
    id_discente: int,
    discente: schemas.DiscenteCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar completamente um discente (PUT).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_discente` (int): ID único do discente a atualizar

    **Body:**
    - `nome` (string): Nome do discente (1-50 caracteres)
    - `email` (string): Email do discente (deve ser único)
    - `tel_celular` (string, opcional): Telefone (máx. 15 caracteres)
    - `id_curso` (int, opcional): ID do curso

    **Restrições:**
    - Discente deve existir e pertencer ao usuário autenticado
    - Email deve ser único (exceto o email atual do discente)
    - Todos os campos obrigatórios são necessários

    **Respostas:**
    - 200: Discente atualizado com sucesso
    - 400: Erro de validação ou email duplicado
    - 403: Usuário não tem permissão para atualizar este discente
    - 404: Discente não encontrado
    - 401: Token ausente ou inválido
    """
    try:
        ra_usuario = (
            usuario_autenticado.ra
            if hasattr(usuario_autenticado, "ra")
            else usuario_autenticado
        )
        _validar_discente_pertence_usuario(db, id_discente, ra_usuario)
        _validar_email_unico(db, discente.email, id_discente)

        db_atualizado = crud.atualizar_discente(db, id_discente, discente)
        return schemas.GenericResponse(
            data=db_atualizado, success=True, message="Discente atualizado com sucesso"
        )
    except (DiscenteNaoEncontrado, EmailDuplicado, PermissaoNegada):
        raise
    except Exception as e:
        raise ErroAoAtualizarDiscente(str(e))


@router.patch(
    "/{id_discente}", response_model=schemas.GenericResponse[schemas.Discente]
)
def atualizar_discente_parcial(
    id_discente: int,
    discente_update: schemas.DiscenteUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar parcialmente um discente (PATCH).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_discente` (int): ID único do discente a atualizar

    **Body (todos os campos opcionais):**
    - `nome` (string, opcional): Nome do discente (1-50 caracteres)
    - `email` (string, opcional): Email do discente (deve ser único)
    - `tel_celular` (string, opcional): Telefone (máx. 15 caracteres)
    - `id_curso` (int, opcional): ID do curso

    **Restrições:**
    - Discente deve existir e pertencer ao usuário autenticado
    - Email deve ser único (exceto o email atual do discente)
    - Apenas campos fornecidos serão atualizados

    **Respostas:**
    - 200: Discente atualizado com sucesso
    - 400: Erro de validação, email duplicado ou nenhum dado fornecido
    - 403: Usuário não tem permissão para atualizar este discente
    - 404: Discente não encontrado
    - 401: Token ausente ou inválido
    """
    try:
        ra_usuario = (
            usuario_autenticado.ra
            if hasattr(usuario_autenticado, "ra")
            else usuario_autenticado
        )
        discente_existente = _validar_discente_pertence_usuario(
            db, id_discente, ra_usuario
        )

        # Verificar se há dados para atualizar
        update_data = discente_update.model_dump(exclude_unset=True)
        if not update_data:
            raise ErroAoAtualizarDiscente("Nenhum dado fornecido para atualização")

        # Validar email se fornecido
        if "email" in update_data:
            _validar_email_unico(db, update_data["email"], id_discente)

        # Preparar dados completos para atualização
        dados_atuais = {
            "nome": str(discente_existente.nome),
            "email": str(discente_existente.email),
            "tel_celular": discente_existente.tel_celular,
            "id_curso": discente_existente.id_curso,
        }
        dados_atuais.update(update_data)

        discente_completo = schemas.DiscenteCreate(**dados_atuais)
        db_atualizado = crud.atualizar_discente(db, id_discente, discente_completo)

        return schemas.GenericResponse(
            data=db_atualizado,
            success=True,
            message="Discente atualizado parcialmente com sucesso",
        )
    except (
        DiscenteNaoEncontrado,
        EmailDuplicado,
        ErroAoAtualizarDiscente,
        PermissaoNegada,
    ):
        raise
    except Exception as e:
        raise ErroAoAtualizarDiscente(str(e))


@router.delete("/{id_discente}", response_model=schemas.GenericResponse[dict])
def deletar_discente(
    id_discente: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Deletar um discente existente.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_discente` (int): ID único do discente a deletar

    **Restrições:**
    - Usuário só pode deletar seus próprios discentes

    **Respostas:**
    - 200: Discente deletado com sucesso
    - 400: Erro ao deletar discente
    - 403: Usuário não tem permissão para deletar este discente
    - 404: Discente não encontrado
    - 401: Token ausente ou inválido
    """
    ra_usuario = (
        usuario_autenticado.ra
        if hasattr(usuario_autenticado, "ra")
        else usuario_autenticado
    )
    _validar_discente_pertence_usuario(db, id_discente, ra_usuario)

    if crud.deletar_discente(db, id_discente):
        return schemas.GenericResponse(
            data={"id_deletado": id_discente},
            success=True,
            message="Discente deletado com sucesso",
        )

    raise ErroAoDeletarDiscente()
