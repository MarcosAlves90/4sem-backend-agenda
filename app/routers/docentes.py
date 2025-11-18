from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from .. import crud, models, schemas

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    prefix="/docentes",
    tags=["Docentes"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# SCHEMAS PARA ATUALIZAÇÃO PARCIAL
# ============================================================================

class DocenteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None

    class Config:
        from_attributes = True

# ============================================================================
# ENDPOINTS - DOCENTES
# ============================================================================

@router.post("/", response_model=schemas.GenericResponse[schemas.Docente], status_code=201)
def criar_docente(
    docente: schemas.DocenteCreate,
    db: Session = Depends(get_db)
):
    """
    Criar novo docente.
    
    **Parâmetros:**
    - `nome`: Nome do docente (1-50 caracteres)
    - `email`: Email do docente (deve ser único)
    """
    try:
        # Verificar se email já existe
        docente_existente = crud.obter_docente_por_email(db, docente.email)
        if docente_existente:
            raise HTTPException(
                status_code=400,
                detail="Email já cadastrado para outro docente"
            )
        
        db_docente = crud.criar_docente(db, docente)
        return schemas.GenericResponse(
            data=db_docente,
            success=True,
            message="Docente criado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=schemas.GenericListResponse[schemas.Docente])
def listar_docentes(
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar todos os docentes cadastrados.
    
    **Parâmetros:**
    - `skip`: Número de registros a saltar (padrão: 0)
    - `limit`: Número máximo de registros (padrão: 100, máximo: 1000)
    """
    docentes = crud.obter_docentes(db, skip, limit)
    total = db.query(models.Docente).count()
    
    return schemas.GenericListResponse(
        data=docentes,
        success=True,
        total=total,
        skip=skip,
        limit=limit,
        message=f"Encontrados {len(docentes)} docentes"
    )


@router.get("/{id_docente}", response_model=schemas.GenericResponse[schemas.Docente])
def obter_docente(
    id_docente: int,
    db: Session = Depends(get_db)
):
    """
    Obter detalhes de um docente específico.
    
    **Parâmetros:**
    - `id_docente`: ID do docente
    """
    db_docente = crud.obter_docente(db, id_docente)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente não encontrado")
    
    return schemas.GenericResponse(
        data=db_docente,
        success=True,
        message="Docente encontrado com sucesso"
    )


@router.put("/{id_docente}", response_model=schemas.GenericResponse[schemas.Docente])
def atualizar_docente(
    id_docente: int,
    docente: schemas.DocenteCreate,
    db: Session = Depends(get_db)
):
    """
    Atualizar um docente (substituição completa).
    
    **Parâmetros:**
    - `id_docente`: ID do docente a atualizar
    - Body: dados completos do docente
    """
    # Verificar se docente existe
    db_docente = crud.obter_docente(db, id_docente)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente não encontrado")
    
    # Verificar se o novo email já existe em outro docente
    if docente.email != db_docente.email:
        docente_existente = crud.obter_docente_por_email(db, docente.email)
        if docente_existente and docente_existente.id_docente != id_docente:
            raise HTTPException(
                status_code=400,
                detail="Email já cadastrado para outro docente"
            )
    
    try:
        db_atualizado = crud.atualizar_docente(db, id_docente, docente)
        return schemas.GenericResponse(
            data=db_atualizado,
            success=True,
            message="Docente atualizado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{id_docente}", response_model=schemas.GenericResponse[schemas.Docente])
def atualizar_parcial_docente(
    id_docente: int,
    docente_update: DocenteUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualizar parcialmente um docente (apenas campos fornecidos).
    
    **Parâmetros:**
    - `id_docente`: ID do docente a atualizar
    - Body: dados parciais do docente (apenas campos a alterar)
    """
    # Verificar se docente existe
    db_docente = crud.obter_docente(db, id_docente)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente não encontrado")
    
    # Verificar se há dados para atualizar
    update_data = docente_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Nenhum dado fornecido para atualização"
        )
    
    # Verificar se o novo email já existe em outro docente
    if "email" in update_data and update_data["email"] != db_docente.email:
        docente_existente = crud.obter_docente_por_email(db, update_data["email"])
        if docente_existente and docente_existente.id_docente != id_docente:
            raise HTTPException(
                status_code=400,
                detail="Email já cadastrado para outro docente"
            )
    
    try:
        # Criar um DocenteCreate com os dados atuais + atualizações
        dados_atuais = {
            "nome": db_docente.nome,
            "email": db_docente.email
        }
        dados_atuais.update(update_data)
        
        docente_completo = schemas.DocenteCreate(**dados_atuais)
        db_atualizado = crud.atualizar_docente(db, id_docente, docente_completo)
        
        return schemas.GenericResponse(
            data=db_atualizado,
            success=True,
            message="Docente atualizado parcialmente com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_docente}", response_model=schemas.GenericResponse[dict])
def deletar_docente(
    id_docente: int,
    db: Session = Depends(get_db)
):
    """
    Deletar um docente.
    
    **Parâmetros:**
    - `id_docente`: ID do docente a deletar
    """
    db_docente = crud.obter_docente(db, id_docente)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente não encontrado")
    
    try:
        if crud.deletar_docente(db, id_docente):
            return schemas.GenericResponse(
                data={"id_deletado": id_docente},
                success=True,
                message="Docente deletado com sucesso"
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/email/{email}", response_model=schemas.GenericResponse[schemas.Docente])
def obter_docente_por_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Obter docente por email.
    
    **Parâmetros:**
    - `email`: Email do docente
    """
    db_docente = crud.obter_docente_por_email(db, email)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente não encontrado")
    
    return schemas.GenericResponse(
        data=db_docente,
        success=True,
        message="Docente encontrado com sucesso"
    )