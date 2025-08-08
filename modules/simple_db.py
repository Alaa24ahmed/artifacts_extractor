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

# Load configuration using the configuration manager
try:
    from .config_manager import load_configuration
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
    
    def check_page_level_cache(self, doc_group: dict, start_page: int, end_page: int,
                              ocr_model: str, extraction_model: str, thresholds: dict) -> tuple:
        """
        Check cache for each page in the requested range
        
        Returns:
            tuple: (cached_artifacts, missing_pages, cache_stats)
        """
        if not self.enabled:
            return [], list(range(start_page, end_page + 1)), {"cached_pages": 0, "missing_pages": end_page - start_page + 1}
        
        # Validate inputs
        if not doc_group or not doc_group.get("EN"):
            logger.error("Invalid doc_group - missing English document")
            return [], list(range(start_page, end_page + 1)), {"cached_pages": 0, "missing_pages": end_page - start_page + 1}
        
        if start_page > end_page:
            logger.error(f"Invalid page range: {start_page} > {end_page}")
            return [], [], {"cached_pages": 0, "missing_pages": 0}
            
        try:
            requested_pages = list(range(start_page, end_page + 1))
            cached_artifacts = []
            missing_pages = []
            
            # Create processing params hash
            processing_params_hash = hashlib.sha256(
                json.dumps(thresholds, sort_keys=True).encode()
            ).hexdigest()
            
            logger.info(f"🔍 Checking cache for pages {start_page}-{end_page}")
            
            for page_num in requested_pages:
                # Create page cache key
                page_cache_key = self._create_page_cache_key(
                    doc_group, page_num, ocr_model, extraction_model, thresholds
                )
                
                # Check if this page exists in cache
                try:
                    result = self.supabase_client.rpc("check_page_cache", {
                        "p_page_cache_key": page_cache_key
                    }).execute()
                except Exception as rpc_error:
                    logger.warning(f"RPC call failed for page {page_num}, falling back to direct query: {rpc_error}")
                    # Fallback to direct table query
                    result = self.supabase_client.table("artifacts").select("*").eq(
                        "page_cache_key", page_cache_key
                    ).execute()
                
                if result.data:
                    # Convert database format back to original format
                    page_artifacts = []
                    for record in result.data:
                        artifact = {
                            "Name_EN": record.get("name_en", ""),
                            "Name_AR": record.get("name_ar", ""),
                            "Name_FR": record.get("name_fr", ""),
                            "Creator": record.get("creator", ""),
                            "Creation Date": record.get("creation_date", ""),
                            "Materials": record.get("materials", ""),
                            "Origin": record.get("origin", ""),
                            "Description": record.get("description", ""),
                            "Category": record.get("category", ""),
                            "source_page": record.get("source_page", page_num),
                            "source_document": record.get("source_document", ""),
                            "Name_validation": record.get("name_validation", "")
                        }
                        page_artifacts.append(artifact)
                    
                    cached_artifacts.extend(page_artifacts)
                    logger.info(f"✅ Page {page_num}: Found {len(page_artifacts)} cached artifacts")
                else:
                    missing_pages.append(page_num)
                    logger.info(f"🔄 Page {page_num}: Needs processing")
            
            cache_stats = {
                "cached_pages": len(requested_pages) - len(missing_pages),
                "missing_pages": len(missing_pages),
                "total_cached_artifacts": len(cached_artifacts)
            }
            
            logger.info(f"📊 Cache Summary: {cache_stats['cached_pages']} cached, {cache_stats['missing_pages']} need processing")
            
            return cached_artifacts, missing_pages, cache_stats
            
        except Exception as e:
            logger.error(f"Error checking page-level cache: {e}")
            # Fallback: treat all pages as missing
            return [], list(range(start_page, end_page + 1)), {"cached_pages": 0, "missing_pages": end_page - start_page + 1}
    
    def _create_page_cache_key(self, doc_group: dict, page_num: int, ocr_model: str, 
                              extraction_model: str, thresholds: dict) -> str:
        """Create unique cache key for a specific page with specific parameters"""
        # Create file hashes for all documents
        file_hashes = {}
        for lang, file_path in doc_group.items():
            if file_path and os.path.exists(file_path):
                file_hashes[lang] = self._hash_file(file_path)
        
        # Create parameter combination
        params = {
            'files': file_hashes,
            'page': page_num,
            'ocr_model': ocr_model,
            'extraction_model': extraction_model,
            'thresholds': json.dumps(thresholds, sort_keys=True)
        }
        
        # Generate SHA-256 hash
        params_str = json.dumps(params, sort_keys=True)
        cache_key = hashlib.sha256(params_str.encode()).hexdigest()
        
        # Debug logging
        logger.debug(f"Created page cache key for page {page_num}: {cache_key[:16]}...")
        logger.debug(f"Parameters: {params_str[:100]}...")
        
        return cache_key
    
    def _create_run_cache_key(self, doc_group: dict, start_page: int, end_page: int,
                             ocr_model: str, extraction_model: str, thresholds: dict) -> str:
        """Create unique cache key for an entire processing run"""
        # Get main English file hash
        en_file = doc_group.get("EN")
        file_hash = self._hash_file(en_file) if en_file else ""
        
        # If we can't hash the original file, generate a content-based fallback for caching
        if not file_hash:
            # For caching purposes, we need a deterministic hash based on document identity
            file_basename = os.path.basename(en_file) if en_file else "unknown_document"
            # Remove the random prefix that Streamlit adds, keep the core identifier
            if file_basename.startswith("imported_file_"):
                core_name = file_basename.replace("imported_file_", "")
            else:
                core_name = file_basename
            
            file_hash = hashlib.sha256(core_name.encode()).hexdigest()
        
        params = {
            'file_hash': file_hash,
            'start_page': start_page,
            'end_page': end_page,
            'ocr_model': ocr_model,
            'extraction_model': extraction_model,
            'thresholds': json.dumps(thresholds, sort_keys=True)
        }
        
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.sha256(params_str.encode()).hexdigest()
    
    def _map_artifact_to_new_schema(self, artifact: dict, page_cache_key: str, 
                                   page_num: int, ocr_model: str, extraction_model: str,
                                   processing_params_hash: str) -> dict:
        """Map artifact fields from old format to new schema with cache keys"""
        return {
            "page_cache_key": page_cache_key,
            "page_number": page_num,
            "name_en": artifact.get("Name_EN", artifact.get("Name", "")),
            "name_ar": artifact.get("Name_AR", ""),
            "name_fr": artifact.get("Name_FR", ""),
            "creator": artifact.get("Creator", ""),
            "creation_date": artifact.get("Creation Date", ""),
            "materials": artifact.get("Materials", ""),
            "origin": artifact.get("Origin", ""),
            "description": artifact.get("Description", ""),
            "category": artifact.get("Category", ""),
            "source_page": artifact.get("source_page", page_num),
            "source_document": artifact.get("source_document", ""),
            "name_validation": artifact.get("Name_validation", ""),
            "ocr_model": ocr_model,
            "extraction_model": extraction_model,
            "processing_params_hash": processing_params_hash
        }

    def save_page_artifacts(self, doc_group: dict, page_num: int, artifacts: List[Dict],
                          ocr_model: str, extraction_model: str, thresholds: dict) -> bool:
        """Save artifacts from a specific page with cache key"""
        if not self.enabled or not artifacts:
            return False
            
        # Debug: Log the models being saved
        logger.info(f"💾 DB Save - OCR model: '{ocr_model}', Extraction model: '{extraction_model}'")
            
        try:
            # Get main file hash
            en_file = doc_group.get("EN", "")
            file_hash = self._hash_file(en_file) if en_file else ""
            
            # If we can't hash the original file (e.g., temporary file no longer exists),
            # we need a content-based fallback for caching to work properly
            if not file_hash:
                # For caching purposes, we need a deterministic hash based on document identity
                # Use the original filename (which contains unique ID) as the basis
                # This allows cache hits when same document is re-uploaded
                file_basename = os.path.basename(en_file) if en_file else "unknown_document"
                # Remove the random prefix that Streamlit adds, keep the core identifier
                if file_basename.startswith("imported_file_"):
                    # Extract the unique part: imported_file_0e6834e5.pdf -> 0e6834e5.pdf
                    core_name = file_basename.replace("imported_file_", "")
                else:
                    core_name = file_basename
                
                file_hash = hashlib.sha256(core_name.encode()).hexdigest()
                logger.warning(f"Using content-based fallback hash for caching: {core_name}")
            
            if not file_hash:
                logger.error("Cannot create file hash for page artifacts")
                return False
            
            # Create cache keys
            page_cache_key = self._create_page_cache_key(
                doc_group, page_num, ocr_model, extraction_model, thresholds
            )
            processing_params_hash = hashlib.sha256(
                json.dumps(thresholds, sort_keys=True).encode()
            ).hexdigest()
            
            # Check if this page is already cached
            existing_check = self.supabase_client.table("artifacts").select("id").eq(
                "page_cache_key", page_cache_key
            ).limit(1).execute()
            
            if existing_check.data:
                logger.info(f"Page {page_num} already cached, skipping save")
                return True
            
            # Map and save each artifact
            saved_count = 0
            for artifact in artifacts:
                mapped_artifact = self._map_artifact_to_new_schema(
                    artifact, page_cache_key, page_num, ocr_model, 
                    extraction_model, processing_params_hash
                )
                
                # Add file hash
                mapped_artifact["file_hash"] = file_hash
                
                try:
                    self.supabase_client.table("artifacts").insert(mapped_artifact).execute()
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving individual artifact: {e}")
                    continue
            
            logger.info(f"💾 Saved {saved_count} artifacts for page {page_num}")
            return saved_count > 0
            
        except Exception as e:
            logger.error(f"Error saving page artifacts: {e}")
            return False

    def save_run_statistics(self, doc_group: dict, start_page: int, end_page: int,
                          ocr_model: str, extraction_model: str, thresholds: dict,
                          total_artifacts: int, cached_pages: int, processed_pages: int) -> bool:
        """Save statistics for a complete processing run"""
        if not self.enabled:
            return False
            
        try:
            # Get main file hash
            en_file = doc_group.get("EN", "")
            file_hash = self._hash_file(en_file) if en_file else ""
            
            # Create run cache key
            run_cache_key = self._create_run_cache_key(
                doc_group, start_page, end_page, ocr_model, extraction_model, thresholds
            )
            processing_params_hash = hashlib.sha256(
                json.dumps(thresholds, sort_keys=True).encode()
            ).hexdigest()
            
            # Save run statistics
            run_record = {
                "run_cache_key": run_cache_key,
                "file_hash": file_hash,
                "start_page": start_page,
                "end_page": end_page,
                "ocr_model": ocr_model,
                "extraction_model": extraction_model,
                "processing_params_hash": processing_params_hash,
                "total_artifacts": total_artifacts,
                "cached_pages": cached_pages,
                "processed_pages": processed_pages,
                "processing_status": "completed"
            }
            
            # Use upsert to avoid duplicates
            result = self.supabase_client.table("processing_cache").upsert(run_record).execute()
            
            logger.info(f"📊 Saved run statistics: {total_artifacts} artifacts, {cached_pages} cached pages, {processed_pages} processed pages")
            return True
            
        except Exception as e:
            logger.error(f"Error saving run statistics: {e}")
            return False

    def save_artifacts_from_data(self, file_hash: str, artifacts_data) -> bool:
        """Legacy method for backward compatibility - converts to page-based saving"""
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
                logger.warning(f"No artifacts found in data")
                return False
            
            # Group artifacts by page for proper caching
            artifacts_by_page = {}
            for artifact in artifacts:
                page_num = artifact.get("source_page", 1)
                if page_num not in artifacts_by_page:
                    artifacts_by_page[page_num] = []
                artifacts_by_page[page_num].append(artifact)
            
            # Save each page separately (using default parameters for legacy data)
            doc_group = {"EN": f"legacy_file_{file_hash[:8]}.pdf"}
            default_model = "gpt-4o"
            default_thresholds = {"EN": 0.05, "AR": 0.10, "FR": 0.07}
            
            total_saved = 0
            for page_num, page_artifacts in artifacts_by_page.items():
                success = self.save_page_artifacts(
                    doc_group, page_num, page_artifacts,
                    default_model, default_model, default_thresholds
                )
                if success:
                    total_saved += len(page_artifacts)
            
            logger.info(f"💾 Successfully saved {total_saved} artifacts across {len(artifacts_by_page)} pages")
            return total_saved > 0
            
        except Exception as e:
            logger.error(f"Error saving artifacts from data: {e}")
            return False
    
    def search_artifacts(self, query: str = None, limit: int = 100) -> List[Dict]:
        """Search artifacts using the new schema"""
        if not self.enabled:
            return []
            
        try:
            # Use the database function for search
            if query:
                result = self.supabase_client.rpc("search_artifacts", {
                    "search_term": query,
                    "limit_count": limit
                }).execute()
            else:
                result = self.supabase_client.table("artifacts").select("*").order(
                    "created_at", desc=True
                ).limit(limit).execute()
            
            # Convert back to original format for compatibility
            artifacts = []
            for record in result.data:
                artifact = {
                    "Name_EN": record.get("name_en", ""),
                    "Name_AR": record.get("name_ar", ""),
                    "Name_FR": record.get("name_fr", ""),
                    "Creator": record.get("creator", ""),
                    "Creation Date": record.get("creation_date", ""),
                    "Materials": record.get("materials", ""),
                    "Origin": record.get("origin", ""),
                    "Description": record.get("description", ""),
                    "Category": record.get("category", ""),
                    "source_page": record.get("source_page", record.get("page_number", "")),
                    "source_document": record.get("source_document", ""),
                    "Name_validation": record.get("name_validation", "")
                }
                artifacts.append(artifact)
            
            logger.info(f"🔍 Found {len(artifacts)} artifacts matching query")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics using the new schema"""
        if not self.enabled:
            return {"enabled": False}
            
        try:
            # Use the enhanced statistics function
            try:
                stats_result = self.supabase_client.rpc("get_artifact_statistics").execute()
            except Exception as rpc_error:
                logger.warning(f"RPC call for statistics failed, falling back to simple counting: {rpc_error}")
                stats_result = None
            
            if stats_result.data:
                stats = stats_result.data[0]
                return {
                    "enabled": True,
                    "total_artifacts": stats.get("total_artifacts", 0),
                    "unique_runs": stats.get("unique_runs", 0),
                    "unique_pages": stats.get("unique_pages", 0),
                    "categories_count": stats.get("categories_count", 0),
                    "creators_count": stats.get("creators_count", 0),
                    "origins_count": stats.get("origins_count", 0),
                    "unique_documents_count": stats.get("unique_documents_count", 0),
                    "last_updated": datetime.now().isoformat()
                }
            else:
                # Fallback to simple counting
                artifacts_count = self.supabase_client.table("artifacts").select(
                    "*", count="exact"
                ).execute()
                
                runs_count = self.supabase_client.table("processing_cache").select(
                    "run_cache_key", count="exact"
                ).execute()
                
                return {
                    "enabled": True,
                    "total_artifacts": artifacts_count.count,
                    "unique_runs": runs_count.count,
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
