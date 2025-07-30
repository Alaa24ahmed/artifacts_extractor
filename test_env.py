#!/usr/bin/env python3
"""Test script to check environment variable loading"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
print(f"🔍 Looking for .env file at: {env_path}")
print(f"📁 .env file exists: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print("✅ Environment file loaded")
else:
    print("❌ Environment file not found")

# Check environment variables
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
enable = os.getenv("ENABLE_SUPABASE", "false")

print(f"\n🔍 Environment Variables:")
print(f"SUPABASE_URL: {'SET' if url else 'NOT SET'}")
print(f"SUPABASE_ANON_KEY: {'SET' if key else 'NOT SET'}")
print(f"ENABLE_SUPABASE: {enable}")

if url and key and enable.lower() == "true":
    print("\n✅ All required environment variables are set!")
    
    # Test database initialization
    try:
        from modules.simple_db import get_simple_db
        db = get_simple_db()
        if db and db.enabled:
            print("✅ Database client initialized successfully!")
        else:
            print("❌ Database client not enabled")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
else:
    print("\n❌ Missing required environment variables")
    if not url:
        print("  - SUPABASE_URL is missing")
    if not key:
        print("  - SUPABASE_ANON_KEY is missing")
    if enable.lower() != "true":
        print(f"  - ENABLE_SUPABASE is '{enable}' (should be 'true')")
