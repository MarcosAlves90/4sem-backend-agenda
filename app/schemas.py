from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Generic, TypeVar, Annotated
from datetime import date
from decimal import Decimal

from . import constants, enums
from .utils.validators import validar_ra, validar_telefone

T = TypeVar("T")


# ============================================================================
# BASE SCHEMA COM CONFIG PADRÃO
# ============================================================================


class BaseSchema(BaseModel):
    """Base schema com configuração padrão para todos os schemas"""

    class Config:
        from_attributes = True


# ============================================================================
# TIPOS ANOTADOS REUTILIZÁVEIS
# ============================================================================

RA = Annotated[
    str,
    Field(
        ...,
        min_length=constants.RA_MIN_LENGTH,
        max_length=constants.RA_MAX_LENGTH,
        description=f"Registro Acadêmico: exatamente {constants.RA_LENGTH} dígitos",
    ),
]

Telefone = Annotated[
    Optional[str],
    Field(
        None,
        max_length=constants.TELEFONE_MAX_LENGTH,
        description=f"Telefone celular (formato internacional com '+' ou mínimo {constants.TELEFONE_MIN_LENGTH} dígitos)",
    ),
]

EmailUsuario = Annotated[
    EmailStr,
    Field(
        ..., max_length=constants.EMAIL_MAX_LENGTH, description="Email único do usuário"
    ),
]

Username = Annotated[
    str,
    Field(
        ...,
        min_length=constants.USERNAME_MIN_LENGTH,
        max_length=constants.USERNAME_MAX_LENGTH,
        description="Username único do usuário",
    ),
]

NotaDecimal = Annotated[
    Optional[Decimal],
    Field(
        None,
        max_digits=4,
        decimal_places=2,
        ge=Decimal("0.0"),
        le=Decimal("10.0"),
        description="Nota em formato decimal (0.0 a 10.0)",
    ),
]


# ============================================================================
# RE-EXPORTAR ENUMS CENTRALIZADOS
# ============================================================================

TipoDataEnum = enums.TipoDataEnum
DiaSemanaEnum = enums.DiaSemanaEnum
NumeroAulaEnum = enums.NumeroAulaEnum
TipoBimestreEnum = enums.TipoBimestreEnum
TipoModuloEnum = enums.TipoModuloEnum


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
    nome: str = Field(
        ...,
        min_length=constants.INSTITUICAO_MIN_LENGTH,
        max_length=constants.INSTITUICAO_MAX_LENGTH,
    )


class Instituicao(BaseSchema):
    id_instituicao: int
    nome: str = Field(
        ...,
        min_length=constants.INSTITUICAO_MIN_LENGTH,
        max_length=constants.INSTITUICAO_MAX_LENGTH,
    )


# ---- CURSO


class CursoCreate(BaseSchema):
    nome: str = Field(
        ...,
        min_length=constants.INSTITUICAO_MIN_LENGTH,
        max_length=constants.INSTITUICAO_MAX_LENGTH,
    )


class Curso(BaseSchema):
    id_curso: int
    nome: str = Field(
        ...,
        min_length=constants.INSTITUICAO_MIN_LENGTH,
        max_length=constants.INSTITUICAO_MAX_LENGTH,
    )


# ---- DOCENTE


