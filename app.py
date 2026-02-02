from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from datetime import datetime, date, timedelta
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'satisfacao_admin_secret_2026'

# Usar SQLite localmente ou PostgreSQL no cloud
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_TYPE = 'postgres'
else:
    DATABASE = 'satisfacao.db'
    DB_TYPE = 'sqlite'

def init_db():
    """Inicializar base de dados"""
    if DB_TYPE == 'sqlite':
        if not os.path.exists(DATABASE):
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS avaliacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo INTEGER NOT NULL,
                    avaliacao_date DATE NOT NULL,
                    avaliacao_time TIME NOT NULL,
                    sequential_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
    else:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS avaliacoes (
                    id SERIAL PRIMARY KEY,
                    tipo INTEGER NOT NULL,
                    avaliacao_date DATE NOT NULL,
                    avaliacao_time TIME NOT NULL,
                    sequential_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao criar tabela: {e}")

def get_db():
    """Obter conexão com base de dados"""
    if DB_TYPE == 'sqlite':
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
    else:
        conn = psycopg2.connect(DATABASE_URL)
    return conn

def get_sequential_number(tipo):
    """Obter número sequencial global para hoje (não por tipo)"""
    today = date.today().isoformat()
    conn = get_db()
    
    if DB_TYPE == 'sqlite':
        cursor = conn.cursor()
        cursor.execute('''
            SELECT MAX(sequential_number) as max_seq 
            FROM avaliacoes 
            WHERE avaliacao_date = ?
        ''', (today,))
        result = cursor.fetchone()
        max_seq = result['max_seq'] if result['max_seq'] else 0
    else:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT MAX(sequential_number) as max_seq 
            FROM avaliacoes 
            WHERE avaliacao_date = %s
        ''', (today,))
        result = cursor.fetchone()
        max_seq = result[0] if result[0] else 0
    
    conn.close()
    return max_seq + 1

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard de estatísticas"""
    return render_template('dashboard.html')

@app.route('/api/avaliar', methods=['POST'])
def registar_avaliacao():
    """Registar avaliação"""
    try:
        data = request.json
        tipo = data.get('tipo')
        
        if not tipo or tipo not in [1, 2, 3]:
            return jsonify({'error': 'Tipo de avaliação inválido'}), 400
        
        now = datetime.now()
        avaliacao_date = now.date().isoformat()
        avaliacao_time = now.strftime('%H:%M')
        sequential_number = get_sequential_number(tipo)
        
        conn = get_db()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                INSERT INTO avaliacoes (tipo, avaliacao_date, avaliacao_time, sequential_number)
                VALUES (?, ?, ?, ?)
            ''', (tipo, avaliacao_date, avaliacao_time, sequential_number))
        else:
            cursor.execute('''
                INSERT INTO avaliacoes (tipo, avaliacao_date, avaliacao_time, sequential_number)
                VALUES (%s, %s, %s, %s)
            ''', (tipo, avaliacao_date, avaliacao_time, sequential_number))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'sequential_number': sequential_number,
            'date': avaliacao_date,
            'time': avaliacao_time
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/avaliacoes', methods=['GET'])
def get_avaliacoes():
    """Obter avaliações de hoje"""
    try:
        today = date.today().isoformat()
        conn = get_db()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                SELECT tipo, sequential_number, avaliacao_date, avaliacao_time
                FROM avaliacoes
                WHERE avaliacao_date = ?
                ORDER BY id DESC
                LIMIT 100
            ''', (today,))
            avaliacoes = cursor.fetchall()
            result = [dict(row) for row in avaliacoes]
        else:
            cursor.execute('''
                SELECT tipo, sequential_number, avaliacao_date, avaliacao_time
                FROM avaliacoes
                WHERE avaliacao_date = %s
                ORDER BY id DESC
                LIMIT 100
            ''', (today,))
            avaliacoes = cursor.fetchall()
            result = [{'tipo': row[0], 'sequential_number': row[1], 'avaliacao_date': row[2], 'avaliacao_time': row[3]} for row in avaliacoes]
        
        conn.close()
        return jsonify({'avaliacoes': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obter estatísticas"""
    try:
        today = date.today().isoformat()
        conn = get_db()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                SELECT tipo, MAX(sequential_number) as total
                FROM avaliacoes
                WHERE avaliacao_date = ?
                GROUP BY tipo
            ''', (today,))
            stats = cursor.fetchall()
            result = {1: 0, 2: 0, 3: 0}
            for row in stats:
                result[row['tipo']] = row['total']
        else:
            cursor.execute('''
                SELECT tipo, MAX(sequential_number) as total
                FROM avaliacoes
                WHERE avaliacao_date = %s
                GROUP BY tipo
            ''', (today,))
            stats = cursor.fetchall()
            result = {1: 0, 2: 0, 3: 0}
            for row in stats:
                result[row[0]] = row[1]
        
        conn.close()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    """Exportar dados para CSV/Excel (todas as datas)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                SELECT tipo, avaliacao_date, avaliacao_time, sequential_number
                FROM avaliacoes
                ORDER BY avaliacao_date DESC, avaliacao_time DESC
            ''')
            avaliacoes = cursor.fetchall()
            data = [dict(row) for row in avaliacoes]
        else:
            cursor.execute('''
                SELECT tipo, avaliacao_date, avaliacao_time, sequential_number
                FROM avaliacoes
                ORDER BY avaliacao_date DESC, avaliacao_time DESC
            ''')
            avaliacoes = cursor.fetchall()
            data = [{'tipo': row[0], 'avaliacao_date': row[1], 'avaliacao_time': row[2], 'sequential_number': row[3]} for row in avaliacoes]
        
        conn.close()
        
        # Criar CSV com ponto e virgula (formato Excel europeu)
        from io import StringIO, BytesIO
        import csv
        
        # Usar BytesIO para adicionar BOM UTF-8
        output = BytesIO()
        # BOM UTF-8 para o Excel reconhecer encoding
        output.write(b'\xef\xbb\xbf')
        
        si = StringIO()
        # Usar ponto e virgula como delimitador (padrao Excel Europa)
        writer = csv.writer(si, delimiter=';', lineterminator='\n')
        
        # Cabecalho
        writer.writerow(['Tipo', 'Avaliacao', 'Data', 'Hora', 'Numero'])
        
        # Dados
        tipos_nome = {1: 'Muito Satisfeito', 2: 'Satisfeito', 3: 'Insatisfeito'}
        for row in data:
            writer.writerow([
                row['tipo'],
                tipos_nome[row['tipo']],
                row['avaliacao_date'],
                row['avaliacao_time'],
                row['sequential_number']
            ])
        
        # Adicionar conteudo CSV ao output
        output.write(si.getvalue().encode('utf-8'))
        
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=avaliacoes_todas.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def login_required(f):
    """Decorator para verificar se o utilizador está autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        # Credenciais hardcoded
        if username == 'pedro' and password == '1234':
            session['user'] = username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401
    
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    """Página de administração"""
    return render_template('admin.html')

