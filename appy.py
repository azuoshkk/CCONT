from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import check_password_hash
from functools import wraps
from cadastro import cadastro_bp

app = Flask(__name__)
app.secret_key = 'salamemingue'

app.register_blueprint(cadastro_bp)

def connect_db():
    conn = sqlite3.connect("studenty.db")
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != role:
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    matricula = request.form.get('matricula')
    senha = request.form.get('senha')

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE matricula = ?", (matricula,))
    user = cursor.fetchone()

    if user and check_password_hash(user['senha'], senha):
        session['user_id'] = user['id']
        session['user_nome'] = user['nome']
        
        cursor.execute("SELECT id FROM alunos WHERE id_usuario = ?", (user['id'],))
        if cursor.fetchone():
            session['role'] = 'aluno'
        else:
            cursor.execute("SELECT id FROM professores WHERE id_usuario = ?", (user['id'],))
            if cursor.fetchone():
                session['role'] = 'professor'
            else:
                session['role'] = 'admin'

        conn.close()
        return redirect(url_for('dashboard'))
    else:
        conn.close()
        flash("Matrícula ou senha incorretos.")
        return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    nome_usuario = session.get('user_nome')
    user_id = session.get('user_id')
    
    conn = connect_db()
    cursor = conn.cursor()
    
    if role == 'aluno':
        cursor.execute("SELECT id FROM alunos WHERE id_usuario = ?", (user_id,))
        aluno = cursor.fetchone()
        
        chamados = []
        cursos = []
        if aluno:
            cursor.execute("""
                SELECT c.id, c.titulo, c.status, c.data_criacao, m.nome as materia_nome
                FROM chamados c
                JOIN materias m ON c.id_materia = m.id
                WHERE c.id_aluno = ?
                ORDER BY c.data_criacao DESC
            """, (aluno['id'],))
            chamados = cursor.fetchall()

            cursor.execute("""
                SELECT m.nome as nome_materia, COALESCE(u.nome, 'A Definir') as nome_professor
                FROM matriculas mat
                JOIN materias m ON mat.id_materia = m.id
                LEFT JOIN professor_materias pm ON m.id = pm.id_materia
                LEFT JOIN professores p ON pm.id_professor = p.id
                LEFT JOIN usuarios u ON p.id_usuario = u.id
                WHERE mat.id_aluno = ?
            """, (aluno['id'],))
            cursos = cursor.fetchall()
            
        conn.close()
        return render_template('aluno.html', name=nome_usuario, chamados=chamados, cursos=cursos)
        
    elif role == 'professor':
        # 1. Pega o ID do professor logado
        cursor.execute("SELECT id FROM professores WHERE id_usuario = ?", (user_id,))
        prof = cursor.fetchone()
        prof_id = prof['id'] if prof else 0
        
        cursor.execute("""
            SELECT c.id, c.titulo, c.status, c.data_criacao, m.nome as materia_nome, u.nome as aluno_nome
            FROM chamados c
            JOIN materias m ON c.id_materia = m.id
            JOIN alunos a ON c.id_aluno = a.id
            JOIN usuarios u ON a.id_usuario = u.id
            JOIN professor_materias pm ON m.id = pm.id_materia
            WHERE pm.id_professor = ?
            ORDER BY c.data_criacao DESC
        """, (prof_id,))
        chamados = cursor.fetchall()

        stats = {'aberto': 0, 'em andamento': 0, 'aguardando': 0, 'finalizado': 0}
        for c in chamados:
            status_atual = c['status'].lower()
            if status_atual in stats:
                stats[status_atual] += 1
        
        conn.close()
        return render_template('professor.html', name=nome_usuario, chamados=chamados, stats=stats)
    elif role == 'admin':
        cursor.execute("""
            SELECT u.id, u.nome, u.matricula, u.email,
                   CASE 
                       WHEN p.id IS NOT NULL THEN 'professor'
                       WHEN a.id IS NOT NULL THEN 'admin'
                       ELSE 'aluno'
                   END as tipo
            FROM usuarios u
            LEFT JOIN professores p ON u.id = p.id_usuario
            LEFT JOIN admins a ON u.id = a.id_usuario
        """)
        usuarios = cursor.fetchall()

        cursor.execute("SELECT id FROM chamados")
        chamados = cursor.fetchall()

        cursor.execute("SELECT * FROM auditoria ORDER BY data_hora DESC LIMIT 10")
        auditoria = cursor.fetchall()

        conn.close()
        return render_template('admin.html', name=nome_usuario, usuarios=usuarios, chamados=chamados, auditoria=auditoria)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/abrir_chamado', methods=['GET', 'POST'])
