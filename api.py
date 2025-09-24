#!/usr/bin/env python3
"""
Simple Flask API for Vercel deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'message': 'BTEB Results API',
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running',
        'database': 'supabase'
    })

@app.route('/api/search-result', methods=['POST'])
def search_result():
    """Search for student results"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        roll_no = data.get('rollNo')
        regulation = data.get('regulation')
        program = data.get('program')
        
        if not all([roll_no, regulation, program]):
            return jsonify({'error': 'Missing required fields: rollNo, regulation, program'}), 400
        
        # For now, return a test response
        return jsonify({
            'success': True,
            'message': 'API is working - Supabase integration needed',
            'roll': roll_no,
            'regulation': regulation,
            'exam': program,
            'test': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
