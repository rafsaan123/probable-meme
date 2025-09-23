#!/usr/bin/env python3

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import datastore
import json
import os

def test_firebase_connection():
    try:
        # Initialize Firebase
        service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        
        if not os.path.exists(service_account_path):
            print("❌ Service account key not found")
            return
        
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        
        print("✅ Firebase Admin SDK initialized")
        
        # Test Firestore with different database names
        print("\n🔍 Testing Firestore connections...")
        
        # Try default database
        try:
            db_default = firestore.client(database_id='(default)')
            print("✅ Default Firestore database connected")
            
            # Try to list collections
            collections = db_default.collections()
            print(f"📁 Collections in default database: {[c.id for c in collections]}")
            
        except Exception as e:
            print(f"❌ Default Firestore failed: {e}")
        
        # Try result1 database
        try:
            db_result1 = firestore.client(database_id='result1')
            print("✅ result1 Firestore database connected")
            
            # Try to list collections
            collections = db_result1.collections()
            print(f"📁 Collections in result1 database: {[c.id for c in collections]}")
            
        except Exception as e:
            print(f"❌ result1 Firestore failed: {e}")
        
        # Test Datastore
        print("\n🔍 Testing Datastore connections...")
        
        try:
            ds_default = datastore.Client(database='(default)')
            print("✅ Default Datastore connected")
        except Exception as e:
            print(f"❌ Default Datastore failed: {e}")
        
        try:
            ds_result1 = datastore.Client(database='result1')
            print("✅ result1 Datastore connected")
        except Exception as e:
            print(f"❌ result1 Datastore failed: {e}")
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")

if __name__ == "__main__":
    test_firebase_connection()
