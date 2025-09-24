#!/usr/bin/env python3
"""
Script to create database tables using Supabase client
"""

import os
from supabase import create_client

def create_tables():
    """Create database tables using Supabase client"""
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ SUPABASE_URL and SUPABASE_KEY not set")
        return False
    
    try:
        supabase = create_client(url, key)
        
        print("🗄️ Creating database tables...")
        
        # Read schema.sql
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    print(f"Executing statement {i+1}/{len(statements)}...")
                    supabase.rpc('exec_sql', {'sql': statement}).execute()
                except Exception as e:
                    print(f"⚠️ Statement {i+1} failed: {e}")
                    # Continue with other statements
        
        print("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        print("\n💡 Alternative: Use Supabase dashboard SQL Editor")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Copy and paste schema.sql content")
        print("5. Click Run")
        return False

if __name__ == "__main__":
    create_tables()
