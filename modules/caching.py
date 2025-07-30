"""
Caching system for artifact processing
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .supabase_client import SupabaseArtifactManager
from ..config import ENABLE_SUPABASE, ENABLE_PROCESSING_CACHE, CACHE_RELEVANT_PARAMS

logger = logging.getLogger(__name__)

class ProcessingCache:
    """Manages caching of processing results"""
    
    def __init__(self):
        self.use_supabase = ENABLE_SUPABASE and ENABLE_PROCESSING_CACHE
        self.supabase_manager = None
        
        if self.use_supabase:
            try:
                self.supabase_manager = SupabaseArtifactManager()
                logger.info("Initialized Supabase-based caching")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase caching: {e}")
                self.use_supabase = False
        
        if not self.use_supabase:
            logger.info("Using local file-based caching fallback")
    
    def _create_processing_params_dict(self, **kwargs) -> Dict:
        """Create a standardized processing parameters dictionary"""
        params = {}
        for key in CACHE_RELEVANT_PARAMS:
            if key in kwargs and kwargs[key] is not None:
                params[key] = kwargs[key]
        
        # Add any additional processing-specific parameters
        for key, value in kwargs.items():
            if key.startswith('correction_threshold') or key.endswith('_model'):
                params[key] = value
        
        return params
    
    def check_cache(self, file_path: str, **processing_params) -> Optional[str]:
        """Check if processing results exist in cache"""
        if not ENABLE_PROCESSING_CACHE:
            return None
        
        try:
            params = self._create_processing_params_dict(**processing_params)
            
            if self.use_supabase and self.supabase_manager:
                return self.supabase_manager.check_processing_cache(
                    file_path, 
                    params.get("model", "gpt-4o"), 
                    params
                )
            else:
                # Local file-based cache fallback
                return self._check_local_cache(file_path, params)
        
        except Exception as e:
            logger.error(f"Error checking cache: {e}")
            return None
    
    def _check_local_cache(self, file_path: str, params: Dict) -> Optional[str]:
        """Check local file-based cache"""
        try:
            import hashlib
            
            # Generate cache key
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
            
            params_str = json.dumps(params, sort_keys=True)
            hasher.update(params_str.encode())
            
            cache_key = hasher.hexdigest()
            file_name = os.path.basename(file_path)
            
            # Check for cache file
            cache_dir = os.path.join(os.path.dirname(file_path), ".cache")
            cache_file = os.path.join(cache_dir, f"{file_name}_{cache_key[:16]}.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Check if cache is still valid (not expired)
                from datetime import datetime, timedelta
                cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
                if datetime.now() - cache_time < timedelta(days=30):  # 30 day expiry
                    logger.info(f"Found valid local cache for {file_name}")
                    return cache_data.get("run_id", cache_key)
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking local cache: {e}")
            return None
    
    def create_processing_run(self, file_path: str, **processing_params) -> str:
        """Create a new processing run entry"""
        try:
            params = self._create_processing_params_dict(**processing_params)
            
            if self.use_supabase and self.supabase_manager:
                return self.supabase_manager.create_processing_run(
                    file_path,
                    params.get("model", "gpt-4o"),
                    params
                )
            else:
                # Local cache fallback
                return self._create_local_run(file_path, params)
        
        except Exception as e:
            logger.error(f"Error creating processing run: {e}")
            # Generate a simple run ID as fallback
            import uuid
            return str(uuid.uuid4())
    
    def _create_local_run(self, file_path: str, params: Dict) -> str:
        """Create local processing run entry"""
        try:
            import uuid
            import hashlib
            
            run_id = str(uuid.uuid4())
            
            # Generate content hash
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
            params_str = json.dumps(params, sort_keys=True)
            hasher.update(params_str.encode())
            content_hash = hasher.hexdigest()
            
            # Create cache directory
            cache_dir = os.path.join(os.path.dirname(file_path), ".cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Save run metadata
            file_name = os.path.basename(file_path)
            cache_file = os.path.join(cache_dir, f"{file_name}_{content_hash[:16]}.json")
            
            cache_data = {
                "run_id": run_id,
                "file_path": file_path,
                "file_name": file_name,
                "params": params,
                "content_hash": content_hash,
                "timestamp": datetime.now().isoformat(),
                "status": "running"
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Created local processing run {run_id}")
            return run_id
        
        except Exception as e:
            logger.error(f"Error creating local run: {e}")
            import uuid
            return str(uuid.uuid4())
    
    def save_artifacts(self, run_id: str, artifacts: List[Dict]) -> bool:
        """Save processing results to cache"""
        try:
            if self.use_supabase and self.supabase_manager:
                self.supabase_manager.save_artifacts(run_id, artifacts)
                self.supabase_manager.update_processing_status(run_id, "completed")
                return True
            else:
                return self._save_local_artifacts(run_id, artifacts)
        
        except Exception as e:
            logger.error(f"Error saving artifacts to cache: {e}")
            return False
    
    def _save_local_artifacts(self, run_id: str, artifacts: List[Dict]) -> bool:
        """Save artifacts to local cache"""
        try:
            # Find the cache file for this run
            cache_dir = None
            cache_file = None
            
            # Search for cache files containing this run_id
            for root, dirs, files in os.walk("."):
                if ".cache" in dirs:
                    cache_dir = os.path.join(root, ".cache")
                    for file in os.listdir(cache_dir):
                        if file.endswith(".json"):
                            try:
                                with open(os.path.join(cache_dir, file), 'r') as f:
                                    data = json.load(f)
                                if data.get("run_id") == run_id:
                                    cache_file = os.path.join(cache_dir, file)
                                    break
                            except:
                                continue
                    if cache_file:
                        break
            
            if cache_file:
                # Update cache file with results
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                cache_data.update({
                    "artifacts": artifacts,
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "artifact_count": len(artifacts)
                })
                
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                logger.info(f"Saved {len(artifacts)} artifacts to local cache")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error saving local artifacts: {e}")
            return False
    
    def get_cached_artifacts(self, run_id: str) -> List[Dict]:
        """Retrieve artifacts from cache"""
        try:
            if self.use_supabase and self.supabase_manager:
                return self.supabase_manager.get_artifacts_by_run_id(run_id)
            else:
                return self._get_local_artifacts(run_id)
        
        except Exception as e:
            logger.error(f"Error retrieving cached artifacts: {e}")
            return []
    
    def _get_local_artifacts(self, run_id: str) -> List[Dict]:
        """Get artifacts from local cache"""
        try:
            # Search for cache file with this run_id
            for root, dirs, files in os.walk("."):
                if ".cache" in dirs:
                    cache_dir = os.path.join(root, ".cache")
                    for file in os.listdir(cache_dir):
                        if file.endswith(".json"):
                            try:
                                with open(os.path.join(cache_dir, file), 'r') as f:
                                    data = json.load(f)
                                if data.get("run_id") == run_id:
                                    return data.get("artifacts", [])
                            except:
                                continue
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting local artifacts: {e}")
            return []
    
    def update_status(self, run_id: str, status: str, error_message: str = None):
        """Update processing status"""
        try:
            if self.use_supabase and self.supabase_manager:
                self.supabase_manager.update_processing_status(run_id, status, error_message)
            else:
                self._update_local_status(run_id, status, error_message)
        
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def _update_local_status(self, run_id: str, status: str, error_message: str = None):
        """Update status in local cache"""
        try:
            # Find and update cache file
            for root, dirs, files in os.walk("."):
                if ".cache" in dirs:
                    cache_dir = os.path.join(root, ".cache")
                    for file in os.listdir(cache_dir):
                        if file.endswith(".json"):
                            cache_file = os.path.join(cache_dir, file)
                            try:
                                with open(cache_file, 'r') as f:
                                    data = json.load(f)
                                
                                if data.get("run_id") == run_id:
                                    data["status"] = status
                                    data["updated_at"] = datetime.now().isoformat()
                                    if error_message:
                                        data["error_message"] = error_message
                                    
                                    with open(cache_file, 'w') as f:
                                        json.dump(data, f, indent=2)
                                    
                                    logger.info(f"Updated local cache status to {status}")
                                    return
                            except:
                                continue
        
        except Exception as e:
            logger.error(f"Error updating local status: {e}")

# Global cache instance
_cache_instance = None

def get_cache() -> ProcessingCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ProcessingCache()
    return _cache_instance
