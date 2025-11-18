from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# ============================================================================
# MODELOS ORM - SQLALCHEMY
# ============================================================================

class Instituicao(Base):
    """Modelo de Instituição de Ensino"""
    __tablename__ = "instituicao"

    id_instituicao = Column(Integer, primary_key=True, index=True)
    nome = Column(String(80), nullable=False)

    # Relacionamento
    usuarios = relationship("Usuario", back_populates="instituicao")
    cursos = relationship("Curso", back_populates="instituicao")


class Usuario(Base):
    """Modelo de Usuário (Aluno)"""
    __tablename__ = "usuario"
    __table_args__ = (
        UniqueConstraint("ra", name="uq_usuario_ra"),
        UniqueConstraint("email", name="uq_usuario_email"),
        UniqueConstraint("username", name="uq_usuario_username"),
    )

    id_usuario = Column(Integer, primary_key=True, index=True)
    ra = Column(String(13), nullable=False, index=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(40), nullable=False, index=True)
    username = Column(String(20), nullable=False, index=True)
    senha_hash = Column(String(60), nullable=False)
    id_instituicao = Column(Integer, ForeignKey("instituicao.id_instituicao"), nullable=False)
    dt_nascimento = Column(Date, nullable=True)
    tel_celular = Column(String(15), nullable=True)
    id_curso = Column(Integer, ForeignKey("curso.id_curso"), nullable=True)
    modulo = Column(Integer, nullable=True, default=1)
    bimestre = Column(Integer, nullable=True)

    # Relacionamentos
    instituicao = relationship("Instituicao", back_populates="usuarios")
    curso = relationship("Curso", back_populates="usuarios")
    calendarios = relationship("Calendario", back_populates="usuario")
    horarios = relationship("Horario", back_populates="usuario")
    notas = relationship("Nota", back_populates="usuario")
    anotacoes = relationship("Anotacao", back_populates="usuario")


class TipoData(Base):
    """Modelo de Tipo de Data (Falta, Não Letivo, Letivo)"""
    __tablename__ = "tipo_data"

    id_tipo_data = Column(Integer, primary_key=True, index=True)
    nome = Column(String(10), nullable=False)

    # Relacionamento
    calendarios = relationship("Calendario", back_populates="tipo_data")


class Calendario(Base):
    """Modelo de Calendário Acadêmico"""
    __tablename__ = "calendario"

    id_data_evento = Column(Integer, primary_key=True, index=True)
    ra = Column(String(13), ForeignKey("usuario.ra"), nullable=False, index=True)
    data_evento = Column(Date, nullable=False)
    id_tipo_data = Column(Integer, ForeignKey("tipo_data.id_tipo_data"), nullable=False)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="calendarios")
    tipo_data = relationship("TipoData", back_populates="calendarios")


class Disciplina(Base):
    """Modelo de Disciplina"""
    __tablename__ = "disciplina"

    id_disciplina = Column(Integer, primary_key=True, index=True)
    nome = Column(String(80), nullable=False)

    # Relacionamentos
    cursos = relationship("CursoDisciplina", back_populates="disciplina")
    docentes = relationship("DisciplinaDocente", back_populates="disciplina")
    notas = relationship("Nota", back_populates="disciplina")


class Curso(Base):
    """Modelo de Curso"""
    __tablename__ = "curso"

    id_curso = Column(Integer, primary_key=True, index=True)
    nome = Column(String(80), nullable=False)
    id_instituicao = Column(Integer, ForeignKey("instituicao.id_instituicao"), nullable=False)

    # Relacionamentos
    instituicao = relationship("Instituicao", back_populates="cursos")
    usuarios = relationship("Usuario", back_populates="curso")
    disciplinas = relationship("CursoDisciplina", back_populates="curso")


