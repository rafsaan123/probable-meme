#!/usr/bin/env python3
"""
Multi-Project BTEB Results API Server using Supabase Database
Supports multiple Supabase projects for different environments or data sources
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from typing import Dict, List, Optional, Any
from multi_supabase import get_supabase_client, supabase_manager
from web_api_fallback import search_student_in_web_apis, test_web_api_connections, list_web_apis, get_web_api_configs, test_web_api_connection

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
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
        projects_info = {}
        for name, project in supabase_manager.projects.items():
            projects_info[name] = {
                'name': name,
                'description': project.description,
                'url': project.url,
                'is_current': name == supabase_manager.current_project
            }
        
        return jsonify({
            'current_project': supabase_manager.current_project,
            'projects': projects_info
        })
    except Exception as e:
        return jsonify({'error': f'Failed to list projects: {str(e)}'}), 500

@app.route('/api/projects/<project_name>/switch', methods=['POST'])
def switch_project(project_name):
    """Switch to a different Supabase project"""
    try:
        if project_name not in supabase_manager.projects:
            return jsonify({'error': f'Project {project_name} not found'}), 404
        
        # Test connection before switching
        project = supabase_manager.projects[project_name]
        if not project.test_connection():
            return jsonify({'error': f'Cannot connect to project {project_name}'}), 400
        
        supabase_manager.set_current_project(project_name)
        supabase_manager.save_config()
        
        return jsonify({
            'message': f'Switched to project: {project_name}',
            'current_project': project_name
        })
    except Exception as e:
        return jsonify({'error': f'Failed to switch project: {str(e)}'}), 500

@app.route('/api/projects/<project_name>/test', methods=['GET'])
def test_project_connection(project_name):
    """Test connection to a specific project"""
    try:
        if project_name not in supabase_manager.projects:
            return jsonify({'error': f'Project {project_name} not found'}), 404
        
        project = supabase_manager.projects[project_name]
        is_connected = project.test_connection()
        
        return jsonify({
            'project': project_name,
            'connected': is_connected,
            'message': 'Connection successful' if is_connected else 'Connection failed'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to test connection: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics for current project"""
    try:
        supabase = get_supabase_client()
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
        
        # Add project info
        stats['current_project'] = supabase_manager.current_project
        stats['project_description'] = supabase_manager.projects[supabase_manager.current_project].description
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@app.route('/api/regulations/<program>', methods=['GET'])
def get_regulations(program):
    """Get available regulations for a program"""
    try:
        supabase = get_supabase_client()
        result = supabase.table('regulations').select('year').eq('program_name', program).execute()
        
        if result.data:
            regulations = [row['year'] for row in result.data]
            regulations.sort()
            return jsonify({'regulations': regulations})
        else:
            return jsonify({'regulations': []})
            
    except Exception as e:
        return jsonify({'error': f'Failed to get regulations: {str(e)}'}), 500

