from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import bcrypt
from . import models, schemas


# ============================================================================
# UTILITÁRIOS DE SEGURANÇA
# ============================================================================


def hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


# ============================================================================
# INSTITUIÇÃO
# ============================================================================


def criar_instituicao(
    db: Session, instituicao: schemas.InstituicaoCreate
) -> models.Instituicao:
    """Criar nova instituição."""
    db_instituicao = models.Instituicao(**instituicao.model_dump())
    db.add(db_instituicao)
    db.commit()
    db.refresh(db_instituicao)
    return db_instituicao


def obter_instituicao(db: Session, id_instituicao: int) -> Optional[models.Instituicao]:
    """Obter instituição por ID."""
    return (
        db.query(models.Instituicao)
        .filter(models.Instituicao.id_instituicao == id_instituicao)
        .first()
    )


def obter_instituicoes(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Instituicao]:
    """Listar todas as instituições com paginação."""
    return db.query(models.Instituicao).offset(skip).limit(limit).all()


def obter_ou_criar_instituicao_por_nome(db: Session, nome: str) -> models.Instituicao:
    """Obter instituição por nome ou criar se não existir."""
    db_instituicao = (
        db.query(models.Instituicao).filter(models.Instituicao.nome == nome).first()
    )

    if not db_instituicao:
        # Criar nova instituição se não existir
        db_instituicao = models.Instituicao(nome=nome)
        db.add(db_instituicao)
        db.commit()
        db.refresh(db_instituicao)

    return db_instituicao


def atualizar_instituicao(
    db: Session, id_instituicao: int, instituicao: schemas.InstituicaoCreate
) -> Optional[models.Instituicao]:
    """Atualizar instituição."""
    db_instituicao = obter_instituicao(db, id_instituicao)
    if db_instituicao:
        for key, value in instituicao.model_dump().items():
            setattr(db_instituicao, key, value)
        db.commit()
        db.refresh(db_instituicao)
    return db_instituicao


def deletar_instituicao(db: Session, id_instituicao: int) -> bool:
    """Deletar instituição."""
    db_instituicao = obter_instituicao(db, id_instituicao)
    if db_instituicao:
        db.delete(db_instituicao)
        db.commit()
        return True
    return False


# ============================================================================
# CURSO
# ============================================================================


def criar_curso(db: Session, curso: schemas.CursoCreate) -> models.Curso:
    """Criar novo curso."""
    db_curso = models.Curso(**curso.model_dump())
    db.add(db_curso)
    db.commit()
    db.refresh(db_curso)
    return db_curso


def obter_curso(db: Session, id_curso: int) -> Optional[models.Curso]:
    """Obter curso por ID."""
    return db.query(models.Curso).filter(models.Curso.id_curso == id_curso).first()


def obter_cursos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Curso]:
    """Listar todos os cursos."""
    return db.query(models.Curso).offset(skip).limit(limit).all()


def obter_cursos_por_instituicao(
    db: Session, id_instituicao: int, skip: int = 0, limit: int = 100
) -> List[models.Curso]:
    """Listar cursos de uma instituição."""
    return (
        db.query(models.Curso)
        .filter(models.Curso.id_instituicao == id_instituicao)
        .offset(skip)
        .limit(limit)
        .all()
    )


def atualizar_curso(
    db: Session, id_curso: int, curso: schemas.CursoCreate
) -> Optional[models.Curso]:
    """Atualizar curso."""
    db_curso = obter_curso(db, id_curso)
    if db_curso:
        for key, value in curso.model_dump().items():
            setattr(db_curso, key, value)
        db.commit()
        db.refresh(db_curso)
    return db_curso


def obter_ou_criar_curso_por_nome(
    db: Session, nome_curso: str, id_instituicao: int
) -> models.Curso:
    """Obter curso por nome ou criar se não existir."""
    try:
        db_curso = (
            db.query(models.Curso)
            .filter(
                models.Curso.nome == nome_curso,
                models.Curso.id_instituicao == id_instituicao,
            )
            .first()
        )

        if not db_curso:
            # Criar novo curso se não existir
            db_curso = models.Curso(nome=nome_curso, id_instituicao=id_instituicao)
            db.add(db_curso)
            db.commit()
            db.refresh(db_curso)

        return db_curso
    except IntegrityError:
        # Se houver erro de integridade (duplicação por race condition), fazer rollback e buscar novamente
        db.rollback()
        db_curso = (
            db.query(models.Curso)
            .filter(
                models.Curso.nome == nome_curso,
                models.Curso.id_instituicao == id_instituicao,
            )
            .first()
        )
        return db_curso


