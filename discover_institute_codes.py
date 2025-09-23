#!/usr/bin/env python3
"""
Script to discover institute codes by testing common patterns
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

def discover_institute_codes(db):
    """Discover institute codes by testing common patterns."""
    if not db:
        print("❌ Database not available")
        return []
    
    found_institutes = []
    tested_codes = set()
    
    # Common institute code patterns for BTEB
    # Based on typical BTEB institute numbering
    base_codes = [
        # 23xxx series (2022 regulation)
        '23001', '23002', '23003', '23004', '23005', '23006', '23007', '23008', '23009', '23010',
        '23011', '23012', '23013', '23014', '23015', '23016', '23017', '23018', '23019', '23020',
        '23021', '23022', '23023', '23024', '23025', '23026', '23027', '23028', '23029', '23030',
        '23031', '23032', '23033', '23034', '23035', '23036', '23037', '23038', '23039', '23040',
        '23041', '23042', '23043', '23044', '23045', '23046', '23047', '23048', '23049', '23050',
        '23051', '23052', '23053', '23054', '23055', '23056', '23057', '23058', '23059', '23060',
        '23061', '23062', '23063', '23064', '23065', '23066', '23067', '23068', '23069', '23070',
        '23071', '23072', '23073', '23074', '23075', '23076', '23077', '23078', '23079', '23080',
        '23081', '23082', '23083', '23084', '23085', '23086', '23087', '23088', '23089', '23090',
        '23091', '23092', '23093', '23094', '23095', '23096', '23097', '23098', '23099', '23100',
        '23101', '23102', '23103', '23104', '23105', '23106', '23107', '23108', '23109', '23110',
        '23111', '23112', '23113', '23114', '23115', '23116', '23117', '23118', '23119', '23120',
        '23121', '23122', '23123', '23124', '23125', '23126', '23127', '23128', '23129', '23130',
        '23131', '23132', '23133', '23134', '23135', '23136', '23137', '23138', '23139', '23140',
        '23141', '23142', '23143', '23144', '23145', '23146', '23147', '23148', '23149', '23150',
        '23151', '23152', '23153', '23154', '23155', '23156', '23157', '23158', '23159', '23160',
        '23161', '23162', '23163', '23164', '23165', '23166', '23167', '23168', '23169', '23170',
        '23171', '23172', '23173', '23174', '23175', '23176', '23177', '23178', '23179', '23180',
        '23181', '23182', '23183', '23184', '23185', '23186', '23187', '23188', '23189', '23190',
        '23191', '23192', '23193', '23194', '23195', '23196', '23197', '23198', '23199', '23200',
        
        # 19xxx series (2019 regulation)
        '19001', '19002', '19003', '19004', '19005', '19006', '19007', '19008', '19009', '19010',
        '19011', '19012', '19013', '19014', '19015', '19016', '19017', '19018', '19019', '19020',
        '19021', '19022', '19023', '19024', '19025', '19026', '19027', '19028', '19029', '19030',
        '19031', '19032', '19033', '19034', '19035', '19036', '19037', '19038', '19039', '19040',
        '19041', '19042', '19043', '19044', '19045', '19046', '19047', '19048', '19049', '19050',
        '19051', '19052', '19053', '19054', '19055', '19056', '19057', '19058', '19059', '19060',
        '19061', '19062', '19063', '19064', '19065', '19066', '19067', '19068', '19069', '19070',
        '19071', '19072', '19073', '19074', '19075', '19076', '19077', '19078', '19079', '19080',
        '19081', '19082', '19083', '19084', '19085', '19086', '19087', '19088', '19089', '19090',
        '19091', '19092', '19093', '19094', '19095', '19096', '19097', '19098', '19099', '19100',
        
        # 16xxx series (2016 regulation)
        '16001', '16002', '16003', '16004', '16005', '16006', '16007', '16008', '16009', '16010',
        '16011', '16012', '16013', '16014', '16015', '16016', '16017', '16018', '16019', '16020',
        '16021', '16022', '16023', '16024', '16025', '16026', '16027', '16028', '16029', '16030',
        '16031', '16032', '16033', '16034', '16035', '16036', '16037', '16038', '16039', '16040',
        '16041', '16042', '16043', '16044', '16045', '16046', '16047', '16048', '16049', '16050',
        '16051', '16052', '16053', '16054', '16055', '16056', '16057', '16058', '16059', '16060',
        '16061', '16062', '16063', '16064', '16065', '16066', '16067', '16068', '16069', '16070',
        '16071', '16072', '16073', '16074', '16075', '16076', '16077', '16078', '16079', '16080',
        '16081', '16082', '16083', '16084', '16085', '16086', '16087', '16088', '16089', '16090',
        '16091', '16092', '16093', '16094', '16095', '16096', '16097', '16098', '16099', '16100',
        
        # 10xxx series (2010 regulation)
        '10001', '10002', '10003', '10004', '10005', '10006', '10007', '10008', '10009', '10010',
        '10011', '10012', '10013', '10014', '10015', '10016', '10017', '10018', '10019', '10020',
        '10021', '10022', '10023', '10024', '10025', '10026', '10027', '10028', '10029', '10030',
        '10031', '10032', '10033', '10034', '10035', '10036', '10037', '10038', '10039', '10040',
        '10041', '10042', '10043', '10044', '10045', '10046', '10047', '10048', '10049', '10050',
        '10051', '10052', '10053', '10054', '10055', '10056', '10057', '10058', '10059', '10060',
        '10061', '10062', '10063', '10064', '10065', '10066', '10067', '10068', '10069', '10070',
        '10071', '10072', '10073', '10074', '10075', '10076', '10077', '10078', '10079', '10080',
        '10081', '10082', '10083', '10084', '10085', '10086', '10087', '10088', '10089', '10090',
        '10091', '10092', '10093', '10094', '10095', '10096', '10097', '10098', '10099', '10100',
    ]
    
    print(f"🔍 Testing {len(base_codes)} potential institute codes...")
    
    # Test each institute code
    for i, code in enumerate(base_codes):
        if i % 50 == 0:
            print(f"📊 Progress: {i}/{len(base_codes)} codes tested...")
        
        # Test institute document
        institute_doc_id = f"Diploma in Engineering_2022_{code}"
        try:
            doc_ref = db.collection('institutes').document(institute_doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                if data:
                    found_institutes.append({
                        'code': code,
                        'name': data.get('name', ''),
                        'district': data.get('district', ''),
                        'program': data.get('program', ''),
                        'regulation_year': data.get('regulation_year', ''),
                        'doc_id': institute_doc_id
                    })
                    print(f"✅ Found institute: {code} - {data.get('name', 'N/A')}")
                    tested_codes.add(code)
        except Exception as e:
            # Silently continue on errors
            continue
    
    print(f"\n✅ Discovery completed!")
    print(f"📊 Found {len(found_institutes)} institutes")
    print(f"📊 Tested {len(tested_codes)} unique codes")
    
    # Extract unique codes
    unique_codes = sorted(list(set([inst['code'] for inst in found_institutes])))
    
    # Save results
    output_data = {
        'institute_codes': unique_codes,
        'institutes_data': found_institutes,
        'total_codes': len(unique_codes),
        'total_records': len(found_institutes)
    }
    
    with open('discovered_institute_codes.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"💾 Saved results to discovered_institute_codes.json")
    print(f"📋 Found institute codes: {unique_codes}")
    
    return unique_codes

def main():
    print("🎓 BTEB Institute Code Discovery Tool")
    print("=" * 45)
    
    # Initialize Firebase
    db = initialize_firebase()
    
    if not db:
        print("❌ Failed to initialize Firebase")
        return
    
    # Discover institute codes
    institute_codes = discover_institute_codes(db)
    
    if institute_codes:
        print(f"\n✅ Successfully discovered {len(institute_codes)} institute codes")
        print("📋 Codes:", institute_codes)
    else:
        print("❌ No institute codes found")

if __name__ == "__main__":
    main()

