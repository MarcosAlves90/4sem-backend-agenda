from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, models, schemas

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    tags=["Calendário"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# FUNÇÕES AUXILIARES DE VALIDAÇÃO
# ============================================================================

def validar_usuario_existe(db: Session, ra: str) -> models.Usuario:
    """
    Valida se usuário com RA informado existe.
    
    Args:
        db: Sessão do banco de dados
        ra: RA do usuário
        
    Returns:
        models.Usuario: Usuário encontrado
        
    Raises:
        HTTPException: 404 se usuário não encontrado
    """
    usuario = crud.obter_usuario_por_ra(db, ra)
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail=f"Usuário com RA {ra} não encontrado"
        )
    return usuario


def validar_tipo_data_existe(db: Session, id_tipo_data: int) -> models.TipoData:
    """
    Valida se tipo de data informado existe.
    
    Args:
        db: Sessão do banco de dados
        id_tipo_data: ID do tipo de data
        
    Returns:
        models.TipoData: Tipo de data encontrado
        
    Raises:
        HTTPException: 400 se tipo de data não existe
    """
    tipo_data = crud.obter_tipo_data(db, id_tipo_data)
    if not tipo_data:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de data {id_tipo_data} não existe"
        )
    return tipo_data


def validar_calendario_existe(db: Session, id_data_evento: int) -> models.Calendario:
    """
    Valida se evento de calendário informado existe.
    
    Args:
        db: Sessão do banco de dados
        id_data_evento: ID do evento de calendário
        
    Returns:
        models.Calendario: Evento encontrado
        
    Raises:
        HTTPException: 404 se evento não encontrado
    """
    db_evento = crud.obter_calendario(db, id_data_evento)
    if not db_evento:
        raise HTTPException(
            status_code=404,
            detail="Evento do calendário não encontrado"
        )
    return db_evento


def validar_evento_duplicado(
    db: Session,
    ra: str,
    data_evento,
    id_data_evento_atual: int | None = None
) -> None:
    """
    Valida se já existe evento para a combinação de RA e data.
    
    Args:
        db: Sessão do banco de dados
        ra: RA do usuário (string)
        data_evento: Data do evento
        id_data_evento_atual: ID do evento atual (para exclusão na verificação)
        
    Raises:
        HTTPException: 409 se evento já existe
    """
    from typing import cast
    
    ra_str = cast(str, ra)
    
    query = db.query(models.Calendario).filter(
        models.Calendario.ra == ra_str,
        models.Calendario.data_evento == data_evento
    )
    
    if id_data_evento_atual is not None:
        query = query.filter(models.Calendario.id_data_evento != id_data_evento_atual)
    
    evento_duplicado = query.first()
    
    if evento_duplicado:
        raise HTTPException(
            status_code=409,
            detail=f"Já existe um evento registrado para o RA {ra_str} na data {data_evento}"
        )

# ============================================================================
# ENDPOINTS - CALENDÁRIO
# ============================================================================


