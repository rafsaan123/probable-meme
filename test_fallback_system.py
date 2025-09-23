#!/usr/bin/env python3
"""
Test script to demonstrate the complete fallback system:
1. Supabase projects (primary, secondary, tertiary, backup1, backup2)
2. Web APIs (btebresulthub)
"""

import requests
import json
import time

def test_fallback_system():
    """Test the complete fallback system"""
    base_url = "http://localhost:3001"
    
    print("🧪 Testing Complete Fallback System")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "rollNo": "721942",
            "regulation": "2022", 
            "program": "Diploma in Engineering",
            "description": "Student in primary Supabase project"
        },
        {
            "rollNo": "999999",
            "regulation": "2022",
            "program": "Diploma in Engineering", 
            "description": "Student not in any Supabase project (should try web APIs)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print(f"   Roll: {test_case['rollNo']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/search-result",
                json=test_case,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found: {data.get('found_in_project')}")
                print(f"   📊 Source: {data.get('source')}")
                print(f"   🔍 Projects searched: {data.get('projects_searched')}")
                print(f"   📈 Semesters: {len(data.get('resultData', []))}")
            elif response.status_code == 404:
                data = response.json()
                print(f"   ❌ Not found: {data.get('error')}")
                print(f"   🔍 Projects searched: {data.get('projects_searched')}")
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        time.sleep(1)  # Brief pause between tests
    
    # Test web API endpoints
    print(f"\n🌐 Testing Web API Endpoints")
    print("=" * 30)
    
    try:
        # List web APIs
        response = requests.get(f"{base_url}/api/web-apis")
        if response.status_code == 200:
            data = response.json()
            print(f"📡 Available web APIs: {data['total_count']}")
            for api in data['web_apis']:
                print(f"   - {api['name']}: {api['description']}")
        
        # Test web API connections
        response = requests.get(f"{base_url}/api/web-apis/test")
        if response.status_code == 200:
            data = response.json()
            print(f"🧪 Web API test results:")
            print(f"   Connected: {data['summary']['connected']}")
            print(f"   Failed: {data['summary']['failed']}")
            for result in data['test_results']:
                status_emoji = "✅" if result['status'] == 'connected' else "❌"
                print(f"   {status_emoji} {result['name']}: {result['status']}")
                
    except Exception as e:
        print(f"❌ Web API endpoint test failed: {e}")

if __name__ == "__main__":
    test_fallback_system()
