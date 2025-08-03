"""
Configuration manager for handling environment variables and Streamlit secrets
"""
import os
import hashlib
import json
from pathlib import Path
from dotenv import load_dotenv

# Import streamlit only when needed to avoid issues in non-Streamlit contexts
def get_streamlit():
    """Safely import and return streamlit, or None if not available"""
    try:
        import streamlit as st
        return st
    except ImportError:
        return None

def load_configuration():
    """
    Load configuration from multiple sources in order of priority:
    1. Streamlit secrets (for deployed apps)
    2. Environment variables (for containers/hosting)
    3. .env file (for local development)
    """
    
    # First, try to load from .env file (local development)
    project_root = Path(__file__).parent.parent if __name__ != "__main__" else Path(__file__).parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)  # Don't override existing vars
    
    # Configuration mapping
    config_vars = {
        # Database configuration
        'SUPABASE_URL': None,
        'SUPABASE_ANON_KEY': None,
        'SUPABASE_SERVICE_KEY': None,
        'ENABLE_SUPABASE': 'false',
        
        # API Keys
        'OPENAI_API_KEY': None,
        'MISTRAL_API_KEY': None,
        'GOOGLE_API_KEY': None,
    }
    
    # Get streamlit safely
    st = get_streamlit()
    
    # Load configuration from various sources
    for var_name in config_vars.keys():
        value = None
        
        # 1. Try Streamlit secrets first (for deployed apps)
        if st is not None:
            try:
                if hasattr(st, 'secrets'):
                    if var_name in ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_KEY', 'ENABLE_SUPABASE']:
                        value = st.secrets.get("database", {}).get(var_name)
                    elif var_name in ['OPENAI_API_KEY', 'MISTRAL_API_KEY', 'GOOGLE_API_KEY']:
                        value = st.secrets.get("api_keys", {}).get(var_name)
            except Exception:
                pass
        
        # 2. Fall back to environment variables
        if not value:
            value = os.getenv(var_name, config_vars[var_name])
        
        # 3. Set the environment variable for other modules to use
        if value:
            os.environ[var_name] = str(value)
    
    return True

def get_config_status():
    """Get the current configuration status for debugging"""
    status = {}
    
    # Get streamlit safely
    st = get_streamlit()
    
    vars_to_check = [
        'SUPABASE_URL', 'SUPABASE_ANON_KEY', 'ENABLE_SUPABASE',
        'OPENAI_API_KEY', 'MISTRAL_API_KEY', 'GOOGLE_API_KEY'
    ]
    
    for var in vars_to_check:
        value = os.getenv(var)
        status[var] = {
            'set': bool(value),
            'source': 'unknown'
        }
        
        # Try to determine source
        if st is not None and hasattr(st, 'secrets'):
            try:
                if var in ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_KEY', 'ENABLE_SUPABASE']:
                    if st.secrets.get("database", {}).get(var):
                        status[var]['source'] = 'streamlit_secrets'
                elif var in ['OPENAI_API_KEY', 'MISTRAL_API_KEY', 'GOOGLE_API_KEY']:
                    if st.secrets.get("api_keys", {}).get(var):
                        status[var]['source'] = 'streamlit_secrets'
            except Exception:
                pass
        
        if status[var]['source'] == 'unknown' and value:
            # Check if .env file exists
            project_root = Path(__file__).parent.parent if __name__ != "__main__" else Path(__file__).parent
            env_path = project_root / ".env"
            if env_path.exists():
                status[var]['source'] = 'env_file'
            else:
                status[var]['source'] = 'environment'
    
    return status

def generate_processing_params_hash(ocr_correction_threshold=None, api_model=None, 
                                  temperature=None, max_tokens=None, **kwargs):
    """
    Generate a hash of processing parameters for cache invalidation.
    This ensures we re-process when any significant parameter changes.
    """
    params = {
        'ocr_correction_threshold': ocr_correction_threshold,
        'api_model': api_model,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    
    # Add any additional parameters
    params.update(kwargs)
    
    # Remove None values and sort for consistent hashing
    filtered_params = {k: v for k, v in params.items() if v is not None}
    
    # Create deterministic JSON string
    params_str = json.dumps(filtered_params, sort_keys=True, default=str)
    
    # Generate SHA256 hash
    return hashlib.sha256(params_str.encode()).hexdigest()[:16]  # 16 chars for brevity

def get_model_identifiers(config):
    """
    Extract model identifiers from configuration for caching purposes.
    Returns tuple of (ocr_model, extraction_model)
    """
    ocr_model = "default_ocr"  # You can make this configurable
    
    # Extract extraction model from API model setting
    api_model = config.get('api_model', 'gpt-4o-mini')
    extraction_model = api_model
    
    return ocr_model, extraction_model

if __name__ == "__main__":
    # For testing
    load_configuration()
    status = get_config_status()
    for var, info in status.items():
        print(f"{var}: {'✅' if info['set'] else '❌'} ({info['source']})")
    
    # Test parameter hashing
    test_hash = generate_processing_params_hash(
        ocr_correction_threshold=0.8,
        api_model="gpt-4o-mini",
        temperature=0.0
    )
    print(f"\nTest hash: {test_hash}")
