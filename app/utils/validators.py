"""
Utilitários de validação centralizados.

Consolidam todas as validações repetidas em um único lugar,
eliminando duplicação de código e garantindo consistência.
"""

from typing import Optional
from .. import constants


def validar_ra(ra: str) -> str:
    """
    Valida um Registro Acadêmico (RA).

    Verificações:
    - Apenas dígitos
    - Exatamente 13 caracteres

    Args:
        ra: String contendo o RA a validar

    Returns:
        str: RA validado

    Raises:
        ValueError: Se RA for inválido
    """
    if not ra:
        raise ValueError(constants.MSG_RA_INVALIDO)

    if not ra.isdigit():
        raise ValueError(constants.MSG_RA_INVALIDO)

    if len(ra) != constants.RA_LENGTH:
        raise ValueError(constants.MSG_RA_INVALIDO)

    return ra


def validar_telefone(telefone: Optional[str]) -> Optional[str]:
    """
    Valida um número de telefone.

    Validações:
    - Se fornecido, deve estar em formato internacional com '+' OU ter mínimo 10 dígitos
    - Máximo de 15 caracteres

    Args:
        telefone: String contendo o telefone (opcional)

    Returns:
        str | None: Telefone validado ou None

    Raises:
        ValueError: Se telefone for inválido
    """
    if telefone is None:
        return None

    if not telefone:
        return None

    # Verificar formato internacional com '+'
    if telefone.startswith("+"):
        if len(telefone) < constants.TELEFONE_MIN_LENGTH:
            raise ValueError(constants.MSG_TELEFONE_INVALIDO)
        return telefone

    # Verificar comprimento mínimo para formato sem '+'
    if len(telefone) < constants.TELEFONE_MIN_LENGTH:
        raise ValueError(constants.MSG_TELEFONE_INVALIDO)

    # Verificar comprimento máximo
    if len(telefone) > constants.TELEFONE_MAX_LENGTH:
        raise ValueError(constants.MSG_TELEFONE_INVALIDO)

    return telefone


def validar_email(email: str) -> str:
    """
    Valida um email (verificação básica).

    Verificações:
    - Não vazio
    - Comprimento máximo respeitado
    - Contém '@' e '.' (validação mínima)

    Args:
        email: String contendo o email

    Returns:
        str: Email validado

    Raises:
        ValueError: Se email for inválido
    """
    if not email:
        raise ValueError(constants.MSG_EMAIL_NAO_VALIDO)

    if len(email) > constants.EMAIL_MAX_LENGTH:
        raise ValueError(
            f"Email muito longo (máximo {constants.EMAIL_MAX_LENGTH} caracteres)"
        )

    if "@" not in email or "." not in email:
        raise ValueError(constants.MSG_EMAIL_NAO_VALIDO)

    return email


def validar_numero_aula(numero_aula: Optional[int]) -> Optional[int]:
    """
    Valida número de uma aula do dia.

    Verificações:
    - Se fornecido, deve estar entre 1 e 4

    Args:
        numero_aula: Número da aula (1-4) ou None

    Returns:
        int | None: Número de aula validado ou None

    Raises:
        ValueError: Se número de aula for inválido
    """
    if numero_aula is None:
        return None

    if not isinstance(numero_aula, int):
        raise ValueError("Número de aula deve ser inteiro")

    if (
        numero_aula < constants.NUMERO_AULA_MIN
        or numero_aula > constants.NUMERO_AULA_MAX
    ):
        raise ValueError(
            f"Número de aula deve estar entre {constants.NUMERO_AULA_MIN} e {constants.NUMERO_AULA_MAX}"
        )

    return numero_aula


def validar_dia_semana(dia_semana: int) -> int:
    """
    Valida um dia da semana.

    Verificações:
    - Deve estar entre 1 (segunda) e 6 (sábado)

    Args:
        dia_semana: Número do dia (1-6)

    Returns:
        int: Dia da semana validado

    Raises:
        ValueError: Se dia da semana for inválido
    """
    if not isinstance(dia_semana, int):
        raise ValueError("Dia da semana deve ser inteiro")

    if dia_semana < constants.DIA_SEMANA_MIN or dia_semana > constants.DIA_SEMANA_MAX:
        raise ValueError(
            f"Dia da semana deve estar entre {constants.DIA_SEMANA_MIN} (segunda) e {constants.DIA_SEMANA_MAX} (sábado)"
        )

    return dia_semana


def validar_bimestre(bimestre: Optional[int]) -> Optional[int]:
    """
    Valida um bimestre.

    Verificações:
    - Se fornecido, deve estar entre 1 e 4

    Args:
        bimestre: Número do bimestre (1-4) ou None

    Returns:
        int | None: Bimestre validado ou None

    Raises:
        ValueError: Se bimestre for inválido
    """
    if bimestre is None:
        return None

    if not isinstance(bimestre, int):
        raise ValueError("Bimestre deve ser inteiro")

    if bimestre < constants.BIMESTRE_MIN or bimestre > constants.BIMESTRE_MAX:
        raise ValueError(
            f"Bimestre deve estar entre {constants.BIMESTRE_MIN} e {constants.BIMESTRE_MAX}"
        )

    return bimestre


def validar_modulo(modulo: Optional[int]) -> Optional[int]:
    """
    Valida um módulo acadêmico.

    Verificações:
    - Se fornecido, deve estar entre 1 e 12

    Args:
        modulo: Número do módulo (1-12) ou None

    Returns:
        int | None: Módulo validado ou None

    Raises:
        ValueError: Se módulo for inválido
    """
    if modulo is None:
        return None

    if not isinstance(modulo, int):
        raise ValueError("Módulo deve ser inteiro")

    if modulo < constants.MODULO_MIN or modulo > constants.MODULO_MAX:
        raise ValueError(
            f"Módulo deve estar entre {constants.MODULO_MIN} e {constants.MODULO_MAX}"
        )

    return modulo


def extrair_ra_usuario(usuario) -> str:
    """
    Extrai RA de um objeto usuário com tratamento de erro explícito.

    Evita try-except silencioso. Trata casos onde RA pode estar em propriedade
    ou na própria instância.

    Args:
        usuario: Objeto usuário (modelo ORM ou dict)

    Returns:
        str: RA extraído

    Raises:
        ValueError: Se RA não puder ser extraído
    """
    # Tentar atributo direto
    if hasattr(usuario, "ra"):
        ra = getattr(usuario, "ra", None)
        if ra is not None:
            return str(ra)

    # Se for dict
    if isinstance(usuario, dict):
        ra = usuario.get("ra")
        if ra is not None:
            return str(ra)

    # RA não encontrado - erro explícito
    raise ValueError(
        "Não foi possível extrair RA do usuário: usuário sem atributo 'ra'"
    )


def validar_intervalo_numerico(
    valor: int, minimo: int, maximo: int, nome_campo: str = "valor"
) -> int:
    """
    Valida que um número está dentro de um intervalo [mínimo, máximo].

    Função genérica para validações de intervalo, eliminando
    duplicação de verificações de range.

    Args:
        valor: Valor a validar
        minimo: Limite inferior inclusor
        maximo: Limite superior inclusor
        nome_campo: Nome do campo para mensagem de erro

    Returns:
        int: Valor validado

    Raises:
        ValueError: Se valor estiver fora do intervalo
    """
    if not isinstance(valor, int):
        raise ValueError(f"{nome_campo} deve ser inteiro")

    if valor < minimo or valor > maximo:
        raise ValueError(
            f"{nome_campo} deve estar entre {minimo} e {maximo}, recebido: {valor}"
        )

    return valor
