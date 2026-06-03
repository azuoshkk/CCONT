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
    
    conn.commit()
    conn.close()

create_db()

@cadastro_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('cadastrar.html')
        
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        if not matricula or not nome or not email or not senha:
            flash("Todos os campos são obrigatórios.")
            return redirect(url_for('cadastro.register'))
            
        hashed_password = generate_password_hash(senha)
        
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
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
            conn.close()
            
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError:
            flash("Email ou matrícula já cadastrados!")
            return redirect(url_for('cadastro.register'))