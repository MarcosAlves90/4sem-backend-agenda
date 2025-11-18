from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Generic, TypeVar, Annotated
from datetime import date
from decimal import Decimal
from enum import IntEnum

T = TypeVar('T')


# ============================================================================
# BASE SCHEMA COM CONFIG PADRÃO
# ============================================================================

class BaseSchema(BaseModel):
    """Base schema com configuração padrão para todos os schemas"""
    class Config:
        from_attributes = True


# ============================================================================
# VALIDADORES REUTILIZÁVEIS
# ============================================================================

def validar_ra(v: str) -> str:
    """Valida RA: deve conter apenas dígitos e ter exatamente 13 caracteres"""
    if not v.isdigit():
        raise ValueError("RA deve conter apenas dígitos e ter exatamente 13 caracteres")
    return v


def validar_telefone(v: Optional[str]) -> Optional[str]:
    """Valida telefone: formato internacional ou mínimo 10 dígitos"""
    if v is not None:
        if not v.startswith("+") and len(v) < 10:
            raise ValueError("Telefone deve estar em formato internacional (+5511979592191) ou ter no mínimo 10 dígitos")
    return v


# Tipos anotados para reutilização
RA = Annotated[str, Field(..., min_length=13, max_length=13, description="Registro Acadêmico: exatamente 13 dígitos")]
Telefone = Annotated[Optional[str], Field(None, max_length=15, description="Telefone celular (formato internacional com '+' ou mínimo 10 dígitos), máximo 15 caracteres")]
EmailUsuario = Annotated[EmailStr, Field(..., max_length=40, description="Email único do usuário (máx. 40 caracteres)")]
Username = Annotated[str, Field(..., min_length=1, max_length=20, description="Username único do usuário (máx. 20 caracteres)")]
NotaDecimal = Annotated[Optional[Decimal], Field(None, max_digits=4, decimal_places=2, ge=Decimal("0.0"), le=Decimal("10.0"), description="Nota em formato decimal (0.0 a 10.0)")]


# ============================================================================
# ENUMS - Valores predefinidos
# ============================================================================

class TipoDataEnum(IntEnum):
    """Tipos de datas no calendário acadêmico"""
    FALTA = 1
    NAO_LETIVO = 2
    LETIVO = 3


class DiaSemanaEnum(IntEnum):
    """Dias da semana"""
    SEGUNDA = 1
    TERCA = 2
    QUARTA = 3
    QUINTA = 4
    SEXTA = 5
    SABADO = 6


# ============================================================================
# RESPONSE GENÉRICO - Base para todas as respostas
# ============================================================================

class GenericResponse(BaseSchema, Generic[T]):
    """Modelo genérico de response para padronizar todas as respostas da API"""
    data: T
    success: bool = True
    message: Optional[str] = None


class GenericListResponse(BaseSchema, Generic[T]):
    """Modelo genérico para respostas com listas"""
    data: List[T]
    success: bool = True
    message: Optional[str] = None
    total: Optional[int] = None
    skip: Optional[int] = None
    limit: Optional[int] = None


# ============================================================================
# SCHEMAS - TABELAS BASE
# ============================================================================

# ---- INSTITUIÇÃO (assumindo que existe referência em usuario.id_instituicao)
class InstituicaoCreate(BaseSchema):
    nome: str = Field(..., min_length=1, max_length=80)


class Instituicao(BaseSchema):
    id_instituicao: int
    nome: str = Field(..., min_length=1, max_length=80)


# ---- TIPO DE DATA
class TipoDataCreate(BaseSchema):
    nome: str = Field(..., min_length=1, max_length=10)


class TipoData(BaseSchema):
    id_tipo_data: int
    nome: str = Field(..., min_length=1, max_length=10)


class DisciplinaCreate(BaseSchema):
    nome: str = Field(..., min_length=1, max_length=80)


class Disciplina(BaseSchema):
    id_disciplina: int
    nome: str = Field(..., min_length=1, max_length=80)


class CursoCreate(BaseSchema):
    nome: str = Field(..., min_length=1, max_length=80)


class Curso(BaseSchema):
    id_curso: int
    nome: str = Field(..., min_length=1, max_length=80)


class DocenteCreate(BaseSchema):
    nome: str = Field(..., min_length=1, max_length=50)
    email: EmailStr


class Docente(BaseSchema):
    id_docente: int
    nome: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    ra: Optional[RA] = None


# ---- DISCENTE
class DiscenteCreate(BaseSchema):
    nome: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    tel_celular: Telefone = None
    id_curso: Optional[int] = None

    @field_validator("tel_celular")
    @classmethod
    def validar_tel(cls, v):
        return validar_telefone(v)


class Discente(BaseSchema):
    id_discente: int
    nome: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    tel_celular: Telefone = None
    id_curso: Optional[int] = None

    @field_validator("tel_celular")
    @classmethod
    def validar_tel(cls, v):
        return validar_telefone(v)


# ============================================================================
# SCHEMAS - USUÁRIO (STUDENT/ACADEMICO)
# ============================================================================

class UsuarioCreate(BaseSchema):
    ra: RA
    nome: str = Field(..., min_length=1, max_length=50)
    email: EmailUsuario
    username: Username
    nome_instituicao: str = Field(..., min_length=1, max_length=80, description="Nome da instituição (será criada se não existir)")
    senha_hash: str = Field(..., min_length=6)
    dt_nascimento: Optional[date] = None
    tel_celular: Telefone = None
    id_curso: Optional[int] = None
    modulo: Optional[int] = Field(1, ge=1, le=12)
    bimestre: Optional[int] = None

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)

    @field_validator("tel_celular")
    @classmethod
    def validar_tel(cls, v):
        return validar_telefone(v)


