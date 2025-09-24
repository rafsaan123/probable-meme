import re
import os
import firebase_admin
from firebase_admin import credentials, firestore
from PyPDF2 import PdfReader
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ---------------------------
# Firebase Initialization
# ---------------------------
def initialize_firebase():
    """Initialize Firebase with proper error handling and explicit database selection."""
    try:
        # Clear any existing apps to ensure clean initialization
        if firebase_admin._apps:
            apps_to_delete = list(firebase_admin._apps.values())
            for app in apps_to_delete:
                firebase_admin.delete_app(app)
        
        # Check if service account key exists
        service_key_path = "serviceAccountKey.json"
        if not os.path.exists(service_key_path):
            print(f"❌ Error: {service_key_path} not found!")
            print("Please download your Firebase service account key and place it in the project directory.")
            return None
        
        # Initialize Firebase with explicit project ID
        cred = credentials.Certificate(service_key_path)
        app = firebase_admin.initialize_app(cred, {
            'projectId': 'bteb-672bd'  # Use your actual project ID
        })
        print("✅ Firebase initialized successfully with project: bteb-672bd")
        
        # Create Firestore client with explicit database ID
        # Always use 'result' database - never fall back to default
        db_client = firestore.client(database_id='result1')
        print("✅ Connected to database: result")
        return db_client
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return None

db = initialize_firebase()

# ---------------------------
# Firestore Helpers
# ---------------------------
def add_institute(program_name, regulation_year, inst_code, inst_name, district):
    """Create or update an institute with flattened structure."""
    # Use a single document ID that combines all hierarchy levels
    doc_id = f"{program_name}_{regulation_year}_{inst_code}"
    
    inst_ref = db.collection("institutes").document(doc_id)
    inst_ref.set({
        "program": program_name,
        "regulation_year": regulation_year,
        "institute_code": inst_code,
        "name": inst_name,
        "district": district
    }, merge=True)

    return inst_ref


def add_student(program_name, regulation_year, inst_code, roll):
    """Create or update student with flattened structure."""
    # Use a single document ID that combines all hierarchy levels
    doc_id = f"{program_name}_{regulation_year}_{inst_code}_{roll}"
    
    student_ref = db.collection("students").document(doc_id)
    student_ref.set({
        "program": program_name,
        "regulation_year": regulation_year,
        "institute_code": inst_code,
        "roll_number": roll
    }, merge=True)
    return student_ref


def add_or_update_gpa(student_ref, semester, gpa_value, ref_subjects=None):
    """Store GPA or reference subjects for a student as document fields."""
    # Get current student data
    student_doc = student_ref.get()
    current_data = student_doc.to_dict() if student_doc.exists else {}
    
    # Initialize gpa_data if it doesn't exist
    if 'gpa_data' not in current_data:
        current_data['gpa_data'] = {}
    
    # Store GPA data for this semester
    if gpa_value == "ref":
        current_data['gpa_data'][f'sem_{semester}'] = {
            "semester": semester,
            "gpa": "ref",
            "ref_subjects": ref_subjects or []
        }
        print(f"⚠️ {student_ref.id} Sem {semester}: GPA is REF with {ref_subjects}")
    else:
        current_data['gpa_data'][f'sem_{semester}'] = {
            "semester": semester,
            "gpa": float(gpa_value),
            "ref_subjects": []
        }
        print(f"✅ {student_ref.id} Sem {semester}: GPA {gpa_value}")
    
    # Update the student document with all GPA data
    student_ref.set(current_data, merge=True)


def add_or_update_cgpa(student_ref, cgpa_value):
    """Store CGPA for a student as document field."""
    # Get current student data
    student_doc = student_ref.get()
    current_data = student_doc.to_dict() if student_doc.exists else {}
    
    # Store CGPA data
    current_data['cgpa_data'] = {
        "cgpa": float(cgpa_value),
        "calculated_from": "all_semesters"
    }
    
    # Update the student document
    student_ref.set(current_data, merge=True)
    print(f"🎯 {student_ref.id}: CGPA {cgpa_value}")


