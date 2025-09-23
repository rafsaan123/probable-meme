#!/usr/bin/env python3
"""
Multi-Project Supabase Configuration
Supports multiple Supabase projects for different environments or data sources
"""

import os
import json
from typing import Dict, List, Optional
from supabase import create_client

class SupabaseProject:
    """Represents a single Supabase project configuration"""
    
    def __init__(self, name: str, url: str, key: str, description: str = ""):
        self.name = name
        self.url = url
        self.key = key
        self.description = description
        self.client = None
    
    def get_client(self):
        """Get or create Supabase client for this project"""
        if not self.client:
            try:
                # Try the simplest approach first - direct client creation
                from supabase import create_client
                self.client = create_client(self.url, self.key)
                print(f"✅ Successfully created Supabase client for {self.name}")
            except Exception as e:
                print(f"❌ Error creating Supabase client for {self.name}: {e}")
                # If that fails, try with environment variable filtering
                try:
                    import os
                    # Remove all proxy-related environment variables
                    proxy_vars = [
                        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'proxy',
                        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
                        'FTP_PROXY', 'ftp_proxy', 'SOCKS_PROXY', 'socks_proxy'
                    ]
                    
                    # Backup and remove proxy variables
                    backup_vars = {}
                    for var in proxy_vars:
                        if var in os.environ:
                            backup_vars[var] = os.environ[var]
                            del os.environ[var]
                    
                    try:
                        self.client = create_client(self.url, self.key)
                        print(f"✅ Successfully created Supabase client for {self.name} (proxy-filtered)")
                    finally:
                        # Restore proxy variables
                        for var, value in backup_vars.items():
                            os.environ[var] = value
                            
                except Exception as e2:
                    print(f"❌ Failed to create Supabase client for {self.name}: {e2}")
                    raise e2
        return self.client
    
    def test_connection(self) -> bool:
        """Test connection to this Supabase project"""
        try:
            client = self.get_client()
            # Test connection by trying to read from programs table
            result = client.table('programs').select('*').limit(1).execute()
            return True
        except Exception as e:
            print(f"❌ Connection test failed for {self.name}: {e}")
            return False