class UsuarioUpdate(BaseSchema):
	nome: Optional[str] = Field(None, min_length=1, max_length=50)
	email: Optional[EmailUsuario] = None
	username: Optional[Username] = None
	senha_hash: Optional[str] = Field(None, min_length=6, description="Senha (será hasheada automaticamente)")
	dt_nascimento: Optional[date] = None
	tel_celular: Telefone = None
	nome_curso: Optional[str] = Field(None, min_length=1, max_length=80, description="Nome do curso (será criado se não existir)")
	modulo: Optional[int] = Field(None, ge=1, le=12)
	bimestre: Optional[int] = None

	@field_validator("tel_celular")
	@classmethod
	def validar_tel(cls, v):
		return validar_telefone(v)
class Usuario(BaseSchema):
    """Modelo sem expor senha_hash"""
    id_usuario: Optional[int] = None
    ra: RA
    nome: str = Field(..., min_length=1, max_length=50)
    email: EmailUsuario
    username: Username
    id_instituicao: int
    nome_instituicao: Optional[str] = None
    dt_nascimento: Optional[date] = None
    tel_celular: Telefone = None
    id_curso: Optional[int] = None
    nome_curso: Optional[str] = None
    modulo: Optional[int] = Field(1, ge=1, le=12)
    bimestre: Optional[int] = None

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)

    @field_validator("tel_celular")
    @classmethod
    def validar_tel(cls, v):
        return validar_telefone(v)


# ============================================================================
# SCHEMAS - TABELAS ASSOCIATIVAS E RELACIONAIS
# ============================================================================

# ---- CURSO_DISCIPLINA
class CursoDisciplinaCreate(BaseSchema):
    id_curso: int
    id_disciplina: int
    modulo: int = Field(..., ge=1, le=12)


class CursoDisciplina(BaseSchema):
    id_curso: int
    id_disciplina: int
    modulo: int = Field(..., ge=1, le=12)


class DisciplinaDocenteCreate(BaseSchema):
    id_disciplina: int
    id_docente: int


class DisciplinaDocente(BaseSchema):
    id_disciplina: int
    id_docente: int


# ---- CALENDÁRIO
class CalendarioCreate(BaseSchema):
    """Schema para criar evento de calendário - RA é obtido do token autenticado"""
    data_evento: date = Field(..., description="Data do evento (formato: YYYY-MM-DD)")
    id_tipo_data: TipoDataEnum = Field(..., description="Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)")


class CalendarioUpdate(BaseSchema):
    """Schema para atualizar evento de calendário - RA é obtido do token autenticado"""
    data_evento: Optional[date] = Field(None, description="Data do evento (formato: YYYY-MM-DD)")
    id_tipo_data: Optional[TipoDataEnum] = Field(None, description="Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)")


class Calendario(BaseSchema):
    """Schema de resposta para evento de calendário"""
    id_data_evento: int
    ra: RA = Field(..., description="RA do usuário (obtido do token)")
    data_evento: date
    id_tipo_data: TipoDataEnum

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


# ---- HORÁRIO
class HorarioCreate(BaseSchema):
    ra: RA
    dia_semana: DiaSemanaEnum
    id_disciplina_1: Optional[int] = None
    id_disciplina_2: Optional[int] = None
    id_disciplina_3: Optional[int] = None
    id_disciplina_4: Optional[int] = None

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


class Horario(BaseSchema):
    id_horario: int
    ra: RA
    dia_semana: DiaSemanaEnum
    id_disciplina_1: Optional[int] = None
    id_disciplina_2: Optional[int] = None
    id_disciplina_3: Optional[int] = None
    id_disciplina_4: Optional[int] = None

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


# ---- NOTA
class NotaCreate(BaseSchema):
    ra: RA
    id_disciplina: int
    bimestre: Optional[int] = None
    nota: NotaDecimal

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


class Nota(BaseSchema):
    id_nota: int
    ra: RA
    id_disciplina: int
    bimestre: Optional[int] = None
    nota: NotaDecimal

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


# ---- ANOTAÇÃO
class AnotacaoCreate(BaseSchema):
    ra: RA
    titulo: str = Field(..., min_length=1, max_length=50)
    anotacao: str = Field(..., min_length=1, max_length=255)

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


class Anotacao(BaseSchema):
    id_anotacao: int
    ra: RA
    titulo: str = Field(..., min_length=1, max_length=50)
    anotacao: str = Field(..., min_length=1, max_length=255)
    dt_anotacao: date

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


# ============================================================================
# SCHEMAS - AUTENTICAÇÃO (JWT)
# ============================================================================

class Login(BaseSchema):
    """Credenciais para login"""
    username: Username
    senha_hash: str = Field(..., min_length=6)


class Token(BaseSchema):
    """Response com token JWT

    Observação: `refresh_token` é opcional aqui porque o refresh token
    será enviado preferencialmente via cookie HttpOnly. Mantemos o campo
    para compatibilidade em casos onde seja necessário retorná-lo no body.
    """
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class RefreshTokenRequest(BaseSchema):
    """Request para renovar access_token"""
    refresh_token: str


# ============================================================================
# SCHEMAS - MODELOS COM RELACIONAMENTOS (OPCIONAL - para consultas complexas)
# ============================================================================

class UsuarioDetail(Usuario):
    """Modelo com dados relacionados do usuário"""
    instituicao: Optional[Instituicao] = None
    curso: Optional[Curso] = None


class CursoDetail(Curso):
    """Modelo com disciplinas do curso"""
    disciplinas: List[CursoDisciplina] = []


class DisciplinaDetail(Disciplina):
    """Modelo com docentes e cursos"""
    docentes: List[Docente] = []
    cursos: List[Curso] = []
