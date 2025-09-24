import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from PyPDF2 import PdfReader
from supabase import create_client, Client
import json

# ---------------------------
# Supabase Initialization
# ---------------------------
def initialize_supabase():
    """Initialize Supabase client with proper error handling."""
    try:
        # Check if Supabase credentials exist
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables not found!")
            print("Please set your Supabase credentials:")
            print("export SUPABASE_URL='your-supabase-url'")
            print("export SUPABASE_KEY='your-supabase-anon-key'")
            return None
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase initialized successfully")
        return supabase
        
    except Exception as e:
        print(f"❌ Supabase initialization failed: {e}")
        return None

# Initialize Supabase client
supabase = initialize_supabase()

# ---------------------------
# Supabase Database Helpers
# ---------------------------
def add_program(program_name):
    """Create or update a program."""
    try:
        result = supabase.table('programs').upsert({
            'name': program_name
        }, on_conflict='name').execute()
        print(f"✅ Program '{program_name}' created/updated")
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error adding program '{program_name}': {e}")
        return None

def add_regulation(program_name, regulation_year):
    """Create or update a regulation under a program."""
    try:
        # First ensure program exists
        program = add_program(program_name)
        if not program:
            return None
            
        result = supabase.table('regulations').upsert({
            'program_name': program_name,
            'year': regulation_year
        }, on_conflict='program_name,year').execute()
        print(f"✅ Regulation '{regulation_year}' for program '{program_name}' created/updated")
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error adding regulation '{regulation_year}' for program '{program_name}': {e}")
        return None

def add_institute(program_name, regulation_year, inst_code, inst_name, district):
    """Create or update an institute under program/regulation."""
    try:
        # First ensure regulation exists
        regulation = add_regulation(program_name, regulation_year)
        if not regulation:
            return None
            
        result = supabase.table('institutes').upsert({
            'program_name': program_name,
            'regulation_year': regulation_year,
            'institute_code': inst_code,
            'name': inst_name,
            'district': district
        }, on_conflict='program_name,regulation_year,institute_code').execute()
        print(f"✅ Institute '{inst_code}' - '{inst_name}' created/updated")
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error adding institute '{inst_code}': {e}")
        return None

def add_student(program_name, regulation_year, inst_code, roll):
    """Create or update student under an institute."""
    try:
        # First ensure institute exists
        institute = add_institute(program_name, regulation_year, inst_code, "", "")
        if not institute:
            return None
            
        result = supabase.table('students').upsert({
            'program_name': program_name,
            'regulation_year': regulation_year,
            'institute_code': inst_code,
            'roll_number': roll
        }, on_conflict='program_name,regulation_year,institute_code,roll_number').execute()
        print(f"✅ Student '{roll}' created/updated")
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error adding student '{roll}': {e}")
        return None

def add_or_update_gpa(program_name, regulation_year, inst_code, roll, semester, gpa_value, ref_subjects=None):
    """Store GPA or reference subjects for a student."""
    try:
        # First ensure student exists
        student = add_student(program_name, regulation_year, inst_code, roll)
        if not student:
            return None
            
        gpa_data = {
            'program_name': program_name,
            'regulation_year': regulation_year,
            'institute_code': inst_code,
            'roll_number': roll,
            'semester': semester,
            'gpa': gpa_value if gpa_value != "ref" else None,
            'is_reference': gpa_value == "ref",
            'ref_subjects': ref_subjects or []
        }
        
        result = supabase.table('gpa_records').upsert(gpa_data, 
            on_conflict='program_name,regulation_year,institute_code,roll_number,semester').execute()
        
        if gpa_value == "ref":
            print(f"⚠️ {roll} Sem {semester}: GPA is REF with {ref_subjects}")
        else:
            print(f"✅ {roll} Sem {semester}: GPA {gpa_value}")
            
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error adding GPA for student '{roll}' semester {semester}: {e}")
        return None

def add_or_update_cgpa(program_name, regulation_year, inst_code, roll, cgpa_value):
    """Store CGPA for a student."""
    try:
        # First ensure student exists
        student = add_student(program_name, regulation_year, inst_code, roll)
        if not student:
            return None
            
        cgpa_data = {
            'program_name': program_name,
            'regulation_year': regulation_year,
            'institute_code': inst_code,
            'roll_number': roll,
            'cgpa': float(cgpa_value),
            'calculated_from': 'all_semesters'
        }
        
        result = supabase.table('cgpa_records').upsert(cgpa_data, 
            on_conflict='program_name,regulation_year,institute_code,roll_number').execute()
        
        print(f"🎯 {roll}: CGPA {cgpa_value}")
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error adding CGPA for student '{roll}': {e}")
        return None