def deletar_curso(db: Session, id_curso: int) -> bool:
    """Deletar curso."""
    db_curso = obter_curso(db, id_curso)
    if db_curso:
        db.delete(db_curso)
        db.commit()
        return True
    return False


# ============================================================================
# DOCENTE
# ============================================================================


def criar_docente(db: Session, docente: schemas.DocenteCreate) -> models.Docente:
    """Criar novo docente."""
    try:
        db_docente = models.Docente(**docente.model_dump())
        db.add(db_docente)
        db.commit()
        db.refresh(db_docente)
        return db_docente
    except IntegrityError:
        db.rollback()
        raise


def obter_docente(db: Session, id_docente: int) -> Optional[models.Docente]:
    """Obter docente por ID."""
    return (
        db.query(models.Docente).filter(models.Docente.id_docente == id_docente).first()
    )


def obter_docente_por_email(db: Session, email: str) -> Optional[models.Docente]:
    """Obter docente por email."""
    return db.query(models.Docente).filter(models.Docente.email == email).first()


def obter_docentes(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Docente]:
    """Listar todos os docentes."""
    return db.query(models.Docente).offset(skip).limit(limit).all()


def atualizar_docente(
    db: Session, id_docente: int, docente: schemas.DocenteCreate
) -> Optional[models.Docente]:
    """Atualizar docente."""
    try:
        db_docente = obter_docente(db, id_docente)
        if db_docente:
            for key, value in docente.model_dump().items():
                setattr(db_docente, key, value)
            db.commit()
            db.refresh(db_docente)
        return db_docente
    except IntegrityError:
        db.rollback()
        raise


def deletar_docente(db: Session, id_docente: int) -> bool:
    """Deletar docente."""
    db_docente = obter_docente(db, id_docente)
    if db_docente:
        db.delete(db_docente)
        db.commit()
        return True
    return False


# ============================================================================
# DISCENTE
# ============================================================================


def criar_discente(db: Session, discente: schemas.DiscenteCreate) -> models.Discente:
    """Criar novo discente."""
    try:
        db_discente = models.Discente(**discente.model_dump())
        db.add(db_discente)
        db.commit()
        db.refresh(db_discente)
        return db_discente
    except IntegrityError:
        db.rollback()
        raise


def obter_discente(db: Session, id_discente: int) -> Optional[models.Discente]:
    """Obter discente por ID."""
    return (
        db.query(models.Discente)
        .filter(models.Discente.id_discente == id_discente)
        .first()
    )


def obter_discente_por_email(db: Session, email: str) -> Optional[models.Discente]:
    """Obter discente por email."""
    return db.query(models.Discente).filter(models.Discente.email == email).first()


def obter_discentes(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Discente]:
    """Listar todos os discentes."""
    return db.query(models.Discente).offset(skip).limit(limit).all()


def obter_discentes_por_curso(
    db: Session, id_curso: int, skip: int = 0, limit: int = 100
) -> List[models.Discente]:
    """Listar discentes de um curso."""
    return (
        db.query(models.Discente)
        .filter(models.Discente.id_curso == id_curso)
        .offset(skip)
        .limit(limit)
        .all()
    )


def atualizar_discente(
    db: Session, id_discente: int, discente: schemas.DiscenteCreate
) -> Optional[models.Discente]:
    """Atualizar discente."""
    try:
        db_discente = obter_discente(db, id_discente)
        if db_discente:
            for key, value in discente.model_dump().items():
                setattr(db_discente, key, value)
            db.commit()
            db.refresh(db_discente)
        return db_discente
    except IntegrityError:
        db.rollback()
        raise


def atualizar_discente_parcial(
    db: Session, id_discente: int, discente: schemas.DiscenteUpdate
) -> Optional[models.Discente]:
    """Atualizar discente (apenas campos fornecidos - PATCH)."""
    try:
        db_discente = obter_discente(db, id_discente)
        if db_discente:
            # Atualizar apenas campos não-nulos
            for key, value in discente.model_dump(exclude_unset=True).items():
                setattr(db_discente, key, value)
            db.commit()
            db.refresh(db_discente)
        return db_discente
    except IntegrityError:
        db.rollback()
        raise


def deletar_discente(db: Session, id_discente: int) -> bool:
    """Deletar discente."""
    db_discente = obter_discente(db, id_discente)
    if db_discente:
        db.delete(db_discente)
        db.commit()
        return True
    return False


