"""
Supabase integration for artifact storage and caching
"""
import os
import json
import hashlib
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    print("Supabase not installed. Install with: pip install supabase")
    raise

# Import config manager
from .config_manager import load_configuration, generate_processing_params_hash, get_model_identifiers

logger = logging.getLogger(__name__)

class SupabaseArtifactManager:
    """Manages artifact storage and retrieval from Supabase database"""
    
    def __init__(self):
        # Load configuration from config manager
        load_configuration()
        
        # Get Supabase credentials - check Streamlit secrets first, then environment
        self.url = self._get_credential("SUPABASE_URL")
        self.key = self._get_credential("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            logger.warning("SUPABASE_URL and SUPABASE_ANON_KEY not set. Using mock mode for testing.")
            self.client = None
            self.mock_mode = True
        else:
            try:
                self.client: Client = create_client(self.url, self.key)
                self.mock_mode = False
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
                self.mock_mode = True
        
        self.table_name = "artifacts"
        self.cache_table = "processing_cache"
        self.page_cache_table = "page_processing_cache"
        self._mock_data = {}  # For mock mode storage
        self._mock_page_cache = {}  # For mock page-level cache
        self._mock_id_counter = 1

    def _get_credential(self, key: str) -> Optional[str]:
        """Get credential from Streamlit secrets first, then environment variables"""
        try:
            # Try Streamlit secrets first
            import streamlit as st
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except (ImportError, AttributeError, KeyError):
            pass
        
        # Fallback to environment variables
        return os.getenv(key)

    def _mock_response(self, operation: str, data: Any = None) -> Any:
        """Return mock response when Supabase is not available"""
        if self.mock_mode:
            logger.warning(f"Mock mode: {operation} operation")
            if operation in ["insert", "update", "get"]:
                return data or {}
            elif operation == "list":
                return list(self._mock_data.values())
            else:
                return []
        return data
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _map_artifact_to_db(self, artifact_data: dict, file_path: str = None, 
                           ocr_model: str = None, extraction_model: str = None,
                           processing_params_hash: str = None) -> dict:
        """Map artifact data to match the new database schema"""
        # Calculate file hash and name if file_path provided
        file_hash = ""
        file_name = ""
        if file_path:
            file_hash = self._calculate_file_hash(file_path)
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
            "ocr_model": ocr_model or artifact_data.get("ocr_model", "default_ocr"),
            "extraction_model": extraction_model or artifact_data.get("extraction_model", "gpt-4o-mini"),
            "processing_params_hash": processing_params_hash or artifact_data.get("processing_params_hash", "")
        }
        
        # Remove None values
        return {k: v for k, v in mapped_data.items() if v is not None}

    def check_file_processed(self, file_path: str, ocr_model: str = "default_ocr", 
                           extraction_model: str = "gpt-4o-mini", processing_params_hash: str = "") -> bool:
        """Check if a file has already been processed with specific models and parameters"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            cache_key = f"cache_{file_hash}_{ocr_model}_{extraction_model}_{processing_params_hash}"
            return cache_key in self._mock_data
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            response = self.client.table(self.cache_table)\
                .select("file_hash")\
                .eq("file_hash", file_hash)\
                .eq("ocr_model", ocr_model)\
                .eq("extraction_model", extraction_model)\
                .eq("processing_params_hash", processing_params_hash)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking file processing status: {e}")
            return False

    def mark_file_processed(self, file_path: str, artifact_count: int = 0,
                          ocr_model: str = "default_ocr", extraction_model: str = "gpt-4o-mini",
                          processing_params_hash: str = ""):
        """Mark a file as processed in cache with model information"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            file_name = os.path.basename(file_path)
            cache_key = f"cache_{file_hash}_{ocr_model}_{extraction_model}_{processing_params_hash}"
            self._mock_data[cache_key] = {
                "file_hash": file_hash,
                "file_name": file_name,
                "ocr_model": ocr_model,
                "extraction_model": extraction_model,
                "processing_params_hash": processing_params_hash,
                "artifact_count": artifact_count
            }
            logger.info(f"Mock: Marked file {file_name} as processed with {artifact_count} artifacts using {ocr_model}/{extraction_model}")
            return
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            file_name = os.path.basename(file_path)
            
            cache_data = {
                "file_hash": file_hash,
                "file_name": file_name,
                "ocr_model": ocr_model,
                "extraction_model": extraction_model,
                "processing_params_hash": processing_params_hash,
                "artifact_count": artifact_count
            }
            
            self.client.table(self.cache_table).insert(cache_data).execute()
            logger.info(f"Marked file {file_name} as processed with {artifact_count} artifacts using {ocr_model}/{extraction_model}")
        except Exception as e:
            logger.error(f"Error marking file as processed: {e}")

    def _generate_processing_params_hash(self, model: str = "gpt-4o", **kwargs) -> str:
        """Generate hash for processing parameters to enable cache invalidation"""
        params = {
            "model": model,
            **kwargs
        }
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()

    def check_page_processed(self, file_path: str, page_number: int, 
                           ocr_model: str = "default_ocr", extraction_model: str = "gpt-4o-mini",
                           processing_params_hash: str = "") -> bool:
        """Check if a specific page has already been processed with specific models"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            cache_key = f"page_{file_hash}_{page_number}_{ocr_model}_{extraction_model}_{processing_params_hash}"
            return cache_key in self._mock_page_cache
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            
            response = self.client.rpc("check_page_processing_cache", {
                "p_file_hash": file_hash,
                "p_page_number": page_number,
                "p_ocr_model": ocr_model,
                "p_extraction_model": extraction_model,
                "p_processing_params_hash": processing_params_hash
            }).execute()
            
            return bool(response.data and response.data[0].get('cached', False))
        except Exception as e:
            logger.error(f"Error checking page processing status: {e}")
            return False

    def get_page_artifacts(self, file_path: str, page_number: int) -> List[dict]:
        """Get all artifacts for a specific page"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            artifacts = [v for k, v in self._mock_data.items() 
                        if k.startswith("artifact_") 
                        and v.get('file_hash') == file_hash 
                        and v.get('source_page') == page_number]
            return sorted(artifacts, key=lambda x: x.get('id', 0))
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            response = self.client.rpc("get_page_artifacts", {
                "p_file_hash": file_hash,
                "p_page_number": page_number
            }).execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting page artifacts: {e}")
            return []

    def mark_page_processed(self, file_path: str, page_number: int, 
                          artifact_count: int = 0, ocr_model: str = "default_ocr", 
                          extraction_model: str = "gpt-4o-mini", processing_params_hash: str = ""):
        """Mark a specific page as processed with model information"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            file_name = os.path.basename(file_path)
            cache_key = f"page_{file_hash}_{page_number}_{ocr_model}_{extraction_model}_{processing_params_hash}"
            
            self._mock_page_cache[cache_key] = {
                "file_hash": file_hash,
                "file_name": file_name,
                "page_number": page_number,
                "ocr_model": ocr_model,
                "extraction_model": extraction_model,
                "processing_params_hash": processing_params_hash,
                "artifact_count": artifact_count,
                "processing_status": "completed"
            }
            logger.info(f"Mock: Marked page {page_number} of {file_name} as processed with {artifact_count} artifacts using {ocr_model}/{extraction_model}")
            return
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            file_name = os.path.basename(file_path)
            
            cache_data = {
                "file_hash": file_hash,
                "file_name": file_name,
                "page_number": page_number,
                "ocr_model": ocr_model,
                "extraction_model": extraction_model,
                "processing_params_hash": processing_params_hash,
                "artifact_count": artifact_count,
                "processing_status": "completed"
            }
            
            self.client.table(self.page_cache_table).insert(cache_data).execute()
            logger.info(f"Marked page {page_number} of {file_name} as processed with {artifact_count} artifacts using {ocr_model}/{extraction_model}")
        except Exception as e:
            logger.error(f"Error marking page as processed: {e}")

    def get_processed_pages(self, file_path: str, model: str = "gpt-4o", 
                          **processing_params) -> List[int]:
        """Get list of already processed page numbers for a file"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            params_hash = self._generate_processing_params_hash(model, **processing_params)
            
            processed_pages = []
            for cache_key, cache_data in self._mock_page_cache.items():
                if (cache_data.get('file_hash') == file_hash and 
                    cache_data.get('processing_model') == model and
                    cache_data.get('processing_params_hash') == params_hash):
                    processed_pages.append(cache_data.get('page_number'))
            
            return sorted(processed_pages)
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            params_hash = self._generate_processing_params_hash(model, **processing_params)
            
            response = self.client.table(self.page_cache_table)\
                .select("page_number")\
                .eq("file_hash", file_hash)\
                .eq("processing_model", model)\
                .eq("processing_params_hash", params_hash)\
                .eq("processing_status", "completed")\
                .order("page_number")\
                .execute()
            
            return [row['page_number'] for row in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting processed pages: {e}")
            return []

    def get_artifacts_by_file(self, file_hash: str) -> List[dict]:
        """Get all artifacts from a specific file"""
        if self.mock_mode:
            # Return artifacts with matching file_hash from mock data
            artifacts = [v for k, v in self._mock_data.items() 
                        if k.startswith("artifact_") and v.get('file_hash') == file_hash]
            return sorted(artifacts, key=lambda x: x.get('source_page', 0))
        
        try:
            response = self.client.table(self.table_name)\
                .select("*")\
                .eq("file_hash", file_hash)\
                .order("source_page")\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting artifacts by file: {e}")
            return []

    def add_artifact(self, artifact_data: dict, file_path: str = None,
                   ocr_model: str = "default_ocr", extraction_model: str = "gpt-4o-mini",
                   processing_params_hash: str = "") -> dict:
        """Add a new artifact to the database with model tracking"""
        if self.mock_mode:
            db_data = self._map_artifact_to_db(artifact_data, file_path, 
                                             ocr_model, extraction_model, processing_params_hash)
            db_data['id'] = self._mock_id_counter
            self._mock_data[f"artifact_{self._mock_id_counter}"] = db_data
            self._mock_id_counter += 1
            logger.info(f"Mock: Added artifact with ID: {db_data['id']} using {ocr_model}/{extraction_model}")
            return db_data
        
        try:
            db_data = self._map_artifact_to_db(artifact_data, file_path, 
                                             ocr_model, extraction_model, processing_params_hash)
            response = self.client.table(self.table_name).insert(db_data).execute()
            
            if response.data:
                logger.info(f"Added artifact with ID: {response.data[0]['id']} using {ocr_model}/{extraction_model}")
                return response.data[0]
            else:
                logger.error("Failed to add artifact: No data returned")
                return {}
                
        except Exception as e:
            logger.error(f"Error adding artifact: {e}")
            return {}

    def get_artifact(self, artifact_id: int) -> dict:
        """Get a single artifact by ID"""
        if self.mock_mode:
            for k, v in self._mock_data.items():
                if k.startswith("artifact_") and v.get('id') == artifact_id:
                    return v
            return {}
        
        try:
            response = self.client.table(self.table_name)\
                .select("*")\
                .eq("id", artifact_id)\
                .single()\
                .execute()
            return response.data if response.data else {}
        except Exception as e:
            logger.error(f"Error getting artifact {artifact_id}: {e}")
            return {}

    def update_artifact(self, artifact_id: int, updates: dict, file_path: str = None) -> dict:
        """Update an existing artifact"""
        if self.mock_mode:
            for k, v in self._mock_data.items():
                if k.startswith("artifact_") and v.get('id') == artifact_id:
                    db_updates = self._map_artifact_to_db(updates, file_path)
                    v.update(db_updates)
                    logger.info(f"Mock: Updated artifact with ID: {artifact_id}")
                    return v
            return {}
        
        try:
            db_updates = self._map_artifact_to_db(updates, file_path)
            response = self.client.table(self.table_name)\
                .update(db_updates)\
                .eq("id", artifact_id)\
                .execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error updating artifact {artifact_id}: {e}")
            return {}

    def delete_artifact(self, artifact_id: int) -> bool:
        """Delete an artifact"""
        if self.mock_mode:
            for k, v in list(self._mock_data.items()):
                if k.startswith("artifact_") and v.get('id') == artifact_id:
                    del self._mock_data[k]
                    logger.info(f"Mock: Deleted artifact with ID: {artifact_id}")
                    return True
            return False
        
        try:
            response = self.client.table(self.table_name)\
                .delete()\
                .eq("id", artifact_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting artifact {artifact_id}: {e}")
            return False

    def list_artifacts(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """List artifacts with pagination"""
        if self.mock_mode:
            artifacts = [v for k, v in self._mock_data.items() if k.startswith("artifact_")]
            return artifacts[offset:offset+limit]
        
        try:
            response = self.client.table(self.table_name)\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error listing artifacts: {e}")
            return []
    def search_artifacts(self, 
                        search_term: str = None,
                        category_filter: str = None,
                        creator_filter: str = None,
                        origin_filter: str = None,
                        limit: int = 100,
                        offset: int = 0) -> List[dict]:
        """Search artifacts using the database function"""
        if self.mock_mode:
            # Simple mock search implementation
            artifacts = [v for k, v in self._mock_data.items() if k.startswith("artifact_")]
            filtered = []
            
            for artifact in artifacts:
                matches = True
                if search_term and search_term.lower() not in str(artifact.get('name_en', '')).lower():
                    matches = False
                if category_filter and artifact.get('category') != category_filter:
                    matches = False
                if creator_filter and creator_filter.lower() not in str(artifact.get('creator', '')).lower():
                    matches = False
                if origin_filter and origin_filter.lower() not in str(artifact.get('origin', '')).lower():
                    matches = False
                
                if matches:
                    filtered.append(artifact)
            
            return filtered[offset:offset+limit]
        
        try:
            response = self.client.rpc("search_artifacts", {
                "search_term": search_term,
                "category_filter": category_filter,
                "creator_filter": creator_filter,
                "origin_filter": origin_filter,
                "limit_count": limit,
                "offset_count": offset
            }).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return []

    def filter_artifacts(self, **filters) -> List[dict]:
        """Filter artifacts by various criteria"""
        if self.mock_mode:
            artifacts = [v for k, v in self._mock_data.items() if k.startswith("artifact_")]
            filtered = []
            
            for artifact in artifacts:
                matches = True
                for key, value in filters.items():
                    if value is not None and artifact.get(key) != value:
                        matches = False
                        break
                
                if matches:
                    filtered.append(artifact)
            
            return filtered
        
        try:
            query = self.client.table(self.table_name).select("*")
            
            for key, value in filters.items():
                if value is not None:
                    query = query.eq(key, value)
                    
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error filtering artifacts: {e}")
            return []

    def get_statistics(self) -> dict:
        """Get artifact statistics using the database function"""
        if self.mock_mode:
            artifacts = [v for k, v in self._mock_data.items() if k.startswith("artifact_")]
            unique_files = len(set(a.get('file_hash', '') for a in artifacts))
            categories = len(set(a.get('category', '') for a in artifacts if a.get('category')))
            creators = len(set(a.get('creator', '') for a in artifacts if a.get('creator')))
            origins = len(set(a.get('origin', '') for a in artifacts if a.get('origin')))
            
            return {
                "total_artifacts": len(artifacts),
                "unique_files": unique_files,
                "categories_count": categories,
                "creators_count": creators,
                "origins_count": origins
            }
        
        try:
            response = self.client.rpc("get_artifact_statistics").execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def check_page_processed(self, file_path: str, page_number: int) -> bool:
        """Check if a specific page has already been processed"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            # Check if any artifacts exist for this file hash and page number
            for k, v in self._mock_data.items():
                if (k.startswith("artifact_") and 
                    v.get('file_hash') == file_hash and 
                    v.get('source_page') == page_number):
                    return True
            return False
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            response = self.client.table(self.table_name)\
                .select("id")\
                .eq("file_hash", file_hash)\
                .eq("source_page", page_number)\
                .limit(1)\
                .execute()
            
            exists = len(response.data) > 0
            if exists:
                logger.info(f"Page {page_number} of {os.path.basename(file_path)} already processed")
            return exists
            
        except Exception as e:
            logger.error(f"Error checking if page {page_number} is processed: {e}")
            return False

    def get_page_artifacts(self, file_path: str, page_number: int) -> List[dict]:
        """Get all artifacts from a specific page"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            artifacts = []
            for k, v in self._mock_data.items():
                if (k.startswith("artifact_") and 
                    v.get('file_hash') == file_hash and 
                    v.get('source_page') == page_number):
                    artifacts.append(v)
            return artifacts
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            response = self.client.table(self.table_name)\
                .select("*")\
                .eq("file_hash", file_hash)\
                .eq("source_page", page_number)\
                .order("id")\
                .execute()
            
            artifacts = response.data if response.data else []
            if artifacts:
                logger.info(f"Retrieved {len(artifacts)} artifacts from page {page_number}")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error getting artifacts for page {page_number}: {e}")
            return []

    def get_processed_pages(self, file_path: str) -> List[int]:
        """Get list of already processed page numbers for a file"""
        if self.mock_mode:
            file_hash = self._calculate_file_hash(file_path)
            pages = set()
            for k, v in self._mock_data.items():
                if (k.startswith("artifact_") and 
                    v.get('file_hash') == file_hash):
                    pages.add(v.get('source_page', 0))
            return sorted(list(pages))
        
        try:
            file_hash = self._calculate_file_hash(file_path)
            response = self.client.table(self.table_name)\
                .select("source_page")\
                .eq("file_hash", file_hash)\
                .execute()
            
            if response.data:
                pages = sorted(list(set(item['source_page'] for item in response.data if item['source_page'])))
                logger.info(f"Found {len(pages)} processed pages: {pages}")
                return pages
            return []
            
        except Exception as e:
            logger.error(f"Error getting processed pages: {e}")
            return []

    def save_artifacts_batch(self, artifacts: List[Dict], file_path: str = None) -> List[int]:
        """Save multiple artifacts to database in batch"""
        if self.mock_mode:
            artifact_ids = []
            file_hash = ""
            file_name = ""
            
            if file_path:
                file_hash = self._calculate_file_hash(file_path)
                file_name = os.path.basename(file_path)
            
            for artifact in artifacts:
                # Ensure file metadata is included
                artifact['file_hash'] = artifact.get('file_hash', file_hash)
                artifact['file_name'] = artifact.get('file_name', file_name)
                artifact['source_document'] = artifact.get('source_document', file_name)
                
                db_data = self._map_artifact_to_db(artifact, file_path)
                db_data['id'] = self._mock_id_counter
                self._mock_data[f"artifact_{self._mock_id_counter}"] = db_data
                artifact_ids.append(self._mock_id_counter)
                self._mock_id_counter += 1
            
            logger.info(f"Mock: Saved {len(artifact_ids)} artifacts in batch")
            
            # Mark file as processed if file_path provided
            if file_path:
                self.mark_file_processed(file_path, len(artifact_ids))
            
            return artifact_ids
        
        try:
            artifact_ids = []
            file_hash = ""
            file_name = ""
            
            if file_path:
                file_hash = self._calculate_file_hash(file_path)
                file_name = os.path.basename(file_path)
            
            db_records = []
            for artifact in artifacts:
                # Ensure file metadata is included
                artifact['file_hash'] = artifact.get('file_hash', file_hash)
                artifact['file_name'] = artifact.get('file_name', file_name)
                artifact['source_document'] = artifact.get('source_document', file_name)
                
                db_record = self._map_artifact_to_db(artifact, file_path)
                db_records.append(db_record)
            
            if db_records:
                response = self.client.table(self.table_name).insert(db_records).execute()
                
                if response.data:
                    artifact_ids = [record['id'] for record in response.data]
                    logger.info(f"Saved {len(artifact_ids)} artifacts in batch")
                    
                    # Mark file as processed if file_path provided
                    if file_path:
                        self.mark_file_processed(file_path, len(artifact_ids))
                
            return artifact_ids
            
        except Exception as e:
            logger.error(f"Error saving artifacts batch: {e}")
            return []
