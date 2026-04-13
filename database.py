"""
database.py — Módulo de acesso ao banco de dados SQLite do BibSSJ
Todas as operações de leitura e escrita passam por aqui.
O banco fica em data/bibssj.db, criado automaticamente na primeira execução.
"""

import sqlite3
import hashlib
import os
from datetime import date, datetime, timedelta
import pandas as pd

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────
DB_DIR  = "data"
DB_PATH = os.path.join(DB_DIR, "bibssj.db")
MULTA_DIA = 2.00  # R$ por dia de atraso


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão com row_factory configurada para dict-like access."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─────────────────────────────────────────────
# DDL — CRIAÇÃO DAS TABELAS
# ─────────────────────────────────────────────
def init_db():
    """Cria todas as tabelas (se não existirem) e popula com seed."""
    conn = get_connection()
    cur  = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS livros (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo           TEXT    NOT NULL,
            autor            TEXT    NOT NULL,
            isbn             TEXT,
            editora          TEXT,
            ano_publicacao   INTEGER,
            categoria        TEXT,
            idioma           TEXT    DEFAULT 'Português',
            edicao           TEXT,
            localizacao      TEXT,
            qtd_exemplares   INTEGER NOT NULL DEFAULT 1,
            qtd_disponivel   INTEGER NOT NULL DEFAULT 1,
            criado_em        TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nome                TEXT    NOT NULL,
            cpf                 TEXT    UNIQUE NOT NULL,
            data_nascimento     TEXT,
            endereco            TEXT,
            email               TEXT    UNIQUE NOT NULL,
            categoria           TEXT    NOT NULL DEFAULT 'Aluno',
            limite_emprestimos  INTEGER NOT NULL DEFAULT 3,
            observacoes         TEXT,
            status              TEXT    NOT NULL DEFAULT 'Regular',
            criado_em           TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS emprestimos (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id              INTEGER NOT NULL REFERENCES usuarios(id),
            livro_id                INTEGER NOT NULL REFERENCES livros(id),
            data_retirada           TEXT    NOT NULL,
            data_devolucao_prevista TEXT    NOT NULL,
            data_devolucao_real     TEXT,
            status                  TEXT    NOT NULL DEFAULT 'Ativo',
            renovacoes              INTEGER NOT NULL DEFAULT 0,
            observacoes             TEXT,
            criado_em               TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS multas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            emprestimo_id    INTEGER NOT NULL REFERENCES emprestimos(id),
            usuario_id       INTEGER NOT NULL REFERENCES usuarios(id),
            valor            REAL    NOT NULL,
            dias_atraso      INTEGER NOT NULL,
            status_pagamento TEXT    NOT NULL DEFAULT 'Pendente',
            data_pagamento   TEXT,
            forma_pagamento  TEXT,
            observacoes      TEXT,
            criado_em        TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS administradores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            senha_hash  TEXT    NOT NULL,
            perfil      TEXT    NOT NULL DEFAULT 'Operador',
            ativo       INTEGER NOT NULL DEFAULT 1,
            criado_em   TEXT    DEFAULT (datetime('now','localtime'))
        );
    """)

    conn.commit()
    conn.close()
    _seed()


# ─────────────────────────────────────────────
# SEED — DADOS INICIAIS (só roda se as tabelas estiverem vazias)
# ─────────────────────────────────────────────
def _seed():
    conn = get_connection()
    cur  = conn.cursor()

    # ── Livros ──
    if cur.execute("SELECT COUNT(*) FROM livros").fetchone()[0] == 0:
        livros = [
            ("Algoritmos: Teoria e Prática", "Cormen et al.",      "978-8535236996", "Campus",    2012, "Computação",      "Português", "3ª", "A-01", 5, 3),
            ("Clean Code",                   "Robert C. Martin",   "978-0132350884", "Prentice",  2008, "Computação",      "Inglês",    "1ª", "A-02", 3, 0),
            ("O Processo",                   "Franz Kafka",        "978-8535922035", "Companhia", 2005, "Literatura",      "Português", "1ª", "B-01", 4, 2),
            ("Cálculo Vol. 1",               "James Stewart",      "978-8522108091", "Cengage",   2013, "Matemática",      "Português", "7ª", "C-01", 8, 5),
            ("Banco de Dados Relacional",    "Abraham Silberschatz","978-8521622994","McGraw",    2019, "Computação",      "Português", "7ª", "A-03", 4, 1),
            ("Sociologia Moderna",           "Anthony Giddens",    "978-8520009480", "Zahar",     2012, "Ciências Sociais","Português", "4ª", "D-01", 3, 3),
            ("Estrutura e Interpretação",    "Abelson & Sussman",  "978-0262510875", "MIT Press", 1996, "Computação",      "Inglês",    "2ª", "A-04", 2, 2),
            ("Física para Engenharia Vol. 2","Hayt & Buck",        "978-8580550375", "McGraw",    2013, "Engenharia",      "Português", "8ª", "E-01", 6, 4),
        ]
        cur.executemany(
            "INSERT INTO livros (titulo,autor,isbn,editora,ano_publicacao,categoria,idioma,edicao,localizacao,qtd_exemplares,qtd_disponivel) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            livros,
        )

    # ── Usuários ──
    if cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        usuarios = [
            ("Ana Beatriz Costa",   "123.456.789-00", "2001-05-10", "Rua A, 100", "ana.costa@univ.edu.br",    "Aluno",     3, "",  "Regular"),
            ("Carlos Eduardo Lima", "987.654.321-00", "1980-03-22", "Rua B, 200", "carlos.lima@univ.edu.br",  "Professor", 5, "",  "Regular"),
            ("Fernanda Oliveira",   "111.222.333-44", "2002-11-15", "Rua C, 300", "f.oliveira@univ.edu.br",   "Aluno",     3, "",  "Inadimplente"),
            ("Pedro Henrique Souza","555.666.777-88", "2000-07-08", "Rua D, 400", "p.souza@univ.edu.br",      "Aluno",     3, "",  "Regular"),
            ("Prof. Marcelo Tavares","999.888.777-66","1975-01-30", "Rua E, 500", "m.tavares@univ.edu.br",    "Professor", 5, "",  "Regular"),
            ("Juliana Martins",     "444.333.222-11", "2003-09-20", "Rua F, 600", "j.martins@univ.edu.br",    "Aluno",     3, "",  "Suspenso"),
        ]
        cur.executemany(
            "INSERT INTO usuarios (nome,cpf,data_nascimento,endereco,email,categoria,limite_emprestimos,observacoes,status) VALUES (?,?,?,?,?,?,?,?,?)",
            usuarios,
        )

    # ── Administradores ──
    if cur.execute("SELECT COUNT(*) FROM administradores").fetchone()[0] == 0:
        admins = [
            ("João da Silva",   "joao.silva@bibssj.edu.br",   _hash("admin123"), "Super Admin", 1),
            ("Maria Fernandes", "m.fernandes@bibssj.edu.br",  _hash("biblio"),   "Bibliotecária", 1),
            ("Rafael Correia",  "r.correia@bibssj.edu.br",    _hash("oper123"),  "Operador",    1),
        ]
        cur.executemany(
            "INSERT INTO administradores (nome,email,senha_hash,perfil,ativo) VALUES (?,?,?,?,?)",
            admins,
        )

    # ── Empréstimos ──
    if cur.execute("SELECT COUNT(*) FROM emprestimos").fetchone()[0] == 0:
        hoje = date.today()
        emprestimos = [
            (1, 1, str(hoje - timedelta(days=4)),  str(hoje + timedelta(days=3)),  None, "Ativo",    0, ""),
            (2, 2, str(hoje - timedelta(days=10)), str(hoje + timedelta(days=4)),  None, "Ativo",    0, ""),
            (3, 4, str(hoje - timedelta(days=14)), str(hoje - timedelta(days=7)),  None, "Atrasado", 0, ""),
            (1, 5, str(hoje - timedelta(days=2)),  str(hoje + timedelta(days=5)),  None, "Ativo",    0, ""),
            (5, 8, str(hoje - timedelta(days=8)),  str(hoje + timedelta(days=6)),  None, "Ativo",    0, ""),
            (4, 3, str(hoje - timedelta(days=3)),  str(hoje + timedelta(days=4)),  None, "Ativo",    0, ""),
            (5, 6, str(hoje - timedelta(days=6)),  str(hoje - timedelta(days=2)),  None, "Atrasado", 0, ""),
        ]
        cur.executemany(
            "INSERT INTO emprestimos (usuario_id,livro_id,data_retirada,data_devolucao_prevista,data_devolucao_real,status,renovacoes,observacoes) VALUES (?,?,?,?,?,?,?,?)",
            emprestimos,
        )

    # ── Multas ──
    if cur.execute("SELECT COUNT(*) FROM multas").fetchone()[0] == 0:
        multas = [
            (3, 3, 14.00, 7,  "Pendente", None,         None,    ""),
            (7, 5,  4.00, 2,  "Pendente", None,         None,    ""),
            (0, 6, 24.00, 12, "Pago",     str(date.today() - timedelta(days=5)), "PIX", ""),
            # multa 3 é histórica (emprestimo_id fictício 0 para seed)
        ]
        # Ajusta: insere apenas as que têm emprestimo_id real
        cur.execute(
            "INSERT INTO multas (emprestimo_id,usuario_id,valor,dias_atraso,status_pagamento,data_pagamento,forma_pagamento,observacoes) VALUES (3,3,14.00,7,'Pendente',NULL,NULL,'')"
        )
        cur.execute(
            "INSERT INTO multas (emprestimo_id,usuario_id,valor,dias_atraso,status_pagamento,data_pagamento,forma_pagamento,observacoes) VALUES (7,5,4.00,2,'Pendente',NULL,NULL,'')"
        )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────
def autenticar(email: str, senha: str) -> dict | None:
    """Retorna dict do admin se credenciais corretas, None caso contrário."""
    conn = get_connection()
    row  = conn.execute(
        "SELECT id, nome, perfil FROM administradores WHERE email=? AND senha_hash=? AND ativo=1",
        (email.strip(), _hash(senha)),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─────────────────────────────────────────────
# LIVROS
# ─────────────────────────────────────────────
def get_livros(busca: str = "", categoria: str = "Todas") -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT id AS 'ID', titulo AS 'Título', autor AS 'Autor', isbn AS 'ISBN',
               categoria AS 'Categoria', qtd_exemplares AS 'Exemplares',
               qtd_disponivel AS 'Disponíveis',
               CASE WHEN qtd_disponivel > 0 THEN 'Disponível' ELSE 'Indisponível' END AS 'Status'
        FROM livros WHERE 1=1
    """
    params = []
    if busca:
        query += " AND (titulo LIKE ? OR autor LIKE ? OR isbn LIKE ?)"
        like = f"%{busca}%"
        params += [like, like, like]
    if categoria and categoria != "Todas":
        query += " AND categoria = ?"
        params.append(categoria)
    query += " ORDER BY titulo"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_categorias() -> list[str]:
    conn  = get_connection()
    rows  = conn.execute("SELECT DISTINCT categoria FROM livros ORDER BY categoria").fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]