# ============================================================================
# USUÁRIO
# ============================================================================


def criar_usuario(db: Session, usuario: schemas.UsuarioCreate) -> models.Usuario:
    """Criar novo usuário (aluno). Cria instituição automaticamente se não existir."""
    try:
        # Obter ou criar instituição baseado no nome fornecido
        db_instituicao = obter_ou_criar_instituicao_por_nome(
            db, usuario.nome_instituicao
        )

        # Preparar dados do usuário
        usuario_data = usuario.model_dump(exclude={"nome_instituicao"})
        usuario_data["id_instituicao"] = db_instituicao.id_instituicao

        # Hash da senha
        usuario_data["senha_hash"] = hash_senha(usuario_data["senha_hash"])

        # Criar usuário
        db_usuario = models.Usuario(**usuario_data)
        db.add(db_usuario)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario
    except IntegrityError:
        db.rollback()
        raise


def obter_usuario(db: Session, id_usuario: int) -> Optional[models.Usuario]:
    """Obter usuário por ID."""
    return (
        db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    )


def obter_usuario_por_ra(db: Session, ra: str) -> Optional[models.Usuario]:
    """Obter usuário por RA."""
    return db.query(models.Usuario).filter(models.Usuario.ra == ra).first()


def obter_usuario_por_email(db: Session, email: str) -> Optional[models.Usuario]:
    """Obter usuário por email."""
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()


def obter_usuario_por_username(db: Session, username: str) -> Optional[models.Usuario]:
    """Obter usuário por username."""
    return db.query(models.Usuario).filter(models.Usuario.username == username).first()


def obter_usuarios(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Usuario]:
    """Listar todos os usuários."""
    return db.query(models.Usuario).offset(skip).limit(limit).all()


def obter_usuarios_por_instituicao(
    db: Session, id_instituicao: int, skip: int = 0, limit: int = 100
) -> List[models.Usuario]:
    """Listar usuários de uma instituição."""
    return (
        db.query(models.Usuario)
        .filter(models.Usuario.id_instituicao == id_instituicao)
        .offset(skip)
        .limit(limit)
        .all()
    )


def obter_usuarios_por_curso(
    db: Session, id_curso: int, skip: int = 0, limit: int = 100
) -> List[models.Usuario]:
    """Listar usuários de um curso."""
    return (
        db.query(models.Usuario)
        .filter(models.Usuario.id_curso == id_curso)
        .offset(skip)
        .limit(limit)
        .all()
    )


def atualizar_usuario(
    db: Session, id_usuario: int, usuario: schemas.UsuarioUpdate
) -> Optional[models.Usuario]:
    """Atualizar usuário (apenas campos fornecidos)."""
    try:
        db_usuario = obter_usuario(db, id_usuario)
        if db_usuario:
            # Atualizar apenas campos não-nulos
            dados_atualizacao = usuario.model_dump(exclude_unset=True)

            # Se nome_curso foi fornecido, resolver para id_curso
            if "nome_curso" in dados_atualizacao and dados_atualizacao["nome_curso"]:
                id_instituicao: int = db_usuario.id_instituicao
                db_curso = obter_ou_criar_curso_por_nome(
                    db, dados_atualizacao["nome_curso"], id_instituicao
                )
                dados_atualizacao["id_curso"] = db_curso.id_curso
                del dados_atualizacao["nome_curso"]
            else:
                # Remover nome_curso se não foi fornecido
                dados_atualizacao.pop("nome_curso", None)

            # Se senha foi fornecida, fazer hash
            if "senha_hash" in dados_atualizacao and dados_atualizacao["senha_hash"]:
                dados_atualizacao["senha_hash"] = hash_senha(
                    dados_atualizacao["senha_hash"]
                )

            for key, value in dados_atualizacao.items():
                setattr(db_usuario, key, value)
            db.commit()
            db.refresh(db_usuario)
        return db_usuario
    except IntegrityError:
        db.rollback()
        raise


def deletar_usuario(db: Session, id_usuario: int) -> bool:
    """Deletar usuário."""
    db_usuario = obter_usuario(db, id_usuario)
    if db_usuario:
        db.delete(db_usuario)
        db.commit()
        return True
    return False


# ============================================================================
# CALENDÁRIO
# ============================================================================


