#!/usr/bin/env python3
"""
Setup script for multiple Supabase projects
Easy way to configure 4-5 Supabase projects for BTEB Results
"""

import json
import os
from multi_supabase import supabase_manager

def setup_projects():
    """Interactive setup for multiple Supabase projects"""
    print("🎯 BTEB Results - Multi-Project Supabase Setup")
    print("=" * 50)
    print("This script will help you configure 4-5 Supabase projects")
    print("for automatic fallback when searching for student results.\n")
    
    projects = {}
    search_order = []
    
    # Project configurations
    project_configs = [
        {
            "name": "primary",
            "description": "Primary BTEB Results Database - Main production data",
            "priority": 1
        },
        {
            "name": "secondary", 
            "description": "Secondary BTEB Results Database - Additional data source",
            "priority": 2
        },
        {
            "name": "tertiary",
            "description": "Tertiary BTEB Results Database - Extended coverage", 
            "priority": 3
        },
        {
            "name": "backup1",
            "description": "Backup Database 1 - Redundancy and failover",
            "priority": 4
        },
        {
            "name": "backup2",
            "description": "Backup Database 2 - Additional redundancy",
            "priority": 5
        }
    ]
    
    print("📋 Please provide details for each project:")
    print("(Press Enter to skip a project)\n")
    
    for config in project_configs:
        print(f"🔧 Project {config['priority']}: {config['name'].upper()}")
        print(f"   Description: {config['description']}")
        
        url = input(f"   Supabase URL: ").strip()
        if not url:
            print(f"   ⏭️ Skipping {config['name']}\n")
            continue
            
        key = input(f"   Supabase Anon Key: ").strip()
        if not key:
            print(f"   ⏭️ Skipping {config['name']} (no key provided)\n")
            continue
        
        projects[config['name']] = {
            "url": url,
            "key": key,
            "description": config['description'],
            "priority": config['priority']
        }
        
        search_order.append(config['name'])
        print(f"   ✅ Added {config['name']}\n")
    
    if not projects:
        print("❌ No projects configured. Exiting.")
        return
    
    # Create configuration
    config_data = {
        "current_project": search_order[0] if search_order else None,
        "search_order": search_order,
        "projects": projects,
        "settings": {
            "enable_fallback": True,
            "max_projects_to_search": len(search_order),
            "timeout_per_project": 10,
            "log_search_attempts": True,
            "cache_results": False
        }
    }
    
    # Save configuration
    config_file = "supabase_projects.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"✅ Configuration saved to {config_file}")
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return
    
    # Test connections
    print(f"\n🧪 Testing connections to {len(projects)} projects...")
    print("=" * 40)
    
    for project_name in search_order:
        print(f"Testing {project_name}...", end=" ")
        try:
            project = supabase_manager.projects.get(project_name)
            if project and project.test_connection():
                print("✅ Connected")
            else:
                print("❌ Failed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Setup complete!")
    print(f"📊 Configured {len(projects)} projects")
    print(f"🔍 Search order: {' → '.join(search_order)}")
    print(f"\n🚀 You can now start the API server:")
    print(f"   python multi_supabase_api_server.py")

def add_single_project():
    """Add a single project to existing configuration"""
    print("🔧 Add Single Supabase Project")
    print("=" * 30)
    
    name = input("Project name: ").strip()
    if not name:
        print("❌ Project name required")
        return
    
    url = input("Supabase URL: ").strip()
    if not url:
        print("❌ URL required")
        return
        
    key = input("Supabase Anon Key: ").strip()
    if not key:
        print("❌ Key required")
        return
    
    description = input("Description (optional): ").strip()
    
    try:
        supabase_manager.add_project(name, url, key, description)
        supabase_manager.save_config()
        print(f"✅ Added project: {name}")
        
        # Test connection
        print(f"Testing connection...", end=" ")
        if supabase_manager.projects[name].test_connection():
            print("✅ Connected")
        else:
            print("❌ Failed")
            
    except Exception as e:
        print(f"❌ Error adding project: {e}")

def main():
    """Main function"""
    print("Choose an option:")
    print("1. Setup multiple projects (4-5 projects)")
    print("2. Add single project")
    print("3. List current projects")
    print("4. Test all connections")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        setup_projects()
    elif choice == "2":
        add_single_project()
    elif choice == "3":
        supabase_manager.list_projects()
    elif choice == "4":
        supabase_manager.test_all_connections()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
