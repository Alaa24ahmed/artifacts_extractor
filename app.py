import streamlit as st
import os
import tempfile
import sys
import json
import pandas as pd
import time
import threading
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import glob
import traceback
import logging
from logging.handlers import RotatingFileHandler
import io
import re

# Add the project root to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Load configuration using the new configuration manager
try:
    from modules.config_manager import load_configuration, get_config_status
    load_configuration()
    print("✅ Configuration loaded successfully")
except Exception as e:
    print(f"⚠️ Error loading configuration: {e}")
    # Fallback to manual loading
    project_root = Path(__file__).parent
    env_path = project_root / ".env"
    load_dotenv(env_path, override=True)

# Import database functionality
try:
    from modules.simple_db import get_simple_db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Set page config
st.set_page_config(
    page_title="Multilingual Museum Artifact Extractor",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for better styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton button {
        background-color: #4169E1;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton button:hover {
        background-color: #2a4fc1;
    }
    .reset-button button {
        background-color: #6c757d;
    }
    .reset-button button:hover {
        background-color: #5a6268;
    }
    .processing-button button {
        background-color: #6c757d !important;
        cursor: not-allowed !important;
    }
    .css-18e3th9 {
        padding-top: 2rem;
    }
    .title-container {
        background-color: #4169E1;
        margin: -1.5rem -1.5rem 1.5rem -1.5rem;
        padding: 2rem 1.5rem;
        color: white;
        border-radius: 0 0 10px 10px;
    }
    .section-header {
        background-color: #f1f3f9;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .upload-section {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    .config-section {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    .status-section {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    .results-section {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.05);
    }
    .stProgress > div > div > div {
        background-color: #4169E1;
    }
    .highlight {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 3px solid #4169E1;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    .success-card {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .info-card {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .warning-card {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .error-card {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .lang-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 3px;
        margin-right: 0.5rem;
        font-weight: 500;
        font-size: 0.8rem;
    }
    .en-badge {
        background-color: #e0f7fa;
        color: #00838f;
    }
    .ar-badge {
        background-color: #f3e5f5;
        color: #7b1fa2;
    }
    .fr-badge {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    .debug-info {
        font-family: monospace;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin: 10px 0;
        font-size: 12px;
    }
    .log-container {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 15px;
        font-family: monospace;
        font-size: 13px;
        height: 600px;
        min-height: 600px;
        max-height: 80vh;
        overflow-y: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.4;
        resize: vertical;
    }
    .button-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        width: 100%;
        max-width: 800px;
        margin: 20px auto;
    }
    .main-button {
        flex: 3;
    }
    .secondary-button {
        flex: 1;
    }
    .progress-container {
        width: 100%;
        max-width: 800px;
        margin: 20px auto;
    }
</style>
""", unsafe_allow_html=True)

# Add the project root to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# ================ LOGGING SETUP ================
def setup_logging():
    """Configure the logging system to capture logs to file and console"""
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove all existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create a file handler
    if os.path.exists(LOG_FILE):
        # Truncate the file when starting a new processing run
        try:
            with open(LOG_FILE, 'w') as f:
                pass
        except Exception as e:
            print(f"Error resetting log file: {e}")
    
    # INCREASED SIZE LIMIT for multi-page processing to prevent log rotation mid-process
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=50*1024*1024, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

# ================ SESSION STATE ================
# Initialize all session state variables to prevent KeyError
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
    print(f"Created temp directory: {st.session_state.temp_dir}")

if 'processing_status' not in st.session_state:
    st.session_state.processing_status = {
        'status': 'idle',
        'progress': 0,
        'message': '',
        'results_dir': None,
        'error': None
    }

if 'uploaded_file_paths' not in st.session_state:
    st.session_state.uploaded_file_paths = {'EN': None, 'AR': None, 'FR': None}
    
if 'uploaded_file_names' not in st.session_state:
    st.session_state.uploaded_file_names = {'EN': None, 'AR': None, 'FR': None}

if 'processing_start_time' not in st.session_state:
    st.session_state.processing_start_time = None

if 'display_logs' not in st.session_state:
    st.session_state.display_logs = True

if 'last_log_position' not in st.session_state:
    st.session_state.last_log_position = 0

# Initialize API keys in session state if they don't exist
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""
if 'mistral_api_key' not in st.session_state:
    st.session_state.mistral_api_key = ""
if 'google_api_key' not in st.session_state:
    st.session_state.google_api_key = ""

# Initialize last processing parameters for database saving
if 'last_processing_params' not in st.session_state:
    st.session_state.last_processing_params = {
        'ocr_model': 'gpt-4o',
        'extraction_model': 'gpt-4o',
        'base_model': 'gpt-4o',
        'correction_thresholds': {"EN": 0.05, "AR": 0.10, "FR": 0.07}
    }

# Files for communication between threads and UI
STATUS_FILE = os.path.join(st.session_state.temp_dir, "processing_status.json")
COMPLETION_MARKER = os.path.join(st.session_state.temp_dir, "processing_completed")
RESULTS_PATH_FILE = os.path.join(st.session_state.temp_dir, "results_path.txt")
PROCESSING_START_TIME_FILE = os.path.join(st.session_state.temp_dir, "processing_start_time.txt")
TRIGGER_REFRESH_FILE = os.path.join(st.session_state.temp_dir, "trigger_refresh.txt")
LOG_FILE = os.path.join(st.session_state.temp_dir, "processing.log")

# Set up logging
if 'logger' not in st.session_state:
    st.session_state.logger = setup_logging()
    st.session_state.logger.info("Logging system initialized")

# ================ UTILITY FUNCTIONS ================
def update_original_filenames():
    """Update the original filenames JSON file with current session state values"""
    original_filenames = {
        "EN": st.session_state.uploaded_file_names['EN'],
        "AR": st.session_state.uploaded_file_names['AR'],
        "FR": st.session_state.uploaded_file_names['FR']
    }
    original_filenames_path = os.path.join(st.session_state.temp_dir, "original_filenames.json")
    try:
        with open(original_filenames_path, 'w') as f:
            json.dump(original_filenames, f)
        print(f"Updated original filenames JSON: {original_filenames}")
    except Exception as e:
        print(f"Error updating original filenames: {e}")

def save_uploaded_file(uploaded_file, lang):
    """Save an uploaded file to the temp directory"""
    if uploaded_file is None:
        return None
        
    # Create a path for the file
    file_ext = uploaded_file.name.split('.')[-1]
    file_path = os.path.join(st.session_state.temp_dir, f"{lang}_document.{file_ext}")
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Store paths and names
    st.session_state.uploaded_file_paths[lang] = file_path
    st.session_state.uploaded_file_names[lang] = uploaded_file.name
    
    # Log the uploaded file details
    print(f"Saved {lang} document: {uploaded_file.name} to {file_path}")
    
    # Immediately update the original filenames JSON file to ensure it's always current
    update_original_filenames()
    
    return file_path

def update_status_file(status, message='', progress=0, results_dir=None, error=None):
    """Update the status file that's used to communicate between threads"""
    status_data = {
        'status': status,
        'message': message,
        'progress': progress,
        'results_dir': results_dir,
        'error': error,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
            
        # Create a completion marker file if completed
        if status == 'completed' and results_dir:
            with open(COMPLETION_MARKER, 'w') as f:
                f.write(results_dir)
                
    except Exception as e:
        print(f"Error updating status file: {e}")

def read_status_file():
    """Read the status file and return the data"""
    if not os.path.exists(STATUS_FILE):
        return None
    
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading status file: {e}")
        return None

def find_results_directory():
    """Find the results directory even if it's not explicitly set"""
    # Check if we have a direct path to the results file
    if os.path.exists(RESULTS_PATH_FILE):
        try:
            with open(RESULTS_PATH_FILE, 'r') as f:
                results_file = f.read().strip()
                if os.path.exists(results_file):
                    print(f"Found results file from path file: {results_file}")
                    return os.path.dirname(results_file)
        except Exception as e:
            print(f"Error reading results path file: {e}")
    
    # First check if we have it in the completion marker
    if os.path.exists(COMPLETION_MARKER):
        try:
            with open(COMPLETION_MARKER, 'r') as f:
                results_dir = f.read().strip()
                if os.path.exists(results_dir):
                    print(f"Found results directory from completion marker: {results_dir}")
                    return results_dir
        except Exception as e:
            print(f"Error reading completion marker: {e}")
    
    # Then check in the session state
    if st.session_state.processing_status.get('results_dir'):
        if os.path.exists(st.session_state.processing_status['results_dir']):
            print(f"Found results directory from session state: {st.session_state.processing_status['results_dir']}")
            return st.session_state.processing_status['results_dir']
    
    # Explicit search for the typical document structure
    pattern = os.path.join(st.session_state.temp_dir, "output", "*", "gpt-4o")
    matching_dirs = glob.glob(pattern)
    if matching_dirs:
        for dir_path in matching_dirs:
            if os.path.exists(dir_path):
                print(f"Found potential results directory by pattern matching: {dir_path}")
                # Check if it contains the multilingual JSON file
                json_files = [f for f in os.listdir(dir_path) if f.endswith("_multilingual.json")]
                if json_files:
                    print(f"Found results directory with multilingual files: {dir_path}")
                    return dir_path
    
    # Search recursively through the temp directory for multilingual JSON files
    for root, dirs, files in os.walk(st.session_state.temp_dir):
        for file in files:
            if file.endswith("_multilingual.json"):
                print(f"Found results file during recursive search: {os.path.join(root, file)}")
                return root
    
    print("Could not find results directory")
    return None

def get_latest_logs(max_lines=50):
    """Read the latest logs from the log file, handling log rotation"""
    if not os.path.exists(LOG_FILE):
        return "No logs available yet."
    
    try:
        # Check current log file size and content
        log_files_to_check = [LOG_FILE]
        
        # If main log file is empty or very small, check backup files
        if os.path.getsize(LOG_FILE) < 100:  # Less than 100 bytes might indicate rotation
            # Add backup files in order (newest first)
            for i in range(1, 6):  # Check up to 5 backup files
                backup_file = f"{LOG_FILE}.{i}"
                if os.path.exists(backup_file):
                    log_files_to_check.append(backup_file)
        
        all_lines = []
        
        # Read from available log files
        for log_file in log_files_to_check:
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        all_lines.extend(lines)
                        # If we have enough lines, we can stop
                        if len(all_lines) >= max_lines * 2:  # Get extra to ensure we have enough
                            break
            except Exception as e:
                # If one file fails, continue with others
                continue
        
        if not all_lines:
            return "No logs available."
        
        # Get the last max_lines
        latest_lines = all_lines[-max_lines:] if len(all_lines) > max_lines else all_lines
        
        # Format the logs for display with proper highlighting
        formatted_lines = []
        for line in latest_lines:
            # Clean up timestamp format for better readability
            line = re.sub(r'^\d{4}-\d{2}-\d{2} ', '', line)
            
            # Highlight different log levels with colors
            if ' INFO - ' in line:
                # Highlight key processing stages more prominently
                if any(x in line for x in ['Processing', 'Extracting', 'Created', 'Results saved']):
                    line = f'<span style="color: #4169E1; font-weight: bold;">{line}</span>'
                else:
                    line = f'<span style="color: #0066cc;">{line}</span>'
            elif ' WARNING - ' in line:
                line = f'<span style="color: #ff9900;">{line}</span>'
            elif ' ERROR - ' in line:
                line = f'<span style="color: #cc0000; font-weight: bold;">{line}</span>'
            
            formatted_lines.append(line)
        
        return "<br>".join(formatted_lines)
    except Exception as e:
        return f"Error reading logs: {str(e)}"

def process_documents(doc_group, output_dir, model, start_page, end_page, 
                     correction_thresholds, prompts, csv_fields, 
                     ocr_model, extraction_model):
    """Process documents in a background thread"""
    try:
        # Ensure configuration is loaded in this background thread
        try:
            from modules.config_manager import load_configuration
            load_configuration()
            print("✅ Configuration loaded in background thread")
        except Exception as e:
            print(f"⚠️ Error loading configuration in background thread: {e}")
            # Fallback to manual loading
            project_root = Path(__file__).parent
            env_path = project_root / ".env"
            load_dotenv(env_path, override=True)
        
        # Update status file to indicate processing has started
        update_status_file(
            status='processing',
            message='Starting processing...',
            progress=5
        )
        
        # Import modules
        from config import MULTILINGUAL_CSV_FIELDS
        from modules.processors import process_multilingual_document_set
        
        # Process the documents
        results = process_multilingual_document_set(
            doc_group=doc_group,
            output_dir=output_dir,
            model=model,
            start_page=start_page,
            end_page=end_page,
            correction_thresholds=correction_thresholds,
            prompts=prompts,
            csv_fields=csv_fields,
            ocr_model=ocr_model,
            extraction_model=extraction_model,
            save_to_db=False  # Disable automatic saving, only save when button is pressed
        )
        
        # Find the actual results directory by explicitly looking for the multilingual file
        results_dir = None
        results_file = None
        
        # First look for multilingual JSON files
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith("_multilingual.json"):
                    results_file = os.path.join(root, file)
                    results_dir = root
                    print(f"Found results file: {results_file}")
                    break
            if results_dir:
                break
                
        if not results_dir:
            results_dir = output_dir
            
        print(f"Final results directory: {results_dir}")
        
        # Save the exact path to the results file
        if results_file:
            try:
                with open(RESULTS_PATH_FILE, "w") as f:
                    f.write(results_file)
                print(f"Saved results file path to: {RESULTS_PATH_FILE}")
            except Exception as e:
                print(f"Error writing results path file: {e}")
        
        # Update status file to indicate processing is complete
        update_status_file(
            status='completed',
            message='Processing complete!',
            progress=100,
            results_dir=results_dir
        )
        
        # Also create a completion marker file with the results directory
        with open(COMPLETION_MARKER, 'w') as f:
            f.write(results_dir)
        
        # Create a flag file to trigger UI refresh
        with open(TRIGGER_REFRESH_FILE, 'w') as f:
            f.write(str(time.time()))
        
    except Exception as e:
        # Error handling - update status file with error information
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"Error during processing: {error_msg}")
        print(f"Traceback: {traceback_str}")
        
        update_status_file(
            status='error',
            message=f"Error: {error_msg}",
            error=error_msg
        )
        
        # Create an error trigger file to ensure UI updates even on error
        with open(TRIGGER_REFRESH_FILE, 'w') as f:
            f.write(f"error-{time.time()}")

def check_status_updates():
    """Check for updates from the background thread via the status file"""
    status_data = read_status_file()
    if status_data:
        # Update session state with the latest status
        st.session_state.processing_status['status'] = status_data['status']
        st.session_state.processing_status['message'] = status_data['message']
        st.session_state.processing_status['progress'] = status_data['progress']
        
        if status_data['results_dir']:
            st.session_state.processing_status['results_dir'] = status_data['results_dir']
            
        if status_data['error']:
            st.session_state.processing_status['error'] = status_data['error']
    
    # Also check the completion marker file
    if os.path.exists(COMPLETION_MARKER) and st.session_state.processing_status['status'] != 'completed':
        try:
            with open(COMPLETION_MARKER, 'r') as f:
                results_dir = f.read().strip()
                if os.path.exists(results_dir):
                    st.session_state.processing_status['status'] = 'completed'
                    st.session_state.processing_status['message'] = 'Processing complete!'
                    st.session_state.processing_status['progress'] = 100
                    st.session_state.processing_status['results_dir'] = results_dir
        except:
            pass
    
    # Check for trigger refresh file
    if os.path.exists(TRIGGER_REFRESH_FILE):
        # Remove the file
        os.remove(TRIGGER_REFRESH_FILE)
        # Force a rerun if status has changed
        if st.session_state.processing_status['status'] in ['completed', 'error']:
            time.sleep(0.5)  # Small delay to ensure files are fully written
            st.rerun()

def display_results(output_dir=None):
    """Display extraction results"""
    # If no output_dir is provided, try to find it
    if not output_dir:
        output_dir = find_results_directory()
    
    print(f"Attempting to display results from: {output_dir}")
    
    if not output_dir or not os.path.exists(output_dir):
        with st.container():
            st.markdown('<div class="warning-card">No results directory found.</div>', unsafe_allow_html=True)
            
            # Check if we have the direct path to the results file
            if os.path.exists(RESULTS_PATH_FILE):
                try:
                    with open(RESULTS_PATH_FILE, 'r') as f:
                        results_file = f.read().strip()
                        if os.path.exists(results_file):
                            st.markdown(f'<div class="info-card">Found results file: {results_file}</div>', unsafe_allow_html=True)
                            output_dir = os.path.dirname(results_file)
                            # Continue with this file
                            st.markdown(f'<div class="info-card">Using directory: {output_dir}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="warning-card">Results file not found: {results_file}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-card">Error reading results path: {str(e)}</div>', unsafe_allow_html=True)
            
            if not output_dir or not os.path.exists(output_dir):
                # Try to find any multilingual files in the temp directory
                json_files = []
                for root, dirs, files in os.walk(st.session_state.temp_dir):
                    for file in files:
                        if file.endswith("_multilingual.json"):
                            json_files.append(os.path.join(root, file))
                
                if json_files:
                    st.markdown(f'<div class="info-card">Found alternative result file: {json_files[0]}</div>', unsafe_allow_html=True)
                    # Use this file instead
                    output_dir = os.path.dirname(json_files[0])
                    st.markdown(f'<div class="info-card">Using directory: {output_dir}</div>', unsafe_allow_html=True)
                else:
                    return
    
    # At this point, output_dir should be a valid directory
    # Find the JSON and CSV files directly in this directory
    json_file = None
    csv_file = None
    
    for file in os.listdir(output_dir):
        if file.endswith("_multilingual.json"):
            json_file = os.path.join(output_dir, file)
        elif file.endswith("_multilingual.csv"):
            csv_file = os.path.join(output_dir, file)
    
    print(f"Found JSON file: {json_file}")
    print(f"Found CSV file: {csv_file}")
    
    if not json_file:
        # Try recursive search one level down
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith("_multilingual.json"):
                    json_file = os.path.join(root, file)
                elif file.endswith("_multilingual.csv"):
                    csv_file = os.path.join(root, file)
            if json_file:  # Stop once we find a JSON file
                break
    
    if json_file and os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                artifacts = json.load(f)
            
            # Replace generic document names with original filenames
            original_names_file = os.path.join(st.session_state.temp_dir, "original_filenames.json")
            if os.path.exists(original_names_file):
                try:
                    with open(original_names_file, 'r') as f:
                        original_names = json.load(f)
                    
                    print(f"Original filenames: {original_names}")
                    
                    # First, print all unique source document names to help debugging
                    unique_sources = set()
                    for artifact in artifacts:
                        if "source_document" in artifact and artifact["source_document"]:
                            unique_sources.add(artifact["source_document"])
                        elif "Source_Document" in artifact and artifact["Source_Document"]:
                            unique_sources.add(artifact["Source_Document"])
                    print(f"Unique source document names found: {unique_sources}")
                    
                    # Create pattern matching for each language (case insensitive)
                    en_patterns = ["en_document", "/en/", "en_document.pdf", "_en_", "/output/en/"]
                    ar_patterns = ["ar_document", "/ar/", "ar_document.pdf", "_ar_", "/output/ar/"]
                    fr_patterns = ["fr_document", "/fr/", "fr_document.pdf", "_fr_", "/output/fr/"]
                    
                    # Create exact matches for direct replacement
                    en_exact = ["EN_document.pdf"]
                    ar_exact = ["AR_document.pdf"]
                    fr_exact = ["FR_document.pdf"]
                    
                    # Replace source document names with more comprehensive pattern matching
                    replacement_count = 0
                    for artifact in artifacts:
                        # Check for both capitalization versions of the field
                        source_field = None
                        if "source_document" in artifact and artifact["source_document"]:
                            source_field = "source_document"
                        elif "Source_Document" in artifact and artifact["Source_Document"]:
                            source_field = "Source_Document"
                        
                        if source_field:
                            doc_name = artifact[source_field]
                            doc_name_lower = doc_name.lower()  # For case-insensitive matching
                            
                            # First try exact matches
                            if doc_name in en_exact and original_names.get("EN"):
                                artifact[source_field] = original_names["EN"]
                                print(f"Exact match - Replaced '{doc_name}' with '{original_names['EN']}'")
                                replacement_count += 1
                            elif doc_name in ar_exact and original_names.get("AR"):
                                artifact[source_field] = original_names["AR"]
                                print(f"Exact match - Replaced '{doc_name}' with '{original_names['AR']}'")
                                replacement_count += 1
                            elif doc_name in fr_exact and original_names.get("FR"):
                                artifact[source_field] = original_names["FR"]
                                print(f"Exact match - Replaced '{doc_name}' with '{original_names['FR']}'")
                                replacement_count += 1
                            
                            # Then try pattern matching
                            elif any(pattern in doc_name_lower for pattern in en_patterns) and original_names.get("EN"):
                                artifact[source_field] = original_names["EN"]
                                print(f"Pattern match - Replaced '{doc_name}' with '{original_names['EN']}'")
                                replacement_count += 1
                            elif any(pattern in doc_name_lower for pattern in ar_patterns) and original_names.get("AR"):
                                artifact[source_field] = original_names["AR"]
                                print(f"Pattern match - Replaced '{doc_name}' with '{original_names['AR']}'")
                                replacement_count += 1
                            elif any(pattern in doc_name_lower for pattern in fr_patterns) and original_names.get("FR"):
                                artifact[source_field] = original_names["FR"]
                                print(f"Pattern match - Replaced '{doc_name}' with '{original_names['FR']}'")
                                replacement_count += 1
                            
                            # Fallback: Try direct language matching if pattern matching fails
                            elif "EN" in doc_name and original_names.get("EN"):
                                artifact[source_field] = original_names["EN"]
                                print(f"Language match - Replaced '{doc_name}' with '{original_names['EN']}'")
                                replacement_count += 1
                            elif "AR" in doc_name and original_names.get("AR"):
                                artifact[source_field] = original_names["AR"]
                                print(f"Language match - Replaced '{doc_name}' with '{original_names['AR']}'")
                                replacement_count += 1
                            elif "FR" in doc_name and original_names.get("FR"):
                                artifact[source_field] = original_names["FR"]
                                print(f"Language match - Replaced '{doc_name}' with '{original_names['FR']}'")
                                replacement_count += 1
                    
                    print(f"Total document name replacements: {replacement_count}")
                    
                except Exception as e:
                    print(f"Error applying original file names: {e}")
                    print(f"Exception details: {traceback.format_exc()}")
            
            # Display summary
            st.markdown(f"""
            <div class="highlight">
                <h3 style="margin-top: 0;">Summary</h3>
                <p>Found <b>{len(artifacts)}</b> artifacts in the documents</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display artifacts table
            st.markdown('<h3>Extracted Artifacts</h3>', unsafe_allow_html=True)
            
            # Create DataFrame
            df = pd.DataFrame(artifacts)
            
            # Filter out caching-related and internal fields
            cache_related_fields = [
                'file_hash', 'processing_params_hash', 'page_cache_key',
                'ocr_model', 'extraction_model', 'created_at', 'updated_at', 'id'
            ]
            
            # Keep only relevant columns for display
            display_columns = [col for col in df.columns if col not in cache_related_fields]
            df = df[display_columns]
            
            # Reorder columns to show names first, then metadata
            name_cols = [col for col in df.columns if col.startswith("Name_")]
            metadata_cols = [col for col in df.columns if col in ["Creator", "Creation Date", "Materials", "Origin", "Description", "Category"]]
            source_cols = [col for col in df.columns if col.startswith("source_")]
            other_cols = [col for col in df.columns if col not in name_cols + metadata_cols + source_cols]
            
            # Create the complete column order (names, metadata, source info, then everything else)
            ordered_columns = name_cols + metadata_cols + source_cols + other_cols
            
            # Reorder the dataframe with filtered columns
            df = df[ordered_columns]
            
            # Add search functionality
            search_term = st.text_input("🔍 Search artifacts", placeholder="Enter search term...", label_visibility="visible")
            
            if search_term:
                # Create a filter mask across all columns
                mask = pd.Series(False, index=df.index)
                for col in df.columns:
                    mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
                filtered_df = df[mask]
                st.markdown(f"<p>Found <b>{len(filtered_df)}</b> artifacts matching '<i>{search_term}</i>'</p>", unsafe_allow_html=True)
                st.dataframe(filtered_df, use_container_width=True, height=400)
            else:
                st.dataframe(df, use_container_width=True, height=400)
            
            # Download buttons
            st.markdown('<h3>Actions</h3>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            # JSON download
            with open(json_file, "rb") as f:
                json_data = f.read()
            
            with col1:
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name="multilingual_artifacts.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            # CSV download
            if csv_file and os.path.exists(csv_file):
                with open(csv_file, "rb") as f:
                    csv_data = f.read()
                
                with col2:
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name="multilingual_artifacts.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            elif json_file:
                # Generate CSV from JSON if CSV not found
                with col2:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV (Generated)",
                        data=csv_data,
                        file_name="multilingual_artifacts.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            # Save to database button - using regular button style, not custom class
            with col3:
                if st.button("💾 Save to Database", use_container_width=True, key="save_to_db_button"):
                    if not DATABASE_AVAILABLE:
                        st.error("Database module not available. Please check your setup.")
                    else:
                        try:
                            db = get_simple_db()
                            
                            if db is None:
                                st.warning("Database not configured. Please check your .env file with Supabase credentials.")
                            elif not db.enabled:
                                st.warning("Database disabled. Please check your environment variables.")
                            else:
                                # Use the same logic as display_results to find files
                                results_file = None
                                
                                # First check if output_dir has multilingual files
                                if output_dir and os.path.exists(output_dir):
                                    for file in os.listdir(output_dir):
                                        if file.endswith("_multilingual.json"):
                                            results_file = os.path.join(output_dir, file)
                                            break
                                
                                # If not found, check the results path file
                                if not results_file and os.path.exists(RESULTS_PATH_FILE):
                                    try:
                                        with open(RESULTS_PATH_FILE, 'r') as f:
                                            results_file_path = f.read().strip()
                                            if os.path.exists(results_file_path) and results_file_path.endswith("_multilingual.json"):
                                                results_file = results_file_path
                                    except Exception:
                                        pass
                                
                                # If still not found, search in temp directory
                                if not results_file:
                                    for root, dirs, files in os.walk(st.session_state.temp_dir):
                                        for file in files:
                                            if file.endswith("_multilingual.json"):
                                                results_file = os.path.join(root, file)
                                                break
                                        if results_file:
                                            break
                                
                                if results_file:
                                    # Load and save artifacts
                                    with open(results_file, 'r', encoding='utf-8') as f:
                                        artifacts_data = json.load(f)
                                    
                                    # Calculate file hash for the processed files
                                    import hashlib
                                    file_content = json.dumps(artifacts_data, sort_keys=True)
                                    file_hash = hashlib.sha256(file_content.encode()).hexdigest()
                                    
                                    # Save to database
                                    with st.spinner("Saving to database..."):
                                        try:
                                            # Group artifacts by page for proper saving
                                            artifacts_by_page = {}
                                            for artifact in artifacts_data:
                                                page_num = artifact.get("source_page", 1)
                                                if page_num not in artifacts_by_page:
                                                    artifacts_by_page[page_num] = []
                                                artifacts_by_page[page_num].append(artifact)
                                            
                                            # Save each page separately with actual user-selected models
                                            # Use actual document name from session state
                                            actual_doc_name = st.session_state.uploaded_file_names.get('EN', 'unknown_document.pdf')
                                            if actual_doc_name is None:
                                                actual_doc_name = 'unknown_document.pdf'
                                            doc_group = {"EN": actual_doc_name}
                                            
                                            # Use the actual models selected by the user from session state
                                            if hasattr(st.session_state, 'last_processing_params') and st.session_state.last_processing_params:
                                                params = st.session_state.last_processing_params
                                                actual_ocr_model = params.get('ocr_model', 'gpt-4o')
                                                actual_extraction_model = params.get('extraction_model', 'gpt-4o')
                                                actual_thresholds = params.get('correction_thresholds', {"EN": 0.05, "AR": 0.10, "FR": 0.07})
                                            else:
                                                # Fallback to defaults if no parameters stored
                                                actual_ocr_model = "gpt-4o"
                                                actual_extraction_model = "gpt-4o"
                                                actual_thresholds = {"EN": 0.05, "AR": 0.10, "FR": 0.07}
                                            
                                            total_saved = 0
                                            for page_num, page_artifacts in artifacts_by_page.items():
                                                success = db.save_page_artifacts(
                                                    doc_group, page_num, page_artifacts,
                                                    actual_ocr_model, actual_extraction_model, actual_thresholds,
                                                    provided_file_hash=file_hash
                                                )
                                                if success:
                                                    total_saved += len(page_artifacts)
                                            
                                            if total_saved > 0:
                                                st.success(f"✅ Successfully saved {total_saved} artifacts to database!")
                                                st.info(f"📁 Saved from: {os.path.basename(results_file)}")
                                                
                                                # Temporary debug info to verify the fixes
                                                with st.expander("📊 Database Save Details", expanded=False):
                                                    st.write(f"**Document name**: {actual_doc_name}")
                                                    if artifacts_by_page:
                                                        temp_start = min(artifacts_by_page.keys())
                                                        temp_end = max(artifacts_by_page.keys())
                                                        st.write(f"**Page range**: {temp_start} to {temp_end}")
                                                    st.write(f"**OCR model**: {actual_ocr_model}")
                                                    st.write(f"**Extraction model**: {actual_extraction_model}")
                                                    st.write(f"**File hash**: {file_hash[:16]}...")
                                                
                                                # Save run statistics with correct page range
                                                # Calculate actual page range from the artifacts themselves
                                                if artifacts_by_page:
                                                    actual_start_page = min(artifacts_by_page.keys())
                                                    actual_end_page = max(artifacts_by_page.keys())
                                                else:
                                                    # Fallback to session state if no artifacts
                                                    if hasattr(st.session_state, 'last_processing_params') and st.session_state.last_processing_params:
                                                        params = st.session_state.last_processing_params
                                                        actual_start_page = params.get('start_page', 1)
                                                        actual_end_page = params.get('end_page', 1)
                                                    else:
                                                        actual_start_page = 1
                                                        actual_end_page = 1
                                                
                                                db.save_run_statistics(
                                                    doc_group, actual_start_page, actual_end_page, 
                                                    actual_ocr_model, actual_extraction_model, actual_thresholds,
                                                    total_saved, 0, len(artifacts_by_page),
                                                    provided_file_hash=file_hash
                                                )
                                            else:
                                                st.error("❌ Failed to save artifacts to database.")
                                        except Exception as save_error:
                                            st.error(f"❌ Error during save: {str(save_error)}")
                                else:
                                    st.error("❌ No artifact results found to save.")
                        except Exception as e:
                            st.error(f"Error saving to database: {str(e)}")
                
        except Exception as e:
            st.markdown(f'<div class="error-card">Error displaying results: {str(e)}</div>', unsafe_allow_html=True)
    else:
        with st.container():
            st.markdown('<div class="warning-card">No artifact results found. Processing may have failed.</div>', unsafe_allow_html=True)

def format_time(seconds):
    """Format seconds into a readable time string"""
    if seconds < 1:
        return "less than 1 second"
    elif seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

# ================ MAIN APP ================
def main():
    """Main application function"""
    # Check for trigger refresh file
    if os.path.exists(TRIGGER_REFRESH_FILE):
        try:
            # Read the file to get the timestamp
            with open(TRIGGER_REFRESH_FILE, 'r') as f:
                trigger_time = f.read().strip()
            
            # Remove the file
            os.remove(TRIGGER_REFRESH_FILE)
            
            # Check if the status file indicates completion
            status_data = read_status_file()
            if status_data and status_data['status'] in ['completed', 'error']:
                st.session_state.processing_status = status_data
                
                # Also check for completion marker
                if os.path.exists(COMPLETION_MARKER):
                    with open(COMPLETION_MARKER, 'r') as f:
                        results_dir = f.read().strip()
                        st.session_state.processing_status['results_dir'] = results_dir
                
                # Reload the page to refresh the UI with results
                time.sleep(0.5)  # Short delay to ensure files are fully written
                st.rerun()
        except Exception as e:
            print(f"Error handling trigger file: {e}")
    
    # Check if session state is initialized correctly
    if 'processing_start_time' not in st.session_state:
        st.session_state.processing_start_time = None
        
    # Check if completion marker exists but status doesn't reflect it
    if os.path.exists(COMPLETION_MARKER) and st.session_state.processing_status.get('status') != 'completed':
        print("Found completion marker but status is not completed. Updating status.")
        try:
            with open(COMPLETION_MARKER, 'r') as f:
                results_dir = f.read().strip()
                st.session_state.processing_status = {
                    'status': 'completed',
                    'message': 'Processing complete!',
                    'progress': 100,
                    'results_dir': results_dir,
                    'error': None
                }
        except Exception as e:
            print(f"Error reading completion marker: {e}")
    
    # Check for processing start time file
    if os.path.exists(PROCESSING_START_TIME_FILE) and not st.session_state.processing_start_time:
        try:
            with open(PROCESSING_START_TIME_FILE, 'r') as f:
                start_time = float(f.read().strip())
                st.session_state.processing_start_time = start_time
                print(f"Loaded processing start time from file: {start_time}")
        except Exception as e:
            print(f"Error reading processing start time: {e}")
    
    # Import configuration and prompts
    from config import CORRECTION_THRESHOLDS, MULTILINGUAL_CSV_FIELDS
    from prompts import (
        OCRPrompt, OCRCorrectionPrompt, 
        ArtifactExtractionPrompt, MultilingualNameExtractionPrompt, 
        cross_language_validation_prompt
    )
    
    # Check for status updates from background thread
    check_status_updates()
    
    # App title and description
    st.markdown('<div class="title-container"><h1>🏛️ Multilingual Museum Artifact Extractor</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
    This application extracts detailed artifact information from multilingual museum catalogs.
    Upload documents in English, Arabic, and French to create a consolidated artifact database.
    
    **Features:**
    - Optical Character Recognition (OCR) with auto-correction
    - Artifact metadata extraction (names, creators, dates, materials, etc.)
    - Cross-language name matching and validation
    - Consolidated multilingual database generation
    """)
    
    # Document Upload Section
    st.markdown('<div class="section-header"><h2 style="margin: 0;">1. Upload Documents</h2></div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        # Only show file uploaders if not processing
        if st.session_state.processing_status['status'] != 'processing':
            # File uploaders in columns
            upload_col1, upload_col2, upload_col3 = st.columns(3)
            
            with upload_col1:
                st.markdown('<p><span class="lang-badge en-badge">EN</span> <b>English Document</b> (Required)</p>', unsafe_allow_html=True)
                en_file = st.file_uploader("English Document", type=["pdf", "jpg", "jpeg", "png"], key="en_uploader", label_visibility="collapsed")
                if en_file:
                    save_uploaded_file(en_file, 'EN')
            
            with upload_col2:
                st.markdown('<p><span class="lang-badge ar-badge">AR</span> <b>Arabic Document</b> (Optional)</p>', unsafe_allow_html=True)
                ar_file = st.file_uploader("Arabic Document", type=["pdf", "jpg", "jpeg", "png"], key="ar_uploader", label_visibility="collapsed")
                if ar_file:
                    save_uploaded_file(ar_file, 'AR')
            
            with upload_col3:
                st.markdown('<p><span class="lang-badge fr-badge">FR</span> <b>French Document</b> (Optional)</p>', unsafe_allow_html=True)
                fr_file = st.file_uploader("French Document", type=["pdf", "jpg", "jpeg", "png"], key="fr_uploader", label_visibility="collapsed")
                if fr_file:
                    save_uploaded_file(fr_file, 'FR')
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Configuration Section
    st.markdown('<div class="section-header"><h2 style="margin: 0;">2. Configure Processing</h2></div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="config-section">', unsafe_allow_html=True)
        
        # Model selection in columns - only showing OCR and Extraction models with descriptive names
        model_col1, model_col2 = st.columns(2)
        
        # Always use GPT-4o as the model (but don't display it in UI)
        model = "gpt-4o"
        
        # Define model display names and mapping
        ocr_model_options = [
            ("GPT-4o", "gpt-4o"),
            ("GPT-4", "gpt-4"),
            ("GPT-4o Mini", "gpt-4o-mini"),
            ("Gemini 2.5 Flash", "gemini"),
            ("Mistral OCR", "mistral-ocr")
        ]
        
        extraction_model_options = [
            ("GPT-4o", "gpt-4o"),
            ("GPT-4", "gpt-4"),
            ("GPT-4o Mini", "gpt-4o-mini"),
            ("Gemini 2.5 Flash", "gemini")
        ]
        
        with model_col1:
            st.markdown("<p><b>OCR Model</b></p>", unsafe_allow_html=True)
            ocr_display_value = st.selectbox(
                "OCR Model",
                [option[0] for option in ocr_model_options],
                index=4,  # Default to Mistral OCR
                disabled=st.session_state.processing_status['status'] == 'processing',
                key="ocr_model_display",
                label_visibility="collapsed"
            )
            # Map display value back to internal value
            ocr_model = next(option[1] for option in ocr_model_options if option[0] == ocr_display_value)
        
        with model_col2:
            st.markdown("<p><b>Extraction Model</b></p>", unsafe_allow_html=True)
            extraction_display_value = st.selectbox(
                "Extraction Model",
                [option[0] for option in extraction_model_options],
                index=0,  # Default to GPT-4o
                disabled=st.session_state.processing_status['status'] == 'processing',
                key="extraction_model_display",
                label_visibility="collapsed"
            )
            # Map display value back to internal value
            extraction_model = next(option[1] for option in extraction_model_options if option[0] == extraction_display_value)
        
        # Store processing parameters in session state for later use
        st.session_state.last_processing_params = {
            'ocr_model': ocr_model,
            'extraction_model': extraction_model,
            'base_model': model
        }
        
        # Initialize default values before the expander
        start_page = 1
        end_page = None
        correction_thresholds = CORRECTION_THRESHOLDS.copy()
        # Set Arabic threshold to 0.05 by default
        correction_thresholds["AR"] = 0.05
        
        # Advanced options
        with st.expander("Advanced Options", expanded=True):
            # Page range
            st.markdown("<p><b>Page Range</b></p>", unsafe_allow_html=True)
            page_col1, page_col2, page_col3 = st.columns([1, 1, 1])
            
            with page_col1:
                start_page = st.number_input("Start Page", min_value=1, value=1, 
                                           disabled=st.session_state.processing_status['status'] == 'processing',
                                           key="start_page")
            
            with page_col2:
                # Add "All pages" checkbox
                all_pages = st.checkbox("Till end of document", 
                                     value=False,
                                     disabled=st.session_state.processing_status['status'] == 'processing',
                                     key="all_pages")
            
            with page_col3:
                if all_pages:
                    # If "all pages" is checked, show disabled input with placeholder
                    st.number_input("End Page", 
                                  min_value=start_page, 
                                  value=start_page,
                                  disabled=True,
                                  key="end_page_disabled",
                                  label_visibility="visible")
                    end_page = None  # Use None to indicate all pages
                else:
                    # If "all pages" is unchecked, allow manual entry
                    end_page_input = st.number_input("End Page", 
                                                 min_value=start_page, 
                                                 value=start_page,
                                                 disabled=st.session_state.processing_status['status'] == 'processing',
                                                 key="end_page_enabled")
                    end_page = end_page_input
            
            # Correction thresholds
            st.markdown("<p><b>OCR Correction Thresholds</b> (lower values mean more correction passes)</p>", unsafe_allow_html=True)
            
            threshold_col1, threshold_col2, threshold_col3 = st.columns(3)
            
            with threshold_col1:
                st.markdown('<span class="lang-badge en-badge">EN</span> <b>English</b>', unsafe_allow_html=True)
                correction_thresholds["EN"] = st.slider("English Threshold", min_value=0.01, max_value=0.2, 
                                       value=CORRECTION_THRESHOLDS["EN"], 
                                       step=0.01, format="%.2f", 
                                       disabled=st.session_state.processing_status['status'] == 'processing',
                                       key="en_threshold",
                                       label_visibility="collapsed")
            
            with threshold_col2:
                st.markdown('<span class="lang-badge fr-badge">FR</span> <b>French</b>', unsafe_allow_html=True)
                correction_thresholds["FR"] = st.slider("French Threshold", min_value=0.01, max_value=0.2, 
                                       value=CORRECTION_THRESHOLDS["FR"], 
                                       step=0.01, format="%.2f", 
                                       disabled=st.session_state.processing_status['status'] == 'processing',
                                       key="fr_threshold",
                                       label_visibility="collapsed")
            
            with threshold_col3:
                st.markdown('<span class="lang-badge ar-badge">AR</span> <b>Arabic</b>', unsafe_allow_html=True)
                correction_thresholds["AR"] = st.slider("Arabic Threshold", min_value=0.01, max_value=0.2, 
                                       value=0.05,  # Default set to 0.05 for Arabic
                                       step=0.01, format="%.2f", 
                                       disabled=st.session_state.processing_status['status'] == 'processing',
                                       key="ar_threshold",
                                       label_visibility="collapsed")
        
        # API Key Management - using session state to store keys
        with st.expander("API Keys", expanded=True):
            # OpenAI API Key
            st.markdown("<p><b>OpenAI API Key</b> (required for GPT models)</p>", unsafe_allow_html=True)
            openai_key = st.text_input("OpenAI API Key", type="password", 
                                     value=st.session_state.openai_api_key,
                                     disabled=st.session_state.processing_status['status'] == 'processing',
                                     placeholder="Enter your OpenAI API key",
                                     key="openai_key_input",
                                     label_visibility="collapsed")
            if openai_key:
                # Store in session state (persists during session)
                st.session_state.openai_api_key = openai_key
                # Set as temporary environment variable (only for this process)
                os.environ["OPENAI_API_KEY"] = openai_key
            
            # Mistral API Key
            st.markdown("<p><b>Mistral API Key</b> (required for Mistral OCR)</p>", unsafe_allow_html=True)
            mistral_key = st.text_input("Mistral API Key", type="password",
                                      value=st.session_state.mistral_api_key,
                                      disabled=st.session_state.processing_status['status'] == 'processing',
                                      placeholder="Enter your Mistral API key",
                                      key="mistral_key_input",
                                      label_visibility="collapsed")
            if mistral_key:
                st.session_state.mistral_api_key = mistral_key
                os.environ["MISTRAL_API_KEY"] = mistral_key
            
            # Google API Key
            st.markdown("<p><b>Google API Key</b> (required for Gemini 2.5 Flash model)</p>", unsafe_allow_html=True)
            google_key = st.text_input("Google API Key", type="password",
                                    value=st.session_state.google_api_key,
                                    disabled=st.session_state.processing_status['status'] == 'processing',
                                    placeholder="Enter your Google API key for Gemini 2.5 Flash",
                                    key="google_key_input",
                                    label_visibility="collapsed")
            if google_key:
                st.session_state.google_api_key = google_key
                os.environ["GOOGLE_API_KEY"] = google_key
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Status and Control Section
    st.markdown('<div class="section-header"><h2 style="margin: 0;">3. Process & Results</h2></div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="status-section">', unsafe_allow_html=True)
        
        status = st.session_state.processing_status['status']
        
        # Check API keys
        missing_keys = []
        if not st.session_state.openai_api_key:  # Always check for OpenAI API key since we're using GPT-4o
            missing_keys.append("OpenAI API Key")
        if ocr_model == "mistral-ocr" and not st.session_state.mistral_api_key:
            missing_keys.append("Mistral API Key")
        if (ocr_model == "gemini" or extraction_model == "gemini") and not st.session_state.google_api_key:
            missing_keys.append("Google API Key")
        
        # Warning about missing API keys - shown above the buttons
        if missing_keys:
            st.markdown(f'<div class="warning-card">Missing required API keys: {", ".join(missing_keys)}</div>', unsafe_allow_html=True)
        
        # Process and Reset buttons in centered flex container
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        
        # Process button - main button
        process_disabled = (st.session_state.uploaded_file_paths['EN'] is None or 
                          st.session_state.processing_status['status'] == 'processing' or 
                          len(missing_keys) > 0)
        
        # Show different button states based on processing status
        if st.session_state.processing_status['status'] == 'processing':
            st.markdown('<div class="main-button processing-button">', unsafe_allow_html=True)
            st.button("⏳ Processing...", disabled=True, use_container_width=True, key="processing_button")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="main-button">', unsafe_allow_html=True)
            if st.button("▶️ Start Processing", disabled=process_disabled, use_container_width=True, key="start_button"):
                # Clear previous logs and timer display from UI
                if 'log_output' in st.session_state:
                    st.session_state.log_output = ""
                
                # Reset any previous completion marker and results path
                if os.path.exists(COMPLETION_MARKER):
                    os.remove(COMPLETION_MARKER)
                if os.path.exists(RESULTS_PATH_FILE):
                    os.remove(RESULTS_PATH_FILE)
                if os.path.exists(TRIGGER_REFRESH_FILE):
                    os.remove(TRIGGER_REFRESH_FILE)
                if os.path.exists(PROCESSING_START_TIME_FILE):
                    os.remove(PROCESSING_START_TIME_FILE)
                
                # Clear previous processing state completely
                st.session_state.processing_start_time = None
                st.session_state.processing_status = {
                    'status': 'processing',  # Set to processing immediately
                    'message': 'Starting processing...',
                    'progress': 5,
                    'results_dir': None
                }
                
                # Reset and reconfigure logging (this clears previous logs)
                st.session_state.logger = setup_logging()
                st.session_state.logger.info("Starting new processing run")
                
                # Store final processing parameters for later use (e.g., database saving)
                st.session_state.last_processing_params.update({
                    'correction_thresholds': correction_thresholds.copy(),
                    'start_page': start_page,
                    'end_page': end_page
                })
                
                # Create document group
                doc_group = {
                    "EN": st.session_state.uploaded_file_paths['EN'],
                    "AR": st.session_state.uploaded_file_paths['AR'],
                    "FR": st.session_state.uploaded_file_paths['FR']
                }
                
                # Save original filenames with more detailed logging
                update_original_filenames()  # Use our dedicated function
                
                # Create output directory
                output_dir = os.path.join(st.session_state.temp_dir, "output")
                os.makedirs(output_dir, exist_ok=True)
                
                # Record processing start time
                start_time = time.time()
                st.session_state.processing_start_time = start_time
                
                # Save start time to file for persistence between refreshes
                with open(PROCESSING_START_TIME_FILE, 'w') as f:
                    f.write(str(start_time))
                
                print(f"Setting processing start time: {st.session_state.processing_start_time}")
                
                # Update status in session state
                st.session_state.processing_status['status'] = 'processing'
                st.session_state.processing_status['message'] = 'Starting processing...'
                st.session_state.processing_status['progress'] = 5
                
                # Also update the status file for the background thread
                update_status_file(
                    status='processing',
                    message='Starting processing...',
                    progress=5
                )
                
                # Set up prompts
                prompts = {
                    "ocr": OCRPrompt(),
                    "correction": OCRCorrectionPrompt(),
                    "artifact": ArtifactExtractionPrompt(),
                    "multilingual": MultilingualNameExtractionPrompt(),
                    "validation": cross_language_validation_prompt
                }
                
                # Start processing in a thread
                thread = threading.Thread(
                    target=process_documents,
                    kwargs={
                        'doc_group': doc_group,
                        'output_dir': output_dir,
                        'model': model,
                        'start_page': start_page,
                        'end_page': end_page,
                        'correction_thresholds': correction_thresholds,
                        'prompts': prompts,
                        'csv_fields': MULTILINGUAL_CSV_FIELDS,
                        'ocr_model': ocr_model,
                        'extraction_model': extraction_model
                    },
                    daemon=True
                )
                thread.start()
                
                # Force a rerun to update the UI immediately
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Reset button - only shown when completed or error
        if st.session_state.processing_status['status'] in ['completed', 'error']:
            st.markdown('<div class="secondary-button reset-button">', unsafe_allow_html=True)
            if st.button("🔄 Reset", use_container_width=True):
                # Reset status in session state
                st.session_state.processing_status = {
                    'status': 'idle',
                    'progress': 0,
                    'message': '',
                    'results_dir': None,
                    'error': None
                }
                
                # Reset processing start time
                st.session_state.processing_start_time = None
                
                # Reset and clear logging (this clears all logs)
                st.session_state.logger = setup_logging()
                
                # Also reset all the files
                for file_path in [STATUS_FILE, COMPLETION_MARKER, RESULTS_PATH_FILE, 
                                PROCESSING_START_TIME_FILE, TRIGGER_REFRESH_FILE]:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # Force UI refresh
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Progress bar in its own centered container
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        if status == 'processing':
            st.progress(st.session_state.processing_status['progress'] / 100)
        elif status == 'completed':
            st.progress(1.0)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Status display
        if status == 'idle':
            st.markdown('<div class="info-card">Upload documents and click "Start Processing" to begin.</div>', unsafe_allow_html=True)
        elif status == 'processing':
            # Check for updates from the background thread
            check_status_updates()
            
            # Calculate elapsed time
            if st.session_state.processing_start_time:
                elapsed_time = time.time() - st.session_state.processing_start_time
                elapsed_str = format_time(elapsed_time)
            else:
                elapsed_str = "calculating..."
            
            # Simulate progress - incremental increase over time
            progress = max(st.session_state.processing_status['progress'], 5)
            if progress < 95:
                # Increment progress based on elapsed time (slow at start, faster in middle)
                if elapsed_time < 60:  # First minute
                    new_progress = min(progress + 0.5, 20)
                elif elapsed_time < 300:  # First 5 minutes
                    new_progress = min(progress + 0.3, 50)
                else:  # After 5 minutes
                    new_progress = min(progress + 0.2, 95)
                
                st.session_state.processing_status['progress'] = new_progress
            
            st.markdown(f"""
            <div class="info-card">
                <p><b>Processing in progress...</b></p>
                <p>Elapsed time: {elapsed_str}</p>
                <p>This may take several minutes depending on document size and complexity.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Processing Logs", expanded=st.session_state.display_logs):
                # Add a toggle for auto-scrolling
                auto_scroll = st.checkbox("Auto-scroll to latest logs", value=True)
                
                # Get the latest log content
                logs_html = get_latest_logs(100)  # Get the latest 100 log lines
                
                # Display logs based on auto-scroll setting
                if auto_scroll:
                    # Create a scrollable iframe that always stays at the bottom
                    log_height = 600  # Increased for better visibility
                    st.markdown(f"""
                    <div style="height: {log_height}px; min-height: {log_height}px; overflow: hidden; margin-bottom: 10px;">
                        <iframe srcdoc='
                            <html>
                            <head>
                                <style>
                                    html, body {{
                                        height: 100%;
                                        min-height: 600px;
                                        margin: 0;
                                        padding: 0;
                                        overflow: hidden;
                                    }}
                                    body {{
                                        font-family: monospace;
                                        font-size: 12px;
                                        line-height: 1.5;
                                        padding: 10px;
                                        background-color: #f8f9fa;
                                        overflow-y: auto;
                                        box-sizing: border-box;
                                        height: 100%;
                                    }}
                                    #log-container {{
                                        height: 100%;
                                        overflow-y: auto;
                                    }}
                                    .info {{
                                        color: #0066cc;
                                    }}
                                    .info-bold {{
                                        color: #4169E1;
                                        font-weight: bold;
                                    }}
                                    .warning {{
                                        color: #ff9900;
                                    }}
                                    .error {{
                                        color: #cc0000;
                                        font-weight: bold;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div id="log-container">
                                    <div id="log-content">{logs_html}</div>
                                    <div id="anchor" style="height: 1px;"></div>
                                </div>
                                <script>
                                    // Force scroll to bottom on load
                                    window.onload = function() {{
                                        document.getElementById("log-container").scrollTop = document.getElementById("log-container").scrollHeight;
                                    }};
                                    // Keep scrolling to bottom
                                    setInterval(function() {{
                                        document.getElementById("log-container").scrollTop = document.getElementById("log-container").scrollHeight;
                                    }}, 100);
                                </script>
                            </body>
                            </html>
                        ' height="{log_height}" width="100%" style="height: {log_height}px; min-height: {log_height}px; border: 1px solid #dee2e6; border-radius: 5px; display: block;"></iframe>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Regular version without auto-scroll
                    st.markdown(f"""
                    <div class="log-container" id="logContainer" style="height: 300px; min-height: 300px; max-height: 300px; overflow-y: auto; display: block;">
                        {logs_html}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Auto-refresh during processing
            st.empty()
            time.sleep(1)  # Add a small delay
            st.rerun()
            
        elif status == 'completed':
            # Calculate processing time
            processing_time = None
            
            # Try to get the processing time from the file first
            if os.path.exists(PROCESSING_START_TIME_FILE):
                try:
                    with open(PROCESSING_START_TIME_FILE, 'r') as f:
                        start_time = float(f.read().strip())
                        processing_time = time.time() - start_time
                        print(f"Processing start time from file: {start_time}")
                        print(f"Current time: {time.time()}")
                        print(f"Calculated processing time: {processing_time} seconds")
                except Exception as e:
                    print(f"Error reading processing start time from file: {e}")
            
            # Fall back to session state if file read fails
            if processing_time is None and st.session_state.processing_start_time:
                processing_time = time.time() - st.session_state.processing_start_time
                print(f"Processing start time from session: {st.session_state.processing_start_time}")
                print(f"Current time: {time.time()}")
                print(f"Calculated processing time: {processing_time} seconds")
            
            if processing_time:
                time_str = format_time(processing_time)
                st.markdown(f"""
                <div class="success-card">
                    <p><b>✅ Processing complete!</b></p>
                    <p>Total processing time: {time_str}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-card"><p><b>✅ Processing complete!</b></p></div>', unsafe_allow_html=True)
            
            # Add a section to show the full logs
            with st.expander("View Processing Logs", expanded=False):
                logs_html = get_latest_logs(200)  # Show more logs when completed
                
                # Use iframe for consistent log display
                log_height = 600  # Increased from 300 to 600 for better visibility
                st.markdown(f"""
                <div style="height: {log_height}px; min-height: {log_height}px; overflow: hidden; margin-bottom: 10px;">
                    <iframe srcdoc='
                        <html>
                        <head>
                            <style>
                                html, body {{
                                    height: 100%;
                                    min-height: 600px;
                                    margin: 0;
                                    padding: 0;
                                    overflow: hidden;
                                }}
                                body {{
                                    font-family: monospace;
                                    font-size: 12px;
                                    line-height: 1.5;
                                    padding: 10px;
                                    background-color: #f8f9fa;
                                    overflow-y: auto;
                                    box-sizing: border-box;
                                    height: 100%;
                                }}
                                #log-container {{
                                    height: 100%;
                                    overflow-y: auto;
                                }}
                                .info {{
                                    color: #0066cc;
                                }}
                                .info-bold {{
                                    color: #4169E1;
                                    font-weight: bold;
                                }}
                                .warning {{
                                    color: #ff9900;
                                }}
                                .error {{
                                    color: #cc0000;
                                    font-weight: bold;
                                }}
                            </style>
                        </head>
                        <body>
                            <div id="log-container">
                                <div id="log-content">{logs_html}</div>
                            </div>
                        </body>
                        </html>
                    ' height="{log_height}" width="100%" style="height: {log_height}px; min-height: {log_height}px; border: 1px solid #dee2e6; border-radius: 5px; display: block;"></iframe>
                </div>
                """, unsafe_allow_html=True)
            
        elif status == 'error':
            st.markdown(f"""
            <div class="error-card">
                <p><b>❌ Error during processing</b></p>
                <p>{st.session_state.processing_status.get('message', 'An unknown error occurred.')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add a section to show the error logs
            with st.expander("View Error Logs", expanded=True):
                logs_html = get_latest_logs(200)  # Show more logs for error diagnosis
                
                # Use iframe for consistent log display
                log_height = 600  # Increased for better error log visibility
                st.markdown(f"""
                <div style="height: {log_height}px; min-height: {log_height}px; overflow: hidden; margin-bottom: 10px;">
                    <iframe srcdoc='
                        <html>
                        <head>
                            <style>
                                html, body {{
                                    height: 100%;
                                    min-height: 600px;
                                    margin: 0;
                                    padding: 0;
                                    overflow: hidden;
                                }}
                                body {{
                                    font-family: monospace;
                                    font-size: 12px;
                                    line-height: 1.5;
                                    padding: 10px;
                                    background-color: #f8f9fa;
                                    overflow-y: auto;
                                    box-sizing: border-box;
                                    height: 100%;
                                }}
                                #log-container {{
                                    height: 100%;
                                    overflow-y: auto;
                                }}
                                .info {{
                                    color: #0066cc;
                                }}
                                .info-bold {{
                                    color: #4169E1;
                                    font-weight: bold;
                                }}
                                .warning {{
                                    color: #ff9900;
                                }}
                                .error {{
                                    color: #cc0000;
                                    font-weight: bold;
                                }}
                            </style>
                        </head>
                        <body>
                            <div id="log-container">
                                <div id="log-content">{logs_html}</div>
                            </div>
                        </body>
                        </html>
                    ' height="{log_height}" width="100%" style="height: {log_height}px; min-height: {log_height}px; border: 1px solid #dee2e6; border-radius: 5px; display: block;"></iframe>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Results section - always try to display results if completed
    if st.session_state.processing_status['status'] == 'completed' or os.path.exists(COMPLETION_MARKER):
        # Find the results directory
        results_dir = find_results_directory() or st.session_state.processing_status.get('results_dir')
        
        # Check for direct result file path
        if not results_dir and os.path.exists(RESULTS_PATH_FILE):
            try:
                with open(RESULTS_PATH_FILE, 'r') as f:
                    results_file = f.read().strip()
                    if os.path.exists(results_file):
                        results_dir = os.path.dirname(results_file)
            except Exception as e:
                print(f"Error reading results path file: {e}")
        
        # If we found a results directory, display the results
        if results_dir:
            st.markdown('<div class="results-section">', unsafe_allow_html=True)
            display_results(results_dir)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # If no results directory found, search for any multilingual files
            json_files = []
            for root, dirs, files in os.walk(st.session_state.temp_dir):
                for file in files:
                    if file.endswith("_multilingual.json"):
                        json_files.append(os.path.join(root, file))
            
            if json_files:
                st.markdown('<div class="results-section">', unsafe_allow_html=True)
                display_results(os.path.dirname(json_files[0]))
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-card">Processing completed but could not locate results directory.</div>', unsafe_allow_html=True)
                
                # Show debug info
                st.markdown(f'<div class="debug-info">Temp directory: {st.session_state.temp_dir}</div>', unsafe_allow_html=True)
                
                # List all files in the temp directory
                all_files = []
                for root, dirs, files in os.walk(st.session_state.temp_dir):
                    rel_path = os.path.relpath(root, st.session_state.temp_dir)
                    if files:
                        all_files.append(f"📁 {rel_path}/")
                        for file in files:
                            all_files.append(f"   📄 {file}")
                
                if all_files:
                    st.markdown('<div class="debug-info">Files found in temp directory:<br>' + 
                              '<br>'.join(all_files[:30]) + 
                              (f'<br>...and {len(all_files)-30} more' if len(all_files) > 30 else '') + 
                              '</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()