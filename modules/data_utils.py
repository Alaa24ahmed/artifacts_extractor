"""Data handling utilities for file operations and document management"""
import os
import re
import csv
import json
import logging

logger = logging.getLogger(__name__)

def save_extracted_text(text, output_file):
    """Save extracted text to a file for reference."""
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"Saved extracted text to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving extracted text: {e}")
        return False

def save_artifacts_to_csv(artifacts, output_file, fieldnames):
    """Save artifacts to a CSV file with proper encoding for multilingual support."""
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Check if file exists to determine if we need to write header
    file_exists = os.path.isfile(output_file)
    
    # Open file with UTF-8 encoding to properly handle multilingual text
    with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header only if file is new
        if not file_exists:
            writer.writeheader()
        
        # Write each artifact as a row
        for artifact in artifacts:
            # Create a copy of the artifact to modify
            row = {k: v for k, v in artifact.items() if k in fieldnames}
            
            # Handle missing fields
            for field in fieldnames:
                if field not in row:
                    row[field] = ""
            
            # Write the row
            writer.writerow(row)

def group_documents_by_language(input_files):
    """Group related documents by language based on filename patterns."""
    document_groups = {}
    
    # Regular expressions to identify language from filename
    patterns = {
        "EN": re.compile(r'(_en\.|_english\.|_eng\.)', re.IGNORECASE),
        "AR": re.compile(r'(_ar\.|_arabic\.)', re.IGNORECASE),
        "FR": re.compile(r'(_fr\.|_french\.)', re.IGNORECASE)
    }
    
    # First, categorize each file by language
    categorized_files = {}
    for input_file in input_files:
        basename = os.path.basename(input_file)
        
        # Determine language from filename
        detected_lang = None
        for lang, pattern in patterns.items():
            if pattern.search(basename):
                detected_lang = lang
                break
        
        if not detected_lang:
            # If no language indicator in filename, default to English
            detected_lang = "EN"
        
        # Get base document name without language suffix
        base_name = basename
        for lang, pattern in patterns.items():
            base_name = pattern.sub('.', base_name)
        
        # Remove any remaining language indicators and extensions
        base_name = re.sub(r'\.(pdf|jpg|png)$', '', base_name)
        
        # Store under the base document name
        if base_name not in categorized_files:
            categorized_files[base_name] = {}
        
        categorized_files[base_name][detected_lang] = input_file
    
    # Create complete triplets with all three languages
    for base_name, lang_files in categorized_files.items():
        # Only include if we have at least the English version
        if "EN" in lang_files:
            document_groups[base_name] = {
                "EN": lang_files.get("EN"),
                "AR": lang_files.get("AR"),
                "FR": lang_files.get("FR")
            }
        else:
            logger.warning(f"Skipping document group {base_name} - no English version found")
    
    return document_groups