import os
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store data in memory (simple for demo)
stored_data = []
columns = []

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_excel():
    global stored_data, columns
    
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
    columns = df.columns.tolist()
    
    # Convert to list of dictionaries
    stored_data = df.to_dict(orient='records')
    
    return jsonify({'success': True, 'rows': len(stored_data), 'columns': len(columns)})

@app.route('/get_data')
def get_data():
    return jsonify(stored_data)

@app.route('/update_cell', methods=['POST'])
def update_cell():
    global stored_data
    
    data = request.json
    row_index = data.get('row_index')
    column = data.get('column')
    value = data.get('value')
    
    if 0 <= row_index < len(stored_data):
        stored_data[row_index][column] = value
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid row'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
