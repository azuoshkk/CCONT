from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import check_password_hash
from cadastro import cadastro_bp

app = Flask(__name__)
app.secret_key = 'salamemingue'

app.register_blueprint(cadastro_bp)

def connect_db():
    conn = sqlite3.connect("studenty.db")
    conn.row_factory = sqlite3.Row
    return conn

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
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    role = session.get('role')
    nome_usuario = session.get('user_nome')
    
    if role == 'aluno':
        return render_template('aluno.html', name=nome_usuario)
    elif role == 'professor':
        return render_template('professor.html', name=nome_usuario)
    else:
        return "Painel de Admin em desenvolvimento."

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)