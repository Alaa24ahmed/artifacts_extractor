#!/usr/bin/env python3
"""Test database connection and save functionality"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

def test_database():
    print("🔍 Testing database connection and save functionality")
    
    # Test environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    enable = os.getenv("ENABLE_SUPABASE", "false")
    
    print(f"SUPABASE_URL: {'SET' if url else 'NOT SET'}")
    print(f"SUPABASE_ANON_KEY: {'SET' if key else 'NOT SET'}")
    print(f"ENABLE_SUPABASE: {enable}")
    
    if not (url and key and enable.lower() == "true"):
        print("❌ Environment variables not properly set")
        return False
    
    # Test database initialization
    try:
        from modules.simple_db import get_simple_db
        db = get_simple_db()
        
        if not db or not db.enabled:
            print("❌ Database not initialized or not enabled")
            return False
            
        print("✅ Database client initialized successfully")
        
        # Test save with sample data
        sample_data = {
            "artifacts": [
                {
                    "name_en": "Test Artifact",
                    "creator": "Test Creator",
                    "description": "Test Description"
                }
            ]
        }
        
        print("🧪 Testing save_artifacts_from_data...")
        success = db.save_artifacts_from_data(
            "test_file", 
            "test_hash_123", 
            sample_data
        )
        
        if success:
            print("✅ Test save successful!")
        else:
            print("❌ Test save failed")
            
        return success
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_database()
