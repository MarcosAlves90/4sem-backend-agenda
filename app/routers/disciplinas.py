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


def _validar_disciplina_pertence_usuario(
    db: Session,
    id_disciplina: int,
    ra_usuario: str
) -> models.Disciplina:
    """Valida se disciplina existe e pertence ao usuário. Retorna disciplina ou lança exceção."""
    disciplina = _validar_disciplina_existe(db, id_disciplina)
    
    # Verificar se a disciplina pertence ao usuário autenticado (comparar por RA)
    if str(disciplina.user_ra) != str(ra_usuario):
        raise HTTPException(status_code=403, detail="Você não tem permissão para acessar esta disciplina")
    
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
    
    **Restrições:**
    - Disciplina deve pertencer ao usuário autenticado
    
    **Respostas:**
    - 200: Disciplina retornada com sucesso
    - 403: Usuário não tem permissão para acessar esta disciplina
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    disciplina = _validar_disciplina_pertence_usuario(db, id_disciplina, str(usuario_autenticado.ra))
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
    Listar disciplinas do usuário autenticado com paginação.
    
    **Autenticação:**
    - Requer token JWT no header `Authorization: Bearer <token>`
    
    **Query Parameters:**
    - `skip` (int): Número de registros a saltar. Padrão: 0
    - `limit` (int): Número máximo de registros por página. Padrão: 100, Máximo: 1000
    
    **Respostas:**
    - 200: Lista de disciplinas retornada com sucesso
    - 401: Token ausente ou inválido
    """
    ra_usuario = str(usuario_autenticado.ra)
    
    disciplinas = db.query(models.Disciplina).filter(
        models.Disciplina.user_ra == ra_usuario
    ).offset(skip).limit(limit).all()
    
    total = db.query(models.Disciplina).filter(
        models.Disciplina.user_ra == ra_usuario
    ).count()

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
    
    **Notas:**
    - O RA do usuário será preenchido automaticamente a partir do token JWT
    
    **Respostas:**
    - 201: Disciplina criada com sucesso
    - 400: Erro de validação
    - 401: Token ausente ou inválido
    """
    try:
        nova_disciplina = models.Disciplina(
            nome=disciplina.nome,
            user_ra=str(usuario_autenticado.ra)
        )
        db.add(nova_disciplina)
        db.commit()
        db.refresh(nova_disciplina)
        
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
    - Disciplina deve existir e pertencer ao usuário autenticado
    - Todos os campos são obrigatórios
    
    **Respostas:**
    - 200: Disciplina atualizada com sucesso
    - 400: Erro de validação
    - 403: Usuário não tem permissão para atualizar esta disciplina
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    try:
        disciplina_existente = _validar_disciplina_pertence_usuario(db, id_disciplina, str(usuario_autenticado.ra))
        
        disciplina_existente.nome = disciplina.nome  # type: ignore
        db.commit()
        db.refresh(disciplina_existente)
        
        return schemas.GenericResponse(
            data=disciplina_existente,
            success=True,
            message="Disciplina atualizada com sucesso"
        )
    except (DisciplinaNaoEncontrada, ErroAoAtualizarDisciplina):
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
    - Disciplina deve existir e pertencer ao usuário autenticado
    - Apenas campos fornecidos serão atualizados
    
    **Respostas:**
    - 200: Disciplina atualizada com sucesso
    - 400: Erro de validação
    - 403: Usuário não tem permissão para atualizar esta disciplina
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    try:
        disciplina_existente = _validar_disciplina_pertence_usuario(db, id_disciplina, str(usuario_autenticado.ra))
        
        if disciplina.nome:
            disciplina_existente.nome = disciplina.nome  # type: ignore
        
        db.commit()
        db.refresh(disciplina_existente)
        
        return schemas.GenericResponse(
            data=disciplina_existente,
            success=True,
            message="Disciplina atualizada parcialmente com sucesso"
        )
    except (DisciplinaNaoEncontrada, ErroAoAtualizarDisciplina):
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
    - Disciplina deve existir e pertencer ao usuário autenticado
    - Ação irreversível
    
    **Respostas:**
    - 200: Disciplina deletada com sucesso
    - 400: Erro ao deletar disciplina
    - 403: Usuário não tem permissão para deletar esta disciplina
    - 404: Disciplina não encontrada
    - 401: Token ausente ou inválido
    """
    disciplina_existente = _validar_disciplina_pertence_usuario(db, id_disciplina, str(usuario_autenticado.ra))
    
    try:
        db.delete(disciplina_existente)
        db.commit()
        return schemas.GenericResponse(
            data={"id_deletado": id_disciplina},
            success=True,
            message="Disciplina deletada com sucesso"
        )
    except Exception as e:
        raise ErroAoDeletarDisciplina()