from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import datastore
import json
import os

app = Flask(__name__)
CORS(app)

def load_institute_codes():
    """Load institute codes from the discovered JSON file."""
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'discovered_institute_codes.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                return data.get('institute_codes', [])
    except Exception as e:
        print(f"❌ Error loading institute codes: {e}")
    
    # Fallback to hardcoded list
    return [
        '16057', '16058', '16059', '16100',  # Rangpur region
        '19057', '19063', '19067', '19078', '19086',  # Joypurhat region  
        '23071', '23104', '23105', '23106', '23107', '23117', '23119', '23189'  # Rajshahi region
    ]

# Initialize Firebase Admin SDK
try:
    # Try to find the service account key file
    service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
    
    if os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        # Try result1 database first (since we know it has data)
        try:
            db = firestore.client(database_id='result1')
            print("✅ Firebase Firestore initialized successfully with database 'result1'")
        except Exception as e:
            print(f"⚠️ result1 database failed, trying default: {e}")
            try:
                db = firestore.client(database_id='(default)')
                print("✅ Firebase Firestore initialized successfully with default database")
            except Exception as e2:
                print(f"⚠️ Firestore failed, trying Datastore: {e2}")
                # Fallback to Datastore
                try:
                    db = datastore.Client(database='result1')
                    print("✅ Firebase Datastore initialized successfully with database 'result1'")
                except Exception as e3:
                    print(f"⚠️ result1 Datastore failed, trying default: {e3}")
                    db = datastore.Client(database='(default)')
                    print("✅ Firebase Datastore initialized successfully with default database")
    else:
        print("❌ Service account key not found. Please add serviceAccountKey.json to bteb_results folder")
        db = None
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    db = None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "firebase_connected": db is not None
    })

@app.route('/api/stats', methods=['GET'])
def get_database_stats():
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 500
        
        # Check if it's Firestore or Datastore
        if hasattr(db, 'collection'):  # Firestore
            # For Enterprise Firestore, we can't use queries, so we'll estimate
            # by trying to access some known document IDs
            print("📊 Enterprise Firestore detected - estimating counts...")
            
            # Try to get some sample documents to estimate
            total_students = 0
            total_institutes = 0
            sample_students = []
            sample_institutes = []
            
            # Try some common document ID patterns
            test_student_ids = [
                "Diploma in Engineering_2022_23106_721942",
                "Diploma in Engineering_2022_23106_721941", 
                "Diploma in Engineering_2022_23106_721940",
                "Diploma in Engineering_2022_23106_721939",
                "Diploma in Engineering_2022_23106_721938"
            ]
            
            test_institute_ids = [
                "Diploma in Engineering_2022_23106",
                "Diploma in Engineering_2022_23107",
                "Diploma in Engineering_2022_23108"
            ]
            
            # Test student documents
            for doc_id in test_student_ids:
                try:
                    doc_ref = db.collection('students').document(doc_id)
                    doc = doc_ref.get()
                    if doc.exists:
                        total_students += 1
                        if len(sample_students) < 5:
                            data = doc.to_dict()
                            sample_students.append({
                                "id": doc.id,
                                "institute_code": data.get('institute_code', 'N/A'),
                                "roll_number": data.get('roll_number', 'N/A')
                            })
                except Exception as e:
                    print(f"❌ Error checking student {doc_id}: {e}")
            
            # Test institute documents  
            for doc_id in test_institute_ids:
                try:
                    doc_ref = db.collection('institutes').document(doc_id)
                    doc = doc_ref.get()
                    if doc.exists:
                        total_institutes += 1
                        if len(sample_institutes) < 5:
                            data = doc.to_dict()
                            sample_institutes.append({
                                "id": doc.id,
                                "code": data.get('code', 'N/A'),
                                "name": data.get('name', 'N/A')
                            })
                except Exception as e:
                    print(f"❌ Error checking institute {doc_id}: {e}")
            
            # If we found some documents, estimate there are more
            if total_students > 0:
                total_students = f"At least {total_students} (estimated from sample)"
            if total_institutes > 0:
                total_institutes = f"At least {total_institutes} (estimated from sample)"
        else:  # Datastore
            # Query students
            students_query = db.query(kind='students')
            students_docs = list(students_query.fetch())
            total_students = len(students_docs)
            
            # Query institutes
            institutes_query = db.query(kind='institutes')
            institutes_docs = list(institutes_query.fetch())
            total_institutes = len(institutes_docs)
            
            # Get sample data
            sample_students = []
            sample_institutes = []
            
            # Get first 5 students as samples
            for i, doc in enumerate(students_docs[:5]):
                sample_students.append({
                    "id": doc.key.name,
                    "institute_code": doc.get('institute_code', 'N/A'),
                    "roll_number": doc.get('roll_number', 'N/A')
                })
            
            # Get first 5 institutes as samples
            for i, doc in enumerate(institutes_docs[:5]):
                sample_institutes.append({
                    "id": doc.key.name,
                    "code": doc.get('code', 'N/A'),
                    "name": doc.get('name', 'N/A')
                })
        
        return jsonify({
            "total_students": total_students,
            "total_institutes": total_institutes,
            "sample_students": sample_students,
            "sample_institutes": sample_institutes,
            "database_type": "Firestore" if hasattr(db, 'collection') else "Datastore"
        })
        
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")
        return jsonify({"error": f"Failed to get database stats: {str(e)}"}), 500

