from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verificar_token
from .. import models, schemas

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    tags=["Horários"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================


class HorarioNaoEncontrado(HTTPException):
    """Horário não encontrado"""

    def __init__(self):
        super().__init__(status_code=404, detail="Horário não encontrado")


class ErroAoCriarHorario(HTTPException):
    """Erro ao criar horário"""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarHorario(HTTPException):
    """Erro ao atualizar horário"""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoDeletarHorario(HTTPException):
    """Erro ao deletar horário"""

    def __init__(self):
        super().__init__(status_code=400, detail="Erro ao deletar horário")


class PermissaoNegada(HTTPException):
    """Usuário não tem permissão para acessar este horário"""

    def __init__(self):
        super().__init__(
            status_code=403, detail="Você não tem permissão para acessar este horário"
        )


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================


def _validar_horario_existe(db: Session, id_horario: int) -> models.Horario:
    """Valida se horário existe. Retorna horário ou lança exceção."""
    horario = (
        db.query(models.Horario).filter(models.Horario.id_horario == id_horario).first()
    )
    if not horario:
        raise HorarioNaoEncontrado()
    return horario


def _validar_horario_pertence_usuario(
    db: Session, id_horario: int, ra_usuario: str
) -> models.Horario:
    """Valida se horário existe e pertence ao usuário. Retorna horário ou lança exceção."""
    horario = _validar_horario_existe(db, id_horario)

    # Verificar se o horário pertence ao usuário autenticado (comparar por RA)
    if str(horario.ra) != str(ra_usuario):
        raise PermissaoNegada()

    return horario


def _validar_numero_aula(numero_aula: int) -> int:
    """Valida se número da aula está no intervalo permitido (1-4). Early return."""
    if numero_aula is None:
        return None
    if not isinstance(numero_aula, int) or numero_aula < 1 or numero_aula > 4:
        raise ErroAoCriarHorario("Número da aula deve estar entre 1 e 4")
    return numero_aula


def _validar_dia_semana(dia_semana: int) -> int:
    """Valida se dia da semana está no intervalo permitido (1-6). Early return."""
    if dia_semana is None:
        raise ErroAoCriarHorario("Dia da semana é obrigatório")
    if not isinstance(dia_semana, int) or dia_semana < 1 or dia_semana > 6:
        raise ErroAoCriarHorario(
            "Dia da semana deve estar entre 1 (Segunda) e 6 (Sábado)"
        )
    return dia_semana


def _aplicar_atualizacoes_parciais(
    horario: models.Horario, dados_atualizacao: schemas.HorarioUpdate
) -> models.Horario:
    """Aplica atualizações parciais ao horário com early returns."""
    update_data = dados_atualizacao.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        if valor is not None:
            if campo == "numero_aula":
                valor = _validar_numero_aula(valor)
            elif campo == "dia_semana":
                valor = _validar_dia_semana(valor)
            setattr(horario, campo, valor)

    return horario


# ============================================================================
# ENDPOINTS - CREATE
# ============================================================================


@router.post(
    "/", response_model=schemas.GenericResponse[schemas.Horario], status_code=201
)
def criar_horario(
    horario: schemas.HorarioCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Criar novo horário.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Body:**
    - `dia_semana` (int): Dia da semana (1=Segunda, 2=Terça, 3=Quarta, 4=Quinta, 5=Sexta, 6=Sábado)
    - `numero_aula` (int, opcional): Número da aula (1=Primeira, 2=Segunda, 3=Terceira, 4=Quarta)
    - `disciplina` (string, opcional): Disciplina/Matéria neste horário (máximo 100 caracteres)

    **Restrições:**
    - RA será associado automaticamente ao do usuário autenticado
    - dia_semana deve ser um valor válido (1-6)
    - numero_aula deve ser um valor válido (1-4) se fornecido

    **Respostas:**
    - 201: Horário criado com sucesso
    - 400: Erro de validação
    - 401: Token ausente ou inválido
    """
    try:
        # Validações explícitas com early returns
        _validar_dia_semana(horario.dia_semana)
        if horario.numero_aula is not None:
            _validar_numero_aula(horario.numero_aula)

        # Criar e persistir horário com RA do usuário autenticado
        novo_horario = models.Horario(
            ra=usuario_autenticado.ra,
            dia_semana=horario.dia_semana,
            numero_aula=horario.numero_aula,
            disciplina=horario.disciplina,
        )

        db.add(novo_horario)
        db.commit()
        db.refresh(novo_horario)

        return schemas.GenericResponse(
            data=novo_horario,
            success=True,
            message="Horário criado com sucesso",
        )
    except ErroAoCriarHorario:
        raise
    except Exception as e:
        raise ErroAoCriarHorario(str(e))


# ============================================================================
# ENDPOINTS - READ
# ============================================================================


@router.get("/", response_model=schemas.GenericListResponse[schemas.Horario])
def listar_todos_horarios(
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar todos os horários do usuário autenticado com paginação.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

    **Respostas:**
    - 200: Lista de horários retornada com sucesso
    - 401: Token ausente ou inválido
    """
    horarios = (
        db.query(models.Horario)
        .filter(models.Horario.ra == usuario_autenticado.ra)
        .offset(skip)
        .limit(limit)
        .all()
    )

    total = (
        db.query(models.Horario)
        .filter(models.Horario.ra == usuario_autenticado.ra)
        .count()
    )

    return schemas.GenericListResponse(
        data=horarios,
        total=total,
        skip=skip,
        limit=limit,
        success=True,
        message="Horários retornados com sucesso",
    )


@router.get("/{id_horario}", response_model=schemas.GenericResponse[schemas.Horario])
def obter_horario(
    id_horario: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Obter horário por ID.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_horario` (int): ID único do horário

    **Restrições:**
    - Horário deve pertencer ao usuário autenticado

    **Respostas:**
    - 200: Horário retornado com sucesso
    - 403: Usuário não tem permissão para acessar este horário
    - 404: Horário não encontrado
    - 401: Token ausente ou inválido
    """
    horario = _validar_horario_pertence_usuario(
        db, id_horario, str(usuario_autenticado.ra)
    )

    return schemas.GenericResponse(
        data=horario,
        success=True,
        message="Horário retornado com sucesso",
    )


@router.get(
    "/dia/{dia_semana}", response_model=schemas.GenericListResponse[schemas.Horario]
)
def listar_horarios_por_dia(
    dia_semana: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar horários de um dia específico com paginação.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `dia_semana` (int): Dia da semana (1=Segunda, 2=Terça, 3=Quarta, 4=Quinta, 5=Sexta, 6=Sábado)

    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000

    **Restrições:**
    - Usuário só pode listar seus próprios horários

    **Respostas:**
    - 200: Lista de horários retornada com sucesso
    - 401: Token ausente ou inválido
    """
    horarios = (
        db.query(models.Horario)
        .filter(
            models.Horario.ra == usuario_autenticado.ra,
            models.Horario.dia_semana == dia_semana,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    total = (
        db.query(models.Horario)
        .filter(
            models.Horario.ra == usuario_autenticado.ra,
            models.Horario.dia_semana == dia_semana,
        )
        .count()
    )

    return schemas.GenericListResponse(
        data=horarios,
        total=total,
        skip=skip,
        limit=limit,
        success=True,
        message="Horários retornados com sucesso",
    )


# ============================================================================
# ENDPOINTS - UPDATE
# ============================================================================


@router.put("/{id_horario}", response_model=schemas.GenericResponse[schemas.Horario])
def atualizar_horario(
    id_horario: int,
    horario_update: schemas.HorarioUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar completamente um horário (PUT).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_horario` (int): ID único do horário a atualizar

    **Body (todos os campos opcionais):**
    - `dia_semana` (int, opcional): Dia da semana (1-6)
    - `numero_aula` (int, opcional): Número da aula (1-4)
    - `disciplina` (string, opcional): Disciplina/Matéria neste horário (máximo 100 caracteres)

    **Respostas:**
    - 200: Horário atualizado com sucesso
    - 400: Erro de validação ou nenhum dado fornecido
    - 403: Usuário não tem permissão para atualizar este horário
    - 404: Horário não encontrado
    - 401: Token ausente ou inválido
    """
    try:
        horario_existente = _validar_horario_pertence_usuario(
            db, id_horario, str(usuario_autenticado.ra)
        )

        # Verificar se há dados para atualizar
        update_data = horario_update.model_dump(exclude_unset=True)
        if not update_data:
            raise ErroAoAtualizarHorario("Nenhum dado fornecido para atualização")

        # Aplicar atualizações
        horario_atualizado = _aplicar_atualizacoes_parciais(
            horario_existente, horario_update
        )

        db.commit()
        db.refresh(horario_atualizado)

        return schemas.GenericResponse(
            data=horario_atualizado,
            success=True,
            message="Horário atualizado com sucesso",
        )
    except (HorarioNaoEncontrado, ErroAoAtualizarHorario, PermissaoNegada):
        raise
    except Exception as e:
        raise ErroAoAtualizarHorario(str(e))


@router.patch("/{id_horario}", response_model=schemas.GenericResponse[schemas.Horario])
def atualizar_parcial_horario(
    id_horario: int,
    horario_update: schemas.HorarioUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar parcialmente um horário (PATCH).

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_horario` (int): ID único do horário a atualizar

    **Body (todos os campos opcionais):**
    - `dia_semana` (int, opcional): Dia da semana (1-6)
    - `numero_aula` (int, opcional): Número da aula (1-4)
    - `disciplina` (string, opcional): Disciplina/Matéria neste horário (máximo 100 caracteres)

    **Restrições:**
    - Horário deve existir e pertencer ao usuário autenticado
    - Apenas campos fornecidos serão atualizados

    **Respostas:**
    - 200: Horário atualizado com sucesso
    - 400: Erro de validação
    - 403: Usuário não tem permissão para atualizar este horário
    - 404: Horário não encontrado
    - 401: Token ausente ou inválido
    """
    try:
        horario_existente = _validar_horario_pertence_usuario(
            db, id_horario, str(usuario_autenticado.ra)
        )

        # Verificar se há dados para atualizar
        update_data = horario_update.model_dump(exclude_unset=True)
        if not update_data:
            raise ErroAoAtualizarHorario("Nenhum dado fornecido para atualização")

        # Aplicar atualizações
        horario_atualizado = _aplicar_atualizacoes_parciais(
            horario_existente, horario_update
        )

        db.commit()
        db.refresh(horario_atualizado)

        return schemas.GenericResponse(
            data=horario_atualizado,
            success=True,
            message="Horário atualizado com sucesso",
        )
    except (HorarioNaoEncontrado, ErroAoAtualizarHorario, PermissaoNegada):
        raise
    except Exception as e:
        raise ErroAoAtualizarHorario(str(e))


# ============================================================================
# ENDPOINTS - DELETE
# ============================================================================


@router.delete("/{id_horario}", response_model=schemas.GenericResponse[dict])
def deletar_horario(
    id_horario: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Deletar um horário existente.

    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`

    **Path Parameters:**
    - `id_horario` (int): ID único do horário a deletar

    **Restrições:**
    - Horário deve existir e pertencer ao usuário autenticado
    - Ação irreversível

    **Respostas:**
    - 200: Horário deletado com sucesso
    - 400: Erro ao deletar horário
    - 403: Usuário não tem permissão para deletar este horário
    - 404: Horário não encontrado
    - 401: Token ausente ou inválido
    """
    horario_existente = _validar_horario_pertence_usuario(
        db, id_horario, str(usuario_autenticado.ra)
    )

    try:
        db.delete(horario_existente)
        db.commit()

        return schemas.GenericResponse(
            data={"id_deletado": id_horario},
            success=True,
            message="Horário deletado com sucesso",
        )
    except Exception:
        raise ErroAoDeletarHorario()
