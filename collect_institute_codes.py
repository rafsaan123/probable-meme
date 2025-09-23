#!/usr/bin/env python3
"""
Script to collect all institute codes from the Firebase database
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
import json

def initialize_firebase():
    """Initialize Firebase with proper error handling."""
    try:
        # Clear any existing apps
        if firebase_admin._apps:
            apps_to_delete = list(firebase_admin._apps.values())
            for app in apps_to_delete:
                firebase_admin.delete_app(app)
        
        # Check if service account key exists
        service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            # Try result1 database first
            try:
                db = firestore.client(database_id='result1')
                print("✅ Firebase Firestore initialized successfully with database 'result1'")
                return db
            except Exception as e:
                print(f"⚠️ result1 database failed, trying default: {e}")
                try:
                    db = firestore.client(database_id='(default)')
                    print("✅ Firebase Firestore initialized successfully with default database")
                    return db
                except Exception as e2:
                    print(f"❌ Firebase initialization failed: {e2}")
                    return None
        else:
            print("❌ Service account key not found")
            return None
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return None

def collect_institute_codes(db):
    """Collect all unique institute codes from the database."""
    if not db:
        print("❌ Database not available")
        return []
    
    institute_codes = set()
    institutes_data = []
    
    try:
        print("🔍 Collecting institute codes from database...")
        
        # Get all institute documents
        institutes_ref = db.collection('institutes')
        docs = institutes_ref.stream()
        
        for doc in docs:
            try:
                data = doc.to_dict()
                if data:
                    institute_code = data.get('institute_code', '')
                    if institute_code:
                        institute_codes.add(institute_code)
                        institutes_data.append({
                            'code': institute_code,
                            'name': data.get('name', ''),
                            'district': data.get('district', ''),
                            'program': data.get('program', ''),
                            'regulation_year': data.get('regulation_year', ''),
                            'doc_id': doc.id
                        })
                        print(f"📊 Found institute: {institute_code} - {data.get('name', 'N/A')}")
            except Exception as e:
                print(f"❌ Error processing institute document {doc.id}: {e}")
                continue
        
        print(f"\n✅ Collected {len(institute_codes)} unique institute codes")
        print(f"📊 Total institute records: {len(institutes_data)}")
        
        # Sort institute codes for consistent ordering
        sorted_codes = sorted(list(institute_codes))
        
        # Save to file
        output_data = {
            'institute_codes': sorted_codes,
            'institutes_data': institutes_data,
            'total_codes': len(institute_codes),
            'total_records': len(institutes_data)
        }
        
        with open('institute_codes.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"💾 Saved institute codes to institute_codes.json")
        print(f"📋 Institute codes: {sorted_codes}")
        
        return sorted_codes
        
    except Exception as e:
        print(f"❌ Error collecting institute codes: {e}")
        return []

def main():
    print("🎓 BTEB Institute Code Collector")
    print("=" * 40)
    
    # Initialize Firebase
    db = initialize_firebase()
    
    if not db:
        print("❌ Failed to initialize Firebase")
        return
    
    # Collect institute codes
    institute_codes = collect_institute_codes(db)
    
    if institute_codes:
        print(f"\n✅ Successfully collected {len(institute_codes)} institute codes")
        print("📋 Codes:", institute_codes)
    else:
        print("❌ No institute codes found")

if __name__ == "__main__":
    main()

