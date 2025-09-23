#!/usr/bin/env python3

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

def check_database():
    try:
        # Initialize Firebase
        service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        
        if not os.path.exists(service_account_path):
            print("❌ Service account key not found")
            return
        
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        print("✅ Firebase connected successfully")
        
        # Get students count
        print("\n📊 Checking students collection...")
        students_ref = db.collection('students')
        students_docs = list(students_ref.stream())
        total_students = len(students_docs)
        print(f"Total students: {total_students}")
        
        # Get institutes count
        print("\n🏫 Checking institutes collection...")
        institutes_ref = db.collection('institutes')
        institutes_docs = list(institutes_ref.stream())
        total_institutes = len(institutes_docs)
        print(f"Total institutes: {total_institutes}")
        
        # Show sample data
        print("\n📋 Sample students (first 5):")
        for i, doc in enumerate(students_docs[:5]):
            data = doc.to_dict()
            print(f"  {i+1}. ID: {doc.id}")
            print(f"     Institute Code: {data.get('institute_code', 'N/A')}")
            print(f"     Roll Number: {data.get('roll_number', 'N/A')}")
            print()
        
        print("🏢 Sample institutes (first 5):")
        for i, doc in enumerate(institutes_docs[:5]):
            data = doc.to_dict()
            print(f"  {i+1}. ID: {doc.id}")
            print(f"     Code: {data.get('code', 'N/A')}")
            print(f"     Name: {data.get('name', 'N/A')}")
            print()
        
        # Check for specific roll numbers
        print("🔍 Checking for roll numbers starting with 721:")
        roll_721_count = 0
        for doc in students_docs:
            data = doc.to_dict()
            roll_number = data.get('roll_number', '')
            if str(roll_number).startswith('721'):
                roll_721_count += 1
                if roll_721_count <= 3:  # Show first 3
                    print(f"  Found: {roll_number} (ID: {doc.id})")
        
        print(f"Total 721xxx students: {roll_721_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database()


