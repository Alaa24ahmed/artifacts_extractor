"""
Simple database client for artifact caching
"""
import os
import json
import hashlib
import logging
import shelve
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load configuration using the configuration manager
try:
    from .config_manager import load_configuration, generate_processing_params_hash, get_model_identifiers
    load_configuration()
    print("✅ Configuration loaded in simple_db.py")
except Exception as e:
    print(f"⚠️ Error loading configuration in simple_db.py: {e}")
    # Fallback to manual loading
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path, override=True)

logger = logging.getLogger(__name__)

class SimpleArtifactDB:
    """Simple database client for artifact storage and caching"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "artifacts.db"
        self.db = shelve.open(self.db_path, writeback=True)
        self.cache_db = shelve.open(f"{self.db_path}_cache", writeback=True)
        self.page_cache_db = shelve.open(f"{self.db_path}_page_cache", writeback=True)
        
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

    def _map_artifact_to_db(self, artifact_data: dict, file_path: str = None,
                           ocr_model: str = None, extraction_model: str = None,
                           processing_params_hash: str = None) -> dict:
        """Map artifact data to match the new database schema"""
        # Calculate file hash and name if file_path provided
        file_hash = ""
        file_name = ""
        if file_path:
            file_hash = self._hash_file(file_path)
            file_name = os.path.basename(file_path)
        
        # Map old field names to new schema
        mapped_data = {
            "file_hash": artifact_data.get("file_hash", file_hash),
            "file_name": artifact_data.get("file_name", file_name),
            "name_en": artifact_data.get("name_english", artifact_data.get("name", artifact_data.get("Name", ""))),
            "name_ar": artifact_data.get("name_arabic", artifact_data.get("Name_AR", "")),
            "name_fr": artifact_data.get("name_french", artifact_data.get("Name_FR", "")),
            "creator": artifact_data.get("creator", artifact_data.get("Creator", "")),
            "creation_date": artifact_data.get("period", artifact_data.get("creation_date", artifact_data.get("Creation Date", ""))),
            "materials": artifact_data.get("material", artifact_data.get("materials", artifact_data.get("Materials", ""))),
            "origin": artifact_data.get("origin", artifact_data.get("Origin", "")),
            "description": artifact_data.get("description", artifact_data.get("Description", "")),
            "category": artifact_data.get("category", artifact_data.get("Category", "")),
            "source_page": artifact_data.get("page_number", artifact_data.get("source_page", 0)),
            "source_document": artifact_data.get("source_document", file_name),
            "name_validation": artifact_data.get("name_validation", ""),
            # Model tracking fields
            "ocr_model": ocr_model or artifact_data.get("ocr_model", "mistral-ocr"),
            "extraction_model": extraction_model or artifact_data.get("extraction_model", "gpt-4o"),
            "processing_params_hash": processing_params_hash or artifact_data.get("processing_params_hash", "")
        }
        
        # Remove None values and empty strings for optional fields
        return {k: v for k, v in mapped_data.items() if v is not None and (k in ["file_hash", "file_name"] or v != "")}
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file (alias for _hash_file for compatibility)"""
        return self._hash_file(file_path)
    
    def add_artifact(self, artifact_data: dict, file_path: str = None,
                   ocr_model: str = None, extraction_model: str = None,
                   processing_params_hash: str = None) -> dict:
        """Add a new artifact to the database with model tracking"""
        try:
            # Set default values for backward compatibility
            if ocr_model is None:
                ocr_model = "mistral-ocr"
            if extraction_model is None:
                extraction_model = "gpt-4o-mini"
            if processing_params_hash is None:
                processing_params_hash = ""
            
            # Map the artifact data to database schema
            db_data = self._map_artifact_to_db(artifact_data, file_path, 
                                             ocr_model, extraction_model, processing_params_hash)
            
            # Generate unique ID
            artifact_id = str(len(self.db) + 1)
            db_data['id'] = artifact_id
            
            # Add timestamps
            db_data['created_at'] = datetime.now().isoformat()
            db_data['updated_at'] = datetime.now().isoformat()
            
            # Save to local database
            self.db[artifact_id] = db_data
            
            logger.info(f"Added artifact with ID: {artifact_id} using {ocr_model}/{extraction_model}")
            return db_data
            
        except Exception as e:
            logger.error(f"Error adding artifact: {e}")
            logger.error(f"Artifact data: {artifact_data}")
            logger.error(f"File path: {file_path}")
            return {}
    
    def get_artifact(self, artifact_id: str) -> dict:
        """Get a single artifact by ID"""
        try:
            return self.db.get(str(artifact_id), {})
        except Exception as e:
            logger.error(f"Error getting artifact {artifact_id}: {e}")
            return {}
    
    def update_artifact(self, artifact_id: str, updates: dict, file_path: str = None) -> dict:
        """Update an existing artifact"""
        try:
            artifact_id = str(artifact_id)
            if artifact_id in self.db:
                current_data = self.db[artifact_id].copy()
                current_data.update(updates)
                
                # Re-map to ensure schema compliance
                mapped_data = self._map_artifact_to_db(current_data, file_path)
                mapped_data['id'] = artifact_id
                mapped_data['updated_at'] = datetime.now().isoformat()
                
                self.db[artifact_id] = mapped_data
                logger.info(f"Updated artifact with ID: {artifact_id}")
                return mapped_data
            else:
                logger.warning(f"Artifact {artifact_id} not found for update")
                return {}
                
        except Exception as e:
            logger.error(f"Error updating artifact {artifact_id}: {e}")
            return {}
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact"""
        try:
            artifact_id = str(artifact_id)
            if artifact_id in self.db:
                del self.db[artifact_id]
                logger.info(f"Deleted artifact with ID: {artifact_id}")
                return True
            else:
                logger.warning(f"Artifact {artifact_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting artifact {artifact_id}: {e}")
            return False
    
    def list_artifacts(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """List artifacts with pagination"""
        try:
            all_artifacts = list(self.db.values())
            # Sort by created_at (most recent first)
            all_artifacts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return all_artifacts[offset:offset+limit]
        except Exception as e:
            logger.error(f"Error listing artifacts: {e}")
            return []
    
    def get_artifacts_by_file(self, file_hash: str) -> List[dict]:
        """Get all artifacts from a specific file"""
        try:
            results = []
            for artifact in self.db.values():
                if artifact.get('file_hash') == file_hash:
                    results.append(artifact)
            
            # Sort by source_page
            results.sort(key=lambda x: x.get('source_page', 0))
            return results
            
        except Exception as e:
            logger.error(f"Error getting artifacts by file: {e}")
            return []
    
    def filter_artifacts(self, **filters) -> List[dict]:
        """Filter artifacts by various criteria"""
        try:
            results = []
            for artifact in self.db.values():
                matches = True
                for key, value in filters.items():
                    if value is not None and artifact.get(key) != value:
                        matches = False
                        break
                
                if matches:
                    results.append(artifact)
            
            return results
            
        except Exception as e:
            logger.error(f"Error filtering artifacts: {e}")
            return []
    
    def close(self):
        """Close the database connections"""
        try:
            self.db.close()
            self.cache_db.close()
            self.page_cache_db.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

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
            
            # Get artifacts using the new schema
            artifacts_result = self.supabase_client.table("artifacts").select("*").eq(
                "file_hash", file_hash
            ).order("source_page").execute()
            
            if artifacts_result.data:
                # Convert database records back to artifact format
                artifacts = []
                for record in artifacts_result.data:
                    artifact = {
                        "id": record.get("id"),
                        "Name": record.get("name_en", ""),
                        "Name_EN": record.get("name_en", ""),
                        "Name_AR": record.get("name_ar", ""),
                        "Name_FR": record.get("name_fr", ""),
                        "Creator": record.get("creator", ""),
                        "Creation Date": record.get("creation_date", ""),
                        "Materials": record.get("materials", ""),
                        "Origin": record.get("origin", ""),
                        "Description": record.get("description", ""),
                        "Category": record.get("category", ""),
                        "source_page": record.get("source_page", 0),
                        "source_document": record.get("source_document", ""),
                        "file_hash": record.get("file_hash", ""),
                        "file_name": record.get("file_name", "")
                    }
                    artifacts.append(artifact)
                
                logger.info(f"🎯 Cache hit! Found {len(artifacts)} artifacts for {os.path.basename(file_path)}")
                return artifacts
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking cache: {e}")
            return None

    def save_artifacts_from_data(self, file_name: str, file_hash: str, artifacts_data) -> bool:
        """Save artifacts to database from JSON data using new schema"""
        if not self.enabled:
            logger.warning("Database not enabled - cannot save artifacts")
            return False
            
        try:
            # Handle different data structures
            artifacts = []
            
            if isinstance(artifacts_data, list):
                artifacts = artifacts_data
                logger.info(f"Received artifacts as list with {len(artifacts)} items")
            elif isinstance(artifacts_data, dict):
                artifacts = artifacts_data.get('artifacts', [])
                logger.info(f"Received artifacts as dict, extracted {len(artifacts)} artifacts")
                
                if not artifacts and artifacts_data:
                    artifacts = [artifacts_data]
                    logger.info("Treating single dict as one artifact")
            else:
                logger.error(f"Unexpected data type: {type(artifacts_data)}")
                return False
            
            if not artifacts:
                logger.warning(f"No artifacts found in data for {file_name}")
                return False
            
            logger.info(f"Attempting to save {len(artifacts)} artifacts for {file_name}")
            
            # Convert each artifact to the new schema and save individually
            saved_count = 0
            for artifact in artifacts:
                try:
                    # Map artifact to new schema
                    mapped_artifact = self._map_artifact_to_db(artifact)
                    mapped_artifact["file_hash"] = file_hash
                    mapped_artifact["file_name"] = file_name
                    
                    # Insert individual artifact
                    result = self.supabase_client.table("artifacts").insert(mapped_artifact).execute()
                    if result.data:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving individual artifact: {e}")
                    continue
            
            if saved_count > 0:
                # Save cache entry
                cache_record = {
                    "file_hash": file_hash,
                    "file_name": file_name,
                    "artifact_count": saved_count
                }
                
                self.supabase_client.table("processing_cache").upsert(cache_record).execute()
                logger.info(f"💾 Successfully saved {saved_count} artifacts for {file_name}")
                return True
            else:
                logger.error(f"Failed to save any artifacts for {file_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error saving artifacts from data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def save_artifacts(self, file_path: str, artifacts: List[Dict]) -> bool:
        """Save artifacts to database using new schema"""
        if not self.enabled or not artifacts:
            return False
            
        try:
            file_hash = self._hash_file(file_path)
            file_name = os.path.basename(file_path)
            
            if not file_hash:
                return False
            
            # Convert and save each artifact individually
            saved_count = 0
            for artifact in artifacts:
                try:
                    mapped_artifact = self._map_artifact_to_db(artifact, file_path)
                    result = self.supabase_client.table("artifacts").insert(mapped_artifact).execute()
                    if result.data:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving individual artifact: {e}")
                    continue
            
            if saved_count > 0:
                # Save cache entry
                cache_record = {
                    "file_hash": file_hash,
                    "file_name": file_name,
                    "artifact_count": saved_count
                }
                
                self.supabase_client.table("processing_cache").upsert(cache_record).execute()
                logger.info(f"💾 Saved {saved_count} artifacts for {file_name}")
                return True
            else:
                logger.error(f"Failed to save any artifacts for {file_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error saving artifacts: {e}")
            return False
    
    def search_artifacts(self, query: str = None, limit: int = 100) -> List[Dict]:
        """Search artifacts using the new schema"""
        if not self.enabled:
            return []
            
        try:
            # Use the database function for search if available
            if query:
                try:
                    result = self.supabase_client.rpc("search_artifacts", {
                        "search_term": query,
                        "limit_count": limit
                    }).execute()
                    return result.data if result.data else []
                except Exception:
                    # Fallback to manual search if RPC function not available
                    query_builder = self.supabase_client.table("artifacts").select("*")
                    query_builder = query_builder.or_(
                        f"name_en.ilike.%{query}%,"
                        f"name_ar.ilike.%{query}%,"
                        f"name_fr.ilike.%{query}%,"
                        f"description.ilike.%{query}%,"
                        f"materials.ilike.%{query}%,"
                        f"creator.ilike.%{query}%"
                    )
                    result = query_builder.limit(limit).execute()
            else:
                result = self.supabase_client.table("artifacts").select("*").order(
                    "created_at", desc=True
                ).limit(limit).execute()
            
            # Convert database records back to artifact format
            artifacts = []
            for record in result.data:
                artifact = {
                    "id": record.get("id"),
                    "Name": record.get("name_en", ""),
                    "Name_EN": record.get("name_en", ""),
                    "Name_AR": record.get("name_ar", ""),
                    "Name_FR": record.get("name_fr", ""),
                    "Creator": record.get("creator", ""),
                    "Creation Date": record.get("creation_date", ""),
                    "Materials": record.get("materials", ""),
                    "Origin": record.get("origin", ""),
                    "Description": record.get("description", ""),
                    "Category": record.get("category", ""),
                    "source_page": record.get("source_page", 0),
                    "source_document": record.get("source_document", ""),
                    "file_hash": record.get("file_hash", ""),
                    "file_name": record.get("file_name", "")
                }
                artifacts.append(artifact)
            
            logger.info(f"🔍 Found {len(artifacts)} artifacts matching query")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics using new schema"""
        if not self.enabled:
            return {"enabled": False}
            
        try:
            # Use the database function if available
            try:
                result = self.supabase_client.rpc("get_artifact_statistics").execute()
                if result.data and len(result.data) > 0:
                    stats = result.data[0]
                    stats["enabled"] = True
                    stats["last_updated"] = datetime.now().isoformat()
                    return stats
            except Exception:
                # Fallback to manual counting
                artifacts_result = self.supabase_client.table("artifacts").select(
                    "id", count="exact"
                ).execute()
                
                cache_result = self.supabase_client.table("processing_cache").select(
                    "file_hash", count="exact"
                ).execute()
                
                return {
                    "enabled": True,
                    "total_artifacts": artifacts_result.count,
                    "unique_files": cache_result.count,
                    "last_updated": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"enabled": True, "error": str(e)}

    def _generate_processing_params_hash(self, model: str = "gpt-4o", **kwargs) -> str:
        """Generate hash for processing parameters to enable cache invalidation"""
        params = {
            "model": model,
            **kwargs
        }
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()

    def check_page_processed(self, file_path: str, page_number: int,
                           ocr_model: str = "mistral-ocr", extraction_model: str = "gpt-4o",
                           processing_params_hash: str = "") -> bool:
        """Check if a specific page has already been processed with specific models"""
        file_hash = self._calculate_file_hash(file_path)
        cache_key = f"{file_hash}_{page_number}_{ocr_model}_{extraction_model}_{processing_params_hash}"
        
        if cache_key in self.page_cache_db:
            return True
        
        # Also check in artifacts table directly
        for artifact in self.db.values():
            if (artifact.get("file_hash") == file_hash and 
                artifact.get("source_page") == page_number and
                artifact.get("ocr_model") == ocr_model and
                artifact.get("extraction_model") == extraction_model):
                return True
        return False

    def get_page_artifacts(self, file_path: str, page_number: int) -> List[dict]:
        """Get all artifacts for a specific page"""
        file_hash = self._calculate_file_hash(file_path)
        artifacts = []
        
        for artifact in self.db.values():
            if (artifact.get("file_hash") == file_hash and 
                artifact.get("source_page") == page_number):
                artifacts.append(artifact)
        
        return sorted(artifacts, key=lambda x: x.get("id", 0))

    def mark_page_processed(self, file_path: str, page_number: int, 
                          artifact_count: int = 0, ocr_model: str = "mistral-ocr", 
                          extraction_model: str = "gpt-4o", processing_params_hash: str = ""):
        """Mark a specific page as processed with model information"""
        file_hash = self._calculate_file_hash(file_path)
        file_name = os.path.basename(file_path)
        cache_key = f"{file_hash}_{page_number}_{ocr_model}_{extraction_model}_{processing_params_hash}"
        
        cache_data = {
            "file_hash": file_hash,
            "file_name": file_name,
            "page_number": page_number,
            "ocr_model": ocr_model,
            "extraction_model": extraction_model,
            "processing_params_hash": processing_params_hash,
            "artifact_count": artifact_count,
            "processing_status": "completed",
            "created_at": datetime.now().isoformat()
        }
        
        self.page_cache_db[cache_key] = cache_data
        logger.info(f"Marked page {page_number} of {file_name} as processed with {artifact_count} artifacts using {ocr_model}/{extraction_model}")

    def get_processed_pages(self, file_path: str) -> List[int]:
        """Get list of already processed page numbers for a file by checking artifacts table"""
        file_hash = self._calculate_file_hash(file_path)
        pages = set()
        
        for artifact in self.db.values():
            if artifact.get("file_hash") == file_hash:
                page_num = artifact.get("source_page")
                if page_num:
                    pages.add(page_num)
        
        return sorted(list(pages))

# Global instance
_db_instance = None

def get_simple_db() -> SimpleArtifactDB:
    """Get the global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SimpleArtifactDB()
    return _db_instance
