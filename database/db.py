import sqlite3
import os

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "ava.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL DEFAULT 'aluno',
    senha TEXT NOT NULL,
    notas TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS turmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_turma TEXT NOT NULL UNIQUE,
    professor_email TEXT NOT NULL,
    FOREIGN KEY (professor_email) REFERENCES usuarios(email)
);

CREATE TABLE IF NOT EXISTS turma_alunos (
    turma_id INTEGER NOT NULL,
    aluno_email TEXT NOT NULL,
    PRIMARY KEY (turma_id, aluno_email),
    FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE,
    FOREIGN KEY (aluno_email) REFERENCES usuarios(email)
);

CREATE TABLE IF NOT EXISTS aulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turma_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ativa',
    assunto TEXT DEFAULT 'Sem assunto definido',
    data_inicio TEXT,
    data_fim TEXT,
    duracao_segundos INTEGER NOT NULL,
    FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS frequencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aula_id INTEGER NOT NULL,
    turma_id INTEGER NOT NULL,
    aluno_email TEXT NOT NULL,
    presente INTEGER NOT NULL DEFAULT 0,
    hora_entrada TEXT,
    FOREIGN KEY (aula_id) REFERENCES aulas(id) ON DELETE CASCADE,
    FOREIGN KEY (turma_id) REFERENCES turmas(id),
    FOREIGN KEY (aluno_email) REFERENCES usuarios(email),
    UNIQUE(aula_id, aluno_email)
);

CREATE TABLE IF NOT EXISTS notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_email TEXT NOT NULL,
    turma_id INTEGER NOT NULL,
    aula_id INTEGER,
    nota REAL NOT NULL,
    peso REAL DEFAULT 1.0,
    descricao TEXT DEFAULT '',
    data_lancamento TEXT NOT NULL,
    professor_email TEXT NOT NULL,
    FOREIGN KEY (aluno_email) REFERENCES usuarios(email),
    FOREIGN KEY (turma_id) REFERENCES turmas(id),
    FOREIGN KEY (aula_id) REFERENCES aulas(id),
    FOREIGN KEY (professor_email) REFERENCES usuarios(email)
);
"""

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()

def query(sql, params=()):
    conn = get_connection()
    cur = conn.execute(sql, params)
    conn.commit()
    rows = cur.fetchall()
    conn.close()
    return rows

def query_one(sql, params=()):
    rows = query(sql, params)
    return dict(rows[0]) if rows else None

def execute(sql, params=()):
    conn = get_connection()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def fetch_all(sql, params=()):
    rows = query(sql, params)
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    print(f"Banco de dados criado em: {DB_PATH}")
