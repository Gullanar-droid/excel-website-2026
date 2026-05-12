import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database connection
def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/excel_data')
    return psycopg2.connect(DATABASE_URL)

# Create table if not exists
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS excel_data (
            id SERIAL PRIMARY KEY,
            row_index INTEGER,
            column_name TEXT,
            cell_value TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Read Excel file
    df = pd.read_excel(filepath)
    
    # Save to database
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM excel_data')
    
    for idx, row in df.iterrows():
        for col in df.columns:
            value = str(row[col]) if pd.notna(row[col]) else ''
            cur.execute(
                'INSERT INTO excel_data (row_index, column_name, cell_value) VALUES (%s, %s, %s)',
                (idx, col, value)
            )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True, 'rows': len(df), 'columns': len(df.columns)})

@app.route('/get_data')
def get_data():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT row_index, column_name, cell_value FROM excel_data ORDER BY row_index')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    data = {}
    for row in rows:
        row_idx = row['row_index']
        if row_idx not in data:
            data[row_idx] = {}
        data[row_idx][row['column_name']] = row['cell_value']
    
    result = [{'id': k, **v} for k, v in data.items()]
    return jsonify(result)

@app.route('/update_cell', methods=['POST'])
def update_cell():
    data = request.json
    row_id = data.get('row_id')
    column = data.get('column')
    value = data.get('value')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'UPDATE excel_data SET cell_value = %s WHERE row_index = %s AND column_name = %s',
        (value, row_id, column)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)