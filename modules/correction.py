"""OCR correction pipeline with adaptive early stopping"""
import os
import logging
import re
from .api_calls import call_api_for_model, extract_content_from_response
from .text_processing import calculate_text_difference
from .data_utils import save_extracted_text

logger = logging.getLogger(__name__)

def perform_ocr_with_adaptive_correction(
    image_path, 
    page_num, 
    document_name, 
    model, 
    ocr_prompt_template,
    correction_prompt_template,
    output_dirs,
    lang="EN",
    correction_threshold=0.05,
    max_corrections=5
):
    """
    Perform OCR with adaptive correction, using early stopping when changes become minimal.
    
    Args:
        image_path: Path to the image to process
        page_num: Page number
        document_name: Name of the document
        model: Model to use (gpt-4o, gemini, mistral-ocr, etc.)
        ocr_prompt_template: Template for the OCR prompt
        correction_prompt_template: Template for the correction prompt
        output_dirs: Dictionary with paths for saving outputs
        lang: Language code ("EN", "AR", "FR")
        correction_threshold: Threshold below which to stop corrections
        max_corrections: Maximum number of correction passes
        
    Returns:
        The final corrected text
    """
    # Extract the OCR directory
    ocr_dir = output_dirs.get("ocr")
    
    # Create the OCR directory if it doesn't exist
    os.makedirs(ocr_dir, exist_ok=True)
    
    # STEP 1: Initial OCR
    ocr_output_file = os.path.join(ocr_dir, f"page_{page_num}_ocr.txt")
    if os.path.exists(ocr_output_file):
        with open(ocr_output_file, 'r', encoding='utf-8') as f:
            current_text = f.read()
    else:
        # Check if using Mistral OCR
        if model == "mistral-ocr":
            # Direct call to Mistral OCR without prompt
            try:
                ocr_response = call_api_for_model(model, "vision", image_path, "")
                current_text = extract_content_from_response(ocr_response, model)
                save_extracted_text(current_text, ocr_output_file)
                logger.info(f"Completed Mistral OCR for {lang} page {page_num}")
            except Exception as e:
                logger.error(f"Error during Mistral OCR for {lang} page {page_num}: {e}")
                raise
        else:
            # Original OCR process with other models
            # Generate OCR prompt
            context = f"Document: {document_name} ({lang})"
            ocr_prompt = ocr_prompt_template.format(
                image_path=image_path,
                page_number=page_num,
                context=context
            )
            
            # Call OCR
            try:
                ocr_response = call_api_for_model(model, "vision", image_path, ocr_prompt)
                current_text = extract_content_from_response(ocr_response, model)
                save_extracted_text(current_text, ocr_output_file)
            except Exception as e:
                logger.error(f"Error during OCR for {lang} page {page_num}: {e}")
                raise
    
    # Determine max corrections - use fewer passes for Mistral OCR since it's typically more accurate
    max_pass = 2 if model == "mistral-ocr" else max_corrections
    
    # Perform correction passes
    for correction_pass in range(1, max_pass + 1):
        # Get the correction directory for this pass
        correction_dir_key = f"corrected{correction_pass}"
        correction_dir = output_dirs.get(correction_dir_key)
        
        # Skip if this correction directory is not provided
        if not correction_dir:
            # If not specified, create a default directory
            correction_dir = os.path.join(os.path.dirname(ocr_dir), f"ocr_corrected{correction_pass}")
            output_dirs[correction_dir_key] = correction_dir
        
        # Create the correction directory if it doesn't exist
        os.makedirs(correction_dir, exist_ok=True)
            
        # Check if this correction has already been done
        corrected_output_file = os.path.join(
            correction_dir, 
            f"page_{page_num}_ocr_corrected{correction_pass}.txt"
        )
        
        if os.path.exists(corrected_output_file):
            with open(corrected_output_file, 'r', encoding='utf-8') as f:
                corrected_text = f.read()
        else:
            # For Mistral OCR, use GPT for correction
            if model == "mistral-ocr":
                # Use GPT-4o for correction of Mistral OCR
                correction_model = "gpt-4o"  
                pass_label = "Final Pass" if correction_pass == max_pass else f"Pass {correction_pass}"
                context = f"Document: {document_name} ({lang}, Correction {pass_label})"
                
                try:
                    correction_response = call_api_for_model(
                        correction_model, "correction", image_path, current_text, 
                        correction_prompt_template, context, page_num
                    )
                    corrected_text = extract_content_from_response(correction_response, correction_model)
                    save_extracted_text(corrected_text, corrected_output_file)
                except Exception as e:
                    logger.error(f"Error during correction {correction_pass} for {lang} page {page_num}: {e}")
                    corrected_text = current_text  # Fallback
            else:
                # Original correction process
                pass_label = "Final Pass" if correction_pass == max_corrections else f"Pass {correction_pass}"
                context = f"Document: {document_name} ({lang}, Correction {pass_label})"
                
                try:
                    correction_response = call_api_for_model(
                        model, "correction", image_path, current_text, 
                        correction_prompt_template, context, page_num
                    )
                    corrected_text = extract_content_from_response(correction_response, model)
                    save_extracted_text(corrected_text, corrected_output_file)
                except Exception as e:
                    logger.error(f"Error during correction {correction_pass} for {lang} page {page_num}: {e}")
                    corrected_text = current_text  # Fallback
        
        # Calculate difference between current and corrected text
        diff_score = calculate_text_difference(current_text, corrected_text)
        logger.info(f"{lang} correction {correction_pass} difference score: {diff_score:.4f}")
        
        # Update current text for next iteration
        current_text = corrected_text
        
        # Check for early stopping
        if diff_score <= correction_threshold:
            logger.info(f"Minimal changes after {lang} correction {correction_pass} (score: {diff_score:.4f}), stopping corrections")
            break
    
    return current_text