from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({'message': 'BTEB Results API', 'status': 'running'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'API is running'})

@app.route('/api/search-result', methods=['POST'])
def search_result():
    data = request.get_json()
    return jsonify({
        'success': True,
        'message': 'API is working',
        'data': data
    })

if __name__ == '__main__':
    app.run()
