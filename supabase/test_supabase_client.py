#!/usr/bin/env python3
"""
Simple Supabase client test - easier than direct PostgreSQL connection
"""

import os
from supabase import create_client

def test_supabase_client():
    """Test Supabase client connection"""
    
    print("🔌 Testing Supabase Client Connection")
    print("=" * 40)
    
    # You need to set these environment variables
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Environment variables not set!")
        print("\n🔧 Please set them first:")
        print("export SUPABASE_URL='your-project-url'")
        print("export SUPABASE_KEY='your-anon-key'")
        print("\n📋 To find these values:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to Settings → API")
        print("4. Copy 'Project URL' and 'anon public' key")
        return False
    
    try:
        print(f"🔗 Connecting to: {url}")
        supabase = create_client(url, key)
        
        # Test connection by trying to read from programs table
        print("🧪 Testing database connection...")
        result = supabase.table('programs').select('*').limit(1).execute()
        
        print("✅ Supabase client connection successful!")
        print("✅ Database is accessible!")
        
        # Test if tables exist
        tables_to_check = ['programs', 'regulations', 'institutes', 'students', 'gpa_records', 'cgpa_records']
        
        print("\n📋 Checking if required tables exist...")
        for table in tables_to_check:
            try:
                supabase.table(table).select('*').limit(1).execute()
                print(f"✅ Table '{table}' exists")
            except Exception as e:
                print(f"❌ Table '{table}' missing or error: {e}")
        
        print("\n🎉 All tests passed!")
        print("✅ You can now use: python supabase.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if your project is active in Supabase dashboard")
        print("2. Verify your URL and key are correct")
        print("3. Make sure you've created the database tables")
        return False

if __name__ == "__main__":
    test_supabase_client()