@app.route('/api/web-apis', methods=['GET'])
def list_web_apis_endpoint():
    """List all configured web APIs"""
    try:
        apis_info = []
        for api_config in get_web_api_configs():
            apis_info.append({
                'name': api_config['name'],
                'description': api_config['description'],
                'base_url': api_config['base_url'],
                'endpoint': api_config['endpoint'],
                'priority': api_config['priority'],
                'timeout': api_config['timeout']
            })
        
        return jsonify({
            'web_apis': apis_info,
            'total_count': len(apis_info)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list web APIs: {str(e)}'}), 500

@app.route('/api/web-apis/test', methods=['GET'])
def test_web_apis_endpoint():
    """Test all web API connections"""
    try:
        results = []
        for api_config in get_web_api_configs():
            is_working = test_web_api_connection(api_config)
            results.append({
                'name': api_config['name'],
                'status': 'connected' if is_working else 'failed',
                'url': api_config['base_url']
            })
        
        return jsonify({
            'test_results': results,
            'summary': {
                'total': len(results),
                'connected': sum(1 for r in results if r['status'] == 'connected'),
                'failed': sum(1 for r in results if r['status'] == 'failed')
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to test web APIs: {str(e)}'}), 500

def search_student_in_project(project_name: str, roll_no: str, regulation: str, program: str):
    """Search for student in a specific project"""
    try:
        supabase = get_supabase_client(project_name)
        print(f"🔍 Searching in project: {project_name}")
        
        # Search for student directly by roll number
        student_result = supabase.table('students').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('roll_number', roll_no).execute()
        
        if not student_result.data:
            print(f"❌ Student not found in {project_name}")
            return None
        
        student_data = student_result.data[0]
        institute_code = student_data['institute_code']
        print(f"✅ Found student in {project_name} with institute code: {institute_code}")
        
        # Get institute data
        institute_result = supabase.table('institutes').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('institute_code', institute_code).execute()
        
        institute_data = None
        if institute_result.data:
            institute_data = institute_result.data[0]
            print(f"✅ Found institute data in {project_name}: {institute_data['name']}")
        
        return {
            'student_data': student_data,
            'institute_data': institute_data,
            'project_name': project_name
        }
        
    except Exception as e:
        print(f"❌ Error searching in {project_name}: {e}")
        return None

@app.route('/api/search-result', methods=['POST'])
def search_result():
    """Search for student results with automatic fallback across projects"""
    try:
        data = request.get_json()
        roll_no = data.get('rollNo', '').strip()
        regulation = data.get('regulation', '').strip()
        program = data.get('program', '').strip()
        
        if not all([roll_no, regulation, program]):
            return jsonify({'error': 'Missing required fields: rollNo, regulation, program'}), 400
        
        print(f"🔍 Searching for: {roll_no}, {regulation}, {program}")
        print(f"📊 Search order: {supabase_manager.get_search_order()}")
        
        # Search across all projects using the manager (includes web API fallback)
        search_result = supabase_manager.search_student_across_projects(roll_no, regulation, program)
        
        if not search_result['student_data']:
            return jsonify({
                'error': 'Student not found in any project or web API',
                'projects_searched': search_result['projects_tried']
            }), 404
        
        # Extract data from successful search
        student_data = search_result['student_data']
        institute_data = search_result['institute_data']
        found_project = search_result['project_name']
        projects_tried = search_result['projects_tried']
        source = search_result.get('source', 'supabase')
        
        print(f"📊 Using data from {source}: {found_project}")
        
        # Handle GPA records based on source
        if source == 'web_api':
            # GPA records come from web API response
            gpa_records = search_result.get('gpa_records', [])
            cgpa_records = []
        else:
            # Get GPA records from Supabase
            supabase = get_supabase_client(found_project)
            gpa_result = supabase.table('gpa_records').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('institute_code', student_data['institute_code']).eq('roll_number', roll_no).order('semester').execute()
            gpa_records = gpa_result.data if gpa_result.data else []
            
            # Search for CGPA records across all projects in the same order as student search
            cgpa_records = []
            for project_name in supabase_manager.get_search_order():
                if project_name not in supabase_manager.projects:
                    continue
                    
                try:
                    project_supabase = get_supabase_client(project_name)
                    cgpa_result = project_supabase.table('cgpa_records').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('institute_code', student_data['institute_code']).eq('roll_number', roll_no).execute()
                    
                    if cgpa_result.data:
                        cgpa_records = cgpa_result.data
                        print(f"📊 Found {len(cgpa_records)} CGPA records in {project_name}")
                        break  # Stop searching once found
                    else:
                        print(f"❌ No CGPA records found in {project_name}")
                        
                except Exception as e:
                    print(f"❌ Error getting CGPA from {project_name}: {e}")
                    continue
        
        # Format the response to match frontend expectations
        response_data = {
            'success': True,
            'time': student_data['created_at'],
            'roll': roll_no,
            'regulation': regulation,
            'exam': program,
            'found_in_project': found_project,
            'projects_searched': projects_tried,
            'source': source,
            'instituteData': {
                'code': student_data.get('institute_code', '00000'),
                'name': institute_data['name'] if institute_data else 'Unknown',
                'district': institute_data['district'] if institute_data else 'Unknown'
            },
            'resultData': [],
            'cgpaData': []
        }
        
        # Process GPA records
        if gpa_records:
            print(f"📊 Found {len(gpa_records)} GPA records")
            
            for gpa_record in gpa_records:
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
        
        # Process CGPA records
        if cgpa_records:
            print(f"📊 Found {len(cgpa_records)} CGPA records")
            
            for cgpa_record in cgpa_records:
                cgpa_result = {
                    'semester': str(cgpa_record.get('semester', 'Final')) if cgpa_record.get('semester') is not None else 'Final',
                    'cgpa': str(cgpa_record['cgpa']) if cgpa_record['cgpa'] is not None else None,
                    'publishedAt': cgpa_record['created_at']
                }
                response_data['cgpaData'].append(cgpa_result)
        
        print(f"✅ Returning data for {roll_no}: {len(response_data['resultData'])} semesters, {len(response_data['cgpaData'])} CGPA records from {source} ({found_project})")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in search_result: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting Multi-Project BTEB Results API Server (Supabase + Web APIs)")
    print("📡 Available endpoints:")
    print("  POST /api/search-result - Search for student results (with web API fallback)")
    print("  GET  /api/regulations/<program> - Get available regulations")
    print("  GET  /api/stats - Get database statistics")
    print("  GET  /api/projects - List all available projects")
    print("  POST /api/projects/<name>/switch - Switch to different project")
    print("  GET  /api/projects/<name>/test - Test project connection")
    print("  GET  /api/web-apis - List all web APIs")
    print("  GET  /api/web-apis/test - Test web API connections")
    print("  GET  /health - Health check")
    print(f"🔗 Current project: {supabase_manager.current_project}")
    
    # List available projects
    supabase_manager.list_projects()
    
    app.run(host='0.0.0.0', port=3001, debug=True)