@role_required('aluno')
def abrir_chamado():
    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        id_materia = request.form.get('id_materia')

        cursor.execute("SELECT id FROM alunos WHERE id_usuario = ?", (session['user_id'],))
        aluno = cursor.fetchone()

        if aluno and titulo and descricao and id_materia:
            cursor.execute("""
                INSERT INTO chamados (titulo, descricao_problema, id_aluno, id_materia)
                VALUES (?, ?, ?, ?)
            """, (titulo, descricao, aluno['id'], id_materia))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

    cursor.execute("""
        SELECT pm.id_materia as id, m.nome as materia_nome, u.nome as professor_nome
        FROM professor_materias pm
        JOIN materias m ON pm.id_materia = m.id
        JOIN professores p ON pm.id_professor = p.id
        JOIN usuarios u ON p.id_usuario = u.id
        ORDER BY u.nome ASC
    """)
    opcoes = cursor.fetchall()
    conn.close()

    return render_template('abrir_chamado.html', opcoes=opcoes)

@app.route('/visualizar_chamado/<int:chamado_id>')
@role_required('aluno')
def visualizar_chamado(chamado_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.*, m.nome as materia_nome
        FROM chamados c
        JOIN materias m ON c.id_materia = m.id
        WHERE c.id = ? AND c.id_aluno = (SELECT id FROM alunos WHERE id_usuario = ?)
    """, (chamado_id, session['user_id']))
    chamado = cursor.fetchone()

    if not chamado:
        conn.close()
        return redirect(url_for('dashboard'))

    cursor.execute("""
        SELECT mc.mensagem, mc.data_envio, u.nome, u.id as id_remetente
        FROM mensagens_chamado mc
        JOIN usuarios u ON mc.id_usuario = u.id
        WHERE mc.id_chamado = ? 
        ORDER BY mc.data_envio ASC
    """, (chamado_id,))
    mensagens = cursor.fetchall()
    conn.close()

    return render_template('ver_chamado.html', chamado=chamado, mensagens=mensagens, user_id=session['user_id'])

@app.route('/notificacoes')
@login_required
def notificacoes():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notificacoes WHERE id_usuario = ? ORDER BY data_criacao DESC", (session['user_id'],))
    lista_notificacoes = cursor.fetchall()

    cursor.execute("UPDATE notificacoes SET lida = 1 WHERE id_usuario = ?", (session['user_id'],))
    conn.commit()
    conn.close()

    return render_template('notificacoes.html', notificacoes=lista_notificacoes)

@app.route('/promover_professor/<int:usuario_id>', methods=['POST'])
@role_required('admin')
def promover_professor(usuario_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM alunos WHERE id_usuario = ?", (usuario_id,))
    aluno = cursor.fetchone()

    if aluno:
        cursor.execute("DELETE FROM alunos WHERE id_usuario = ?", (usuario_id,))
        cursor.execute("INSERT INTO professores (id_usuario, departamento, titulacao) VALUES (?, 'A Definir', 'A Definir')", (usuario_id,))
        
        cursor.execute("SELECT id FROM admins WHERE id_usuario = ?", (session['user_id'],))
        admin = cursor.fetchone()
        if admin:
            cursor.execute("INSERT INTO auditoria (id_admin, acao, tabela_afetada, id_registro_afetado, detalhe) VALUES (?, 'Promover', 'usuarios', ?, 'Promovido a Professor')", (admin['id'], usuario_id))
        
        conn.commit()

    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/enviar_mensagem/<int:chamado_id>', methods=['POST'])
@login_required
def enviar_mensagem(chamado_id):
    mensagem = request.form.get('mensagem')
    if mensagem:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mensagens_chamado (id_chamado, id_usuario, mensagem) VALUES (?, ?, ?)", (chamado_id, session['user_id'], mensagem))
        conn.commit()
        conn.close()
        
    if session.get('role') == 'aluno':
        return redirect(url_for('visualizar_chamado', chamado_id=chamado_id))
    return redirect(url_for('responder_chamado', chamado_id=chamado_id))

@app.route('/responder_chamado/<int:chamado_id>', methods=['GET', 'POST'])
@role_required('professor')
def responder_chamado(chamado_id):
    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        novo_status = request.form.get('status')
        retorno = request.form.get('retorno_tecnico')

        if novo_status:
            cursor.execute("""
                UPDATE chamados 
                SET status = ?, retorno_tecnico = ? 
                WHERE id = ?
            """, (novo_status, retorno, chamado_id))

            cursor.execute("SELECT id_usuario FROM alunos WHERE id = (SELECT id_aluno FROM chamados WHERE id = ?)", (chamado_id,))
            aluno_user = cursor.fetchone()
            if aluno_user:
                msg = f"Seu chamado #{chamado_id:03d} foi atualizado para: {novo_status.capitalize()}"
                cursor.execute("INSERT INTO notificacoes (id_usuario, mensagem) VALUES (?, ?)", (aluno_user['id_usuario'], msg))

            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

    cursor.execute("""
        SELECT c.*, m.nome as materia_nome, u.nome as aluno_nome 
        FROM chamados c
        JOIN materias m ON c.id_materia = m.id
        JOIN alunos a ON c.id_aluno = a.id
        JOIN usuarios u ON a.id_usuario = u.id
        WHERE c.id = ?
    """, (chamado_id,))
    chamado = cursor.fetchone()

    cursor.execute("""
        SELECT mc.mensagem, mc.data_envio, u.nome, u.id as id_remetente
        FROM mensagens_chamado mc
        JOIN usuarios u ON mc.id_usuario = u.id
        WHERE mc.id_chamado = ? 
        ORDER BY mc.data_envio ASC
    """, (chamado_id,))
    mensagens = cursor.fetchall()
    conn.close()

    return render_template('responder_chamado.html', chamado=chamado, mensagens=mensagens, user_id=session['user_id'])
    
@app.route('/nova_matricula', methods=['GET', 'POST'])
@role_required('aluno')
def nova_matricula():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM alunos WHERE id_usuario = ?", (session['user_id'],))
    aluno = cursor.fetchone()

    if request.method == 'POST':
        id_materia = request.form.get('id_materia')

        if aluno and id_materia:
            cursor.execute("SELECT * FROM matriculas WHERE id_aluno = ? AND id_materia = ?", (aluno['id'], id_materia))
            if cursor.fetchone():
                flash('Você já está matriculado nesta matéria.')
            else:
                cursor.execute("INSERT INTO matriculas (id_aluno, id_materia) VALUES (?, ?)", (aluno['id'], id_materia))
                conn.commit()
                conn.close()
                return redirect(url_for('dashboard'))

    cursor.execute("""
        SELECT m.id, m.nome as materia_nome, COALESCE(u.nome, 'Sem Professor') as professor_nome
        FROM materias m
        LEFT JOIN professor_materias pm ON m.id = pm.id_materia
        LEFT JOIN professores p ON pm.id_professor = p.id
        LEFT JOIN usuarios u ON p.id_usuario = u.id
        WHERE m.id NOT IN (SELECT id_materia FROM matriculas WHERE id_aluno = ?)
    """, (aluno['id'],))
    materias_disponiveis = cursor.fetchall()
    
    conn.close()
    return render_template('nova_matricula.html', materias=materias_disponiveis)

@app.route('/gerenciar_materias', methods=['GET', 'POST'])
@role_required('professor')
def gerenciar_materias():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM professores WHERE id_usuario = ?", (session['user_id'],))
    prof = cursor.fetchone()

    if request.method == 'POST':
        nova_materia = request.form.get('nova_materia')
        if nova_materia:
            cursor.execute("INSERT INTO materias (nome) VALUES (?)", (nova_materia,))
            materia_id = cursor.lastrowid
            cursor.execute("INSERT INTO professor_materias (id_professor, id_materia) VALUES (?, ?)", (prof['id'], materia_id))
            conn.commit()
            return redirect(url_for('gerenciar_materias'))

    cursor.execute("""
        SELECT m.nome 
        FROM professor_materias pm
        JOIN materias m ON pm.id_materia = m.id
        WHERE pm.id_professor = ?
    """, (prof['id'],))
    minhas_materias = cursor.fetchall()
    conn.close()

    return render_template('gerenciar_materias.html', materias=minhas_materias)

if __name__ == '__main__':
    app.run(debug=True)