class DocenteCreate(BaseSchema):
    nome: str = Field(
        ..., min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: EmailStr
    disciplina: Optional[str] = Field(None, max_length=constants.DISCIPLINA_MAX_LENGTH)


class Docente(BaseSchema):
    id_docente: int
    nome: str = Field(
        ..., min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: EmailStr
    ra: Optional[RA] = None
    disciplina: Optional[str] = Field(None, max_length=constants.DISCIPLINA_MAX_LENGTH)


# ---- DISCENTE
class DiscenteCreate(BaseSchema):
    nome: str = Field(
        ..., min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: EmailStr
    tel_celular: Telefone = None
    id_curso: Optional[int] = None

    @field_validator("tel_celular")
    @classmethod
    def validar_tel(cls, v):
        return validar_telefone(v)


class Discente(BaseSchema):
    id_discente: int
    nome: str = Field(
        ..., min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: EmailStr
    tel_celular: Telefone = None
    id_curso: Optional[int] = None
    ra: Optional[RA] = None

    @field_validator("tel_celular")
    @classmethod
    def validar_tel(cls, v):
        return validar_telefone(v)


class DiscenteUpdate(BaseSchema):
    """Schema para atualização parcial (PATCH) de Discente"""

    nome: Optional[str] = Field(
        None, min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: Optional[EmailStr] = None
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
    nome: str = Field(
        ..., min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: EmailUsuario
    username: Username
    nome_instituicao: str = Field(
        ...,
        min_length=constants.INSTITUICAO_MIN_LENGTH,
        max_length=constants.INSTITUICAO_MAX_LENGTH,
        description="Nome da instituição (será criada se não existir)",
    )
    senha_hash: str = Field(..., min_length=constants.SENHA_MIN_LENGTH)
    dt_nascimento: Optional[date] = None
    tel_celular: Telefone = None
    id_curso: Optional[int] = None
    modulo: Optional[int] = Field(1, ge=constants.MODULO_MIN, le=constants.MODULO_MAX)
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
    nome: Optional[str] = Field(
        None, min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: Optional[EmailUsuario] = None
    username: Optional[Username] = None
    senha_hash: Optional[str] = Field(
        None,
        min_length=constants.SENHA_MIN_LENGTH,
        description="Senha (será hasheada automaticamente)",
    )
    dt_nascimento: Optional[date] = None
    tel_celular: Telefone = None
    nome_curso: Optional[str] = Field(
        None,
        min_length=constants.INSTITUICAO_MIN_LENGTH,
        max_length=constants.INSTITUICAO_MAX_LENGTH,
        description="Nome do curso (será criado se não existir)",
    )
    modulo: Optional[int] = Field(
        None, ge=constants.MODULO_MIN, le=constants.MODULO_MAX
    )
    bimestre: Optional[int] = None

    @field_validator("tel_celular")
    @classmethod
    def validar_tel(cls, v):
        return validar_telefone(v)


class Usuario(BaseSchema):
    """Modelo sem expor senha_hash"""

    id_usuario: Optional[int] = None
    ra: RA
    nome: str = Field(
        ..., min_length=constants.NOME_MIN_LENGTH, max_length=constants.NOME_MAX_LENGTH
    )
    email: EmailUsuario
    username: Username
    id_instituicao: int
    nome_instituicao: Optional[str] = None
    dt_nascimento: Optional[date] = None
    tel_celular: Telefone = None
    id_curso: Optional[int] = None
    nome_curso: Optional[str] = None
    modulo: Optional[int] = Field(1, ge=constants.MODULO_MIN, le=constants.MODULO_MAX)
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
# SCHEMAS - TABELAS RELACIONAIS
# ============================================================================


# ---- CALENDÁRIO
class CalendarioCreate(BaseSchema):
    """Schema para criar evento de calendário - RA é obtido do token autenticado"""

    data_evento: date = Field(..., description="Data do evento (formato: YYYY-MM-DD)")
    id_tipo_data: TipoDataEnum = Field(
        ..., description="Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)"
    )


class CalendarioUpdate(BaseSchema):
    """Schema para atualizar evento de calendário - RA é obtido do token autenticado"""

    data_evento: Optional[date] = Field(
        None, description="Data do evento (formato: YYYY-MM-DD)"
    )
    id_tipo_data: Optional[TipoDataEnum] = Field(
        None, description="Tipo de data (1=Falta, 2=Não Letivo, 3=Letivo)"
    )


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
    dia_semana: DiaSemanaEnum
    numero_aula: Optional[int] = Field(
        None,
        ge=constants.NUMERO_AULA_MIN,
        le=constants.NUMERO_AULA_MAX,
        description=f"Número da aula ({constants.NUMERO_AULA_MIN}-{constants.NUMERO_AULA_MAX})",
    )
    disciplina: Optional[str] = Field(None, max_length=constants.DISCIPLINA_MAX_LENGTH)


class Horario(BaseSchema):
    id_horario: int
    ra: RA
    dia_semana: DiaSemanaEnum
    numero_aula: Optional[int] = Field(
        None,
        ge=constants.NUMERO_AULA_MIN,
        le=constants.NUMERO_AULA_MAX,
        description=f"Número da aula ({constants.NUMERO_AULA_MIN}-{constants.NUMERO_AULA_MAX})",
    )
    disciplina: Optional[str] = Field(None, max_length=constants.DISCIPLINA_MAX_LENGTH)

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


class HorarioUpdate(BaseSchema):
    dia_semana: Optional[DiaSemanaEnum] = None
    numero_aula: Optional[int] = Field(
        None,
        ge=constants.NUMERO_AULA_MIN,
        le=constants.NUMERO_AULA_MAX,
        description=f"Número da aula ({constants.NUMERO_AULA_MIN}-{constants.NUMERO_AULA_MAX})",
    )
    disciplina: Optional[str] = Field(None, max_length=constants.DISCIPLINA_MAX_LENGTH)


# ---- NOTA
class NotaCreate(BaseSchema):
    bimestre: Optional[int] = None
    nota: str = Field(
        ..., min_length=constants.NOTA_MIN_LENGTH, max_length=constants.NOTA_MAX_LENGTH
    )
    disciplina: Optional[str] = Field(None, max_length=constants.DISCIPLINA_MAX_LENGTH)


class Nota(BaseSchema):
    id_nota: int
    ra: RA
    bimestre: Optional[int] = None
    nota: str = Field(
        ..., min_length=constants.NOTA_MIN_LENGTH, max_length=constants.NOTA_MAX_LENGTH
    )
    disciplina: Optional[str] = Field(None, max_length=constants.DISCIPLINA_MAX_LENGTH)

    @field_validator("ra")
    @classmethod
    def validar_ra_campo(cls, v):
        return validar_ra(v)


# atualizar nota
class NotaUpdate(BaseSchema):
    bimestre: Optional[int] = None
    nota: Optional[str] = Field(
        None, min_length=constants.NOTA_MIN_LENGTH, max_length=constants.NOTA_MAX_LENGTH
    )
    disciplina: Optional[str] = Field(None, max_length=100)


# ---- ANOTAÇÃO
class AnotacaoCreate(BaseSchema):
    titulo: str = Field(
        ...,
        min_length=constants.TITULO_ANOTACAO_MIN_LENGTH,
        max_length=constants.TITULO_ANOTACAO_MAX_LENGTH,
    )
    anotacao: str = Field(
        ...,
        min_length=constants.ANOTACAO_MIN_LENGTH,
        max_length=constants.ANOTACAO_MAX_LENGTH,
    )


class Anotacao(BaseSchema):
    id_anotacao: int
    ra: RA
    titulo: str = Field(
        ...,
        min_length=constants.TITULO_ANOTACAO_MIN_LENGTH,
        max_length=constants.TITULO_ANOTACAO_MAX_LENGTH,
    )
    anotacao: str = Field(
        ...,
        min_length=constants.ANOTACAO_MIN_LENGTH,
        max_length=constants.ANOTACAO_MAX_LENGTH,
    )
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
    senha_hash: str = Field(..., min_length=constants.SENHA_MIN_LENGTH)


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
