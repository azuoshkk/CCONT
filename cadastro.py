from flask import Blueprint, request, render_template, redirect, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash

cadastro_bp = Blueprint('cadastro', __name__)

def connect_db():
    conn = sqlite3.connect("studenty.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            matricula TEXT UNIQUE,
            senha TEXT NOT NULL,
            data_nascimento DATE,
            email TEXT UNIQUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER UNIQUE,
            curso TEXT,
            ano_ingresso INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER UNIQUE,
            departamento TEXT,
            titulacao TEXT,
            criado_por INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER UNIQUE,
            nivel_acesso TEXT,
            ultimo_acesso TIMESTAMP,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            descricao TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_materias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_professor INTEGER,
            id_materia INTEGER,
            funcao TEXT,
            FOREIGN KEY(id_professor) REFERENCES professores(id),
            FOREIGN KEY(id_materia) REFERENCES materias(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            descricao_problema TEXT,
            retorno_tecnico TEXT,
            status TEXT DEFAULT 'aberto',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            id_aluno INTEGER,
            id_professor INTEGER,
            id_materia INTEGER,
            FOREIGN KEY(id_aluno) REFERENCES alunos(id),
            FOREIGN KEY(id_professor) REFERENCES professores(id),
            FOREIGN KEY(id_materia) REFERENCES materias(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_admin INTEGER,
            acao TEXT,
            tabela_afetada TEXT,
            id_registro_afetado INTEGER,
            detalhe TEXT,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_origem TEXT,
            FOREIGN KEY(id_admin) REFERENCES admins(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matriculas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aluno INTEGER,
            id_materia INTEGER,
            data_matricula TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_aluno) REFERENCES alunos(id),
            FOREIGN KEY(id_materia) REFERENCES materias(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            mensagem TEXT,
            lida INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        )
    """)
    
    conn.commit()
    conn.close()

create_db()

@cadastro_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('cadastrar.html')
        
    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        matricula = request.form.get('matricula')
        email = request.form.get('email')

        if not all([nome, senha, confirmar_senha, matricula, email]):
            flash("Todos os campos são obrigatórios.")
            return redirect(url_for('cadastro.register'))

        if senha != confirmar_senha:
            flash("As senhas não coincidem. Tente novamente.")
            return redirect(url_for('cadastro.register'))

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id FROM usuarios WHERE matricula = ? OR email = ?", (matricula, email))
            if cursor.fetchone():
                flash("Erro: Matrícula ou E-mail já estão cadastrados no sistema.")
                return redirect(url_for('cadastro.register'))
                
            hashed_password = generate_password_hash(senha)
            
            cursor.execute("""
                INSERT INTO usuarios (nome, matricula, email, senha) 
                VALUES (?, ?, ?, ?)
            """, (nome.upper(), matricula, email, hashed_password))
            
            id_novo_usuario = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO alunos (id_usuario) 
                VALUES (?)
            """, (id_novo_usuario,))
            
            conn.commit()
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError:
            flash("Email ou matrícula já cadastrados!")
            return redirect(url_for('cadastro.register'))
        finally:
            conn.close()