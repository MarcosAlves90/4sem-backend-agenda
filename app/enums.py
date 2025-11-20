"""
Enumerações tipadas para valores predefinidos.

Substitui magic numbers por tipos strongly-typed, melhorando segurança
e legibilidade do código.
"""

from enum import IntEnum


class TipoDataEnum(IntEnum):
    """
    Tipos de datas no calendário acadêmico.

    Substitui mágica números (1, 2, 3) por nomes descritivos.
    """

    FALTA = 1
    NAO_LETIVO = 2
    LETIVO = 3

    @classmethod
    def descricao(cls, valor: int) -> str:
        """Retorna descrição legível do tipo de data."""
        mapa = {
            1: "Falta",
            2: "Não Letivo",
            3: "Letivo",
        }
        return mapa.get(valor, "Desconhecido")


class DiaSemanaEnum(IntEnum):
    """
    Dias da semana.

    Substitui números (1-6) por nomes descritivos.
    """

    SEGUNDA = 1
    TERCA = 2
    QUARTA = 3
    QUINTA = 4
    SEXTA = 5
    SABADO = 6

    @classmethod
    def descricao(cls, valor: int) -> str:
        """Retorna nome legível do dia da semana."""
        mapa = {
            1: "Segunda-feira",
            2: "Terça-feira",
            3: "Quarta-feira",
            4: "Quinta-feira",
            5: "Sexta-feira",
            6: "Sábado",
        }
        return mapa.get(valor, "Desconhecido")


class NumeroAulaEnum(IntEnum):
    """
    Números de aulas do dia (tipicamente 4 aulas).

    Substitui números (1-4) por nomes descritivos.
    """

    PRIMEIRA = 1
    SEGUNDA = 2
    TERCEIRA = 3
    QUARTA = 4

    @classmethod
    def descricao(cls, valor: int) -> str:
        """Retorna nome legível do número da aula."""
        mapa = {
            1: "Primeira Aula",
            2: "Segunda Aula",
            3: "Terceira Aula",
            4: "Quarta Aula",
        }
        return mapa.get(valor, "Desconhecido")


class TipoBimestreEnum(IntEnum):
    """
    Bimestres do ano letivo (4 bimestres).
    """

    PRIMEIRO = 1
    SEGUNDO = 2
    TERCEIRO = 3
    QUARTO = 4

    @classmethod
    def descricao(cls, valor: int) -> str:
        """Retorna nome legível do bimestre."""
        mapa = {
            1: "Primeiro Bimestre",
            2: "Segundo Bimestre",
            3: "Terceiro Bimestre",
            4: "Quarto Bimestre",
        }
        return mapa.get(valor, "Desconhecido")


class TipoModuloEnum(IntEnum):
    """
    Módulos acadêmicos (até 12 módulos possíveis).
    """

    MODULO_1 = 1
    MODULO_2 = 2
    MODULO_3 = 3
    MODULO_4 = 4
    MODULO_5 = 5
    MODULO_6 = 6
    MODULO_7 = 7
    MODULO_8 = 8
    MODULO_9 = 9
    MODULO_10 = 10
    MODULO_11 = 11
    MODULO_12 = 12

    @classmethod
    def descricao(cls, valor: int) -> str:
        """Retorna nome legível do módulo."""
        return f"Módulo {valor}" if 1 <= valor <= 12 else "Desconhecido"
