from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verificar_token
from .. import models, schemas

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    tags=["Notas"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================


class NotaNaoEncontrada(HTTPException):
    """Nota não encontrada"""

    def __init__(self):
        super().__init__(status_code=404, detail="Nota não encontrada")


class ErroAoCriarNota(HTTPException):
    """Erro ao criar nota"""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarNota(HTTPException):
    """Erro ao atualizar nota"""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoDeletarNota(HTTPException):
    """Erro ao deletar nota"""

    def __init__(self):
        super().__init__(status_code=400, detail="Erro ao deletar nota")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================


def _validar_nota_existe(db: Session, id_nota: int) -> models.Nota:
    """Valida se nota existe. Retorna nota ou lança exceção."""
    nota = db.query(models.Nota).filter(models.Nota.id_nota == id_nota).first()
    if not nota:
        raise NotaNaoEncontrada()
    return nota


def _validar_nota_pertence_usuario(
    db: Session, id_nota: int, ra_usuario: str
) -> models.Nota:
    """Valida se nota existe e pertence ao usuário. Retorna nota ou lança exceção."""
    nota = _validar_nota_existe(db, id_nota)

    # Verificar se a nota pertence ao usuário autenticado (comparar por RA)
    if str(nota.ra) != str(ra_usuario):
        raise HTTPException(
            status_code=403, detail="Você não tem permissão para acessar esta nota"
        )

    return nota


def _aplicar_atualizacoes_parciais(
    nota: models.Nota, dados_atualizacao: schemas.NotaUpdate
) -> models.Nota:
    """Aplica atualizações parciais à nota com early returns."""
    update_data = dados_atualizacao.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        if valor is not None:
            setattr(nota, campo, valor)

    return nota


def _contar_notas(db: Session, query_filter=None) -> int:
    """Conta total de notas com filtro opcional."""
    query = db.query(models.Nota)
    if query_filter is not None:
        query = query.filter(query_filter)
    return query.count()


# ============================================================================
# ENDPOINTS - CREATE
# ============================================================================


@router.post("/", response_model=schemas.GenericResponse[schemas.Nota], status_code=201)
def criar_nota(
    nota: schemas.NotaCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Criar nova nota.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Body:**
    - `nota` (string): Valor da nota (obrigatório, 1-255 caracteres)
    - `bimestre` (int, opcional): Número do bimestre
    - `disciplina` (string, opcional): Nome da disciplina (máximo 100 caracteres)

    **Restrições:**
    - RA será associado automaticamente ao do usuário autenticado

    **Respostas:**
    - 201: Nota criada com sucesso
    - 400: Erro de validação
    - 401: Token ausente ou inválido
    """
    try:
        # Criar e persistir nota com RA do usuário autenticado
        nova_nota = models.Nota(
            ra=usuario_autenticado.ra,
            bimestre=nota.bimestre,
            nota=nota.nota,
            disciplina=nota.disciplina,
        )

        db.add(nova_nota)
        db.commit()
        db.refresh(nova_nota)

        return schemas.GenericResponse(
            data=nova_nota,
            success=True,
            message="Nota criada com sucesso",
        )
    except ErroAoCriarNota:
        raise
    except Exception as e:
        raise ErroAoCriarNota(str(e))


# ============================================================================
# ENDPOINTS - READ
# ============================================================================


@router.get("/", response_model=schemas.GenericListResponse[schemas.Nota])
def listar_todas_notas(
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar todas as notas do usuário autenticado com paginação.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

    **Respostas:**
    - 200: Lista de notas retornada com sucesso
    - 401: Token ausente ou inválido
    """
    notas = (
        db.query(models.Nota)
        .filter(models.Nota.ra == usuario_autenticado.ra)
        .offset(skip)
        .limit(limit)
        .all()
    )

    total = (
        db.query(models.Nota).filter(models.Nota.ra == usuario_autenticado.ra).count()
    )

    return schemas.GenericListResponse(
        data=notas,
        total=total,
        skip=skip,
        limit=limit,
        success=True,
        message="Notas retornadas com sucesso",
    )


@router.get("/{id_nota}", response_model=schemas.GenericResponse[schemas.Nota])
def obter_nota(
    id_nota: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Obter nota por ID.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_nota` (int): ID único da nota

    **Restrições:**
    - Nota deve pertencer ao usuário autenticado

    **Respostas:**
    - 200: Nota retornada com sucesso
    - 403: Usuário não tem permissão para acessar esta nota
    - 404: Nota não encontrada
    - 401: Token ausente ou inválido
    """
    nota = _validar_nota_pertence_usuario(db, id_nota, str(usuario_autenticado.ra))

    return schemas.GenericResponse(
        data=nota,
        success=True,
        message="Nota retornada com sucesso",
    )


@router.get("/ra/{ra}", response_model=schemas.GenericListResponse[schemas.Nota])
def listar_notas_por_ra(
    ra: str,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar notas de um aluno específico (por RA) com paginação.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `ra` (string): RA do aluno (exatamente 13 dígitos)

    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

    **Restrições:**
    - Usuário só pode listar notas de seu próprio RA

    **Respostas:**
    - 200: Lista de notas retornada com sucesso
    - 403: Usuário não tem permissão para acessar notas de outro RA
    - 401: Token ausente ou inválido
    """
    # Validar se o RA solicitado corresponde ao do usuário autenticado
    if ra != str(usuario_autenticado.ra):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para acessar notas de outro RA",
        )

    notas = (
        db.query(models.Nota)
        .filter(models.Nota.ra == ra)
        .offset(skip)
        .limit(limit)
        .all()
    )

    total = _contar_notas(db, models.Nota.ra == ra)

    return schemas.GenericListResponse(
        data=notas,
        total=total,
        skip=skip,
        limit=limit,
        success=True,
        message="Notas do aluno retornadas com sucesso",
    )


# ============================================================================
# ENDPOINTS - UPDATE
# ============================================================================


@router.put("/{id_nota}", response_model=schemas.GenericResponse[schemas.Nota])
def atualizar_nota(
    id_nota: int,
    nota_update: schemas.NotaUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar todos os campos de uma nota (PUT).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_nota` (int): ID único da nota a atualizar

    **Body (todos os campos opcionais):**
    - `bimestre` (int, opcional): Número do bimestre
    - `nota` (string, opcional): Valor da nota
    - `disciplina` (string, opcional): Nome da disciplina (máximo 100 caracteres)

    **Restrições:**
    - Nota deve existir e pertencer ao usuário autenticado

    **Respostas:**
    - 200: Nota atualizada com sucesso
    - 400: Erro de validação
    - 403: Usuário não tem permissão para atualizar esta nota
    - 404: Nota não encontrada
    - 401: Token ausente ou inválido
    """
    try:
        nota_existente = _validar_nota_pertence_usuario(
            db, id_nota, str(usuario_autenticado.ra)
        )

        # Aplicar atualizações
        nota_atualizada = _aplicar_atualizacoes_parciais(nota_existente, nota_update)

        db.commit()
        db.refresh(nota_atualizada)

        return schemas.GenericResponse(
            data=nota_atualizada,
            success=True,
            message="Nota atualizada com sucesso",
        )
    except (NotaNaoEncontrada, ErroAoAtualizarNota):
        raise
    except Exception as e:
        raise ErroAoAtualizarNota(str(e))


@router.patch("/{id_nota}", response_model=schemas.GenericResponse[schemas.Nota])
def atualizar_parcial_nota(
    id_nota: int,
    nota_update: schemas.NotaUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar parcialmente uma nota (PATCH).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_nota` (int): ID único da nota a atualizar

    **Body (todos os campos opcionais):**
    - `bimestre` (int, opcional): Número do bimestre
    - `nota` (string, opcional): Valor da nota
    - `disciplina` (string, opcional): Nome da disciplina (máximo 100 caracteres)

    **Restrições:**
    - Nota deve existir e pertença ao usuário autenticado
    - Apenas campos fornecidos serão atualizados

    **Respostas:**
    - 200: Nota atualizada com sucesso
    - 400: Erro de validação ou nenhum dado fornecido
    - 403: Usuário não tem permissão para atualizar esta nota
    - 404: Nota não encontrada
    - 401: Token ausente ou inválido
    """
    try:
        nota_existente = _validar_nota_pertence_usuario(
            db, id_nota, str(usuario_autenticado.ra)
        )

        # Verificar se há dados para atualizar
        update_data = nota_update.model_dump(exclude_unset=True)
        if not update_data:
            raise ErroAoAtualizarNota("Nenhum dado fornecido para atualização")

        # Aplicar atualizações
        nota_atualizada = _aplicar_atualizacoes_parciais(nota_existente, nota_update)

        db.commit()
        db.refresh(nota_atualizada)

        return schemas.GenericResponse(
            data=nota_atualizada,
            success=True,
            message="Nota atualizada parcialmente com sucesso",
        )
    except (NotaNaoEncontrada, ErroAoAtualizarNota):
        raise
    except Exception as e:
        raise ErroAoAtualizarNota(str(e))


# ============================================================================
# ENDPOINTS - DELETE
# ============================================================================


@router.delete("/{id_nota}", response_model=schemas.GenericResponse[dict])
def deletar_nota(
    id_nota: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Deletar uma nota existente.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_nota` (int): ID único da nota a deletar

    **Restrições:**
    - Nota deve existir e pertencer ao usuário autenticado
    - Ação irreversível

    **Respostas:**
    - 200: Nota deletada com sucesso
    - 400: Erro ao deletar nota
    - 403: Usuário não tem permissão para deletar esta nota
    - 404: Nota não encontrada
    - 401: Token ausente ou inválido
    """
    nota_existente = _validar_nota_pertence_usuario(
        db, id_nota, str(usuario_autenticado.ra)
    )

    try:
        db.delete(nota_existente)
        db.commit()

        return schemas.GenericResponse(
            data={"id_deletado": id_nota},
            success=True,
            message="Nota deletada com sucesso",
        )
    except Exception:
        raise ErroAoDeletarNota()
