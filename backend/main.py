from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import tempfile
from ollama_chain import ask_llm, convert_to_serializable
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# store uploaded dataframes
df_store = {}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    ext = file.filename.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        # read file based on extension
        df = pd.read_csv(tmp_path) if ext == "csv" else pd.read_excel(tmp_path)
        session_id = file.filename
        df_store[session_id] = df
        return jsonify({'session_id': session_id, 'columns': list(df.columns)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/ask', methods=['POST'])
def ask_question():
    session_id = request.form.get('session_id')
    question = request.form.get('question')
    
    if not session_id or session_id not in df_store:
        return jsonify({'error': 'Session not found. Please upload your file again.'}), 404
    
    df = df_store[session_id]
    try:
        # prepare spreadsheet data
        spreadsheet_data = {
            "name": session_id,
            "sheets": ["Sheet1"],
            "columns": len(df.columns),
            "rows": len(df),
            "time_period": "Unknown",
            "summary": df.describe(),
            "column_descriptions": {col: df[col].dtype.name for col in df.columns},
            "data": df.to_dict('records')  # Include actual data
        }
        
        answer = ask_llm(question, model="deepseek-r1", spreadsheet_data=spreadsheet_data)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# static file routes
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory(os.path.join(app.static_folder, 'css'), path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory(os.path.join(app.static_folder, 'js'), path)

@app.route('/<path:path>')
def serve_static_html(path):
    if path.endswith('.html'):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True) 