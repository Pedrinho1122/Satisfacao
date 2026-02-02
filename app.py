from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, date
import os

app = Flask(__name__)

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
    """Obter número sequencial da avaliação para hoje"""
    today = date.today().isoformat()
    conn = get_db()
    
    if DB_TYPE == 'sqlite':
        cursor = conn.cursor()
        cursor.execute('''
            SELECT MAX(sequential_number) as max_seq 
            FROM avaliacoes 
            WHERE tipo = ? AND avaliacao_date = ?
        ''', (tipo, today))
        result = cursor.fetchone()
        max_seq = result['max_seq'] if result['max_seq'] else 0
    else:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT MAX(sequential_number) as max_seq 
            FROM avaliacoes 
            WHERE tipo = %s AND avaliacao_date = %s
        ''', (tipo, today))
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
    """Exportar dados para CSV (todas as datas)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                SELECT tipo, avaliacao_date, avaliacao_time, sequential_number
                FROM avaliacoes
                ORDER BY id DESC
            ''')
            avaliacoes = cursor.fetchall()
            data = [dict(row) for row in avaliacoes]
        else:
            cursor.execute('''
                SELECT tipo, avaliacao_date, avaliacao_time, sequential_number
                FROM avaliacoes
                ORDER BY id DESC
            ''')
            avaliacoes = cursor.fetchall()
            data = [{'tipo': row[0], 'avaliacao_date': row[1], 'avaliacao_time': row[2], 'sequential_number': row[3]} for row in avaliacoes]
        
        conn.close()
        
        # Criar CSV
        from io import StringIO
        import csv
        
        si = StringIO()
        writer = csv.writer(si)
        
        # Cabeçalho
        writer.writerow(['Tipo', 'Avaliação', 'Data', 'Hora', 'Número'])
        
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
        
        output = si.getvalue()
        
        from flask import make_response
        response = make_response(output)
        response.headers["Content-Disposition"] = "attachment; filename=avaliacoes_todas.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
