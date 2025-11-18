from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, models, schemas

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    tags=["Tipo de Data"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# ENDPOINTS - TIPOS DE DATA
# ============================================================================


@router.post("/", response_model=schemas.GenericResponse[schemas.TipoData], status_code=201)
def criar_tipo_data(
    tipo_data: schemas.TipoDataCreate,
    db: Session = Depends(get_db)
):
    """
    Criar novo tipo de data.
    
    **Parâmetros:**
    - `nome`: Nome do tipo de data (ex: "Falta", "Não Letivo", "Letivo")
    """
    try:
        db_tipo_data = crud.criar_tipo_data(db, tipo_data)
        return schemas.GenericResponse(
            data=db_tipo_data,
            success=True,
            message="Tipo de data criado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=schemas.GenericListResponse[schemas.TipoData])
def listar_tipos_data(
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar todos os tipos de data cadastrados.
    
    **Parâmetros:**
    - `skip`: Número de registros a saltar (padrão: 0)
    - `limit`: Número máximo de registros (padrão: 100, máximo: 1000)
    """
    tipos_data = crud.obter_tipos_data(db, skip, limit)
    total = db.query(models.TipoData).count()
    
    return schemas.GenericListResponse(
        data=tipos_data,
        success=True,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{id_tipo_data}", response_model=schemas.GenericResponse[schemas.TipoData])
def obter_tipo_data(
    id_tipo_data: int,
    db: Session = Depends(get_db)
):
    """
    Obter detalhes de um tipo de data específico.
    
    **Parâmetros:**
    - `id_tipo_data`: ID do tipo de data
    """
    db_tipo_data = crud.obter_tipo_data(db, id_tipo_data)
    if not db_tipo_data:
        raise HTTPException(status_code=404, detail="Tipo de data não encontrado")
    
    return schemas.GenericResponse(
        data=db_tipo_data,
        success=True
    )


@router.put("/{id_tipo_data}", response_model=schemas.GenericResponse[schemas.TipoData])
def atualizar_tipo_data(
    id_tipo_data: int,
    tipo_data: schemas.TipoDataCreate,
    db: Session = Depends(get_db)
):
    """
    Atualizar um tipo de data.
    
    **Parâmetros:**
    - `id_tipo_data`: ID do tipo de data a atualizar
    - Body: dados atualizados
    """
    db_tipo_data = crud.obter_tipo_data(db, id_tipo_data)
    if not db_tipo_data:
        raise HTTPException(status_code=404, detail="Tipo de data não encontrado")
    
    try:
        db_atualizado = crud.atualizar_tipo_data(db, id_tipo_data, tipo_data)
        return schemas.GenericResponse(
            data=db_atualizado,
            success=True,
            message="Tipo de data atualizado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_tipo_data}", response_model=schemas.GenericResponse[dict])
def deletar_tipo_data(
    id_tipo_data: int,
    db: Session = Depends(get_db)
):
    """
    Deletar um tipo de data.
    
    **Parâmetros:**
    - `id_tipo_data`: ID do tipo de data a deletar
    """
    db_tipo_data = crud.obter_tipo_data(db, id_tipo_data)
    if not db_tipo_data:
        raise HTTPException(status_code=404, detail="Tipo de data não encontrado")
    
    if crud.deletar_tipo_data(db, id_tipo_data):
        return schemas.GenericResponse(
            data={"id_deletado": id_tipo_data},
            success=True,
            message="Tipo de data deletado com sucesso"
        )
    raise HTTPException(status_code=400, detail="Erro ao deletar tipo de data")