@app.route('/api/search-result', methods=['POST'])
def search_result():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        roll_no = data.get('rollNo')
        regulation = data.get('regulation', '2022')
        program = data.get('program', 'Diploma in Engineering')
        
        if not roll_no:
            return jsonify({"error": "Roll number is required"}), 400
        
        print(f"🔍 Searching for: {roll_no}, {regulation}, {program}")
        
        if not db:
            return jsonify({"error": "Database not available"}), 500
        
        # For Enterprise Firestore, we need to construct the exact document ID
        # Based on the nn.py structure: "{program}_{regulation}_{institute_code}_{roll_number}"
        # We need to try different institute codes to find the student
        
        # Load all discovered institute codes from the database
        institute_codes = load_institute_codes()
        print(f"🔍 Searching through {len(institute_codes)} institute codes: {institute_codes}")
        
        student_data = None
        found_doc_id = None
        
        # Try different institute codes
        for inst_code in institute_codes:
            doc_id = f"{program}_{regulation}_{inst_code}_{roll_no}"
            try:
                doc_ref = db.collection('students').document(doc_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    student_data = doc.to_dict()
                    found_doc_id = doc_id
                    print(f"✅ Found student with document ID: {doc_id}")
                    break
            except Exception as e:
                print(f"❌ Error checking document {doc_id}: {e}")
                continue
        
        if not student_data:
            print(f"❌ Student {roll_no} not found in any institute")
            return jsonify({"error": "Student not found"}), 404
        
        # Extract institute data
        institute_code = student_data.get('institute_code', '')
        institute_data = {"code": institute_code, "name": "", "district": ""}
        
        if institute_code:
            # Try to get institute details
            institute_doc_id = f"{program}_{regulation}_{institute_code}"
            try:
                inst_ref = db.collection('institutes').document(institute_doc_id)
                inst_doc = inst_ref.get()
                if inst_doc.exists:
                    inst_data = inst_doc.to_dict()
                    institute_data["name"] = inst_data.get('name', '')
                    institute_data["district"] = inst_data.get('district', '')
                    print(f"✅ Found institute data: {institute_data['name']}")
            except Exception as e:
                print(f"❌ Error fetching institute data: {e}")
        
        # Extract GPA data from the correct structure
        gpa_data = student_data.get('gpa_data', {})
        cgpa_data = student_data.get('cgpa_data', {})
        
        print(f"📊 Found GPA data for {len(gpa_data)} semesters")
        
        # Build response in the expected format
        result_data = []
        
        # Process each semester from gpa_data
        for semester_key, semester_info in gpa_data.items():
            if isinstance(semester_info, dict) and 'semester' in semester_info:
                semester_num = semester_info.get('semester')
                gpa_value = semester_info.get('gpa')
                ref_subjects = semester_info.get('ref_subjects', [])
                
                # Determine if passed (GPA >= 2.0 or not "ref")
                passed = False
                if gpa_value == "ref":
                    passed = False
                else:
                    try:
                        gpa_float = float(gpa_value)
                        passed = gpa_float >= 2.0
                    except (ValueError, TypeError):
                        passed = False
                
                # Build result structure
                semester_result = {
                    "publishedAt": "",  # Not available in current data
                    "semester": str(semester_num),
                    "passed": passed,
                    "gpa": gpa_value,
                    "result": {
                        "gpa": gpa_value,
                        "passed": passed,
                        "ref_subjects": ref_subjects if gpa_value == "ref" else []
                    }
                }
                result_data.append(semester_result)
        
        # Sort by semester number
        result_data.sort(key=lambda x: int(x['semester']) if x['semester'].isdigit() else 0)
        
        # Add CGPA if available
        if cgpa_data and 'cgpa' in cgpa_data:
            print(f"📊 Found CGPA: {cgpa_data['cgpa']}")
        
        response = {
            "success": True,
            "time": "2025-01-27T00:00:00.000Z",
            "roll": roll_no,
            "regulation": regulation,
            "exam": "diploma-in-engineering",
            "instituteData": institute_data,
            "resultData": result_data,
            "cgpa": cgpa_data.get('cgpa', None) if cgpa_data else None
        }
        
        print(f"✅ Returning data for {roll_no}: {len(result_data)} semesters")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in search_result: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/regulations/<program>', methods=['GET'])
def get_regulations(program):
    try:
        # Since Firebase Enterprise doesn't support queries, return hardcoded regulations
        regulations = ['2022']
        return jsonify(regulations)
    except Exception as e:
        print(f"❌ Error getting regulations: {e}")
        return jsonify({"error": "Failed to get regulations"}), 500

if __name__ == '__main__':
    print("🚀 Starting BTEB Results API Server...")
    print("📡 Available endpoints:")
    print("  POST /api/search-result - Search for student results")
    print("  GET  /api/regulations/<program> - Get available regulations")
    print("  GET  /health - Health check")
    app.run(host='0.0.0.0', port=3001, debug=True)