def batch_write_to_firestore(batch_data, batch_size=10):
    """Write data to Firestore using batch operations for maximum speed."""
    if not db:
        print("❌ Firebase not initialized. Cannot proceed.")
        return False
    
    total_operations = len(batch_data)
    print(f"🚀 Starting batch write: {total_operations} operations")
    
    start_time = time.time()
    successful_writes = 0
    
    # Process in batches of 500 (Firestore limit)
    for i in range(0, total_operations, batch_size):
        batch = db.batch()
        current_batch = batch_data[i:i + batch_size]
        
        for operation in current_batch:
            try:
                if operation['type'] == 'institute':
                    doc_id = f"{operation['program']}_{operation['regulation']}_{operation['inst_code']}"
                    doc_ref = db.collection("institutes").document(doc_id)
                    batch.set(doc_ref, operation['data'])
                
                elif operation['type'] == 'student':
                    doc_id = f"{operation['program']}_{operation['regulation']}_{operation['inst_code']}_{operation['roll']}"
                    doc_ref = db.collection("students").document(doc_id)
                    batch.set(doc_ref, operation['data'])
                
                # GPA data is now embedded in student documents, so no separate GPA operations needed
                
            except Exception as e:
                print(f"❌ Error preparing batch operation: {e}")
                continue
        
        # Commit the batch
        try:
            batch.commit()
            successful_writes += len(current_batch)
            progress = (i + len(current_batch)) / total_operations * 100
            print(f"📊 Progress: {progress:.1f}% ({successful_writes}/{total_operations} operations)")
            
            # Add delay between batches to avoid quota limits
            if i + batch_size < total_operations:  # Don't delay after last batch
                time.sleep(5)  # 5 second delay between batches
                
        except Exception as e:
            print(f"❌ Error committing batch: {e}")
            print(f"⏳ Waiting 5 seconds before retry...")
            time.sleep(5)  # Wait 5 seconds before continuing
            continue
    
    end_time = time.time()
    duration = end_time - start_time
    ops_per_second = successful_writes / duration if duration > 0 else 0
    
    print(f"✅ Batch write completed!")
    print(f"📊 Successfully wrote: {successful_writes}/{total_operations} operations")
    print(f"⏱️ Time taken: {duration:.2f} seconds")
    print(f"🚀 Speed: {ops_per_second:.1f} operations/second")
    
    return successful_writes == total_operations


