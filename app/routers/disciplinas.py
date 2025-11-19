from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verificar_token
from .. import crud, models, schemas

# ============================================================================
# CONFIGURAÇÃO DO ROUTER
# ============================================================================

router = APIRouter(
    prefix="/disciplinas",
    tags=["Disciplinas"],
    responses={404: {"description": "Não encontrado"}},
)

# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class DisciplinaNaoEncontrada(HTTPException):
    """Disciplina não encontrada"""
    def __init__(self):
        super().__init__(status_code=404, detail="Disciplina não encontrada")


class ErroAoCriarDisciplina(HTTPException):
    """Erro ao criar disciplina"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoAtualizarDisciplina(HTTPException):
    """Erro ao atualizar disciplina"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class ErroAoDeletarDisciplina(HTTPException):
    """Erro ao deletar disciplina"""
    def __init__(self):
        super().__init__(status_code=400, detail="Erro ao deletar disciplina")


# ============================================================================
# VALIDADORES (Responsabilidade Única)
# ============================================================================

def _validar_disciplina_existe(db: Session, id_disciplina: int) -> models.Disciplina:
    """Valida se disciplina existe. Retorna disciplina ou lança exceção."""
    disciplina = crud.obter_disciplina(db, id_disciplina)
    if not disciplina:
        raise DisciplinaNaoEncontrada()
    return disciplina


# ============================================================================
# ENDPOINTS - READ
# ============================================================================

@router.get("/{id_disciplina}", response_model=schemas.GenericResponse[schemas.Disciplina])
def obter_disciplina(
    id_disciplina: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Obter disciplina por ID.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_disciplina` (int): ID único da disciplina
    
    **Respostas:**
    - 200: Disciplina retornada com sucesso
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    disciplina = _validar_disciplina_existe(db, id_disciplina)
    return schemas.GenericResponse(
        data=disciplina,
        success=True,
        message="Disciplina retornada com sucesso"
    )


@router.get("/", response_model=schemas.GenericListResponse[schemas.Disciplina])
def listar_disciplinas(
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    skip: int = Query(0, ge=0, description="Paginação: saltar registros"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db),
):
    """
    Listar todas as disciplinas com paginação.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
    
    **Respostas:**
    - 200: Lista de disciplinas retornada com sucesso
    - 401: Token ausente ou inválido
    """
    disciplinas = crud.obter_disciplinas(db, skip, limit)
    total = db.query(models.Disciplina).count()

    return schemas.GenericListResponse(
        data=disciplinas,
        success=True,
        message="Disciplinas retornadas com sucesso",
        total=total,
        skip=skip,
        limit=limit,
    )


# ============================================================================
# ENDPOINTS - CREATE
# ============================================================================

@router.post("/", response_model=schemas.GenericResponse[schemas.Disciplina], status_code=201)
def criar_disciplina(
    disciplina: schemas.DisciplinaCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Criar nova disciplina.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Body:**
    - `nome` (string): Nome da disciplina (1-80 caracteres)
    
    **Respostas:**
    - 201: Disciplina criada com sucesso
    - 400: Erro de validação
    - 401: Token ausente ou inválido
    """
    try:
        nova_disciplina = crud.criar_disciplina(db, disciplina)
        return schemas.GenericResponse(
            data=nova_disciplina,
            success=True,
            message="Disciplina criada com sucesso"
        )
    except Exception as e:
        raise ErroAoCriarDisciplina(str(e))


# ============================================================================
# ENDPOINTS - UPDATE
# ============================================================================

@router.put("/{id_disciplina}", response_model=schemas.GenericResponse[schemas.Disciplina])
def atualizar_disciplina(
    id_disciplina: int,
    disciplina: schemas.DisciplinaCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar todos os campos de uma disciplina (PUT).
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_disciplina` (int): ID único da disciplina a atualizar
    
    **Body:**
    - `nome` (string): Nome da disciplina (1-80 caracteres)
    
    **Restrições:**
    - Disciplina deve existir
    - Todos os campos são obrigatórios
    
    **Respostas:**
    - 200: Disciplina atualizada com sucesso
    - 400: Erro de validação
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    try:
        _validar_disciplina_existe(db, id_disciplina)
        disciplina_atualizada = crud.atualizar_disciplina(db, id_disciplina, disciplina)
        return schemas.GenericResponse(
            data=disciplina_atualizada,
            success=True,
            message="Disciplina atualizada com sucesso"
        )
    except DisciplinaNaoEncontrada:
        raise
    except Exception as e:
        raise ErroAoAtualizarDisciplina(str(e))


@router.patch("/{id_disciplina}", response_model=schemas.GenericResponse[schemas.Disciplina])
def atualizar_disciplina_parcial(
    id_disciplina: int,
    disciplina: schemas.DisciplinaCreate,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Atualizar parcialmente uma disciplina (PATCH).
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_disciplina` (int): ID único da disciplina a atualizar
    
    **Body (todos os campos opcionais):**
    - `nome` (string, opcional): Nome da disciplina (1-80 caracteres)
    
    **Restrições:**
    - Disciplina deve existir
    - Apenas campos fornecidos serão atualizados
    
    **Respostas:**
    - 200: Disciplina atualizada com sucesso
    - 400: Erro de validação
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    try:
        disciplina_existente = _validar_disciplina_existe(db, id_disciplina)
        disciplina_atualizada = crud.atualizar_disciplina(db, id_disciplina, disciplina)
        return schemas.GenericResponse(
            data=disciplina_atualizada,
            success=True,
            message="Disciplina atualizada parcialmente com sucesso"
        )
    except DisciplinaNaoEncontrada:
        raise
    except Exception as e:
        raise ErroAoAtualizarDisciplina(str(e))


# ============================================================================
# ENDPOINTS - DELETE
# ============================================================================

@router.delete("/{id_disciplina}", response_model=schemas.GenericResponse[dict])
def deletar_disciplina(
    id_disciplina: int,
    usuario_autenticado: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db),
):
    """
    Deletar uma disciplina existente.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Path Parameters:**
    - `id_disciplina` (int): ID único da disciplina a deletar
    
    **Restrições:**
    - Disciplina deve existir
    - Ação irreversível
    
    **Respostas:**
    - 200: Disciplina deletada com sucesso
    - 400: Erro ao deletar disciplina
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    _validar_disciplina_existe(db, id_disciplina)
    
    if crud.deletar_disciplina(db, id_disciplina):
        return schemas.GenericResponse(
            data={"id_deletado": id_disciplina},
            success=True,
            message="Disciplina deletada com sucesso"
        )
    
    raise ErroAoDeletarDisciplina()