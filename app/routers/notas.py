from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(
    prefix="/notas",
    tags=["Notas"]
)

#ENDPOINTS
@router.post("/novaNota", response_model=schemas.GenericResponse[schemas.Nota], status_code=201)
def criar_nota(nota: schemas.NotaCreate, db: Session = Depends(get_db)):
    
    nova = models.Nota(
        ra=nota.ra,
        id_disciplina=nota.id_disciplina,
        bimestre=nota.bimestre,
        nota=nota.nota,
    )

    db.add(nova)
    db.commit()
    db.refresh(nova)

    return schemas.GenericResponse(
        data=nova,
        success=True,
        message="Nota criada com sucesso."
    )

@router.get("/todasNotas", response_model=schemas.GenericListResponse[schemas.Nota])
def listar_todas_notas(db: Session = Depends(get_db)):

    notas = db.query(models.Nota).all()

    return schemas.GenericListResponse(
        data=notas,
        success=True,
        total=len(notas),
        skip=0,
        limit=len(notas)
    )

@router.get("/disciplina/{id_disciplina}", response_model=schemas.GenericListResponse[schemas.Nota])
def listar_notas_por_disciplina(id_disciplina: int, db: Session = Depends(get_db)):
    notas = db.query(models.Nota).filter(models.Nota.id_disciplina == id_disciplina).all()
    return schemas.GenericListResponse(
        data=notas,
        success=True,
        total=len(notas),
        skip=0,
        limit=len(notas)
    )


@router.put("/{idNota}", response_model=schemas.GenericResponse[schemas.Nota])
def atualizar_nota(
    idNota: int,
    dados: schemas.NotaUpdate,
    db: Session = Depends(get_db),
):

    nota = db.query(models.Nota).filter(models.Nota.id_nota == idNota).first()

    if not nota:
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    if dados.ra is not None:
        nota.ra = dados.ra
    if dados.id_disciplina is not None:
        nota.id_disciplina = dados.id_disciplina
    if dados.bimestre is not None:
        nota.bimestre = dados.bimestre
    if dados.nota is not None:
        nota.nota = dados.nota

    db.commit()
    db.refresh(nota)

    return schemas.GenericResponse(
        data=nota,
        success=True,
        message="Nota atualizada com sucesso."
    )

@router.delete("/{idNota}", response_model=schemas.GenericResponse[schemas.Nota])
def deletar_nota(idNota: int, db: Session = Depends(get_db)):

    nota = db.query(models.Nota).filter(models.Nota.id_nota == idNota).first()

    if not nota:
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    db.delete(nota)
    db.commit()

    return schemas.GenericResponse(
        data=nota,
        success=True,
        message="Nota deletada com sucesso."
    )
