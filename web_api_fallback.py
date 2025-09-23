#!/usr/bin/env python3
"""
Web API Fallback System for BTEB Results
Falls back to external web APIs when Supabase projects don't have the data
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

class WebAPIFallback:
    """Handles fallback to external web APIs"""
    
    def __init__(self):
        self.web_apis = [
            {
                'name': 'btebresulthub',
                'base_url': 'https://btebresulthub-server.vercel.app',
                'endpoint': '/results/individual/{roll}',
                'params': {
                    'exam': 'diploma-in-engineering',
                    'regulation': '{regulation}'
                },
                'timeout': 10,
                'priority': 1,
                'description': 'BTEB Result Hub API'
            }
        ]
        
        # Add more web APIs here as needed
        # self.web_apis.append({
        #     'name': 'another_api',
        #     'base_url': 'https://another-api.com',
        #     'endpoint': '/search',
        #     'params': {'roll': '{roll}', 'year': '{regulation}'},
        #     'timeout': 10,
        #     'priority': 2,
        #     'description': 'Another BTEB API'
        # })
    
    def search_student_in_web_api(self, api_config: Dict, roll_no: str, regulation: str, program: str) -> Optional[Dict]:
        """Search for student in a specific web API"""
        try:
            print(f"🌐 Searching in web API: {api_config['name']}")
            
            # Build URL
            endpoint = api_config['endpoint'].format(roll=roll_no)
            url = api_config['base_url'] + endpoint
            
            # Build parameters
            params = {}
            for key, value in api_config['params'].items():
                if '{roll}' in value:
                    params[key] = value.format(roll=roll_no)
                elif '{regulation}' in value:
                    params[key] = value.format(regulation=regulation)
                elif '{program}' in value:
                    params[key] = value.format(program=program.lower().replace(' ', '-'))
                else:
                    params[key] = value
            
            # Make request
            response = requests.get(
                url, 
                params=params, 
                timeout=api_config['timeout'],
                headers={
                    'User-Agent': 'BTEB-Results-App/1.0',
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found student in {api_config['name']}")
                return self.convert_web_api_response(data, api_config['name'], roll_no, regulation, program)
            elif response.status_code == 404:
                print(f"❌ Student not found in {api_config['name']}")
                return None
            else:
                print(f"❌ Error in {api_config['name']}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout searching in {api_config['name']}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error in {api_config['name']}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error searching in {api_config['name']}: {e}")
            return None
    
    def convert_web_api_response(self, data: Dict, api_name: str, roll_no: str, regulation: str, program: str) -> Dict:
        """Convert web API response to our standard format"""
        try:
            # Convert BTEB Result Hub API response format to our standard format
            # The API returns: {"success":true,"time":"...","roll":"...","regulation":"...","exam":"...","instituteData":{...},"resultData":[...]}
            
            # Extract student data
            student_data = {
                'roll_number': data.get('roll', roll_no),
                'program_name': data.get('exam', program),
                'regulation_year': data.get('regulation', regulation),
                'created_at': data.get('time', '2025-01-01T00:00:00Z'),
                'institute_code': data.get('instituteData', {}).get('code', '00000')
            }
            
            # Extract institute data
            institute_data = {
                'name': data.get('instituteData', {}).get('name', 'Unknown Institute'),
                'district': data.get('instituteData', {}).get('district', 'Unknown'),
                'code': data.get('instituteData', {}).get('code', '00000')
            }
            
            # Extract GPA records from resultData
            result_data = data.get('resultData', [])
            gpa_records = []
            
            for result in result_data:
                # The API returns "result" field with GPA value, and "passed" boolean
                gpa_value = result.get('result')
                is_passed = result.get('passed', True)
                
                # Convert GPA to float if it's a number
                try:
                    gpa_float = float(gpa_value) if gpa_value and gpa_value != 'ref' else None
                except (ValueError, TypeError):
                    gpa_float = None
                
                gpa_record = {
                    'semester': int(result.get('semester', 1)),
                    'gpa': gpa_float,
                    'is_reference': not is_passed or gpa_value == 'ref',
                    'ref_subjects': [],  # Web API doesn't provide ref subjects details
                    'created_at': result.get('publishedAt', '2025-01-01T00:00:00Z')
                }
                gpa_records.append(gpa_record)
            
            return {
                'student_data': student_data,
                'institute_data': institute_data,
                'gpa_records': gpa_records,
                'source': f'web_api_{api_name}',
                'raw_response': data
            }
            
        except Exception as e:
            print(f"❌ Error converting response from {api_name}: {e}")
            return None
    
    def search_student_across_web_apis(self, roll_no: str, regulation: str, program: str) -> Optional[Dict]:
        """Search for student across all web APIs"""
        print(f"🌐 Starting web API fallback search for: {roll_no}")
        
        # Sort APIs by priority
        sorted_apis = sorted(self.web_apis, key=lambda x: x['priority'])
        
        for api_config in sorted_apis:
            result = self.search_student_in_web_api(api_config, roll_no, regulation, program)
            if result:
                print(f"🎯 Student found in web API: {api_config['name']}")
                return result
            else:
                print(f"⏭️ Trying next web API...")
        
        print(f"❌ Student not found in any web API")
        return {
            'success': False,
            'error': 'Student not found in any web API',
            'roll': roll_no,
            'regulation': regulation,
            'exam': program,
            'web_apis_tried': [api['name'] for api in sorted_apis]
        }
    
    def test_web_api_connection(self, api_config: Dict) -> bool:
        """Test connection to a web API"""
        try:
            # Test with a known roll number
            test_roll = "721942"
            test_regulation = "2022"
            test_program = "Diploma in Engineering"
            
            endpoint = api_config['endpoint'].format(roll=test_roll)
            url = api_config['base_url'] + endpoint
            
            params = {}
            for key, value in api_config['params'].items():
                if '{roll}' in value:
                    params[key] = value.format(roll=test_roll)
                elif '{regulation}' in value:
                    params[key] = value.format(regulation=test_regulation)
                elif '{program}' in value:
                    params[key] = value.format(program=test_program.lower().replace(' ', '-'))
                else:
                    params[key] = value
            
            response = requests.get(
                url, 
                params=params, 
                timeout=5,
                headers={'User-Agent': 'BTEB-Results-App/1.0'}
            )
            
            return response.status_code in [200, 404]  # 404 is also OK (means API is working)
            
        except Exception as e:
            print(f"❌ Web API test failed for {api_config['name']}: {e}")
            return False
    
    def test_all_web_apis(self):
        """Test all web API connections"""
        print("\n🌐 Testing all web API connections:")
        print("=" * 40)
        
        for api_config in self.web_apis:
            print(f"Testing {api_config['name']}...", end=" ")
            if self.test_web_api_connection(api_config):
                print("✅ Connected")
            else:
                print("❌ Failed")
    
    def list_web_apis(self):
        """List all configured web APIs"""
        print("\n🌐 Available Web APIs:")
        print("=" * 30)
        
        for api_config in self.web_apis:
            print(f"📡 {api_config['name']}: {api_config['description']}")
            print(f"   URL: {api_config['base_url']}{api_config['endpoint']}")
            print(f"   Priority: {api_config['priority']}")
            print()

# Global instance
web_api_fallback = WebAPIFallback()

def search_student_in_web_apis(roll_no: str, regulation: str, program: str) -> Optional[Dict]:
    """Search for student in web APIs"""
    return web_api_fallback.search_student_across_web_apis(roll_no, regulation, program)

def test_web_api_connections():
    """Test all web API connections"""
    web_api_fallback.test_all_web_apis()

def list_web_apis():
    """List all web APIs"""
    web_api_fallback.list_web_apis()

def get_web_api_configs():
    """Get web API configurations"""
    return web_api_fallback.web_apis

def test_web_api_connection(api_config):
    """Test connection to a web API"""
    return web_api_fallback.test_web_api_connection(api_config)

if __name__ == "__main__":
    print("🌐 Web API Fallback System")
    print("=" * 30)
    
    # List web APIs
    list_web_apis()
    
    # Test connections
    test_web_api_connections()
    
    # Example search
    print("\n🔍 Example search:")
    result = search_student_in_web_apis("721942", "2022", "Diploma in Engineering")
    if result:
        print(f"✅ Found student from: {result['source']}")
    else:
        print("❌ Student not found in any web API")
