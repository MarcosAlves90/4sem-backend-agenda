from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from .. import crud, models, schemas
from ..auth import verificar_token

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    tags=["Calendário"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# CONSTANTES E MAPEAMENTOS
# ============================================================================

TIPO_DATA_NOMES = {1: "Falta", 2: "Não Letivo", 3: "Letivo"}

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS (Early Return Pattern)
# ============================================================================

class CalendarioNotFound(HTTPException):
    """Evento de calendário não encontrado"""
    def __init__(self):
        super().__init__(status_code=404, detail="Evento do calendário não encontrado")


class EventoDuplicado(HTTPException):
    """Evento duplicado para mesma data e RA"""
    def __init__(self, ra: str, data: str):
        super().__init__(
            status_code=409,
            detail=f"Já existe um evento registrado para o RA {ra} na data {data}"
        )


class TipoDataInvalido(HTTPException):
    """Tipo de data inválido"""
    def __init__(self, id_tipo_data: int):
        super().__init__(status_code=400, detail=f"Tipo de data {id_tipo_data} não existe")


class FormatoDataInvalido(HTTPException):
    """Formato de data inválido"""
    def __init__(self):
        super().__init__(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")


class PermissaoNegada(HTTPException):
    """Usuário não tem permissão"""
    def __init__(self):
        super().__init__(status_code=403, detail="Você não tem permissão para acessar este evento")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_tipo_data_existe(db: Session, id_tipo_data: int) -> None:
    """Valida se tipo de data existe. Lança exceção se inválido."""
    if not crud.obter_tipo_data(db, id_tipo_data):
        raise TipoDataInvalido(id_tipo_data)


def _validar_evento_nao_duplicado(
    db: Session,
    ra: str,
    data_evento,
    excluir_id: int | None = None
) -> None:
    """Valida se evento já existe para esta combinação RA+data."""
    query = db.query(models.Calendario).filter(
        models.Calendario.ra == ra,
        models.Calendario.data_evento == data_evento
    )
    
    if excluir_id:
        query = query.filter(models.Calendario.id_data_evento != excluir_id)
    
    if query.first():
        raise EventoDuplicado(ra, str(data_evento))


def _validar_evento_pertence_usuario(db: Session, id_evento: int, ra: str) -> models.Calendario:
    """Valida se evento existe e pertence ao usuário. Retorna evento ou lança exceção."""
    evento = crud.obter_calendario(db, id_evento)
    
    if not evento:
        raise CalendarioNotFound()
    
    if str(evento.ra) != str(ra):
        raise PermissaoNegada()
    
    return evento


def _parsear_data(data_str: str):
    """Parse data em formato YYYY-MM-DD. Lança FormatoDataInvalido se falhar."""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        raise FormatoDataInvalido()

# ============================================================================
# ENDPOINTS - CREATE
# ============================================================================

@router.post("/", response_model=schemas.GenericResponse[schemas.Calendario], status_code=201)
def criar_evento_calendario(
    calendario: schemas.CalendarioCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Criar novo evento no calendário acadêmico.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Body:**
    - `data_evento` (date): Data do evento no formato YYYY-MM-DD
    - `id_tipo_data` (int): Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)
    
    **Restrições:**
    - Apenas um evento por combinação de RA e data é permitido
    - RA é obtido automaticamente do token autenticado
    
    **Respostas:**
    - 201: Evento criado com sucesso
    - 400: Tipo de data inválido
    - 409: Evento já existe para esta data
    - 401: Token ausente ou inválido
    """
    ra = str(usuario_autenticado.ra)
    
    # Validações
    _validar_tipo_data_existe(db, calendario.id_tipo_data)
    _validar_evento_nao_duplicado(db, ra, calendario.data_evento)
    
    # Preparar dados
    evento_data = calendario.model_dump()
    evento_data['ra'] = ra
    
    # Criar
    db_evento = models.Calendario(**evento_data)
    db.add(db_evento)
    db.commit()
    db.refresh(db_evento)
    
    return schemas.GenericResponse(
        data=db_evento,
        success=True,
        message="Evento do calendário criado com sucesso"
    )


# ============================================================================
# ENDPOINTS - READ
# ============================================================================

@router.get("/", response_model=schemas.GenericListResponse[schemas.Calendario])
def listar_eventos_calendario(
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar todos os eventos do calendário do usuário autenticado.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
    
    **Respostas:**
    - 200: Lista de eventos retornada com sucesso
    - 404: Nenhum evento encontrado para o usuário
    - 401: Token ausente ou inválido
    """
    ra = str(usuario_autenticado.ra)
    
    eventos = crud.obter_calendarios_por_usuario(db, ra, skip, limit)
    total = db.query(models.Calendario).filter(models.Calendario.ra == ra).count()
    
    if total == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum evento encontrado para o RA {ra}"
        )
    
    return schemas.GenericListResponse(
        data=eventos,
        success=True,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{id_data_evento}", response_model=schemas.GenericResponse[schemas.Calendario])
def obter_evento_calendario(
    id_data_evento: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Obter detalhes de um evento específico do calendário.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_data_evento` (int): ID único do evento de calendário
    
    **Restrições:**
    - Usuário só pode acessar seus próprios eventos
    
    **Respostas:**
    - 200: Evento retornado com sucesso
    - 403: Usuário não tem permissão para acessar este evento
    - 404: Evento não encontrado
    - 401: Token ausente ou inválido
    """
    ra = str(usuario_autenticado.ra)
    evento = _validar_evento_pertence_usuario(db, id_data_evento, ra)
    
    return schemas.GenericResponse(data=evento, success=True)


@router.get("/data/{data_evento}", response_model=schemas.GenericResponse[schemas.Calendario])
def obter_evento_por_data(
    data_evento: str = Path(..., description="Data no formato YYYY-MM-DD"),
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Obter evento de calendário para uma data específica do usuário autenticado.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `data_evento` (string): Data do evento no formato YYYY-MM-DD. Obrigatório.
    
    **Respostas:**
    - 200: Evento retornado com sucesso
    - 400: Formato de data inválido
    - 404: Nenhum evento encontrado para esta data
    - 401: Token ausente ou inválido
    """
    ra = usuario_autenticado.ra
    data_parsed = _parsear_data(data_evento)
    
    evento = db.query(models.Calendario).filter(
        models.Calendario.ra == ra,
        models.Calendario.data_evento == data_parsed
    ).first()
    
    if not evento:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum evento encontrado para o RA {ra} na data {data_evento}"
        )
    
    return schemas.GenericResponse(data=evento, success=True)


@router.get("/tipo/{id_tipo_data}", response_model=schemas.GenericListResponse[schemas.Calendario])
def listar_eventos_por_tipo(
    id_tipo_data: int = Path(..., ge=1, le=3, description="Tipo (1=Falta, 2=Não Letivo, 3=Letivo)"),
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Listar eventos do calendário filtrados por tipo de data para o usuário autenticado.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_tipo_data` (int): Tipo de data. Valores válidos: 1=Falta, 2=Não Letivo, 3=Letivo
    
    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
    
    **Respostas:**
    - 200: Lista de eventos retornada com sucesso
    - 400: Tipo de data inválido
    - 404: Nenhum evento encontrado para este tipo
    - 401: Token ausente ou inválido
    """
    ra = str(usuario_autenticado.ra)
    
    # Validação
    _validar_tipo_data_existe(db, id_tipo_data)
    
    # Buscar eventos
    eventos = crud.obter_calendarios_por_tipo(db, ra, id_tipo_data, skip, limit)
    total = db.query(models.Calendario).filter(
        models.Calendario.ra == ra,
        models.Calendario.id_tipo_data == id_tipo_data
    ).count()
    
    if total == 0:
        tipo_nome = TIPO_DATA_NOMES.get(id_tipo_data, f"Tipo {id_tipo_data}")
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum evento do tipo '{tipo_nome}' encontrado para o RA {ra}"
        )
    
    return schemas.GenericListResponse(
        data=eventos,
        success=True,
        total=total,
        skip=skip,
        limit=limit
    )


# ============================================================================
# ENDPOINTS - UPDATE
# ============================================================================

@router.put("/{id_data_evento}", response_model=schemas.GenericResponse[schemas.Calendario])
def atualizar_evento_calendario(
    id_data_evento: int,
    calendario: schemas.CalendarioCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Atualizar todos os campos de um evento do calendário (PUT).
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_data_evento` (int): ID único do evento a atualizar
    
    **Body:**
    - `data_evento` (date): Nova data do evento no formato YYYY-MM-DD
    - `id_tipo_data` (int): Novo tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)
    
    **Restrições:**
    - Usuário só pode atualizar seus próprios eventos
    - Apenas um evento por combinação de RA e data é permitido
    - Todos os campos são obrigatórios (use PATCH para atualização parcial)
    
    **Respostas:**
    - 200: Evento atualizado com sucesso
    - 400: Tipo de data inválido ou outro erro de validação
    - 403: Usuário não tem permissão para atualizar este evento
    - 404: Evento não encontrado
    - 409: Evento já existe para esta data
    - 401: Token ausente ou inválido
    """
    ra = str(usuario_autenticado.ra)
    
    # Validações
    evento = _validar_evento_pertence_usuario(db, id_data_evento, ra)
    _validar_tipo_data_existe(db, calendario.id_tipo_data)
    _validar_evento_nao_duplicado(db, ra, calendario.data_evento, id_data_evento)
    
    # Atualizar
    evento_data = calendario.model_dump()
    evento_data['ra'] = ra
    
    for key, value in evento_data.items():
        setattr(evento, key, value)
    
    db.commit()
    db.refresh(evento)
    
    return schemas.GenericResponse(
        data=evento,
        success=True,
        message="Evento do calendário atualizado com sucesso"
    )


@router.patch("/{id_data_evento}", response_model=schemas.GenericResponse[schemas.Calendario])
def atualizar_parcial_evento_calendario(
    id_data_evento: int,
    calendario: schemas.CalendarioUpdate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Atualizar parcialmente um evento do calendário (PATCH).
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_data_evento` (int): ID único do evento a atualizar
    
    **Body (todos os campos opcionais):**
    - `data_evento` (date, opcional): Nova data do evento no formato YYYY-MM-DD
    - `id_tipo_data` (int, opcional): Novo tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)
    
    **Restrições:**
    - Usuário só pode atualizar seus próprios eventos
    - Apenas um evento por combinação de RA e data é permitido
    - Apenas campos fornecidos serão atualizados
    
    **Respostas:**
    - 200: Evento atualizado com sucesso
    - 400: Tipo de data inválido ou outro erro de validação
    - 403: Usuário não tem permissão para atualizar este evento
    - 404: Evento não encontrado
    - 409: Evento já existe para esta data
    - 401: Token ausente ou inválido
    """
    ra = str(usuario_autenticado.ra)
    
    # Validação de propriedade
    evento = _validar_evento_pertence_usuario(db, id_data_evento, ra)
    
    # Validar tipo se fornecido
    if calendario.id_tipo_data:
        _validar_tipo_data_existe(db, calendario.id_tipo_data)
    
    # Validar duplicação se data foi alterada
    if calendario.data_evento:
        _validar_evento_nao_duplicado(db, ra, calendario.data_evento, id_data_evento)
    
    # Atualizar apenas campos fornecidos
    dados_atualizacao = calendario.model_dump(exclude_unset=True)
    dados_atualizacao['ra'] = ra
    
    for key, value in dados_atualizacao.items():
        setattr(evento, key, value)
    
    db.commit()
    db.refresh(evento)
    
    return schemas.GenericResponse(
        data=evento,
        success=True,
        message="Evento do calendário atualizado parcialmente com sucesso"
    )


# ============================================================================
# ENDPOINTS - DELETE
# ============================================================================

@router.delete("/{id_data_evento}", response_model=schemas.GenericResponse[dict])
def deletar_evento_calendario(
    id_data_evento: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Deletar um evento do calendário.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_data_evento` (int): ID único do evento a deletar
    
    **Restrições:**
    - Usuário só pode deletar seus próprios eventos
    
    **Respostas:**
    - 200: Evento deletado com sucesso
    - 403: Usuário não tem permissão para deletar este evento
    - 404: Evento não encontrado
    - 401: Token ausente ou inválido
    """
    ra = str(usuario_autenticado.ra)
    
    # Validação
    _validar_evento_pertence_usuario(db, id_data_evento, ra)
    
    # Deletar
    if crud.deletar_calendario(db, id_data_evento):
        return schemas.GenericResponse(
            data={"id_deletado": id_data_evento},
            success=True,
            message="Evento do calendário deletado com sucesso"
        )
    
    raise HTTPException(
        status_code=400,
        detail="Erro ao deletar evento do calendário"
    )