@app.route('/logout')
def logout():
    """Fazer logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/admin/stats-temporal', methods=['GET'])
@login_required
def get_stats_temporal():
    """Obter estatísticas temporais (últimos 30 dias)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        today = date.today()
        start_date = (today - timedelta(days=29)).isoformat()
        end_date = today.isoformat()
        
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                SELECT avaliacao_date, tipo, MAX(sequential_number) as total
                FROM avaliacoes
                WHERE avaliacao_date BETWEEN ? AND ?
                GROUP BY avaliacao_date, tipo
                ORDER BY avaliacao_date DESC
            ''', (start_date, end_date))
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        else:
            cursor.execute('''
                SELECT avaliacao_date, tipo, MAX(sequential_number) as total
                FROM avaliacoes
                WHERE avaliacao_date BETWEEN %s AND %s
                GROUP BY avaliacao_date, tipo
                ORDER BY avaliacao_date DESC
            ''', (start_date, end_date))
            rows = cursor.fetchall()
            result = [{'avaliacao_date': row[0], 'tipo': row[1], 'total': row[2]} for row in rows]
        
        conn.close()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/historico', methods=['GET'])
@login_required
def get_historico():
    """Obter histórico completo de avaliações"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        conn = get_db()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                SELECT tipo, avaliacao_date, avaliacao_time, sequential_number
                FROM avaliacoes
                ORDER BY avaliacao_date DESC, avaliacao_time DESC
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            
            cursor.execute('SELECT COUNT(*) as total FROM avaliacoes')
            total = cursor.fetchone()['total']
        else:
            cursor.execute('''
                SELECT tipo, avaliacao_date, avaliacao_time, sequential_number
                FROM avaliacoes
                ORDER BY avaliacao_date DESC, avaliacao_time DESC
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
            rows = cursor.fetchall()
            data = [{'tipo': row[0], 'avaliacao_date': row[1], 'avaliacao_time': row[2], 'sequential_number': row[3]} for row in rows]
            
            cursor.execute('SELECT COUNT(*) as total FROM avaliacoes')
            total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'historico': data,
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/resumo-geral', methods=['GET'])
@login_required
def get_resumo_geral():
    """Obter resumo geral de estatísticas"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            # Total de avaliações
            cursor.execute('SELECT COUNT(*) as total FROM avaliacoes')
            total = cursor.fetchone()['total']
            
            # Total por tipo (último valor de sequential_number para cada tipo)
            cursor.execute('''
                SELECT tipo, MAX(sequential_number) as total
                FROM avaliacoes
                GROUP BY tipo
            ''')
            stats = cursor.fetchall()
            result_stats = {1: 0, 2: 0, 3: 0}
            for row in stats:
                result_stats[row['tipo']] = row['total']
            
            # Dados de hoje
            today = date.today().isoformat()
            cursor.execute('''
                SELECT tipo, MAX(sequential_number) as total
                FROM avaliacoes
                WHERE avaliacao_date = ?
                GROUP BY tipo
            ''', (today,))
            today_stats = cursor.fetchall()
            today_result = {1: 0, 2: 0, 3: 0}
            for row in today_stats:
                today_result[row['tipo']] = row['total']
        else:
            cursor.execute('SELECT COUNT(*) as total FROM avaliacoes')
            total = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT tipo, MAX(sequential_number) as total
                FROM avaliacoes
                GROUP BY tipo
            ''')
            stats = cursor.fetchall()
            result_stats = {1: 0, 2: 0, 3: 0}
            for row in stats:
                result_stats[row[0]] = row[1]
            
            today = date.today().isoformat()
            cursor.execute('''
                SELECT tipo, MAX(sequential_number) as total
                FROM avaliacoes
                WHERE avaliacao_date = %s
                GROUP BY tipo
            ''', (today,))
            today_stats = cursor.fetchall()
            today_result = {1: 0, 2: 0, 3: 0}
            for row in today_stats:
                today_result[row[0]] = row[1]
        
        conn.close()
        
        return jsonify({
            'total_geral': total,
            'stats_geral': result_stats,
            'stats_hoje': today_result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
