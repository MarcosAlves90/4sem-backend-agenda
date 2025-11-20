"""
Constantes globais da aplicação.

Centraliza todos os valores mágicos (magic numbers/strings) com nomes descritivos
para melhor legibilidade e manutenção.
"""

# ============================================================================
# VALIDAÇÕES - COMPRIMENTOS
# ============================================================================

RA_LENGTH = 13
"""Comprimento exato de um Registro Acadêmico (RA). Exemplo: 1234567890123"""

RA_MIN_LENGTH = 13
"""Comprimento mínimo de um RA"""

RA_MAX_LENGTH = 13
"""Comprimento máximo de um RA"""

USERNAME_MAX_LENGTH = 20
"""Comprimento máximo de um username de usuário"""

USERNAME_MIN_LENGTH = 1
"""Comprimento mínimo de um username"""

EMAIL_MAX_LENGTH = 40
"""Comprimento máximo de um email"""

NOME_MAX_LENGTH = 50
"""Comprimento máximo de um nome (usuário, docente, discente, anotação)"""

NOME_MIN_LENGTH = 1
"""Comprimento mínimo de um nome"""

INSTITUICAO_MAX_LENGTH = 80
"""Comprimento máximo do nome de uma instituição"""

INSTITUICAO_MIN_LENGTH = 1
"""Comprimento mínimo do nome de uma instituição"""

DISCIPLINA_MAX_LENGTH = 100
"""Comprimento máximo do nome de uma disciplina"""

TELEFONE_MAX_LENGTH = 15
"""Comprimento máximo de um telefone (formato internacional)"""

TELEFONE_MIN_LENGTH = 10
"""Comprimento mínimo de um telefone (sem internacionalização)"""

ANOTACAO_MAX_LENGTH = 255
"""Comprimento máximo de texto de uma anotação"""

ANOTACAO_MIN_LENGTH = 1
"""Comprimento mínimo de uma anotação"""

TITULO_ANOTACAO_MAX_LENGTH = 50
"""Comprimento máximo de um título de anotação"""

TITULO_ANOTACAO_MIN_LENGTH = 1
"""Comprimento mínimo de um título de anotação"""

NOTA_MAX_LENGTH = 255
"""Comprimento máximo de um campo nota (representação textual)"""

NOTA_MIN_LENGTH = 1
"""Comprimento mínimo de um campo nota"""

TIPO_DATA_MAX_LENGTH = 10
"""Comprimento máximo do nome de um tipo de data"""

TIPO_DATA_MIN_LENGTH = 1
"""Comprimento mínimo do nome de um tipo de data"""

SENHA_MIN_LENGTH = 6
"""Comprimento mínimo de uma senha antes de hash"""

SENHA_HASH_LENGTH = 60
"""Comprimento de uma senha hasheada (bcrypt)"""

# ============================================================================
# VALIDAÇÕES - RANGES NUMÉRICOS
# ============================================================================

NUMERO_AULA_MIN = 1
"""Número mínimo de aula do dia"""

NUMERO_AULA_MAX = 4
"""Número máximo de aulas por dia"""

DIA_SEMANA_MIN = 1
"""Número mínimo representando dia da semana (segunda)"""

DIA_SEMANA_MAX = 6
"""Número máximo representando dia da semana (sábado)"""

MODULO_MIN = 1
"""Módulo acadêmico mínimo"""

MODULO_MAX = 12
"""Módulo acadêmico máximo"""

BIMESTRE_MIN = 1
"""Bimestre mínimo"""

BIMESTRE_MAX = 4
"""Bimestre máximo"""

NOTA_DECIMAL_MIN = 0.0
"""Nota decimal mínima (0.0)"""

NOTA_DECIMAL_MAX = 10.0
"""Nota decimal máxima (10.0)"""

SKIP_QUERY_DEFAULT = 0
"""Valor padrão de skip em queries de paginação"""

SKIP_QUERY_MIN = 0
"""Valor mínimo de skip em queries"""

LIMIT_QUERY_DEFAULT = 100
"""Valor padrão de limit em queries de paginação"""

LIMIT_QUERY_MIN = 1
"""Valor mínimo de limit em queries"""

LIMIT_QUERY_MAX = 1000
"""Valor máximo de limit em queries"""

# ============================================================================
# AUTENTICAÇÃO - JWT
# ============================================================================

JWT_ALGORITHM = "HS256"
"""Algoritmo de assinatura JWT padrão"""

JWT_SECRET_KEY = "chave_temporaria_ultra_secreta"
"""Chave secreta JWT (DEVE ser carregada de env var em produção)"""

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
"""Tempo de expiração do access token em minutos"""

JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
"""Tempo de expiração do refresh token em dias"""

# ============================================================================
# COOKIES
# ============================================================================

COOKIE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
"""Idade máxima do cookie em segundos (7 dias)"""

COOKIE_HTTPONLY = True
"""Cookie deve estar protegido contra acesso JavaScript"""

COOKIE_SECURE = False
"""Cookie requer HTTPS (False para desenvolvimento, True em produção)"""

COOKIE_SAMESITE = "lax"
"""Política SameSite do cookie (lax, strict, none)"""

# ============================================================================
# VERSÃO DA API
# ============================================================================

# TODO: [HIGH] Mudar versão da API para 1.1.0 aqui, no README e no health

API_VERSION = "1.1.0"
"""Versão atual da API"""

# ============================================================================
# BANCO DE DADOS
# ============================================================================

DATABASE_URL_DEFAULT = "sqlite:///./test.db"
"""URL padrão de conexão com banco de dados (deve usar env var em produção)"""

# ============================================================================
# CORS E SEGURANÇA
# ============================================================================

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
"""Lista de origens permitidas para CORS (domínios específicos, sem wildcard)"""

CORS_ALLOW_CREDENTIALS = True
"""Permitir cookies em requisições CORS"""

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
"""Métodos HTTP permitidos em CORS"""

CORS_ALLOW_HEADERS = ["*"]
"""Headers permitidos em CORS"""

# ============================================================================
# MENSAGENS
# ============================================================================

MSG_EMAIL_DUPLICADO = "Email já cadastrado para outro discente"
"""Mensagem de erro: email duplicado"""

MSG_EMAIL_NAO_VALIDO = "Email não é válido"
"""Mensagem de erro: email inválido"""

MSG_RA_INVALIDO = "RA deve conter apenas dígitos e ter exatamente 13 caracteres"
"""Mensagem de erro: RA inválido"""

MSG_TELEFONE_INVALIDO = "Telefone deve estar em formato internacional (+5511979592191) ou ter no mínimo 10 dígitos"
"""Mensagem de erro: telefone inválido"""

MSG_DISCENTE_NAO_ENCONTRADO = "Discente não encontrado"
"""Mensagem de erro: discente não encontrado"""

MSG_PERMISSAO_NEGADA = "Você não tem permissão para acessar este discente"
"""Mensagem de erro: permissão negada"""

MSG_NENHUM_DADO_ATUALIZACAO = "Nenhum dado fornecido para atualização"
"""Mensagem de erro: nenhum dado para atualizar"""

MSG_USUARIO_CRIADO = "Discente criado com sucesso"
"""Mensagem de sucesso: discente criado"""

MSG_USUARIO_ATUALIZADO = "Discente atualizado com sucesso"
"""Mensagem de sucesso: discente atualizado"""

MSG_USUARIO_DELETADO = "Discente deletado com sucesso"
"""Mensagem de sucesso: discente deletado"""
