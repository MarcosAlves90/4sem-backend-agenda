from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from .. import crud, models, schemas

# Router config
router = APIRouter(
    prefix="/discentes",
    tags=["Discentes"],
    responses={404: {"description": "Not found"}},
)


# Endpoints

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

@router.get("/{student_id}", response_model=schemas.GenericResponse[schemas.Discente])
def get_student(student_id: int, db: Session = Depends(get_db)):
    """
    Retorna um discente pelo ID.
        - **student_id**: O ID do discente a ser retornado
    """
    student = crud.obter_discente(db, student_id)
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