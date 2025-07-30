"""
Supabase integration for artifact storage and caching
"""
import os
import json
import hashlib
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

try:
    from supabase import create_client, Client
except ImportError:
    print("Supabase not installed. Install with: pip install supabase")
    raise

logger = logging.getLogger(__name__)

class SupabaseArtifactManager:
    """Manages artifact storage and retrieval from Supabase database"""
    
    def __init__(self):
        # Get Supabase credentials from environment
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized successfully")
    
    def _generate_content_hash(self, file_path: str, model: str, processing_params: Dict) -> str:
        """Generate a unique hash for the processing configuration"""
        hasher = hashlib.sha256()
        
        # Include file content hash
        with open(file_path, 'rb') as f:
            file_content = f.read()
            hasher.update(file_content)
        
        # Include processing parameters
        params_str = json.dumps(processing_params, sort_keys=True)
        hasher.update(params_str.encode())
        hasher.update(model.encode())
        
        return hasher.hexdigest()
    
    def check_processing_cache(self, file_path: str, model: str, processing_params: Dict) -> Optional[str]:
        """Check if this exact processing has been done before"""
        try:
            content_hash = self._generate_content_hash(file_path, model, processing_params)
            file_name = os.path.basename(file_path)
            
            result = self.client.table("processing_cache").select("*").eq(
                "content_hash", content_hash
            ).eq("file_name", file_name).execute()
            
            if result.data:
                cache_entry = result.data[0]
                logger.info(f"Found cached processing for {file_name} with hash {content_hash[:8]}...")
                return cache_entry["processing_run_id"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking processing cache: {e}")
            return None
    
    def create_processing_run(self, file_path: str, model: str, processing_params: Dict) -> str:
        """Create a new processing run record"""
        try:
            run_id = str(uuid.uuid4())
            content_hash = self._generate_content_hash(file_path, model, processing_params)
            
            processing_run = {
                "id": run_id,
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "model": model,
                "processing_params": processing_params,
                "content_hash": content_hash,
                "status": "running",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.client.table("processing_runs").insert(processing_run).execute()
            
            # Also add to cache
            cache_entry = {
                "content_hash": content_hash,
                "file_name": os.path.basename(file_path),
                "processing_run_id": run_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.client.table("processing_cache").insert(cache_entry).execute()
            
            logger.info(f"Created processing run {run_id} for {os.path.basename(file_path)}")
            return run_id
            
        except Exception as e:
            logger.error(f"Error creating processing run: {e}")
            raise
    
    def update_processing_status(self, run_id: str, status: str, error_message: str = None):
        """Update the status of a processing run"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            self.client.table("processing_runs").update(update_data).eq("id", run_id).execute()
            logger.info(f"Updated processing run {run_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Error updating processing status: {e}")
    
    def save_artifacts(self, run_id: str, artifacts: List[Dict]) -> List[str]:
        """Save extracted artifacts to database"""
        try:
            artifact_ids = []
            
            for artifact in artifacts:
                artifact_id = str(uuid.uuid4())
                
                artifact_record = {
                    "id": artifact_id,
                    "processing_run_id": run_id,
                    "name_en": artifact.get("Name", artifact.get("Name_EN", "")),
                    "name_ar": artifact.get("Name_AR", ""),
                    "name_fr": artifact.get("Name_FR", ""),
                    "creator": artifact.get("Creator", ""),
                    "creation_date": artifact.get("Creation Date", ""),
                    "materials": artifact.get("Materials", ""),
                    "origin": artifact.get("Origin", ""),
                    "description": artifact.get("Description", ""),
                    "category": artifact.get("Category", ""),
                    "source_page": artifact.get("source_page"),
                    "source_document": artifact.get("source_document", ""),
                    "metadata": artifact,  # Store full artifact data as JSON
                    "created_at": datetime.utcnow().isoformat()
                }
                
                result = self.client.table("artifacts").insert(artifact_record).execute()
                artifact_ids.append(artifact_id)
            
            logger.info(f"Saved {len(artifacts)} artifacts for run {run_id}")
            return artifact_ids
            
        except Exception as e:
            logger.error(f"Error saving artifacts: {e}")
            raise
    
    def get_artifacts_by_run_id(self, run_id: str) -> List[Dict]:
        """Retrieve all artifacts for a processing run"""
        try:
            result = self.client.table("artifacts").select("*").eq(
                "processing_run_id", run_id
            ).execute()
            
            artifacts = []
            for record in result.data:
                # Convert back to original format
                artifact = record["metadata"] if record["metadata"] else {}
                
                # Ensure basic fields are populated
                artifact.update({
                    "Name": record["name_en"] or artifact.get("Name", ""),
                    "Name_EN": record["name_en"] or artifact.get("Name_EN", ""),
                    "Name_AR": record["name_ar"] or artifact.get("Name_AR", ""),
                    "Name_FR": record["name_fr"] or artifact.get("Name_FR", ""),
                    "Creator": record["creator"] or artifact.get("Creator", ""),
                    "Creation Date": record["creation_date"] or artifact.get("Creation Date", ""),
                    "Materials": record["materials"] or artifact.get("Materials", ""),
                    "Origin": record["origin"] or artifact.get("Origin", ""),
                    "Description": record["description"] or artifact.get("Description", ""),
                    "Category": record["category"] or artifact.get("Category", ""),
                    "source_page": record["source_page"] or artifact.get("source_page"),
                    "source_document": record["source_document"] or artifact.get("source_document", "")
                })
                
                artifacts.append(artifact)
            
            logger.info(f"Retrieved {len(artifacts)} artifacts for run {run_id}")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error retrieving artifacts: {e}")
            return []
    
    def search_artifacts(self, query: str = None, language: str = None, 
                        category: str = None, creator: str = None, 
                        limit: int = 100) -> List[Dict]:
        """Search artifacts with various filters"""
        try:
            query_builder = self.client.table("artifacts").select("*")
            
            if query:
                # Search in names and descriptions
                query_builder = query_builder.or_(f"name_en.ilike.%{query}%,name_ar.ilike.%{query}%,name_fr.ilike.%{query}%,description.ilike.%{query}%")
            
            if category:
                query_builder = query_builder.eq("category", category)
            
            if creator:
                query_builder = query_builder.ilike("creator", f"%{creator}%")
            
            result = query_builder.limit(limit).execute()
            
            artifacts = []
            for record in result.data:
                artifact = record["metadata"] if record["metadata"] else {}
                artifact.update({
                    "Name_EN": record["name_en"],
                    "Name_AR": record["name_ar"],
                    "Name_FR": record["name_fr"],
                    "Creator": record["creator"],
                    "Category": record["category"],
                    "Description": record["description"]
                })
                artifacts.append(artifact)
            
            logger.info(f"Found {len(artifacts)} artifacts matching search criteria")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return []
    
    def get_processing_runs(self, limit: int = 50) -> List[Dict]:
        """Get recent processing runs"""
        try:
            result = self.client.table("processing_runs").select("*").order(
                "created_at", desc=True
            ).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error retrieving processing runs: {e}")
            return []
    
    def delete_processing_run(self, run_id: str) -> bool:
        """Delete a processing run and all its artifacts"""
        try:
            # Delete artifacts first (due to foreign key constraint)
            self.client.table("artifacts").delete().eq("processing_run_id", run_id).execute()
            
            # Delete from cache
            self.client.table("processing_cache").delete().eq("processing_run_id", run_id).execute()
            
            # Delete processing run
            self.client.table("processing_runs").delete().eq("id", run_id).execute()
            
            logger.info(f"Deleted processing run {run_id} and all associated data")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting processing run: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            # Count total artifacts
            artifacts_result = self.client.table("artifacts").select("id", count="exact").execute()
            total_artifacts = artifacts_result.count
            
            # Count processing runs
            runs_result = self.client.table("processing_runs").select("id", count="exact").execute()
            total_runs = runs_result.count
            
            # Count by status
            completed_runs = self.client.table("processing_runs").select("id", count="exact").eq("status", "completed").execute().count
            failed_runs = self.client.table("processing_runs").select("id", count="exact").eq("status", "failed").execute().count
            
            # Count by category
            categories_result = self.client.table("artifacts").select("category").execute()
            categories = {}
            for record in categories_result.data:
                cat = record.get("category", "Unknown")
                categories[cat] = categories.get(cat, 0) + 1
            
            return {
                "total_artifacts": total_artifacts,
                "total_processing_runs": total_runs,
                "completed_runs": completed_runs,
                "failed_runs": failed_runs,
                "running_runs": total_runs - completed_runs - failed_runs,
                "categories": categories
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
