#!/usr/bin/env python3
"""
Simple test script to verify Vercel deployment
"""

import requests
import json

def test_vercel_api():
    base_url = "https://probable-meme.vercel.app"
    
    print("🧪 Testing Vercel API Deployment")
    print("=" * 40)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed: {data.get('status', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Student search
    print("\n2. Testing student search...")
    try:
        payload = {
            "rollNo": "721942",
            "regulation": "2022", 
            "program": "Diploma in Engineering"
        }
        response = requests.post(
            f"{base_url}/api/search-result",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Student found: {data.get('roll')}")
                print(f"   📊 Semesters: {len(data.get('resultData', []))}")
            else:
                print(f"   ⚠️ Student not found: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Search failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Search error: {e}")
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_vercel_api()
