from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db
from .. import crud, models,schemas

#=================================================================================
# CONFIGURAÇÃO ROUTER
#=================================================================================

router = APIRouter(tags=["Anotacoes"], responses={404:{"description": "not found"}})

#=================================================================================
# FUNÇÕES
#=================================================================================

"""
def verifica_user(ra:str,db = Depends(get_db)):
    user = crud.obter_usuario_por_ra(db, ra)
    if not user: 
        raise HTTPException(status_code=404, detail="Usúario não encontrado")
    return user
"""

#=================================================================================
# ENDPOINTS
#=================================================================================

#============================ Endpoints GET ======================================
@router.get("/todas",response_model=schemas.GenericListResponse[schemas.Anotacao])
async def todas_anotacoes(ra:str,db = Depends(get_db)):
    try:        
        anotacoes = crud.obter_anotacoes_por_usuario(db,ra)
        return {
            "data": anotacoes,
            "total": len(anotacoes),
            "message": "Todas anotações do usuario retornadas"
        }
    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))
    
@router.get("/{id_anotacao}", response_model=schemas.GenericResponse[schemas.Anotacao])
async def anotacao_id(id_anotacao:int,db = Depends(get_db)):
    try:
        anotacao = crud.obter_anotacao(db,id_anotacao)
        if not anotacao:
            raise HTTPException(status_code=404, detail="Anotação não encontrada")
        return{
            "data":anotacao,
            "message": "Anotação retornada"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


#=========================== Endpoints Post ======================================
@router.post("/criar",response_model=schemas.GenericResponse[schemas.Anotacao])
async def criar_anotacao(anotacao: schemas.AnotacaoCreate,db = Depends(get_db)):
    try:
        nova_anotacao = crud.criar_anotacao(db, anotacao)
        return{
            "data": nova_anotacao,
            "message":"Anotação criada com sucesso!!!"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
#=========================== Endpoints DELETE ====================================
@router.delete("/apagar/{id_anotacao}", response_model=schemas.GenericResponse[dict])
async def apagar_anotacao(id_anotacao:int,db = Depends(get_db)):
    try:
        if crud.deletar_anotacao(db,id_anotacao):
            return {
                "data": {"id_deletado":id_anotacao},
                "message": "Anotação excluida!"
            }
        else:
            raise HTTPException(status_code=404, detail="Anotação não encontrada")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
#============================ Endpoints PUT ======================================
@router.put("/editar/{id_anotacao}", response_model=schemas.GenericResponse[schemas.AnotacaoCreate])
async def editar_anotacao(id_anotacao:int,anotacao:schemas.AnotacaoCreate, db = Depends(get_db)):
    try:
        anotacao_velha = crud.obter_anotacao(db,id_anotacao)
        if not anotacao_velha:
            raise HTTPException(status_code=404, detail="Anotação não encontrada")
        crud.atualizar_anotacao(db,id_anotacao,anotacao)
        return{
            "data":anotacao,
            "message":"Anotação alterada com sucesso!"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