class CursoDisciplina(Base):
    """Modelo Associativo: Curso-Disciplina"""
    __tablename__ = "curso_disciplina"

    id_curso = Column(Integer, ForeignKey("curso.id_curso"), primary_key=True)
    id_disciplina = Column(Integer, ForeignKey("disciplina.id_disciplina"), primary_key=True)
    modulo = Column(Integer, nullable=False)

    # Relacionamentos
    curso = relationship("Curso", back_populates="disciplinas")
    disciplina = relationship("Disciplina", back_populates="cursos")


class Horario(Base):
    """Modelo de Horário de Aulas"""
    __tablename__ = "horario"

    id_horario = Column(Integer, primary_key=True, index=True)
    ra = Column(String(13), ForeignKey("usuario.ra"), nullable=False, index=True)
    dia_semana = Column(Integer, nullable=False)
    id_disciplina_1 = Column(Integer, ForeignKey("disciplina.id_disciplina"), nullable=True)
    id_disciplina_2 = Column(Integer, ForeignKey("disciplina.id_disciplina"), nullable=True)
    id_disciplina_3 = Column(Integer, ForeignKey("disciplina.id_disciplina"), nullable=True)
    id_disciplina_4 = Column(Integer, ForeignKey("disciplina.id_disciplina"), nullable=True)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="horarios")
    disciplina_1_rel = relationship("Disciplina", foreign_keys=[id_disciplina_1])
    disciplina_2_rel = relationship("Disciplina", foreign_keys=[id_disciplina_2])
    disciplina_3_rel = relationship("Disciplina", foreign_keys=[id_disciplina_3])
    disciplina_4_rel = relationship("Disciplina", foreign_keys=[id_disciplina_4])


class Docente(Base):
    """Modelo de Docente (Professor)"""
    __tablename__ = "docente"
    __table_args__ = (
        UniqueConstraint("email", name="uq_docente_email"),
    )

    id_docente = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(40), nullable=False, index=True)

    # Relacionamento
    disciplinas = relationship("DisciplinaDocente", back_populates="docente")


class DisciplinaDocente(Base):
    """Modelo Associativo: Disciplina-Docente"""
    __tablename__ = "disciplina_docente"

    id_disciplina = Column(Integer, ForeignKey("disciplina.id_disciplina"), primary_key=True)
    id_docente = Column(Integer, ForeignKey("docente.id_docente"), primary_key=True)

    # Relacionamentos
    disciplina = relationship("Disciplina", back_populates="docentes")
    docente = relationship("Docente", back_populates="disciplinas")


class Discente(Base):
    """Modelo de Discente (Aluno - sem login)"""
    __tablename__ = "discente"
    __table_args__ = (
        UniqueConstraint("email", name="uq_discente_email"),
    )

    id_discente = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(40), nullable=False, index=True)
    tel_celular = Column(String(15), nullable=True)
    id_curso = Column(Integer, ForeignKey("curso.id_curso"), nullable=True)

    # Relacionamento
    curso = relationship("Curso")


class Nota(Base):
    """Modelo de Nota de Avaliação"""
    __tablename__ = "nota"

    id_nota = Column(Integer, primary_key=True, index=True)
    ra = Column(String(13), ForeignKey("usuario.ra"), nullable=False, index=True)
    id_disciplina = Column(Integer, ForeignKey("disciplina.id_disciplina"), nullable=False)
    bimestre = Column(Integer, nullable=False)
    nota = Column(Numeric(4, 2), nullable=True)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="notas")
    disciplina = relationship("Disciplina", back_populates="notas")


class Anotacao(Base):
    """Modelo de Anotação/Memo do Usuário"""
    __tablename__ = "anotacao"

    id_anotacao = Column(Integer, primary_key=True, index=True)
    ra = Column(String(13), ForeignKey("usuario.ra"), nullable=False, index=True)
    titulo = Column(String(50), nullable=False)
    anotacao = Column(String(255), nullable=False)
    dt_anotacao = Column(Date, nullable=False, default=func.now())

    # Relacionamento
    usuario = relationship("Usuario", back_populates="anotacoes")