@router.post("/", response_model=schemas.GenericResponse[schemas.Calendario], status_code=201)
def criar_evento_calendario(
    calendario: schemas.CalendarioCreate,
    db: Session = Depends(get_db)
):
    """
    Criar novo evento no calendário acadêmico.
    
    **Restrição:** Apenas um evento por data e usuário é permitido.
    
    **Parâmetros:**
    - `ra`: RA do usuário (13 dígitos)
    - `data_evento`: Data do evento (formato: YYYY-MM-DD)
    - `id_tipo_data`: Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)
    """
    validar_usuario_existe(db, calendario.ra)
    validar_tipo_data_existe(db, calendario.id_tipo_data)
    validar_evento_duplicado(db, calendario.ra, calendario.data_evento)
    
    try:
        db_calendario = crud.criar_calendario(db, calendario)
        return schemas.GenericResponse(
            data=db_calendario,
            success=True,
            message="Evento do calendário criado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=schemas.GenericListResponse[schemas.Calendario])
def listar_eventos_calendario(
    ra: str = Query(..., min_length=13, max_length=13, description="RA do usuário"),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar todos os eventos de calendário do usuário.
    
    Retorna 404 se nenhum evento for encontrado.
    
    **Parâmetros:**
    - `ra`: RA do usuário (13 dígitos) - obrigatório
    - `skip`: Número de registros a saltar (padrão: 0)
    - `limit`: Número máximo de registros (padrão: 100, máximo: 1000)
    """
    validar_usuario_existe(db, ra)
    
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
    db: Session = Depends(get_db)
):
    """
    Obter detalhes de um evento específico do calendário.
    
    **Parâmetros:**
    - `id_data_evento`: ID do evento de calendário
    """
    db_evento = validar_calendario_existe(db, id_data_evento)
    
    return schemas.GenericResponse(
        data=db_evento,
        success=True
    )


@router.get("/data/{data_evento}", response_model=schemas.GenericResponse[schemas.Calendario])
def obter_evento_por_data(
    data_evento: str = Path(..., description="Data do evento (formato: YYYY-MM-DD)"),
    ra: str = Query(..., min_length=13, max_length=13, description="RA do usuário"),
    db: Session = Depends(get_db)
):
    """
    Obter evento de calendário para uma data específica do usuário.
    
    Retorna 404 se nenhum evento for encontrado para a combinação de RA e data.
    
    **Parâmetros:**
    - `data_evento`: Data no formato YYYY-MM-DD (no path) - obrigatório
    - `ra`: RA do usuário (13 dígitos, query param) - obrigatório
    """
    validar_usuario_existe(db, ra)
    
    try:
        from datetime import datetime
        data_parsed = datetime.strptime(data_evento, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use YYYY-MM-DD"
        )
    
    evento = db.query(models.Calendario).filter(
        models.Calendario.ra == ra,
        models.Calendario.data_evento == data_parsed
    ).first()
    
    if evento is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum evento encontrado para o RA {ra} na data {data_evento}"
        )
    
    return schemas.GenericResponse(
        data=evento,
        success=True
    )


@router.get("/tipo/{id_tipo_data}", response_model=schemas.GenericListResponse[schemas.Calendario])
def listar_eventos_por_tipo(
    id_tipo_data: int = Path(..., ge=1, le=3, description="Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)"),
    ra: str = Query(..., min_length=13, max_length=13, description="RA do usuário"),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar eventos de calendário filtrados por tipo de data.
    
    Retorna 404 se nenhum evento for encontrado para o tipo especificado.
    
    **Parâmetros:**
    - `id_tipo_data`: Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo) (no path) - obrigatório
    - `ra`: RA do usuário (13 dígitos, query param) - obrigatório
    - `skip`: Número de registros a saltar (padrão: 0)
    - `limit`: Número máximo de registros (padrão: 100, máximo: 1000)
    """
    # Validações
    validar_usuario_existe(db, ra)
    validar_tipo_data_existe(db, id_tipo_data)
    
    eventos = crud.obter_calendarios_por_tipo(db, ra, id_tipo_data, skip, limit)
    total = db.query(models.Calendario).filter(
        models.Calendario.ra == ra,
        models.Calendario.id_tipo_data == id_tipo_data
    ).count()
    
    if total == 0:
        tipo_nome = {1: "Falta", 2: "Não Letivo", 3: "Letivo"}.get(id_tipo_data, f"Tipo {id_tipo_data}")
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


@router.put("/{id_data_evento}", response_model=schemas.GenericResponse[schemas.Calendario])
def atualizar_evento_calendario(
    id_data_evento: int,
    calendario: schemas.CalendarioCreate,
    db: Session = Depends(get_db)
):
    """
    Atualizar um evento do calendário.
    
    **Restrição:** Apenas um evento por data e usuário é permitido.
    
    **Parâmetros:**
    - `id_data_evento`: ID do evento a atualizar
    - Body:
        - `ra`: RA do usuário
        - `data_evento`: Data do evento
        - `id_tipo_data`: Tipo de data
    """
    validar_calendario_existe(db, id_data_evento)
    validar_usuario_existe(db, calendario.ra)
    validar_tipo_data_existe(db, calendario.id_tipo_data)
    validar_evento_duplicado(db, calendario.ra, calendario.data_evento, id_data_evento)
    
    try:
        db_atualizado = crud.atualizar_calendario(db, id_data_evento, calendario)
        return schemas.GenericResponse(
            data=db_atualizado,
            success=True,
            message="Evento do calendário atualizado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{id_data_evento}", response_model=schemas.GenericResponse[schemas.Calendario])
def atualizar_parcial_evento_calendario(
    id_data_evento: int,
    calendario: schemas.CalendarioUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualizar parcialmente um evento do calendário (PATCH).
    
    Apenas os campos fornecidos serão atualizados.
    **Restrição:** Apenas um evento por data e usuário é permitido.
    
    **Parâmetros:**
    - `id_data_evento`: ID do evento a atualizar
    - Body (todos opcionais):
        - `ra`: RA do usuário
        - `data_evento`: Data do evento
        - `id_tipo_data`: Tipo de data
    """
    db_evento = validar_calendario_existe(db, id_data_evento)
    
    if calendario.ra:
        validar_usuario_existe(db, calendario.ra)
    
    if calendario.id_tipo_data:
        validar_tipo_data_existe(db, calendario.id_tipo_data)
    
    # Se data ou RA foram alterados, verificar se já existe evento para essa combinação
    if calendario.ra or calendario.data_evento:
        ra_para_verificar = str(calendario.ra) if calendario.ra else str(db_evento.ra)
        data_para_verificar = calendario.data_evento if calendario.data_evento else db_evento.data_evento
        validar_evento_duplicado(db, ra_para_verificar, data_para_verificar, id_data_evento)
    
    try:
        db_atualizado = crud.atualizar_calendario_parcial(db, id_data_evento, calendario)
        return schemas.GenericResponse(
            data=db_atualizado,
            success=True,
            message="Evento do calendário atualizado parcialmente com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_data_evento}", response_model=schemas.GenericResponse[dict])
def deletar_evento_calendario(
    id_data_evento: int,
    db: Session = Depends(get_db)
):
    """
    Deletar um evento do calendário.
    
    **Parâmetros:**
    - `id_data_evento`: ID do evento a deletar
    """
    validar_calendario_existe(db, id_data_evento)
    
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


# ============================================================================
# FIM DO ARQUIVO
# ============================================================================