def parallel_batch_write(batch_data, max_workers=4, batch_size=500):
    """Write data to Firestore using parallel batch operations for maximum speed."""
    if not db:
        print("❌ Firebase not initialized. Cannot proceed.")
        return False
    
    total_operations = len(batch_data)
    print(f"🚀 Starting parallel batch write: {total_operations} operations")
    print(f"🔧 Using {max_workers} parallel workers")
    
    start_time = time.time()
    successful_writes = 0
    lock = threading.Lock()
    
    def process_batch(batch_chunk):
        """Process a single batch chunk."""
        local_db = firestore.client(database_id='result1')  # Create new client for thread
        batch = local_db.batch()
        local_successful = 0
        
        for operation in batch_chunk:
            try:
                if operation['type'] == 'institute':
                    doc_id = f"{operation['program']}_{operation['regulation']}_{operation['inst_code']}"
                    doc_ref = local_db.collection("institutes").document(doc_id)
                    batch.set(doc_ref, operation['data'])
                
                elif operation['type'] == 'student':
                    doc_id = f"{operation['program']}_{operation['regulation']}_{operation['inst_code']}_{operation['roll']}"
                    doc_ref = local_db.collection("students").document(doc_id)
                    batch.set(doc_ref, operation['data'])
                
                # GPA data is now embedded in student documents, so no separate GPA operations needed
                
            except Exception as e:
                print(f"❌ Error preparing batch operation: {e}")
                continue
        
        # Commit the batch
        try:
            batch.commit()
            local_successful = len(batch_chunk)
        except Exception as e:
            print(f"❌ Error committing batch: {e}")
        
        return local_successful
    
    # Split data into chunks for parallel processing
    chunks = [batch_data[i:i + batch_size] for i in range(0, total_operations, batch_size)]
    
    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(process_batch, chunk): chunk for chunk in chunks}
        
        for future in as_completed(future_to_chunk):
            try:
                chunk_successful = future.result()
                with lock:
                    successful_writes += chunk_successful
                    progress = successful_writes / total_operations * 100
                    print(f"📊 Progress: {progress:.1f}% ({successful_writes}/{total_operations} operations)")
            except Exception as e:
                print(f"❌ Error in parallel processing: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    ops_per_second = successful_writes / duration if duration > 0 else 0
    
    print(f"✅ Parallel batch write completed!")
    print(f"📊 Successfully wrote: {successful_writes}/{total_operations} operations")
    print(f"⏱️ Time taken: {duration:.2f} seconds")
    print(f"🚀 Speed: {ops_per_second:.1f} operations/second")
    
    return successful_writes == total_operations


# ---------------------------
# PDF Parser
# ---------------------------
def parse_pdf_results(pdf_path, debug=False):
    """
    Optimized PDF parser for 4th and 6th semester BTEB results:
    - 4th Semester: GPA1-GPA4
    - 6th Semester: GPA1-GPA6
    Focuses on semester GPA data without CGPA complexity.
    """
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file '{pdf_path}' not found!")
        return {}
    
    try:
        print(f"📖 Reading PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        
        # Optimize: Extract text from all pages at once
        text = ""
        total_pages = len(reader.pages)
        print(f"📄 Processing {total_pages} pages...")
        
        for i, page in enumerate(reader.pages):
            if debug and i % 100 == 0:  # Progress indicator for large PDFs
                print(f"  📄 Processed {i}/{total_pages} pages...")
            text += page.extract_text() + "\n"
            
        print(f"✅ PDF reading completed: {len(text)} characters")
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return {}

    institutes = {}
    current_inst = None
    current_student_data = {}
    current_ref_subjects = []
    pending_gpa_data = {}  # Store GPA data that needs to be added to students
    
    if debug:
        print("🔍 DEBUG MODE: Analyzing PDF structure...")
        print(f"📄 Total characters: {len(text)}")
        print()

    # Split text into lines and process
    lines = text.splitlines()
    
    if debug:
        print(f"📄 Total lines: {len(lines)}")
        print("🔍 First 20 non-empty lines:")
        count = 0
        for i, line in enumerate(lines):
            if line.strip() and count < 20:
                count += 1
                print(f"{count:2d}: {line}")
        print()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        # Look for institute headers: "11044 - Himaloy Polytechnic Institute of Technology, Panchagar"
        # Handle cases like "Page 1 of 122311044 - Himaloy Polytechnic Institute of Technology, Panchagar"
        # The institute code should be 5 digits (like 11044), not the page number (1223)
        inst_match = re.search(r'(\d{5})\s*-\s*([^,]+),\s*([A-Za-z\s]+)', line)
        if inst_match:
            inst_code = inst_match.group(1).strip()
            inst_name = inst_match.group(2).strip()
            district = inst_match.group(3).strip()
            current_inst = inst_code
            institutes[current_inst] = {
                "name": inst_name,
                "district": district,
                "students": {}
            }
            print(f"🏫 Found Institute: {inst_code} - {inst_name}, {district}")
            continue

        # Optimized student processing for 4th and 6th semester formats
        if current_inst:
            # Pattern: Standard format with parentheses: "700014 (gpa4: 3.76, gpa3: 3.54, gpa2: 3.34,"
            # Enhanced to handle incomplete patterns and multi-line GPA values
            student_matches = re.findall(r'(\d{6,8})\s*[\(\{]([^)]*)', line)
            
            # Process standard format students
            for roll, data in student_matches:
                if roll not in institutes[current_inst]["students"]:
                    institutes[current_inst]["students"][roll] = {
                        "gpas": {},
                        "ref_subjects": []
                    }
                
                # Extract GPA values from the data - FIXED to capture only numeric values
                # Pattern: gpa1: 3.36) or gpa1: ref, or gpa1: 3.36, - stops at ) or , or space
                gpa_matches = re.findall(r'gpa(\d+):\s*([\d.]+|ref)(?:\)|,|\s|$)', data, re.IGNORECASE)
                for sem_str, gpa in gpa_matches:
                    sem_num = int(sem_str)
                    if 1 <= sem_num <= 8:  # Supports GPA1 to GPA8
                        # Handle empty GPA values (incomplete patterns)
                        if not gpa or gpa.strip() == '':
                            if debug:
                                print(f"    ⚠️ Incomplete GPA {sem_num} for student {roll} - will check next line")
                            # Mark this as incomplete - we'll check the next line
                            institutes[current_inst]["students"][roll]["incomplete_gpa"] = sem_num
                            continue
                        institutes[current_inst]["students"][roll]["gpas"][sem_num] = gpa
                        if debug:
                            print(f"    📝 Added GPA {sem_num}: {gpa} to student {roll}")
                
                # Extract referred subjects
                ref_match = re.search(r'ref_sub:\s*([^}]+)', data, re.IGNORECASE)
                if ref_match:
                    subs = ref_match.group(1).strip()
                    ref_subjects = [s.strip() for s in subs.split(',') if s.strip()]
                    institutes[current_inst]["students"][roll]["ref_subjects"].extend(ref_subjects)
                    if debug:
                        print(f"    📝 Added ref subjects: {ref_subjects} to student {roll}")
                
                if debug:
                    print(f"👨‍🎓 Processing Student: {roll} with data: {data}")
            
            # Check for continuation GPA values on the current line (for incomplete patterns)
            # Look for patterns like "3.60, ref_sub: 28542(T) }" or just "3.60"
            if institutes[current_inst]["students"]:
                last_roll = list(institutes[current_inst]["students"].keys())[-1]
                last_student = institutes[current_inst]["students"][last_roll]
                
                # Check if the last student has an incomplete GPA
                if "incomplete_gpa" in last_student:
                    incomplete_sem = last_student["incomplete_gpa"]
                    
                    # Look for GPA value at the start of the line
                    gpa_value_match = re.match(r'^\s*([\d.]+)', line.strip())
                    if gpa_value_match:
                        gpa_value = gpa_value_match.group(1)
                        last_student["gpas"][incomplete_sem] = gpa_value
                        if "incomplete_gpa" in last_student:
                            del last_student["incomplete_gpa"]  # Remove the incomplete marker
                        if debug:
                            print(f"    📝 Added continuation GPA {incomplete_sem}: {gpa_value} to student {last_roll}")
                    
                    # Also check for GPA values followed by ref_sub or closing brace
                    gpa_with_context = re.search(r'([\d.]+),\s*ref_sub:', line)
                    if gpa_with_context:
                        gpa_value = gpa_with_context.group(1)
                        last_student["gpas"][incomplete_sem] = gpa_value
                        if "incomplete_gpa" in last_student:
                            del last_student["incomplete_gpa"]
                        if debug:
                            print(f"    📝 Added continuation GPA {incomplete_sem}: {gpa_value} to student {last_roll} (with ref_sub)")
            
            
            # Look for continuation GPA data that applies to the last student(s)
            # Enhanced patterns to handle all continuation cases
            gpa_continuation_matches = re.findall(r'gpa(\d+):\s*([\d.]+|ref)\)?(\d+)?', line)
            
            for sem_str, gpa, next_roll in gpa_continuation_matches:
                sem_num = int(sem_str)
                if 1 <= sem_num <= 8 and gpa and gpa.strip():
                    # If there's a next roll number, this GPA belongs to the previous student
                    if next_roll:
                        # Find the student just before this roll number
                        student_rolls = list(institutes[current_inst]["students"].keys())
                        if student_rolls:
                            # Find the student with roll number less than next_roll
                            for roll in reversed(student_rolls):
                                if int(roll) < int(next_roll):
                                    institutes[current_inst]["students"][roll]["gpas"][sem_num] = gpa
                                    if debug:
                                        print(f"    📝 Added GPA {sem_num}: {gpa} to student {roll} (before {next_roll})")
                                    break
                    else:
                        # No next roll, add to the most recent student
                        if institutes[current_inst]["students"]:
                            last_roll = list(institutes[current_inst]["students"].keys())[-1]
                            institutes[current_inst]["students"][last_roll]["gpas"][sem_num] = gpa
                            if debug:
                                print(f"    📝 Added GPA {sem_num}: {gpa} to student {last_roll}")
            
            # Enhanced continuation pattern for incomplete lines
            # Handle cases like "gpa1: 3.36)700022" or "3.50, gpa5: 3.61, gpa4: 3.22)500027"
            continuation_pattern = re.search(r'([\d.]+),\s*gpa(\d+):\s*([\d.]+|ref)', line)
            if continuation_pattern:
                prev_gpa, sem_str, gpa = continuation_pattern.groups()
                sem_num = int(sem_str)
                if 1 <= sem_num <= 8 and institutes[current_inst]["students"]:
                    last_roll = list(institutes[current_inst]["students"].keys())[-1]
                    # Add the previous GPA value to the last student
                    if prev_gpa and prev_gpa.strip():
                        # Find which semester this belongs to (usually the previous one)
                        existing_semesters = list(institutes[current_inst]["students"][last_roll]["gpas"].keys())
                        if existing_semesters:
                            prev_sem = max(existing_semesters)
                            if prev_sem not in institutes[current_inst]["students"][last_roll]["gpas"]:
                                institutes[current_inst]["students"][last_roll]["gpas"][prev_sem] = prev_gpa
                                if debug:
                                    print(f"    📝 Added continuation GPA {prev_sem}: {prev_gpa} to student {last_roll}")
                    
                    # Add the current GPA
                    institutes[current_inst]["students"][last_roll]["gpas"][sem_num] = gpa
                    if debug:
                        print(f"    📝 Added continuation GPA {sem_num}: {gpa} to student {last_roll}")
            
            # NEW: Handle GPA values on continuation lines (like "3.60, ref_sub:" or "3.50)")
            # This catches cases where GPA1 value is on the next line after "gpa1:"
            continuation_gpa_pattern = re.search(r'^\s*([\d.]+)(?:,\s*(?:ref_sub|\})|\))', line)
            if continuation_gpa_pattern and institutes[current_inst]["students"]:
                gpa_value = continuation_gpa_pattern.group(1)
                last_roll = list(institutes[current_inst]["students"].keys())[-1]
                last_student = institutes[current_inst]["students"][last_roll]
                
                # Check if this student has an incomplete GPA
                if "incomplete_gpa" in last_student:
                    incomplete_sem = last_student["incomplete_gpa"]
                    last_student["gpas"][incomplete_sem] = gpa_value
                    del last_student["incomplete_gpa"]  # Remove the incomplete marker
                    if debug:
                        print(f"    📝 Added continuation GPA {incomplete_sem}: {gpa_value} to student {last_roll}")
                else:
                    # If no incomplete GPA marker, try to determine which semester this belongs to
                    # Look for the most recent incomplete semester
                    existing_semesters = sorted(last_student["gpas"].keys())
                    if existing_semesters:
                        # Find the gap in semesters (e.g., if we have 4,3,2 but missing 1)
                        for sem in range(1, max(existing_semesters) + 1):
                            if sem not in existing_semesters:
                                last_student["gpas"][sem] = gpa_value
                                if debug:
                                    print(f"    📝 Added missing GPA {sem}: {gpa_value} to student {last_roll}")
                                break
            
            # Additional pattern: Look for GPA data that might be on separate lines or in different formats
            standalone_gpa_matches = re.findall(r'gpa(\d+):\s*([\d.]+|ref)(?:\)|,|\s|$)', line)
            for sem_str, gpa in standalone_gpa_matches:
                sem_num = int(sem_str)
                if 1 <= sem_num <= 8 and institutes[current_inst]["students"] and gpa and gpa.strip():
                    # Add to the most recent student if not already present
                    last_roll = list(institutes[current_inst]["students"].keys())[-1]
                    if sem_num not in institutes[current_inst]["students"][last_roll]["gpas"]:
                        institutes[current_inst]["students"][last_roll]["gpas"][sem_num] = gpa
                        if debug:
                            print(f"    📝 Added standalone GPA {sem_num}: {gpa} to student {last_roll}")
            
            
            # Look for reference subjects continuation: "ref_sub: 28542(T) }"
            ref_continuation = re.search(r'ref_sub:\s*([^}]+)', line)
            if ref_continuation:
                subs = ref_continuation.group(1).strip()
                ref_subjects = [s.strip() for s in subs.split(',') if s.strip()]
                
                # Add to the most recent student
                if institutes[current_inst]["students"]:
                    last_roll = list(institutes[current_inst]["students"].keys())[-1]
                    institutes[current_inst]["students"][last_roll]["ref_subjects"].extend(ref_subjects)
                    if debug:
                        print(f"    📝 Added ref subjects: {ref_subjects} to student {last_roll}")
            
            # Look for subject lists: "25841(T), 25931(T), 26811(T,P),"
            subject_match = re.search(r'(\d+\([TP]\)[^,\s]*)', line)
            if subject_match:
                # Extract all subject codes from the line
                subjects = re.findall(r'(\d+\([TP]\)[^,\s]*)', line)
                if subjects:
                    # Add to the most recent student
                    if institutes[current_inst]["students"]:
                        last_roll = list(institutes[current_inst]["students"].keys())[-1]
                        institutes[current_inst]["students"][last_roll]["ref_subjects"].extend(subjects)
                        if debug:
                            print(f"    📝 Added subjects: {subjects} to student {last_roll}")

    # Clean up and validate data
    total_students = 0
    total_gpas = 0
    
    for inst_code, inst_data in institutes.items():
        for roll, student_data in inst_data["students"].items():
            total_students += 1
            total_gpas += len(student_data["gpas"])
            
            # Remove duplicates from ref_subjects
            inst_data["students"][roll]["ref_subjects"] = list(set(student_data["ref_subjects"]))
            
            if debug and len(student_data["gpas"]) > 0:
                semesters = sorted(student_data["gpas"].keys())
                print(f"👨‍🎓 Student {roll}: Semesters {semesters}, {len(student_data['ref_subjects'])} ref subjects")
                
                # Check for missing semesters in sequence
                if len(semesters) > 1:
                    expected_semesters = list(range(min(semesters), max(semesters) + 1))
                    missing_semesters = [s for s in expected_semesters if s not in semesters]
                    if missing_semesters:
                        print(f"    ⚠️ Missing semesters for student {roll}: {missing_semesters}")

    # Clean up any temporary fields
    for inst_code, inst_data in institutes.items():
        for roll, student_data in inst_data["students"].items():
            # Remove any temporary fields
            if "incomplete_gpa" in student_data:
                del student_data["incomplete_gpa"]

    print(f"📊 Parsed {len(institutes)} institutes with {total_students} students and {total_gpas} GPA records")
    return institutes


# ---------------------------
# Transfer to Firebase
# ---------------------------
def transfer_pdf_to_firestore(pdf_path, program, regulation):
    """
    Transfer parsed PDF data to Firestore with proper hierarchy:
    programs → regulations → institutes → students → gpa
    Optimized for faster batch processing.
    """
    if not db:
        print("❌ Firebase not initialized. Cannot proceed.")
        return False
    
    print(f"🚀 Starting transfer: {program} - {regulation}")
    institutes = parse_pdf_results(pdf_path, debug=False)
    
    if not institutes:
        print("❌ No institutes found in PDF. Check the file format.")
        return False

    print(f"📊 Preparing batch data for {len(institutes)} institutes...")
    
    # Prepare all data for batch writing
    batch_data = []
    total_students = 0
    total_gpas = 0
    
    for inst_code, inst_data in institutes.items():
        # Add institute data
        batch_data.append({
            'type': 'institute',
            'program': program,
            'regulation': regulation,
            'inst_code': inst_code,
            'data': {
                "program": program,
                "regulation_year": regulation,
                "institute_code": inst_code,
                "name": inst_data["name"],
                "district": inst_data["district"]
            }
        })
        
        # Add student data with GPA data embedded
        for roll, data in inst_data["students"].items():
            total_students += 1
            
            # Prepare GPA data for this student
            gpa_data = {}
            for sem, gpa_value in data["gpas"].items():
                total_gpas += 1
                
                if gpa_value == "ref":
                    gpa_data[f"sem_{sem}"] = {
                        "semester": sem,
                        "gpa": "ref",
                        "ref_subjects": data["ref_subjects"] or []
                    }
                else:
                    try:
                        gpa_float = float(gpa_value)
                        if 0.0 <= gpa_float <= 4.0:  # Validate GPA range (0.0 to 4.0)
                            gpa_data[f"sem_{sem}"] = {
                                "semester": sem,
                                "gpa": gpa_float,
                                "ref_subjects": []
                            }
                        else:
                            print(f"    ⚠️ Invalid GPA {gpa_value} for semester {sem} (should be 0.0-4.0)")
                            continue
                    except ValueError:
                        print(f"    ⚠️ Could not convert GPA '{gpa_value}' to float for semester {sem}")
                        continue
            
            # Add student data with embedded GPA data
            student_data = {
                "program": program,
                "regulation_year": regulation,
                "institute_code": inst_code,
                "roll_number": roll,
                "gpa_data": gpa_data
            }
            
            batch_data.append({
                'type': 'student',
                'program': program,
                'regulation': regulation,
                'inst_code': inst_code,
                'roll': roll,
                'data': student_data
            })
    
    print(f"📊 Prepared {len(batch_data)} operations:")
    print(f"  - Institutes: {len(institutes)}")
    print(f"  - Students: {total_students}")
    print(f"  - GPA Records: {total_gpas}")
    
    # Execute batch write (choose method based on data size)
    print(f"\n🚀 Starting batch write to Firestore...")
    if len(batch_data) > 10000:  # Use parallel processing for large datasets
        print("🔧 Using parallel processing for large dataset...")
        success = parallel_batch_write(batch_data, max_workers=4)
    else:
        print("🔧 Using standard batch processing...")
        success = batch_write_to_firestore(batch_data)
    
    if success:
        print(f"\n✅ Transfer completed successfully!")
        print(f"📊 Summary: {len(institutes)} institutes, {total_students} students, {total_gpas} GPA records")
        return True
    else:
        print(f"\n❌ Transfer failed!")
        return False


# ---------------------------
# Main Execution
# ---------------------------
def debug_pdf(pdf_path):
    """Debug function to analyze PDF content without transferring to Firestore."""
    print("🔍 PDF Debug Mode - Analyzing content without transfer")
    print("=" * 60)
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file '{pdf_path}' not found!")
        return
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return
    
    lines = text.splitlines()
    print(f"📄 Total lines in PDF: {len(lines)}")
    print(f"📄 Non-empty lines: {len([l for l in lines if l.strip()])}")
    
    print("\n🔍 First 100 non-empty lines:")
    print("-" * 80)
    count = 0
    for i, line in enumerate(lines):
        if line.strip() and count < 100:
            count += 1
            print(f"{count:3d}: {line}")
    print("-" * 80)
    
    # Look for potential institute patterns
    print("\n🔍 Searching for potential institute patterns...")
    institute_candidates = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Look for lines that might be institute headers
        if re.search(r'\d+', line) and (',' in line or '-' in line):
            institute_candidates.append((i+1, line))
    
    print(f"Found {len(institute_candidates)} potential institute lines:")
    for line_num, line in institute_candidates[:20]:  # Show first 20
        print(f"  {line_num:4d}: {line}")
    
    if len(institute_candidates) > 20:
        print(f"  ... and {len(institute_candidates) - 20} more")

def main():
    """Main function to run the PDF to Firestore transfer."""
    print("🎓 BTEB Results PDF to Firestore Transfer Tool")
    print("=" * 50)
    
    # Check Firebase initialization
    if not db:
        print("❌ Firebase initialization failed. Please check your service account key.")
        return
    
    # Get user inputs
    try:
        PDF_FILE = input("📄 Enter PDF file path: ").strip()
        if not PDF_FILE:
            print("❌ PDF file path is required!")
            return
            
        # Ask if user wants to debug first
        debug_choice = input("🔍 Debug PDF content first? (y/N): ").strip().lower()
        if debug_choice in ['y', 'yes']:
            debug_pdf(PDF_FILE)
            print("\n" + "="*60)
            
        PROGRAM = input("🎓 Enter Program name (e.g., 'Diploma in Engineering'): ").strip()
        if not PROGRAM:
            print("❌ Program name is required!")
            return
            
        REGULATION = input("📅 Enter Regulation year (e.g., '2022'): ").strip()
        if not REGULATION:
            print("❌ Regulation year is required!")
            return
            
        # Validate regulation year format
        if not REGULATION.isdigit() or len(REGULATION) != 4:
            print("⚠️ Warning: Regulation year should be a 4-digit year (e.g., 2022)")
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        return
    except Exception as e:
        print(f"❌ Error getting input: {e}")
        return
    
    # Confirm before proceeding
    print(f"\n📋 Summary:")
    print(f"   PDF File: {PDF_FILE}")
    print(f"   Program: {PROGRAM}")
    print(f"   Regulation: {REGULATION}")
    
    confirm = input("\n❓ Proceed with transfer? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Transfer cancelled.")
        return
    
    # Execute transfer
    success = transfer_pdf_to_firestore(PDF_FILE, PROGRAM, REGULATION)
    
    if success:
        print("\n🎉 Transfer completed successfully!")
    else:
        print("\n❌ Transfer failed. Please check the errors above.")

if __name__ == "__main__":
    main()
