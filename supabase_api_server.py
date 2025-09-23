#!/usr/bin/env python3
"""
BTEB Results API Server using Supabase Database
Replaces Firebase with Supabase for better performance and reliability
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import os
import json
from typing import Dict, List, Optional, Any

app = Flask(__name__)
CORS(app)

# Supabase configuration
SUPABASE_URL = "https://hddphaneexloretrisiy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkZHBoYW5lZXhsb3JldHJpc2l5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MTEzNjksImV4cCI6MjA3NDE4NzM2OX0.eMyOCUDI-iqcGY_tJUbAMw41sPnDDXfHbdMJNfcwP-w"

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Supabase client: {e}")
    supabase = None

def load_institute_codes() -> List[str]:
    """Load institute codes from Supabase database."""
    if not supabase:
        return []
    
    try:
        # Get all unique institute codes from the database
        result = supabase.table('institutes').select('institute_code').execute()
        
        if result.data:
            codes = list(set([row['institute_code'] for row in result.data]))
            codes.sort()
            print(f"📊 Loaded {len(codes)} institute codes from Supabase")
            return codes
        else:
            print("⚠️ No institute codes found in database")
            return []
            
    except Exception as e:
        print(f"❌ Error loading institute codes: {e}")
        # Fallback to known codes
        return [
            '16057', '16058', '16059', '16100',  # Rangpur region
            '19057', '19063', '19067', '19078', '19086',  # Joypurhat region  
            '23071', '23104', '23105', '23106', '23107', '23117', '23119', '23189'  # Rajshahi region
        ]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if supabase:
            # Test connection
            result = supabase.table('programs').select('*').limit(1).execute()
            return jsonify({
                'status': 'healthy',
                'supabase_connected': True,
                'database': 'supabase',
                'message': 'API server is running and connected to Supabase'
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'supabase_connected': False,
                'message': 'Supabase client not initialized'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'supabase_connected': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    if not supabase:
        return jsonify({'error': 'Supabase not initialized'}), 500
    
    try:
        stats = {}
        
        # Get program count
        programs_result = supabase.table('programs').select('*', count='exact').execute()
        stats['total_programs'] = programs_result.count
        
        # Get regulation count
        regulations_result = supabase.table('regulations').select('*', count='exact').execute()
        stats['total_regulations'] = regulations_result.count
        
        # Get institute count
        institutes_result = supabase.table('institutes').select('*', count='exact').execute()
        stats['total_institutes'] = institutes_result.count
        
        # Get student count
        students_result = supabase.table('students').select('*', count='exact').execute()
        stats['total_students'] = students_result.count
        
        # Get GPA records count
        gpa_result = supabase.table('gpa_records').select('*', count='exact').execute()
        stats['total_gpa_records'] = gpa_result.count
        
        # Get sample institutes
        sample_institutes = supabase.table('institutes').select('institute_code, name, district').limit(10).execute()
        stats['sample_institutes'] = sample_institutes.data
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@app.route('/api/regulations/<program>', methods=['GET'])
def get_regulations(program):
    """Get available regulations for a program"""
    if not supabase:
        return jsonify({'error': 'Supabase not initialized'}), 500
    
    try:
        result = supabase.table('regulations').select('year').eq('program_name', program).execute()
        
        if result.data:
            regulations = [row['year'] for row in result.data]
            regulations.sort()
            return jsonify({'regulations': regulations})
        else:
            return jsonify({'regulations': []})
            
    except Exception as e:
        return jsonify({'error': f'Failed to get regulations: {str(e)}'}), 500

@app.route('/api/search-result', methods=['POST'])
def search_result():
    """Search for student results"""
    if not supabase:
        return jsonify({'error': 'Supabase not initialized'}), 500
    
    try:
        data = request.get_json()
        roll_no = data.get('rollNo', '').strip()
        regulation = data.get('regulation', '').strip()
        program = data.get('program', '').strip()
        
        if not all([roll_no, regulation, program]):
            return jsonify({'error': 'Missing required fields: rollNo, regulation, program'}), 400
        
        print(f"🔍 Searching for: {roll_no}, {regulation}, {program}")
        
        # Search for student directly using roll number (much faster)
        print(f"🔍 Searching for student: {roll_no}")
        
        try:
            # Search for student directly by roll number
            student_result = supabase.table('students').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('roll_number', roll_no).execute()
            
            if not student_result.data:
                return jsonify({'error': 'Student not found'}), 404
            
            student_data = student_result.data[0]
            institute_code = student_data['institute_code']
            print(f"✅ Found student with institute code: {institute_code}")
            
            # Get institute data
            institute_result = supabase.table('institutes').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('institute_code', institute_code).execute()
            
            institute_data = None
            if institute_result.data:
                institute_data = institute_result.data[0]
                print(f"✅ Found institute data: {institute_data['name']}")
                
        except Exception as e:
            print(f"❌ Error searching for student: {e}")
            return jsonify({'error': f'Search failed: {str(e)}'}), 500
        
        if not student_data:
            return jsonify({'error': 'Student not found'}), 404
        
        # Get GPA records for the student
        gpa_result = supabase.table('gpa_records').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('institute_code', student_data['institute_code']).eq('roll_number', roll_no).order('semester').execute()
        
        # Get CGPA record
        cgpa_result = supabase.table('cgpa_records').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('institute_code', student_data['institute_code']).eq('roll_number', roll_no).execute()
        
        # Format the response to match frontend expectations
        response_data = {
            'success': True,
            'time': student_data['created_at'],
            'roll': roll_no,
            'regulation': regulation,
            'exam': program,
            'instituteData': {
                'code': student_data['institute_code'],
                'name': institute_data['name'] if institute_data else 'Unknown',
                'district': institute_data['district'] if institute_data else 'Unknown'
            },
            'resultData': []
        }
        
        # Process GPA records
        if gpa_result.data:
            print(f"📊 Found {len(gpa_result.data)} GPA records")
            
            for gpa_record in gpa_result.data:
                semester_result = {
                    'publishedAt': gpa_record['created_at'],
                    'semester': str(gpa_record['semester']),
                    'passed': not gpa_record['is_reference'],
                    'gpa': str(gpa_record['gpa']) if gpa_record['gpa'] is not None else "ref",
                    'result': {
                        'gpa': str(gpa_record['gpa']) if gpa_record['gpa'] is not None else "ref",
                        'ref_subjects': gpa_record['ref_subjects'] if gpa_record['ref_subjects'] else []
                    }
                }
                response_data['resultData'].append(semester_result)
        
        print(f"✅ Returning data for {roll_no}: {len(response_data['resultData'])} semesters")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in search_result: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting BTEB Results API Server (Supabase)")
    print("📡 Available endpoints:")
    print("  POST /api/search-result - Search for student results")
    print("  GET  /api/regulations/<program> - Get available regulations")
    print("  GET  /api/stats - Get database statistics")
    print("  GET  /health - Health check")
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
    
    app.run(host='0.0.0.0', port=3001, debug=True)
