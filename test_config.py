#!/usr/bin/env python3
"""
Test the configuration manager and database connection
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_configuration():
    """Test the configuration loading and database connection"""
    print("🔍 Testing Configuration Manager...")
    
    try:
        from modules.config_manager import load_configuration, get_config_status
        
        # Load configuration
        print("📋 Loading configuration...")
        load_configuration()
        
        # Get status
        print("📊 Getting configuration status...")
        config_status = get_config_status()
        
        print("\n" + "="*50)
        print("CONFIGURATION STATUS")
        print("="*50)
        
        print("\n🗄️ Database Configuration:")
        db_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'ENABLE_SUPABASE']
        for var in db_vars:
            status = config_status.get(var, {})
            icon = "✅" if status.get('set') else "❌"
            source = status.get('source', 'unknown')
            print(f"  {var}: {icon} (Source: {source})")
        
        print("\n🔑 API Keys:")
        api_vars = ['OPENAI_API_KEY', 'MISTRAL_API_KEY', 'GOOGLE_API_KEY']
        for var in api_vars:
            status = config_status.get(var, {})
            icon = "✅" if status.get('set') else "❌"
            source = status.get('source', 'unknown')
            print(f"  {var}: {icon} (Source: {source})")
        
        print("\n" + "="*50)
        
        # Test database connection
        print("\n🗄️ Testing Database Connection...")
        try:
            from modules.simple_db import get_simple_db
            db = get_simple_db()
            if db and db.enabled:
                print("✅ Database connection successful!")
            else:
                print("❌ Database connection failed or disabled")
        except Exception as e:
            print(f"❌ Database connection error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    test_configuration()
