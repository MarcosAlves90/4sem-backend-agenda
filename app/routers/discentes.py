from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from .. import crud, models, schemas


router = APIRouter(
    prefix="/api/v1/alunos",  
    tags=["Alunos (Discentes)"],
    responses={404: {"description": "Not found"}},
)




@router.get("/", response_model=schemas.GenericListResponse[schemas.Discente])
def get_all_students(
    skip : int = Query(0, ge=0, description="Números de itens para pular"), 
    limit : int = Query(100, ge=0, le=1000, description="Números maximo de itens para retornar"),
    db: Session = Depends(get_db)
):
    """
    Retorna todos os discentes com paginação.
        - **skip**: Numero de items para pular
        - **limit**: Numero maximo de items para retornar
    """
    students = crud.obter_discentes(db, skip=skip, limit=limit)
    total = db.query(models.Discente).count()
    return schemas.GenericListResponse(
        data=students,
        success=True,
        total=total,
        skip=skip,
        limit=limit,
        message=f"{len(students)} Discentes retornados com sucesso"
        )

@router.get("/{id_discente}", response_model=schemas.GenericResponse[schemas.Discente])
def get_student(id_discente: int, db: Session = Depends(get_db)):
    """
    Retorna um discente pelo ID.
        - **id_discente**: O ID do discente a ser retornado
    """
    student = crud.obter_discente(db, id_discente)
    if not student:
        raise HTTPException(status_code=404, detail="Discente não encontrado")
    return schemas.GenericResponse(
        data=student,
        success=True,
        message="Discente retornado com sucesso"
    )

@router.post("/", response_model=schemas.GenericResponse[schemas.Discente])
def create_student(student: schemas.DiscenteCreate, db: Session = Depends(get_db)):
    """
    Cria um novo discente.
        - **student**: O discente a ser criado
    """
    try:
        student_exists = crud.obter_discente_por_email(db, email=student.email)
        
        if student_exists:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        
        new_student = crud.criar_discente(db=db, discente=student)
        return schemas.GenericResponse(
            data=new_student,
            success=True,
            message="Discente criado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.put(
    "/{id_discente}",
    response_model=schemas.GenericResponse[schemas.Discente],
    summary="Atualizar um discente (PUT)"
)
def update_discente(
    id_discente: int,
    discente: schemas.DiscenteCreate, 
    db: Session = Depends(get_db)
):
    """
    Atualiza completamente um discente pelo seu ID (operação PUT).

    Substitui todos os dados do discente existente pelos dados fornecidos.
    """
    db_discente = crud.obter_discente(db, id_discente=id_discente)
    if db_discente is None:
        raise HTTPException(status_code=404, detail="Discente não encontrado")

    try:
        updated_discente = crud.atualizar_discente(db, id_discente=id_discente, discente=discente)
        return schemas.GenericResponse(
            data=updated_discente,
            success=True,
            message="Discente atualizado com sucesso"
        )
    except crud.IntegrityError:
       
        raise HTTPException(status_code=400, detail="Email já cadastrado")


@router.patch(
    "/{id_discente}",
    response_model=schemas.GenericResponse[schemas.Discente],
    summary="Atualizar um discente parcialmente (PATCH)"
)
def patch_discente(
    id_discente: int,
    discente: schemas.DiscenteUpdate,  
    db: Session = Depends(get_db)
):
    """
    Atualiza parcialmente um discente pelo seu ID (operação PATCH).

    Atualiza apenas os campos fornecidos no corpo da requisição.
    """
    db_discente = crud.obter_discente(db, id_discente=id_discente)
    if db_discente is None:
        raise HTTPException(status_code=404, detail="Discente não encontrado")

    try:
       
        patched_discente = crud.atualizar_discente_parcial(db, id_discente=id_discente, discente=discente)
        return schemas.GenericResponse(
            data=patched_discente,
            success=True,
            message="Discente atualizado parcialmente com sucesso"
        )
    except crud.IntegrityError:
        raise HTTPException(status_code=400, detail="Email já cadastrado")


@router.delete(
    "/{id_discente}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar um discente"
)
def delete_discente(
    id_discente: int,
    db: Session = Depends(get_db)
):
    """
    Deleta um discente pelo seu ID.
    """
    db_discente = crud.obter_discente(db, id_discente=id_discente)
    if db_discente is None:
        raise HTTPException(status_code=404, detail="Discente não encontrado")

    success = crud.deletar_discente(db, id_discente=id_discente)
    if not success:
        
        raise HTTPException(status_code=500, detail="Erro ao deletar discente")

    return  