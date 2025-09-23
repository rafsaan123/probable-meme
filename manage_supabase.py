#!/usr/bin/env python3
"""
Supabase Project Management Script
Easy management of multiple Supabase projects
"""

import sys
import os
from multi_supabase import (
    supabase_manager, 
    add_supabase_project, 
    switch_supabase_project,
    list_supabase_projects,
    test_supabase_connections
)

def print_help():
    """Print help information"""
    print("""
🎯 Supabase Project Manager

Usage: python manage_supabase.py <command> [options]

Commands:
  list                    - List all available projects
  test                    - Test connections to all projects
  add <name> <url> <key>  - Add a new project
  switch <name>           - Switch to a different project
  remove <name>           - Remove a project
  current                 - Show current project
  help                    - Show this help

Examples:
  python manage_supabase.py list
  python manage_supabase.py add production https://prod.supabase.co prod-key
  python manage_supabase.py switch production
  python manage_supabase.py test
""")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_supabase_projects()
        
    elif command == "test":
        test_supabase_connections()
        
    elif command == "add":
        if len(sys.argv) < 5:
            print("❌ Usage: add <name> <url> <key> [description]")
            return
        
        name = sys.argv[2]
        url = sys.argv[3]
        key = sys.argv[4]
        description = sys.argv[5] if len(sys.argv) > 5 else f"Supabase project: {name}"
        
        add_supabase_project(name, url, key, description)
        supabase_manager.save_config()
        
    elif command == "switch":
        if len(sys.argv) < 3:
            print("❌ Usage: switch <project_name>")
            return
        
        project_name = sys.argv[2]
        switch_supabase_project(project_name)
        supabase_manager.save_config()
        
    elif command == "remove":
        if len(sys.argv) < 3:
            print("❌ Usage: remove <project_name>")
            return
        
        project_name = sys.argv[2]
        if project_name in supabase_manager.projects:
            supabase_manager.remove_project(project_name)
            supabase_manager.save_config()
        else:
            print(f"❌ Project {project_name} not found")
            
    elif command == "current":
        if supabase_manager.current_project:
            project = supabase_manager.projects[supabase_manager.current_project]
            print(f"🟢 Current project: {supabase_manager.current_project}")
            print(f"   Description: {project.description}")
            print(f"   URL: {project.url}")
        else:
            print("❌ No current project set")
            
    elif command == "help":
        print_help()
        
    else:
        print(f"❌ Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()
