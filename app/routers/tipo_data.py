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
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class TipoDataNaoEncontrado(HTTPException):
	"""Tipo de data não encontrado"""
	def __init__(self):
		super().__init__(status_code=404, detail="Tipo de data não encontrado")


class ErroAoCriarTipoData(HTTPException):
	"""Erro ao criar tipo de data"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarTipoData(HTTPException):
	"""Erro ao atualizar tipo de data"""
	def __init__(self, detail: str):
		super().__init__(status_code=400, detail=detail)


class ErroAoDeletarTipoData(HTTPException):
	"""Erro ao deletar tipo de data"""
	def __init__(self):
		super().__init__(status_code=400, detail="Erro ao deletar tipo de data")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_tipo_data_existe(db: Session, id_tipo_data: int) -> models.TipoData:
	"""Valida se tipo de data existe. Retorna tipo ou lança exceção."""
	tipo_data = crud.obter_tipo_data(db, id_tipo_data)
	if not tipo_data:
		raise TipoDataNaoEncontrado()
	return tipo_data


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
    
    **Body:**
    - `nome` (string): Nome do tipo de data. Exemplos: "Falta", "Não Letivo", "Letivo"
    
    **Restrições:**
    - Nome é obrigatório e deve ser único
    
    **Respostas:**
    - 201: Tipo de data criado com sucesso
    - 400: Erro de validação
    """
    try:
        db_tipo_data = crud.criar_tipo_data(db, tipo_data)
        return schemas.GenericResponse(
            data=db_tipo_data,
            success=True,
            message="Tipo de data criado com sucesso"
        )
    except Exception as e:
        raise ErroAoCriarTipoData(str(e))


@router.get("/", response_model=schemas.GenericListResponse[schemas.TipoData])
def listar_tipos_data(
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Paginação: limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar todos os tipos de data cadastrados com paginação.
    
    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
    
    **Respostas:**
    - 200: Lista de tipos retornada com sucesso
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
    
    **Path Parameters:**
    - `id_tipo_data` (int): ID único do tipo de data
    
    **Respostas:**
    - 200: Tipo de data retornado com sucesso
    - 404: Tipo de data não encontrado
    """
    tipo_data = _validar_tipo_data_existe(db, id_tipo_data)
    
    return schemas.GenericResponse(
        data=tipo_data,
        success=True
    )


@router.put("/{id_tipo_data}", response_model=schemas.GenericResponse[schemas.TipoData])
def atualizar_tipo_data(
    id_tipo_data: int,
    tipo_data: schemas.TipoDataCreate,
    db: Session = Depends(get_db)
):
    """
    Atualizar um tipo de data existente.
    
    **Path Parameters:**
    - `id_tipo_data` (int): ID único do tipo de data a atualizar
    
    **Body:**
    - `nome` (string): Novo nome do tipo de data
    
    **Restrições:**
    - Tipo de data deve existir
    - Nome deve ser único
    
    **Respostas:**
    - 200: Tipo de data atualizado com sucesso
    - 400: Erro de validação
    - 404: Tipo de data não encontrado
    """
    _validar_tipo_data_existe(db, id_tipo_data)
    
    try:
        db_atualizado = crud.atualizar_tipo_data(db, id_tipo_data, tipo_data)
        return schemas.GenericResponse(
            data=db_atualizado,
            success=True,
            message="Tipo de data atualizado com sucesso"
        )
    except Exception as e:
        raise ErroAoAtualizarTipoData(str(e))


@router.delete("/{id_tipo_data}", response_model=schemas.GenericResponse[dict])
def deletar_tipo_data(
    id_tipo_data: int,
    db: Session = Depends(get_db)
):
    """
    Deletar um tipo de data existente.
    
    **Path Parameters:**
    - `id_tipo_data` (int): ID único do tipo de data a deletar
    
    **Restrições:**
    - Tipo de data deve existir
    - Não pode ter eventos associados para ser deletado
    
    **Respostas:**
    - 200: Tipo de data deletado com sucesso
    - 400: Erro ao deletar tipo de data
    - 404: Tipo de data não encontrado
    """
    _validar_tipo_data_existe(db, id_tipo_data)
    
    if crud.deletar_tipo_data(db, id_tipo_data):
        return schemas.GenericResponse(
            data={"id_deletado": id_tipo_data},
            success=True,
            message="Tipo de data deletado com sucesso"
        )
    
    raise ErroAoDeletarTipoData()

