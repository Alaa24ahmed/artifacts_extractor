"""Artifact and multilingual name extraction functions"""
import os
import json
import logging
from .api_calls import call_api_for_model, extract_content_from_response
from .text_processing import parse_artifacts_from_text, parse_multilingual_names
from .correction import perform_ocr_with_adaptive_correction

logger = logging.getLogger(__name__)

def extract_artifacts_from_page(image_path, page_num, document_name, model, final_corrected_text, 
                               artifact_prompt_template, results_dir):
    """Extract artifacts from a page using both text and image."""
    logger.info(f"Extracting artifacts from page {page_num}")
    
    # Create the artifact extraction prompt with the corrected text
    formatted_prompt = artifact_prompt_template.format(
        page_number=page_num,
        context=document_name,
        extracted_text=final_corrected_text
    )
    
    # Since we need both image and text processing, use the "correction" API type
    # which is designed to handle both inputs in your API system
    response = call_api_for_model(
        model=model, 
        api_type="correction",  # Use correction which handles both image and text
        image_path=image_path,
        prompt=final_corrected_text,  # The raw text input
        prompt_template=formatted_prompt,  # The formatted prompt
        context=document_name,
        page_num=page_num
    )
    
    try:
        content = extract_content_from_response(response, model)
        
        # Check if no artifacts were found
        if content.strip() == "NO_ARTIFACTS_MENTIONED":
            logger.info(f"No artifacts found on page {page_num}")
            return []
        
        # Parse the artifacts from the response
        try:
            # First attempt to parse the entire content
            if '[' in content and ']' in content:
                # Try to extract JSON from a potentially larger text response
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                json_content = content[start_idx:end_idx]
                artifacts = json.loads(json_content)
            else:
                logger.warning(f"Response doesn't contain JSON array markers, attempting full parse")
                artifacts = json.loads(content)
            
            # Validate artifacts - ensure they have required fields
            valid_artifacts = []
            for artifact in artifacts:
                # Check for required fields
                if "Name" not in artifact or not artifact.get("Name"):
                    logger.warning(f"Skipping artifact without name: {artifact}")
                    continue
                
                # Ensure it has a category
                if "Category" not in artifact or not artifact.get("Category"):
                    logger.warning(f"Artifact missing category, assigning OTHER: {artifact['Name']}")
                    artifact["Category"] = "OTHER"
                
                # Add source metadata
                artifact["source_page"] = page_num
                artifact["source_document"] = document_name
                
                # Add to valid artifacts
                valid_artifacts.append(artifact)
            
            # Save artifacts for this page
            page_output_file = os.path.join(results_dir, f"page_{page_num}_artifacts.json")
            with open(page_output_file, 'w', encoding='utf-8') as f:
                json.dump(valid_artifacts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Extracted {len(valid_artifacts)} artifacts from page {page_num}")
            return valid_artifacts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse artifacts from response: {e}")
            logger.debug(f"Raw response content: {content[:500]}...")
            return []
            
    except Exception as e:
        logger.error(f"Error extracting artifacts: {e}")
        return []
    

def extract_multilingual_names_from_page(image_path, page_num, page_artifacts, document_name, model, lang, 
                                        name_extraction_prompt, ocr_prompt_template, correction_prompt_template, 
                                        output_dirs, results_dir, correction_threshold):
    """Extract artifact names in another language for a specific page."""
    logger.info(f"Extracting {lang} names for artifacts on page {page_num}: {', '.join([a.get('Name', 'Unknown') for a in page_artifacts])}")
    
    # First check if OCR text exists, if not, perform OCR
    ocr_output_file = os.path.join(output_dirs["ocr"], f"page_{page_num}_ocr.txt")
    ocr_corrected2_file = os.path.join(output_dirs["corrected2"], f"page_{page_num}_ocr_corrected2.txt")
    ocr_corrected3_file = os.path.join(output_dirs["corrected3"], f"page_{page_num}_ocr_corrected3.txt")
    
    # Try to read existing OCR text
    ocr_text = None
    if os.path.exists(ocr_corrected3_file):
        with open(ocr_corrected3_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    elif os.path.exists(ocr_corrected2_file):
        with open(ocr_corrected2_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    elif os.path.exists(ocr_output_file):
        with open(ocr_output_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    
    # If no OCR text exists, perform OCR with correction
    if not ocr_text:
        logger.info(f"No existing OCR text found for {lang} page {page_num}, performing OCR")
        try:
            ocr_text = perform_ocr_with_adaptive_correction(
                image_path=image_path,
                page_num=page_num,
                document_name=document_name,
                model=model,
                ocr_prompt_template=ocr_prompt_template,
                correction_prompt_template=correction_prompt_template,
                output_dirs=output_dirs,
                lang=lang,
                correction_threshold=correction_threshold
            )
        except Exception as e:
            logger.error(f"Failed to perform OCR for {lang} page {page_num}: {e}")
            return []
    
    # Create the multilingual name extraction prompt
    prompt_template = name_extraction_prompt.format(
        artifact_list=page_artifacts,
        target_language=lang,
        page_number=page_num,
        context=document_name
    )
    
    # Now replace the {extracted_text} placeholder with the actual OCR text
    prompt = prompt_template.replace("{extracted_text}", ocr_text)
    
    # Call the API (using text-only since we've already incorporated the OCR text)
    response = call_api_for_model(model, "text", prompt=prompt)
    
    try:
        content = extract_content_from_response(response, model)
        
        # Parse the name mappings from the response
        try:
            # Clean up the content by removing markdown code block markers
            # This handles responses with ```json [JSON content] ``` format
            clean_content = content
            
            # Remove markdown code block markers if present
            if "```" in clean_content:
                # Strip any line with ``` at the beginning or end
                lines = clean_content.split('\n')
                filtered_lines = []
                for line in lines:
                    if line.strip().startswith("```") or line.strip().endswith("```"):
                        continue
                    filtered_lines.append(line)
                clean_content = '\n'.join(filtered_lines)
            
            # Ensure we have valid JSON
            clean_content = clean_content.strip()
            if not (clean_content.startswith('[') and clean_content.endswith(']')):
                # Try to find JSON array in the text
                start_idx = clean_content.find('[')
                end_idx = clean_content.rfind(']')
                if start_idx != -1 and end_idx != -1:
                    clean_content = clean_content[start_idx:end_idx+1]
            
            name_mappings = json.loads(clean_content)
            
            # Save name mappings for this page
            page_output_file = os.path.join(results_dir, f"page_{page_num}_{lang.lower()}_names.json")
            with open(page_output_file, 'w', encoding='utf-8') as f:
                json.dump(name_mappings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Extracted {len(name_mappings)} {lang} names from page {page_num}")
            return name_mappings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {lang} name mappings from response: {content}")
            
            # More aggressive fallback parsing for badly formatted JSON
            try:
                # Try to extract JSON using regex
                import re
                json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                if json_match:
                    potential_json = json_match.group(0)
                    name_mappings = json.loads(potential_json)
                    
                    # Save name mappings for this page
                    page_output_file = os.path.join(results_dir, f"page_{page_num}_{lang.lower()}_names.json")
                    with open(page_output_file, 'w', encoding='utf-8') as f:
                        json.dump(name_mappings, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"Extracted {len(name_mappings)} {lang} names from page {page_num} (using fallback parser)")
                    return name_mappings
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {fallback_error}")
            
            return []
            
    except Exception as e:
        logger.error(f"Error during {lang} name extraction for page {page_num}: {e}")
        return []