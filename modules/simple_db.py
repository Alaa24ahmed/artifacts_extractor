"""
Simple database client for artifact caching
"""
import os
import json
import hashlib
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the project root - force reload
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(env_path, override=True)  # Force override existing values

# Also try to load from current directory as fallback
load_dotenv(".env", override=False)  # Don't override if already set

# Debug: Check if variables are loaded
import os
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY") 
enable = os.getenv("ENABLE_SUPABASE", "false")
print(f"🔧 simple_db.py environment load - URL: {'SET' if url else 'NOT SET'}, KEY: {'SET' if key else 'NOT SET'}, ENABLE: {enable}")

logger = logging.getLogger(__name__)

class SimpleArtifactDB:
    """Simple database client for artifact storage and caching"""
    
    def __init__(self):
        self.supabase_client = None
        self.enabled = False
        
        # Try to initialize Supabase
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
            enable = os.getenv("ENABLE_SUPABASE", "false").lower()
            
            logger.info(f"🔍 Environment check - URL: {'SET' if url else 'NOT SET'}, "
                       f"KEY: {'SET' if key else 'NOT SET'}, "
                       f"ENABLE: {enable}")
            
            if url and key and enable == "true":
                from supabase import create_client
                self.supabase_client = create_client(url, key)
                self.enabled = True
                logger.info("✅ Simple database client initialized")
            else:
                logger.info(f"📝 Database disabled - URL: {bool(url)}, KEY: {bool(key)}, ENABLE: {enable}")
                
        except Exception as e:
            logger.warning(f"⚠️ Database initialization failed: {e}")
            self.enabled = False
    
    def _hash_file(self, file_path: str) -> str:
        """Generate SHA-256 hash of file content"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""
    
    def check_cache(self, file_path: str) -> Optional[List[Dict]]:
        """Check if artifacts exist for this file"""
        if not self.enabled:
            return None
            
        try:
            file_hash = self._hash_file(file_path)
            if not file_hash:
                return None
            
            # Check cache table first
            result = self.supabase_client.table("processing_cache").select("*").eq(
                "file_hash", file_hash
            ).execute()
            
            if not result.data:
                return None
            
            # Get artifacts
            artifacts_result = self.supabase_client.table("artifacts").select("*").eq(
                "file_hash", file_hash
            ).execute()
            
            if artifacts_result.data:
                # Extract artifact data from JSONB
                artifacts = []
                for record in artifacts_result.data:
                    if record.get("artifact_data"):
                        if isinstance(record["artifact_data"], list):
                            artifacts.extend(record["artifact_data"])
                        else:
                            artifacts.append(record["artifact_data"])
                
                logger.info(f"🎯 Cache hit! Found {len(artifacts)} artifacts for {os.path.basename(file_path)}")
                return artifacts
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking cache: {e}")
            return None
    
    def save_artifacts_from_data(self, file_name: str, file_hash: str, artifacts_data) -> bool:
        """Save artifacts to database from JSON data (when we don't have the original file)"""
        if not self.enabled:
            logger.warning("Database not enabled - cannot save artifacts")
            return False
            
        try:
            # Handle different data structures
            artifacts = []
            
            if isinstance(artifacts_data, list):
                # If artifacts_data is already a list of artifacts
                artifacts = artifacts_data
                logger.info(f"Received artifacts as list with {len(artifacts)} items")
            elif isinstance(artifacts_data, dict):
                # If artifacts_data is a dict, look for 'artifacts' key
                artifacts = artifacts_data.get('artifacts', [])
                logger.info(f"Received artifacts as dict, extracted {len(artifacts)} artifacts")
                
                # If no 'artifacts' key, maybe the dict itself is an artifact
                if not artifacts and artifacts_data:
                    artifacts = [artifacts_data]
                    logger.info("Treating single dict as one artifact")
            else:
                logger.error(f"Unexpected data type: {type(artifacts_data)}")
                return False
            
            if not artifacts:
                logger.warning(f"No artifacts found in data for {file_name}")
                if isinstance(artifacts_data, dict):
                    logger.debug(f"Available keys in artifacts_data: {list(artifacts_data.keys())}")
                return False
            
            logger.info(f"Attempting to save {len(artifacts)} artifacts for {file_name}")
            
            # Save artifacts
            artifact_record = {
                "file_name": file_name,
                "file_hash": file_hash,
                "artifact_data": artifacts,
                "artifact_count": len(artifacts)
            }
            
            logger.debug(f"Inserting artifact record with {len(artifacts)} artifacts")
            artifacts_result = self.supabase_client.table("artifacts").insert(artifact_record).execute()
            logger.debug(f"Artifacts insert result: {artifacts_result}")
            
            # Save cache entry
            cache_record = {
                "file_hash": file_hash,
                "file_name": file_name,
                "artifact_count": len(artifacts)
            }
            
            logger.debug(f"Upserting cache record: {cache_record}")
            cache_result = self.supabase_client.table("processing_cache").upsert(cache_record).execute()
            logger.debug(f"Cache upsert result: {cache_result}")
            
            logger.info(f"💾 Successfully saved {len(artifacts)} artifacts for {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving artifacts from data: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def save_artifacts(self, file_path: str, artifacts: List[Dict]) -> bool:
        """Save artifacts to database"""
        if not self.enabled or not artifacts:
            return False
            
        try:
            file_hash = self._hash_file(file_path)
            file_name = os.path.basename(file_path)
            
            if not file_hash:
                return False
            
            # Save artifacts
            artifact_record = {
                "file_name": file_name,
                "file_hash": file_hash,
                "artifact_data": artifacts,
                "artifact_count": len(artifacts)
            }
            
            self.supabase_client.table("artifacts").insert(artifact_record).execute()
            
            # Save cache entry
            cache_record = {
                "file_hash": file_hash,
                "file_name": file_name,
                "artifact_count": len(artifacts)
            }
            
            # Use upsert to avoid duplicates
            self.supabase_client.table("processing_cache").upsert(cache_record).execute()
            
            logger.info(f"💾 Saved {len(artifacts)} artifacts for {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving artifacts: {e}")
            return False
    
    def search_artifacts(self, query: str = None, limit: int = 100) -> List[Dict]:
        """Search artifacts"""
        if not self.enabled:
            return []
            
        try:
            # Use the database function for search
            if query:
                result = self.supabase_client.rpc("search_artifacts_simple", {
                    "search_term": query,
                    "limit_count": limit
                }).execute()
            else:
                result = self.supabase_client.table("artifacts").select("*").order(
                    "created_at", desc=True
                ).limit(limit).execute()
            
            artifacts = []
            for record in result.data:
                if record.get("artifact_data"):
                    if isinstance(record["artifact_data"], list):
                        artifacts.extend(record["artifact_data"])
                    else:
                        artifacts.append(record["artifact_data"])
            
            logger.info(f"🔍 Found {len(artifacts)} artifacts matching query")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get simple database statistics"""
        if not self.enabled:
            return {"enabled": False}
            
        try:
            # Count total artifacts
            artifacts_count = self.supabase_client.table("artifacts").select(
                "artifact_count"
            ).execute()
            
            total_artifacts = sum(r.get("artifact_count", 0) for r in artifacts_count.data)
            
            # Count files processed
            cache_count = self.supabase_client.table("processing_cache").select(
                "file_hash", count="exact"
            ).execute()
            
            return {
                "enabled": True,
                "total_artifacts": total_artifacts,
                "files_processed": cache_count.count,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"enabled": True, "error": str(e)}

# Global instance
_db_instance = None

def get_simple_db() -> SimpleArtifactDB:
    """Get the global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SimpleArtifactDB()
    return _db_instance