def insert_livro(titulo, autor, isbn, editora, ano, categoria, idioma, edicao, localizacao, qtd) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO livros (titulo,autor,isbn,editora,ano_publicacao,categoria,idioma,edicao,localizacao,qtd_exemplares,qtd_disponivel) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (titulo, autor, isbn, editora, ano, categoria, idioma, edicao, localizacao, qtd, qtd),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_livros_disponiveis() -> list[dict]:
    conn  = get_connection()
    rows  = conn.execute(
        "SELECT id, titulo FROM livros WHERE qtd_disponivel > 0 ORDER BY titulo"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# USUÁRIOS
# ─────────────────────────────────────────────
def get_usuarios(busca: str = "", categoria: str = "Todos") -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT u.id AS 'ID', u.nome AS 'Nome', u.cpf AS 'CPF', u.email AS 'E-mail',
               u.categoria AS 'Categoria', u.limite_emprestimos AS 'Limite',
               COUNT(e.id) AS 'Empréstimos Ativos', u.status AS 'Status'
        FROM usuarios u
        LEFT JOIN emprestimos e ON e.usuario_id = u.id AND e.status IN ('Ativo','Atrasado')
        WHERE 1=1
    """
    params = []
    if busca:
        query += " AND (u.nome LIKE ? OR u.cpf LIKE ? OR u.email LIKE ?)"
        like = f"%{busca}%"
        params += [like, like, like]
    if categoria and categoria != "Todos":
        query += " AND u.categoria = ?"
        params.append(categoria)
    query += " GROUP BY u.id ORDER BY u.nome"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_usuarios_ativos() -> list[dict]:
    """Lista para selectbox de empréstimos (apenas não suspensos)."""
    conn  = get_connection()
    rows  = conn.execute(
        "SELECT id, nome, categoria FROM usuarios WHERE status != 'Suspenso' ORDER BY nome"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_usuario(nome, cpf, nasc, endereco, email, categoria, limite, obs) -> tuple[bool, str]:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO usuarios (nome,cpf,data_nascimento,endereco,email,categoria,limite_emprestimos,observacoes) VALUES (?,?,?,?,?,?,?,?)",
            (nome, cpf, str(nasc), endereco, email, categoria, limite, obs),
        )
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError as e:
        msg = "CPF já cadastrado." if "cpf" in str(e) else "E-mail já cadastrado."
        return False, msg


def update_usuario_status(usuario_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE usuarios SET status=? WHERE id=?", (status, usuario_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# EMPRÉSTIMOS
# ─────────────────────────────────────────────
def get_emprestimos(apenas_ativos: bool = False) -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT e.id AS 'ID',
               u.nome AS 'Usuário',
               l.titulo AS 'Livro',
               e.data_retirada AS 'Retirada',
               e.data_devolucao_prevista AS 'Devolução Prevista',
               e.status AS 'Status'
        FROM emprestimos e
        JOIN usuarios u ON u.id = e.usuario_id
        JOIN livros   l ON l.id = e.livro_id
    """
    if apenas_ativos:
        query += " WHERE e.status IN ('Ativo','Atrasado')"
    query += " ORDER BY e.data_devolucao_prevista"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_emprestimos_ativos_lista() -> list[dict]:
    """Retorna lista de empréstimos ativos para selectbox de devolução."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT e.id, u.nome, l.titulo, e.data_devolucao_prevista
        FROM emprestimos e
        JOIN usuarios u ON u.id = e.usuario_id
        JOIN livros   l ON l.id = e.livro_id
        WHERE e.status IN ('Ativo','Atrasado')
        ORDER BY e.data_devolucao_prevista
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_usuarios_com_emprestimo(busca: str) -> list[dict]:
    """Retorna usuários que possuem empréstimos ativos e cujo nome contém 'busca'."""
    conn  = get_connection()
    like  = f"%{busca}%"
    rows  = conn.execute("""
        SELECT DISTINCT u.id, u.nome, u.categoria,
               COUNT(e.id) AS total_ativos
        FROM usuarios u
        JOIN emprestimos e ON e.usuario_id = u.id
        WHERE e.status IN ('Ativo','Atrasado')
          AND u.nome LIKE ?
        GROUP BY u.id
        ORDER BY u.nome
    """, (like,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_emprestimos_ativos_por_usuario(usuario_id: int) -> list[dict]:
    """Retorna todos os empréstimos ativos de um usuário com detalhes completos."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT e.id,
               l.titulo,
               l.autor,
               l.localizacao,
               e.data_retirada,
               e.data_devolucao_prevista,
               e.status,
               e.renovacoes,
               CAST(julianday('now','localtime') - julianday(e.data_devolucao_prevista) AS INTEGER) AS dias_atraso_atual
        FROM emprestimos e
        JOIN livros l ON l.id = e.livro_id
        WHERE e.usuario_id = ?
          AND e.status IN ('Ativo','Atrasado')
        ORDER BY e.data_devolucao_prevista
    """, (usuario_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_emprestimo(usuario_id: int, livro_id: int,
                      data_retirada: date, data_prevista: date, obs: str) -> tuple[bool, str]:
    """Registra empréstimo e decrementa qtd_disponivel."""
    try:
        conn = get_connection()
        # Verifica disponibilidade
        disp = conn.execute(
            "SELECT qtd_disponivel FROM livros WHERE id=?", (livro_id,)
        ).fetchone()[0]
        if disp <= 0:
            conn.close()
            return False, "Nenhum exemplar disponível."

        # Verifica limite do usuário
        ativos = conn.execute(
            "SELECT COUNT(*) FROM emprestimos WHERE usuario_id=? AND status IN ('Ativo','Atrasado')",
            (usuario_id,),
        ).fetchone()[0]
        limite = conn.execute(
            "SELECT limite_emprestimos FROM usuarios WHERE id=?", (usuario_id,)
        ).fetchone()[0]
        if ativos >= limite:
            conn.close()
            return False, f"Usuário atingiu o limite de {limite} empréstimos ativos."

        conn.execute(
            "INSERT INTO emprestimos (usuario_id,livro_id,data_retirada,data_devolucao_prevista,status,observacoes) VALUES (?,?,?,?,?,?)",
            (usuario_id, livro_id, str(data_retirada), str(data_prevista), "Ativo", obs),
        )
        conn.execute(
            "UPDATE livros SET qtd_disponivel = qtd_disponivel - 1 WHERE id=?", (livro_id,)
        )
        conn.commit()
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e)


def registrar_devolucao(emprestimo_id: int, data_real: date) -> dict:
    """
    Finaliza empréstimo, incrementa qtd_disponivel e gera multa se houver atraso.
    Retorna {'sucesso': bool, 'multa': float, 'dias_atraso': int}.
    """
    conn = get_connection()
    emp  = conn.execute(
        "SELECT livro_id, usuario_id, data_devolucao_prevista FROM emprestimos WHERE id=?",
        (emprestimo_id,),
    ).fetchone()

    data_prevista = date.fromisoformat(emp["data_devolucao_prevista"])
    dias_atraso   = max(0, (data_real - data_prevista).days)
    multa         = round(dias_atraso * MULTA_DIA, 2)
    novo_status   = "Devolvido"

    conn.execute(
        "UPDATE emprestimos SET data_devolucao_real=?, status=? WHERE id=?",
        (str(data_real), novo_status, emprestimo_id),
    )
    conn.execute(
        "UPDATE livros SET qtd_disponivel = qtd_disponivel + 1 WHERE id=?",
        (emp["livro_id"],),
    )

    if multa > 0:
        conn.execute(
            "INSERT INTO multas (emprestimo_id,usuario_id,valor,dias_atraso,status_pagamento) VALUES (?,?,?,?,?)",
            (emprestimo_id, emp["usuario_id"], multa, dias_atraso, "Pendente"),
        )
        # Marca usuário como inadimplente se atraso > 5 dias
        if dias_atraso > 5:
            conn.execute(
                "UPDATE usuarios SET status='Inadimplente' WHERE id=? AND status='Regular'",
                (emp["usuario_id"],),
            )

    conn.commit()
    conn.close()
    return {"sucesso": True, "multa": multa, "dias_atraso": dias_atraso}


def sincronizar_atrasos():
    """Marca como 'Atrasado' empréstimos que passaram da data prevista."""
    conn = get_connection()
    conn.execute(
        "UPDATE emprestimos SET status='Atrasado' WHERE status='Ativo' AND data_devolucao_prevista < date('now','localtime')"
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# MULTAS / FINANCEIRO
# ─────────────────────────────────────────────
def get_multas() -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT m.id AS 'ID',
               u.nome AS 'Usuário',
               l.titulo AS 'Livro',
               m.dias_atraso AS 'Dias de Atraso',
               m.valor AS 'Multa (R$)',
               m.status_pagamento AS 'Status Pagamento'
        FROM multas m
        JOIN usuarios   u ON u.id = m.usuario_id
        JOIN emprestimos e ON e.id = m.emprestimo_id
        JOIN livros      l ON l.id = e.livro_id
        ORDER BY m.status_pagamento DESC, m.criado_em DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_multas_pendentes_lista() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.id, u.nome, m.valor
        FROM multas m
        JOIN usuarios u ON u.id = m.usuario_id
        WHERE m.status_pagamento = 'Pendente'
        ORDER BY u.nome
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def confirmar_pagamento(multa_id: int, forma: str, obs: str) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE multas SET status_pagamento='Pago', data_pagamento=date('now','localtime'), forma_pagamento=?, observacoes=? WHERE id=?",
            (forma, obs, multa_id),
        )
        # Reavalia se o usuário ainda tem multas pendentes
        usuario_id = conn.execute(
            "SELECT usuario_id FROM multas WHERE id=?", (multa_id,)
        ).fetchone()[0]
        pendentes = conn.execute(
            "SELECT COUNT(*) FROM multas WHERE usuario_id=? AND status_pagamento='Pendente'",
            (usuario_id,),
        ).fetchone()[0]
        if pendentes == 0:
            conn.execute(
                "UPDATE usuarios SET status='Regular' WHERE id=? AND status='Inadimplente'",
                (usuario_id,),
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# ADMINISTRADORES
# ─────────────────────────────────────────────
def get_administradores() -> list[dict]:
    conn  = get_connection()
    rows  = conn.execute(
        "SELECT id, nome, email, perfil, ativo FROM administradores ORDER BY nome"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_administrador(nome: str, email: str, senha: str, perfil: str) -> tuple[bool, str]:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO administradores (nome,email,senha_hash,perfil) VALUES (?,?,?,?)",
            (nome, email, _hash(senha), perfil),
        )
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        return False, "E-mail já cadastrado."


def atualizar_senha_administrador(admin_id: int, nova_senha: str) -> tuple[bool, str]:
    """Atualiza a senha de um administrador."""
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE administradores SET senha_hash = ? WHERE id = ?",
            (_hash(nova_senha), admin_id),
        )
        conn.commit()
        conn.close()
        return True, "Senha atualizada com sucesso."
    except Exception as e:
        return False, f"Erro ao atualizar senha: {str(e)}"


# ─────────────────────────────────────────────
# DASHBOARD — ESTATÍSTICAS
# ─────────────────────────────────────────────
def get_stats() -> dict:
    conn  = get_connection()
    stats = {}

    stats["total_exemplares"]  = conn.execute("SELECT COALESCE(SUM(qtd_exemplares),0) FROM livros").fetchone()[0]
    stats["total_usuarios"]    = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    stats["emprestimos_ativos"]= conn.execute("SELECT COUNT(*) FROM emprestimos WHERE status IN ('Ativo','Atrasado')").fetchone()[0]
    stats["atrasados"]         = conn.execute("SELECT COUNT(*) FROM emprestimos WHERE status='Atrasado'").fetchone()[0]
    stats["inadimplentes"]     = conn.execute("SELECT COUNT(*) FROM usuarios WHERE status='Inadimplente'").fetchone()[0]
    stats["multas_pendentes"]  = conn.execute("SELECT COALESCE(SUM(valor),0) FROM multas WHERE status_pagamento='Pendente'").fetchone()[0]
    stats["multas_recebidas"]  = conn.execute("SELECT COALESCE(SUM(valor),0) FROM multas WHERE status_pagamento='Pago'").fetchone()[0]

    # Livros mais emprestados
    top = conn.execute("""
        SELECT l.titulo, COUNT(e.id) AS total
        FROM emprestimos e JOIN livros l ON l.id = e.livro_id
        GROUP BY l.id ORDER BY total DESC LIMIT 4
    """).fetchall()
    stats["top_livros"] = [dict(r) for r in top]

    # Acervo por categoria
    cats = conn.execute(
        "SELECT categoria, SUM(qtd_exemplares) AS total FROM livros GROUP BY categoria ORDER BY total DESC"
    ).fetchall()
    stats["categorias"] = [dict(r) for r in cats]

    # Totais para resumo admin
    stats["total_titulos"]       = conn.execute("SELECT COUNT(*) FROM livros").fetchone()[0]
    stats["total_disponiveis"]   = conn.execute("SELECT COALESCE(SUM(qtd_disponivel),0) FROM livros").fetchone()[0]
    stats["usuarios_ativos"]     = conn.execute("SELECT COUNT(*) FROM usuarios WHERE status != 'Suspenso'").fetchone()[0]
    stats["devolucoes_atrasadas"]= stats["atrasados"]

    conn.close()
    return stats


def get_livros_paginado(busca: str = "", categoria: str = "Todas",
                        limit: int = 20, offset: int = 0) -> pd.DataFrame:
    conn   = get_connection()
    cond   = "WHERE 1=1"
    params: list = []
    if busca:
        cond  += " AND (titulo LIKE ? OR autor LIKE ? OR isbn LIKE ?)"
        like   = f"%{busca}%"
        params += [like, like, like]
    if categoria and categoria != "Todas":
        cond  += " AND categoria = ?"
        params.append(categoria)
    query = f"""
        SELECT id AS 'ID', titulo AS 'Título', autor AS 'Autor', isbn AS 'ISBN',
               categoria AS 'Categoria', ano_publicacao AS 'Ano',
               qtd_exemplares AS 'Exemplares', qtd_disponivel AS 'Disponíveis',
               CASE WHEN qtd_disponivel > 0 THEN 'Disponível' ELSE 'Indisponível' END AS 'Status'
        FROM livros {cond} ORDER BY titulo LIMIT ? OFFSET ?
    """
    df = pd.read_sql_query(query, conn, params=params + [limit, offset])
    conn.close()
    return df


def count_livros(busca: str = "", categoria: str = "Todas") -> int:
    conn   = get_connection()
    cond   = "WHERE 1=1"
    params: list = []
    if busca:
        cond  += " AND (titulo LIKE ? OR autor LIKE ? OR isbn LIKE ?)"
        like   = f"%{busca}%"
        params += [like, like, like]
    if categoria and categoria != "Todas":
        cond  += " AND categoria = ?"
        params.append(categoria)
    total = conn.execute(f"SELECT COUNT(*) FROM livros {cond}", params).fetchone()[0]
    conn.close()
    return total


def get_acervo_stats() -> dict:
    """Totais rápidos para o header do acervo."""
    conn = get_connection()
    r = conn.execute("""
        SELECT COUNT(*)                         AS titulos,
               COALESCE(SUM(qtd_exemplares), 0) AS exemplares,
               COALESCE(SUM(qtd_disponivel), 0) AS disponiveis
        FROM livros
    """).fetchone()
    conn.close()
    return {"titulos": r[0], "exemplares": r[1], "disponiveis": r[2]}

def get_livro_por_id(livro_id: int) -> dict | None:
    """Retorna todos os campos de um livro pelo ID."""
    conn = get_connection()
    row  = conn.execute("SELECT * FROM livros WHERE id = ?", (livro_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_livro(livro_id: int, titulo: str, autor: str, isbn: str,
                 editora: str, ano: int, categoria: str, idioma: str,
                 edicao: str, localizacao: str, qtd_exemplares: int) -> tuple[bool, str]:
    try:
        conn  = get_connection()
        atual = conn.execute(
            "SELECT qtd_exemplares, qtd_disponivel FROM livros WHERE id = ?",
            (livro_id,)
        ).fetchone()
        if not atual:
            conn.close()
            return False, "Livro não encontrado."

        em_uso          = atual["qtd_exemplares"] - atual["qtd_disponivel"]
        novo_disponivel = max(0, qtd_exemplares - em_uso)

        conn.execute("""
            UPDATE livros SET
                titulo         = ?,
                autor          = ?,
                isbn           = ?,
                editora        = ?,
                ano_publicacao = ?,
                categoria      = ?,
                idioma         = ?,
                edicao         = ?,
                localizacao    = ?,
                qtd_exemplares = ?,
                qtd_disponivel = ?
            WHERE id = ?
        """, (titulo, autor, isbn, editora, ano, categoria, idioma,
              edicao, localizacao, qtd_exemplares, novo_disponivel, livro_id))
        conn.commit()
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e)

def sincronizar_multas():
    """
    Atualiza valores e dias de atraso de multas pendentes baseado nos empréstimos atrasados.
    Recalcula multa = dias_atraso * MULTA_DIA para cada multa pendente.
    """
    conn = get_connection()
    cur  = conn.cursor()
    
    # Busca todas as multas pendentes com seus empréstimos
    multas_pendentes = cur.execute("""
        SELECT m.id, e.data_devolucao_prevista, m.usuario_id
        FROM multas m
        JOIN emprestimos e ON e.id = m.emprestimo_id
        WHERE m.status_pagamento = 'Pendente'
    """).fetchall()
    
    hoje = date.today()
    
    for multa in multas_pendentes:
        multa_id = multa["id"]
        data_prevista = date.fromisoformat(multa["data_devolucao_prevista"])
        usuario_id = multa["usuario_id"]
        
        # Calcula dias de atraso atual
        dias_atraso = max(0, (hoje - data_prevista).days)
        novo_valor = round(dias_atraso * MULTA_DIA, 2)
        
        # Atualiza multa
        cur.execute("""
            UPDATE multas 
            SET dias_atraso = ?, valor = ?
            WHERE id = ?
        """, (dias_atraso, novo_valor, multa_id))
        
        # Se atraso > 5 dias e usuário não é inadimplente, marca como tal
        if dias_atraso > 5:
            cur.execute("""
                UPDATE usuarios 
                SET status = 'Inadimplente' 
                WHERE id = ? AND status = 'Regular'
            """, (usuario_id,))
    
    conn.commit()
    conn.close()