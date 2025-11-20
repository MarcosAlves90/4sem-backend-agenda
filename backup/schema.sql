-- ============================================================================
-- SCHEMA SQL - POSTGRESQL
-- ============================================================================
-- Script de criação do banco de dados para o sistema de agenda acadêmica
-- ============================================================================

-- ============================================================================
-- TABELAS BÁSICAS
-- ============================================================================

-- Tabela de Instituições de Ensino
CREATE TABLE IF NOT EXISTS instituicao (
    id_instituicao SERIAL PRIMARY KEY,
    nome VARCHAR(80) NOT NULL
);

-- Tabela de Tipos de Data (Letivo, Falta, Não Letivo)
CREATE TABLE IF NOT EXISTS tipo_data (
    id_tipo_data SERIAL PRIMARY KEY,
    nome VARCHAR(20) NOT NULL UNIQUE
);

-- Tabela de Cursos
CREATE TABLE IF NOT EXISTS curso (
    id_curso SERIAL PRIMARY KEY,
    nome VARCHAR(80) NOT NULL,
    id_instituicao INTEGER NOT NULL,
    FOREIGN KEY (id_instituicao) REFERENCES instituicao(id_instituicao) ON DELETE CASCADE
);

-- ============================================================================
-- TABELAS DE USUÁRIOS
-- ============================================================================

-- Tabela de Usuários (Alunos com login)
CREATE TABLE IF NOT EXISTS usuario (
    id_usuario SERIAL PRIMARY KEY,
    ra VARCHAR(13) NOT NULL UNIQUE,
    nome VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    username VARCHAR(20) NOT NULL UNIQUE,
    senha_hash VARCHAR(60) NOT NULL,
    id_instituicao INTEGER NOT NULL,
    dt_nascimento DATE,
    tel_celular VARCHAR(15),
    id_curso INTEGER,
    modulo INTEGER DEFAULT 1,
    bimestre INTEGER,
    FOREIGN KEY (id_instituicao) REFERENCES instituicao(id_instituicao) ON DELETE CASCADE,
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso) ON DELETE SET NULL
);

-- Tabela de Docentes (Professores)
CREATE TABLE IF NOT EXISTS docente (
    id_docente SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL,
    ra VARCHAR(13) NOT NULL,
    disciplina VARCHAR(100),
    FOREIGN KEY (ra) REFERENCES usuario(ra) ON DELETE CASCADE
);

-- Índice para melhorar buscas por RA nos docentes
CREATE INDEX IF NOT EXISTS idx_docente_ra ON docente(ra);

-- Tabela de Discentes (Alunos sem login)
CREATE TABLE IF NOT EXISTS discente (
    id_discente SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    tel_celular VARCHAR(15),
    id_curso INTEGER,
    ra VARCHAR(13) NOT NULL,
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso) ON DELETE SET NULL,
    FOREIGN KEY (ra) REFERENCES usuario(ra) ON DELETE CASCADE
);

-- ============================================================================
-- TABELAS ACADÊMICAS
-- ============================================================================

-- Tabela de Calendário Acadêmico
CREATE TABLE IF NOT EXISTS calendario (
    id_data_evento SERIAL PRIMARY KEY,
    ra VARCHAR(13) NOT NULL,
    data_evento DATE NOT NULL,
    id_tipo_data INTEGER NOT NULL,
    FOREIGN KEY (ra) REFERENCES usuario(ra) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_data) REFERENCES tipo_data(id_tipo_data) ON DELETE RESTRICT
);

-- Índice para melhorar buscas por RA no calendário
CREATE INDEX IF NOT EXISTS idx_calendario_ra ON calendario(ra);

-- Tabela de Horários de Aulas
CREATE TABLE IF NOT EXISTS horario (
    id_horario SERIAL PRIMARY KEY,
    ra VARCHAR(13) NOT NULL,
    dia_semana INTEGER NOT NULL,
    numero_aula INTEGER,
    disciplina VARCHAR(100),
    FOREIGN KEY (ra) REFERENCES usuario(ra) ON DELETE CASCADE
);

-- Índice para melhorar buscas por RA nos horários
CREATE INDEX IF NOT EXISTS idx_horario_ra ON horario(ra);

-- Tabela de Notas de Avaliação
CREATE TABLE IF NOT EXISTS nota (
    id_nota SERIAL PRIMARY KEY,
    ra VARCHAR(13) NOT NULL,
    bimestre INTEGER,
    nota VARCHAR(255) NOT NULL,
    disciplina VARCHAR(100),
    FOREIGN KEY (ra) REFERENCES usuario(ra) ON DELETE CASCADE
);

-- Índice para melhorar buscas por RA nas notas
CREATE INDEX IF NOT EXISTS idx_nota_ra ON nota(ra);

-- Tabela de Anotações/Memos do Usuário
CREATE TABLE IF NOT EXISTS anotacao (
    id_anotacao SERIAL PRIMARY KEY,
    ra VARCHAR(13) NOT NULL,
    titulo VARCHAR(50) NOT NULL,
    anotacao VARCHAR(255) NOT NULL,
    dt_anotacao DATE NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (ra) REFERENCES usuario(ra) ON DELETE CASCADE
);

-- Índice para melhorar buscas por RA nas anotações
CREATE INDEX IF NOT EXISTS idx_anotacao_ra ON anotacao(ra);

-- ============================================================================
-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================================================

-- Índices nas chaves estrangeiras principais
CREATE INDEX IF NOT EXISTS idx_usuario_instituicao ON usuario(id_instituicao);
CREATE INDEX IF NOT EXISTS idx_usuario_email ON usuario(email);
CREATE INDEX IF NOT EXISTS idx_usuario_username ON usuario(username);
CREATE INDEX IF NOT EXISTS idx_usuario_ra ON usuario(ra);
CREATE INDEX IF NOT EXISTS idx_curso_instituicao ON curso(id_instituicao);
CREATE INDEX IF NOT EXISTS idx_docente_email ON docente(email);
CREATE INDEX IF NOT EXISTS idx_docente_ra ON docente(ra);
CREATE INDEX IF NOT EXISTS idx_discente_email ON discente(email);
CREATE INDEX IF NOT EXISTS idx_discente_ra ON discente(ra);

-- ============================================================================
-- DADOS INICIAIS
-- ============================================================================

-- Inserir tipos de data padrão com IDs específicos
INSERT INTO tipo_data (id_tipo_data, nome) VALUES (1, 'Falta') ON CONFLICT DO NOTHING;
INSERT INTO tipo_data (id_tipo_data, nome) VALUES (2, 'Não letivo') ON CONFLICT DO NOTHING;
INSERT INTO tipo_data (id_tipo_data, nome) VALUES (3, 'Letivo') ON CONFLICT DO NOTHING;