def criar_calendario(
    db: Session, calendario: schemas.CalendarioCreate
) -> models.Calendario:
    """Criar novo evento de calendário."""
    try:
        db_calendario = models.Calendario(**calendario.model_dump())
        db.add(db_calendario)
        db.commit()
        db.refresh(db_calendario)
        return db_calendario
    except IntegrityError:
        db.rollback()
        raise


def obter_tipo_data(db: Session, id_tipo_data: int) -> Optional[models.TipoData]:
    """Obter tipo de data por ID."""
    return (
        db.query(models.TipoData)
        .filter(models.TipoData.id_tipo_data == id_tipo_data)
        .first()
    )


def obter_calendario(db: Session, id_data_evento: int) -> Optional[models.Calendario]:
    """Obter evento de calendário por ID."""
    return (
        db.query(models.Calendario)
        .filter(models.Calendario.id_data_evento == id_data_evento)
        .first()
    )


def obter_calendarios_por_usuario(
    db: Session, ra: str, skip: int = 0, limit: int = 100
) -> List[models.Calendario]:
    """Listar eventos de calendário do usuário."""
    return (
        db.query(models.Calendario)
        .filter(models.Calendario.ra == ra)
        .offset(skip)
        .limit(limit)
        .all()
    )


def obter_calendarios_por_tipo(
    db: Session, ra: str, id_tipo_data: int, skip: int = 0, limit: int = 100
) -> List[models.Calendario]:
    """Listar eventos de calendário por tipo."""
    return (
        db.query(models.Calendario)
        .filter(
            models.Calendario.ra == ra, models.Calendario.id_tipo_data == id_tipo_data
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def atualizar_calendario(
    db: Session, id_data_evento: int, calendario: schemas.CalendarioCreate
) -> Optional[models.Calendario]:
    """Atualizar evento de calendário."""
    try:
        db_calendario = obter_calendario(db, id_data_evento)
        if db_calendario:
            for key, value in calendario.model_dump().items():
                setattr(db_calendario, key, value)
            db.commit()
            db.refresh(db_calendario)
        return db_calendario
    except IntegrityError:
        db.rollback()
        raise


def atualizar_calendario_parcial(
    db: Session, id_data_evento: int, calendario: schemas.CalendarioUpdate
) -> Optional[models.Calendario]:
    """Atualizar evento de calendário (apenas campos fornecidos)."""
    try:
        db_calendario = obter_calendario(db, id_data_evento)
        if db_calendario:
            for key, value in calendario.model_dump(exclude_unset=True).items():
                setattr(db_calendario, key, value)
            db.commit()
            db.refresh(db_calendario)
        return db_calendario
    except IntegrityError:
        db.rollback()
        raise


def deletar_calendario(db: Session, id_data_evento: int) -> bool:
    """Deletar evento de calendário."""
    db_calendario = obter_calendario(db, id_data_evento)
    if db_calendario:
        db.delete(db_calendario)
        db.commit()
        return True
    return False


# ============================================================================
# HORÁRIO
# ============================================================================


def criar_horario(db: Session, horario: schemas.HorarioCreate) -> models.Horario:
    """Criar novo horário."""
    try:
        db_horario = models.Horario(**horario.model_dump())
        db.add(db_horario)
        db.commit()
        db.refresh(db_horario)
        return db_horario
    except IntegrityError:
        db.rollback()
        raise


def obter_horario(db: Session, id_horario: int) -> Optional[models.Horario]:
    """Obter horário por ID."""
    return (
        db.query(models.Horario).filter(models.Horario.id_horario == id_horario).first()
    )


def obter_horarios_por_usuario(
    db: Session, ra: str, skip: int = 0, limit: int = 100
) -> List[models.Horario]:
    """Listar horários do usuário."""
    return (
        db.query(models.Horario)
        .filter(models.Horario.ra == ra)
        .offset(skip)
        .limit(limit)
        .all()
    )


def obter_horario_por_dia(
    db: Session, ra: str, dia_semana: int
) -> Optional[models.Horario]:
    """Obter horário de um dia específico."""
    return (
        db.query(models.Horario)
        .filter(models.Horario.ra == ra, models.Horario.dia_semana == dia_semana)
        .first()
    )


def atualizar_horario(
    db: Session, id_horario: int, horario: schemas.HorarioCreate
) -> Optional[models.Horario]:
    """Atualizar horário."""
    try:
        db_horario = obter_horario(db, id_horario)
        if db_horario:
            for key, value in horario.model_dump().items():
                setattr(db_horario, key, value)
            db.commit()
            db.refresh(db_horario)
        return db_horario
    except IntegrityError:
        db.rollback()
        raise


def deletar_horario(db: Session, id_horario: int) -> bool:
    """Deletar horário."""
    db_horario = obter_horario(db, id_horario)
    if db_horario:
        db.delete(db_horario)
        db.commit()
        return True
    return False


# ============================================================================
# NOTA
# ============================================================================


def criar_nota(db: Session, nota: schemas.NotaCreate) -> models.Nota:
    """Criar nova nota."""
    try:
        db_nota = models.Nota(**nota.model_dump())
        db.add(db_nota)
        db.commit()
        db.refresh(db_nota)
        return db_nota
    except IntegrityError:
        db.rollback()
        raise


def obter_nota(db: Session, id_nota: int) -> Optional[models.Nota]:
    """Obter nota por ID."""
    return db.query(models.Nota).filter(models.Nota.id_nota == id_nota).first()


def obter_notas_por_usuario(
    db: Session, ra: str, skip: int = 0, limit: int = 100
) -> List[models.Nota]:
    """Listar notas do usuário."""
    return (
        db.query(models.Nota)
        .filter(models.Nota.ra == ra)
        .offset(skip)
        .limit(limit)
        .all()
    )


def obter_notas_por_disciplina(
    db: Session, ra: str, id_disciplina: int, skip: int = 0, limit: int = 100
) -> List[models.Nota]:
    """Listar notas de uma disciplina."""
    return (
        db.query(models.Nota)
        .filter(models.Nota.ra == ra, models.Nota.id_disciplina == id_disciplina)
        .offset(skip)
        .limit(limit)
        .all()
    )


def obter_notas_por_bimestre(
    db: Session, ra: str, bimestre: int, skip: int = 0, limit: int = 100
) -> List[models.Nota]:
    """Listar notas de um bimestre."""
    return (
        db.query(models.Nota)
        .filter(models.Nota.ra == ra, models.Nota.bimestre == bimestre)
        .offset(skip)
        .limit(limit)
        .all()
    )


def atualizar_nota(
    db: Session, id_nota: int, nota: schemas.NotaCreate
) -> Optional[models.Nota]:
    """Atualizar nota."""
    try:
        db_nota = obter_nota(db, id_nota)
        if db_nota:
            for key, value in nota.model_dump().items():
                setattr(db_nota, key, value)
            db.commit()
            db.refresh(db_nota)
        return db_nota
    except IntegrityError:
        db.rollback()
        raise


def deletar_nota(db: Session, id_nota: int) -> bool:
    """Deletar nota."""
    db_nota = obter_nota(db, id_nota)
    if db_nota:
        db.delete(db_nota)
        db.commit()
        return True
    return False


# ============================================================================
# ANOTAÇÃO
# ============================================================================


def criar_anotacao(db: Session, anotacao: schemas.AnotacaoCreate) -> models.Anotacao:
    """Criar nova anotação."""
    try:
        db_anotacao = models.Anotacao(**anotacao.model_dump())
        db.add(db_anotacao)
        db.commit()
        db.refresh(db_anotacao)
        return db_anotacao
    except IntegrityError:
        db.rollback()
        raise


def obter_anotacao(db: Session, id_anotacao: int) -> Optional[models.Anotacao]:
    """Obter anotação por ID."""
    return (
        db.query(models.Anotacao)
        .filter(models.Anotacao.id_anotacao == id_anotacao)
        .first()
    )


def obter_anotacoes_por_usuario(
    db: Session, ra: str, skip: int = 0, limit: int = 100
) -> List[models.Anotacao]:
    """Listar anotações do usuário."""
    return (
        db.query(models.Anotacao)
        .filter(models.Anotacao.ra == ra)
        .offset(skip)
        .limit(limit)
        .all()
    )


def atualizar_anotacao(
    db: Session, id_anotacao: int, anotacao: schemas.AnotacaoCreate
) -> Optional[models.Anotacao]:
    """Atualizar anotação."""
    try:
        db_anotacao = obter_anotacao(db, id_anotacao)
        if db_anotacao:
            for key, value in anotacao.model_dump().items():
                setattr(db_anotacao, key, value)
            db.commit()
            db.refresh(db_anotacao)
        return db_anotacao
    except IntegrityError:
        db.rollback()
        raise


def deletar_anotacao(db: Session, id_anotacao: int) -> bool:
    """Deletar anotação."""
    db_anotacao = obter_anotacao(db, id_anotacao)
    if db_anotacao:
        db.delete(db_anotacao)
        db.commit()
        return True
    return False