class MultiSupabaseManager:
    """Manages multiple Supabase projects"""
    
    def __init__(self, config_file: str = "supabase_projects.json"):
        self.config_file = config_file
        self.projects: Dict[str, SupabaseProject] = {}
        self.current_project: Optional[str] = None
        self.load_config()
    
    def load_config(self):
        """Load project configurations from file or environment"""
        self.search_order = []
        self.settings = {}
        
        # Try to load from config file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                    # Load projects
                    for project_name, project_config in config_data.get('projects', {}).items():
                        self.projects[project_name] = SupabaseProject(
                            name=project_name,
                            url=project_config['url'],
                            key=project_config['key'],
                            description=project_config.get('description', '')
                        )
                    
                    # Load search order
                    self.search_order = config_data.get('search_order', list(self.projects.keys()))
                    
                    # Load settings
                    self.settings = config_data.get('settings', {})
                    
                    self.current_project = config_data.get('current_project')
                    print(f"✅ Loaded {len(self.projects)} Supabase projects from config")
                    print(f"📋 Search order: {self.search_order}")
            except Exception as e:
                print(f"❌ Error loading config file: {e}")
        
        # Load from environment variables as fallback
        self.load_from_environment()
        
        # Set default search order if not specified
        if not self.search_order:
            self.search_order = list(self.projects.keys())
    
    def load_from_environment(self):
        """Load projects from environment variables"""
        # Primary project (current one)
        primary_url = os.getenv('SUPABASE_URL')
        primary_key = os.getenv('SUPABASE_KEY')
        
        if primary_url and primary_key:
            if 'primary' not in self.projects:
                self.projects['primary'] = SupabaseProject(
                    name='primary',
                    url=primary_url,
                    key=primary_key,
                    description='Primary Supabase project'
                )
                if not self.current_project:
                    self.current_project = 'primary'
                print("✅ Loaded primary project from environment")
        
        # Additional projects
        project_index = 1
        while True:
            url_key = f'SUPABASE_URL_{project_index}'
            key_key = f'SUPABASE_KEY_{project_index}'
            name_key = f'SUPABASE_NAME_{project_index}'
            
            url = os.getenv(url_key)
            key = os.getenv(key_key)
            name = os.getenv(name_key, f'project_{project_index}')
            
            if url and key:
                self.projects[name] = SupabaseProject(
                    name=name,
                    url=url,
                    key=key,
                    description=f'Supabase project {project_index}'
                )
                print(f"✅ Loaded {name} project from environment")
                project_index += 1
            else:
                break
    
    def add_project(self, name: str, url: str, key: str, description: str = ""):
        """Add a new project"""
        self.projects[name] = SupabaseProject(name, url, key, description)
        print(f"✅ Added project: {name}")
    
    def remove_project(self, name: str):
        """Remove a project"""
        if name in self.projects:
            del self.projects[name]
            if self.current_project == name:
                self.current_project = None
            print(f"✅ Removed project: {name}")
    
    def set_current_project(self, name: str):
        """Set the current active project"""
        if name in self.projects:
            self.current_project = name
            print(f"✅ Switched to project: {name}")
        else:
            print(f"❌ Project {name} not found")
    
    def get_current_client(self):
        """Get client for current project"""
        if not self.current_project or self.current_project not in self.projects:
            raise Exception("No current project set")
        return self.projects[self.current_project].get_client()
    
    def get_client(self, project_name: str):
        """Get client for specific project"""
        if project_name not in self.projects:
            raise Exception(f"Project {project_name} not found")
        return self.projects[project_name].get_client()
    
    def list_projects(self):
        """List all available projects"""
        print("\n📋 Available Supabase Projects:")
        print("=" * 50)
        for name, project in self.projects.items():
            status = "🟢 Active" if name == self.current_project else "⚪"
            print(f"{status} {name}: {project.description}")
            print(f"   URL: {project.url}")
            print()
    
    def test_all_connections(self):
        """Test connections to all projects"""
        print("\n🧪 Testing all project connections:")
        print("=" * 40)
        
        for name, project in self.projects.items():
            print(f"Testing {name}...", end=" ")
            if project.test_connection():
                print("✅ Connected")
            else:
                print("❌ Failed")
    
    def get_search_order(self):
        """Get the ordered list of projects to search"""
        return self.search_order
    
    def search_student_across_projects(self, roll_no: str, regulation: str, program: str):
        """Search for student across all projects in order, then web APIs"""
        projects_tried = []
        
        # First, search in Supabase projects
        for project_name in self.search_order:
            if project_name not in self.projects:
                continue
                
            projects_tried.append(project_name)
            print(f"🔍 Searching in project: {project_name}")
            
            try:
                project = self.projects[project_name]
                client = project.get_client()
                
                # Search for student
                student_result = client.table('students').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('roll_number', roll_no).execute()
                
                if student_result.data:
                    student_data = student_result.data[0]
                    institute_code = student_data['institute_code']
                    print(f"✅ Found student in {project_name} with institute code: {institute_code}")
                    
                    # Get institute data
                    institute_result = client.table('institutes').select('*').eq('program_name', program).eq('regulation_year', regulation).eq('institute_code', institute_code).execute()
                    
                    institute_data = None
                    if institute_result.data:
                        institute_data = institute_result.data[0]
                        print(f"✅ Found institute data in {project_name}: {institute_data['name']}")
                    
                    return {
                        'student_data': student_data,
                        'institute_data': institute_data,
                        'project_name': project_name,
                        'projects_tried': projects_tried,
                        'source': 'supabase'
                    }
                else:
                    print(f"❌ Student not found in {project_name}")
                    
            except Exception as e:
                print(f"❌ Error searching in {project_name}: {e}")
                continue
        
        # If not found in any Supabase project, return None
        print(f"❌ Student not found in any Supabase project")
        return None
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            'current_project': self.current_project,
            'search_order': self.search_order,
            'projects': {},
            'settings': self.settings
        }
        
        for name, project in self.projects.items():
            config_data['projects'][name] = {
                'url': project.url,
                'key': project.key,
                'description': project.description
            }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")

# Global instance
supabase_manager = MultiSupabaseManager()

def get_supabase_client(project_name: str = None):
    """Get Supabase client for specified project or current project"""
    if project_name:
        return supabase_manager.get_client(project_name)
    else:
        return supabase_manager.get_current_client()

def add_supabase_project(name: str, url: str, key: str, description: str = ""):
    """Add a new Supabase project"""
    supabase_manager.add_project(name, url, key, description)

def switch_supabase_project(name: str):
    """Switch to a different Supabase project"""
    supabase_manager.set_current_project(name)

def list_supabase_projects():
    """List all available Supabase projects"""
    supabase_manager.list_projects()

def test_supabase_connections():
    """Test connections to all Supabase projects"""
    supabase_manager.test_all_connections()

if __name__ == "__main__":
    # Example usage
    print("🎯 Multi-Project Supabase Manager")
    print("=" * 40)
    
    # List current projects
    list_supabase_projects()
    
    # Test all connections
    test_supabase_connections()
    
    # Example: Add a new project
    # add_supabase_project(
    #     name="production",
    #     url="https://your-prod-project.supabase.co",
    #     key="your-prod-anon-key",
    #     description="Production database"
    # )
    
    # Example: Switch projects
    # switch_supabase_project("production")
    
    # Save configuration
    supabase_manager.save_config()
