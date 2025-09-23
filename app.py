#!/usr/bin/env python3
"""
Multi-Project BTEB Results API Server using Supabase Database
Production-ready version for Render deployment with isolated Supabase client
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from typing import Dict, List, Optional, Any

app = Flask(__name__)
CORS(app)

# Production configuration
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Initialize Supabase manager with error handling
try:
    from multi_supabase import get_supabase_client, supabase_manager
    from web_api_fallback import web_api_fallback, test_web_api_connections, list_web_apis
    SUPABASE_AVAILABLE = True
    print("✅ Supabase modules loaded successfully")
except Exception as e:
    print(f"❌ Error loading Supabase modules: {e}")
    SUPABASE_AVAILABLE = False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({
                'status': 'unhealthy',
                'supabase_connected': False,
                'error': 'Supabase modules not available'
            }), 500
        
        # Test current project connection
        supabase = get_supabase_client()
        result = supabase.table('programs').select('*').limit(1).execute()
        
        return jsonify({
            'status': 'healthy',
            'supabase_connected': True,
            'database': 'supabase',
            'current_project': supabase_manager.current_project,
            'available_projects': list(supabase_manager.projects.keys()),
            'message': 'API server is running and connected to Supabase'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'supabase_connected': False,
            'error': str(e)
        }), 500

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all available Supabase projects"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        projects_info = {}
        for name, project in supabase_manager.projects.items():
            projects_info[name] = {
                'name': name,
                'description': project.description,
                'url': project.url,
                'is_active': name == supabase_manager.current_project
            }
        return jsonify(projects_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_name>/test', methods=['GET'])
def test_project(project_name):
    """Test connection to a specific project"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        if project_name not in supabase_manager.projects:
            return jsonify({'error': f'Project {project_name} not found'}), 404
        
        # Switch to the project temporarily
        original_project = supabase_manager.current_project
        supabase_manager.switch_project(project_name)
        
        try:
            supabase = get_supabase_client()
            result = supabase.table('programs').select('*').limit(1).execute()
            
            return jsonify({
                'project': project_name,
                'status': 'connected',
                'message': 'Project connection successful'
            })
        finally:
            # Restore original project
            supabase_manager.switch_project(original_project)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_name>/switch', methods=['POST'])
def switch_project(project_name):
    """Switch to a different Supabase project"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        if project_name not in supabase_manager.projects:
            return jsonify({'error': f'Project {project_name} not found'}), 404
        
        supabase_manager.switch_project(project_name)
        
        return jsonify({
            'message': f'Switched to project: {project_name}',
            'current_project': project_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web-apis', methods=['GET'])
def list_web_apis():
    """List all configured web APIs"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        apis = list_web_apis()
        return jsonify(apis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web-apis/test', methods=['GET'])
def test_web_apis():
    """Test all web API connections"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        results = test_web_api_connections()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-result', methods=['POST'])
def search_result():
    """Search for student results across all Supabase projects with web API fallback"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        roll_no = data.get('rollNo')
        regulation = data.get('regulation')
        program = data.get('program')
        
        if not all([roll_no, regulation, program]):
            return jsonify({'error': 'Missing required fields: rollNo, regulation, program'}), 400
        
        print(f"🔍 Searching for: {roll_no}, {regulation}, {program}")
        
        # Search across Supabase projects
        result = supabase_manager.search_student_across_projects(roll_no, regulation, program)
        
        if result and result.get('success'):
            # Get CGPA data if available
            cgpa_data = []
            if result.get('source') == 'supabase':
                # Search for CGPA records across all projects
                for project_name in supabase_manager.get_search_order():
                    try:
                        supabase_manager.switch_project(project_name)
                        supabase = get_supabase_client()
                        
                        cgpa_records = supabase.table('cgpa_records').select('*').eq('roll_number', roll_no).execute()
                        
                        if cgpa_records.data:
                            for cgpa_record in cgpa_records.data:
                                cgpa_data.append({
                                    'semester': cgpa_record.get('semester', 'Final'),
                                    'cgpa': str(cgpa_record.get('cgpa', '0.00')),
                                    'publishedAt': cgpa_record.get('created_at', '2025-01-01T00:00:00Z')
                                })
                            break  # Stop searching once we find CGPA data
                    except Exception as e:
                        print(f"❌ Error getting CGPA from {project_name}: {e}")
                        continue
                
                # Restore original project
                supabase_manager.switch_project(result.get('found_in_project', 'primary'))
            
            # Add CGPA data to result
            if cgpa_data:
                result['cgpaData'] = cgpa_data
            
            return jsonify(result)
        else:
            # Try web API fallback
            print(f"🌐 Student not found in any Supabase project, trying web APIs...")
            web_result = web_api_fallback(roll_no, regulation, program)
            
            if web_result and web_result.get('success'):
                return jsonify(web_result)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Student not found in any database or web API',
                    'roll': roll_no,
                    'regulation': regulation,
                    'exam': program,
                    'projects_searched': supabase_manager.get_search_order(),
                    'web_apis_tried': ['btebresulthub']
                }), 404
                
    except Exception as e:
        print(f"❌ Error in search_result: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regulations/<program>', methods=['GET'])
def get_regulations(program):
    """Get available regulations for a program"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        supabase = get_supabase_client()
        result = supabase.table('regulations').select('regulation_year').eq('program_name', program).execute()
        
        regulations = [row['regulation_year'] for row in result.data]
        return jsonify({'regulations': regulations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        supabase = get_supabase_client()
        
        # Get counts from different tables
        programs_count = supabase.table('programs').select('*', count='exact').execute()
        institutes_count = supabase.table('institutes').select('*', count='exact').execute()
        students_count = supabase.table('students').select('*', count='exact').execute()
        
        return jsonify({
            'programs': programs_count.count,
            'institutes': institutes_count.count,
            'students': students_count.count,
            'current_project': supabase_manager.current_project
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # For production deployment (Render, Heroku, etc.)
    pass