# ---------------------------
# Batch Processing Functions
# ---------------------------
def batch_write_to_supabase(batch_data, batch_size=1000):
    """Write data to Supabase using batch operations for maximum speed."""
    if not supabase:
        print("❌ Supabase not initialized. Cannot proceed.")
        return False
    
    total_operations = len(batch_data)
    print(f"🚀 Starting batch write: {total_operations} operations")
    
    start_time = time.time()
    successful_writes = 0
    
    # Process in batches
    for i in range(0, total_operations, batch_size):
        current_batch = batch_data[i:i + batch_size]
        
        try:
            # Group operations by table type
            programs = []
            regulations = []
            institutes = []
            students = []
            gpa_records = []
            cgpa_records = []
            
            for operation in current_batch:
                if operation['type'] == 'program':
                    programs.append(operation['data'])
                elif operation['type'] == 'regulation':
                    regulations.append(operation['data'])
                elif operation['type'] == 'institute':
                    institutes.append(operation['data'])
                elif operation['type'] == 'student':
                    students.append(operation['data'])
                elif operation['type'] == 'gpa':
                    gpa_records.append(operation['data'])
                elif operation['type'] == 'cgpa':
                    cgpa_records.append(operation['data'])
            
            # Execute batch inserts/upserts for each table
            if programs:
                supabase.table('programs').upsert(programs, on_conflict='name').execute()
            if regulations:
                supabase.table('regulations').upsert(regulations, on_conflict='program_name,year').execute()
            if institutes:
                supabase.table('institutes').upsert(institutes, on_conflict='program_name,regulation_year,institute_code').execute()
            if students:
                supabase.table('students').upsert(students, on_conflict='program_name,regulation_year,institute_code,roll_number').execute()
            if gpa_records:
                supabase.table('gpa_records').upsert(gpa_records, on_conflict='program_name,regulation_year,institute_code,roll_number,semester').execute()
            if cgpa_records:
                supabase.table('cgpa_records').upsert(cgpa_records, on_conflict='program_name,regulation_year,institute_code,roll_number').execute()
            
            successful_writes += len(current_batch)
            progress = (i + len(current_batch)) / total_operations * 100
            print(f"📊 Progress: {progress:.1f}% ({successful_writes}/{total_operations} operations)")
            
            # Add delay between batches to avoid rate limits
            if i + batch_size < total_operations:
                time.sleep(1)  # 1 second delay between batches
                
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

# ---------------------------
# PDF Parser (Same as original)
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
# Transfer to Supabase
# ---------------------------
def transfer_pdf_to_supabase(pdf_path, program, regulation):
    """
    Transfer parsed PDF data to Supabase with proper hierarchy:
    programs → regulations → institutes → students → gpa_records
    """
    if not supabase:
        print("❌ Supabase not initialized. Cannot proceed.")
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
    
    # Add program data
    batch_data.append({
        'type': 'program',
        'data': {'name': program}
    })
    
    # Add regulation data
    batch_data.append({
        'type': 'regulation',
        'data': {
            'program_name': program,
            'year': regulation
        }
    })
    
    for inst_code, inst_data in institutes.items():
        # Add institute data
        batch_data.append({
            'type': 'institute',
            'data': {
                'program_name': program,
                'regulation_year': regulation,
                'institute_code': inst_code,
                'name': inst_data["name"],
                'district': inst_data["district"]
            }
        })
        
        # Add student and GPA data
        for roll, data in inst_data["students"].items():
            total_students += 1
            
            # Add student data
            batch_data.append({
                'type': 'student',
                'data': {
                    'program_name': program,
                    'regulation_year': regulation,
                    'institute_code': inst_code,
                    'roll_number': roll
                }
            })
            
            # Add GPA data
            for sem, gpa_value in data["gpas"].items():
                total_gpas += 1
                
                if gpa_value == "ref":
                    gpa_data = {
                        'program_name': program,
                        'regulation_year': regulation,
                        'institute_code': inst_code,
                        'roll_number': roll,
                        'semester': sem,
                        'gpa': None,
                        'is_reference': True,
                        'ref_subjects': data["ref_subjects"] or []
                    }
                else:
                    try:
                        gpa_float = float(gpa_value)
                        if 0.0 <= gpa_float <= 4.0:  # Validate GPA range (0.0 to 4.0)
                            gpa_data = {
                                'program_name': program,
                                'regulation_year': regulation,
                                'institute_code': inst_code,
                                'roll_number': roll,
                                'semester': sem,
                                'gpa': gpa_float,
                                'is_reference': False,
                                'ref_subjects': []
                            }
                        else:
                            print(f"    ⚠️ Invalid GPA {gpa_value} for semester {sem} (should be 0.0-4.0)")
                            continue
                    except ValueError:
                        print(f"    ⚠️ Could not convert GPA '{gpa_value}' to float for semester {sem}")
                        continue
                
                batch_data.append({
                    'type': 'gpa',
                    'data': gpa_data
                })
    
    print(f"📊 Prepared {len(batch_data)} operations:")
    print(f"  - Programs: 1")
    print(f"  - Regulations: 1")
    print(f"  - Institutes: {len(institutes)}")
    print(f"  - Students: {total_students}")
    print(f"  - GPA Records: {total_gpas}")
    
    # Execute batch write
    print(f"\n🚀 Starting batch write to Supabase...")
    success = batch_write_to_supabase(batch_data)
    
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
def main():
    """Main function to run the PDF to Supabase transfer."""
    print("🎓 BTEB Results PDF to Supabase Transfer Tool")
    print("=" * 50)
    
    # Check Supabase initialization
    if not supabase:
        print("❌ Supabase initialization failed. Please check your credentials.")
        return
    
    # Get user inputs
    try:
        PDF_FILE = input("📄 Enter PDF file path: ").strip()
        if not PDF_FILE:
            print("❌ PDF file path is required!")
            return
            
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
    success = transfer_pdf_to_supabase(PDF_FILE, PROGRAM, REGULATION)
    
    if success:
        print("\n🎉 Transfer completed successfully!")
    else:
        print("\n❌ Transfer failed. Please check the errors above.")

if __name__ == "__main__":
    main()
