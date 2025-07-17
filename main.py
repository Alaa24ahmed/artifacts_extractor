# #!/usr/bin/env python3
# """
# Efficient Multilingual Museum Artifact Text Extraction System
# This script implements a two-phase approach:
# 1. Process English documents fully (OCR + correction + extraction)
# 2. For each artifact found in English, extract just the name in Arabic/French
# 3. Create a consolidated database with English metadata + all language names
# """
# import os
# import argparse
# import logging
# import sys
# from dotenv import load_dotenv
# import re

# # Add the script directory to Python path
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, SCRIPT_DIR)

# # Import configuration
# from config import (
#     BASE_DIR, SELECTED_MODEL, 
#     EN_DOCUMENT_PATH, AR_DOCUMENT_PATH, FR_DOCUMENT_PATH,
#     CORRECTION_THRESHOLDS, MULTILINGUAL_CSV_FIELDS,
#     logger
# )

# # Import modules
# from modules.data_utils import group_documents_by_language
# from modules.processors import process_multilingual_document_set

# # Import prompts
# from prompts import (
#     OCRPrompt, OCRCorrectionPrompt, 
#     ArtifactExtractionPrompt, MultilingualNameExtractionPrompt, 
#     cross_language_validation_prompt
# )

# def main():
#     # Load environment variables
#     load_dotenv(dotenv_path="/home/alaa.elsetohy/Desktop/internship/SCAI/config/.env")

#     # Parse command line arguments
#     parser = argparse.ArgumentParser(description="Efficient multilingual museum artifact extraction")
#     parser.add_argument("--input_files", nargs='+', help="List of input files (different language versions)")
#     parser.add_argument("--data_dir", default=os.path.join(SCRIPT_DIR, "data_multilin"), 
#                         help="Directory containing document files")
#     parser.add_argument("--output_dir", default="clean_code/results", 
#                         help="Directory to save results")
#     parser.add_argument("--model", default=SELECTED_MODEL, 
#                         choices=["gpt-4", "gpt-4o", "gpt-4o-mini", "gemini"],
#                         help="Model to use for text analysis")
#     parser.add_argument("--start_page", type=int, default=1, help="Page to start processing from")
#     parser.add_argument("--end_page", type=int, default=None, help="Page to end processing at")
#     parser.add_argument("--use_global_paths", action="store_true", 
#                         help="Use the global document paths defined in the script")
#     parser.add_argument("--correction_threshold", type=float, default=None,
#                         help="Override the default language-specific correction thresholds")
    
#     args = parser.parse_args()
    
#     # Prepare the output directory
#     output_dir = os.path.join(BASE_DIR, args.output_dir)
    
#     # Use model specified in args or default
#     model = args.model or SELECTED_MODEL
#     logger.info(f"Using model: {model}")
#     logger.info(f"Mode: Two-Phase Multilingual Processing (English First, Then Align)")
#     logger.info(f"Output directory: {output_dir}")
    
#     # Set up correction thresholds
#     correction_thresholds = CORRECTION_THRESHOLDS.copy()
#     if args.correction_threshold is not None:
#         # Override all thresholds with the manual value
#         for lang in correction_thresholds:
#             correction_thresholds[lang] = args.correction_threshold
    
#     logger.info(f"OCR correction thresholds: EN={correction_thresholds['EN']:.4f}, "
#                 f"FR={correction_thresholds['FR']:.4f}, AR={correction_thresholds['AR']:.4f}")
    
#     # Set up prompts
#     prompts = {
#         "ocr": OCRPrompt(),
#         "correction": OCRCorrectionPrompt(),
#         "artifact": ArtifactExtractionPrompt(),
#         "multilingual": MultilingualNameExtractionPrompt(),
#         "validation": cross_language_validation_prompt
#     }
    
#     # If using global paths defined at the top of the script
#     if args.use_global_paths or (not args.input_files and EN_DOCUMENT_PATH):
#         logger.info("Using global document paths defined in the script")
        
#         # Create a document group from the global paths
#         doc_group = {
#             "EN": EN_DOCUMENT_PATH if os.path.exists(EN_DOCUMENT_PATH) else None,
#             "AR": AR_DOCUMENT_PATH if os.path.exists(AR_DOCUMENT_PATH) else None,
#             "FR": FR_DOCUMENT_PATH if os.path.exists(FR_DOCUMENT_PATH) else None
#         }
        
#         # Validate paths
#         if not doc_group["EN"]:
#             logger.error("English document path is not valid. English is required.")
#             return
        
#         # Log which documents are being processed
#         logger.info(f"Processing English document: {doc_group['EN']}")
#         if doc_group["AR"]:
#             logger.info(f"Processing Arabic document: {doc_group['AR']}")
#         if doc_group["FR"]:
#             logger.info(f"Processing French document: {doc_group['FR']}")
        
#         # Process the document set
#         process_multilingual_document_set(
#             doc_group=doc_group,
#             output_dir=output_dir,
#             model=model,
#             start_page=args.start_page,
#             end_page=args.end_page,
#             correction_thresholds=correction_thresholds,
#             prompts=prompts,
#             csv_fields=MULTILINGUAL_CSV_FIELDS
#         )
        
#     # If input files provided, process those
#     elif args.input_files:
#         # Convert relative input file paths to absolute paths if needed
#         absolute_input_files = []
#         for file_path in args.input_files:
#             if not os.path.isabs(file_path):
#                 file_path = os.path.join(SCRIPT_DIR, file_path)
#             absolute_input_files.append(file_path)
        
#         # Group documents by language
#         doc_groups = group_documents_by_language(absolute_input_files)
        
#         if not doc_groups:
#             logger.error("Could not identify any valid document groups with English version")
#             return
        
#         logger.info(f"Found {len(doc_groups)} document groups to process")
        
#         # Process each document group
#         for doc_name, doc_group in doc_groups.items():
#             process_multilingual_document_set(
#                 doc_group=doc_group,
#                 output_dir=output_dir,
#                 model=model,
#                 start_page=args.start_page,
#                 end_page=args.end_page,
#                 correction_thresholds=correction_thresholds,
#                 prompts=prompts,
#                 csv_fields=MULTILINGUAL_CSV_FIELDS
#             )
    
#     # Otherwise search the data directory for documents
#     else:
#         # Make data_dir absolute if it's relative
#         if not os.path.isabs(args.data_dir):
#             data_dir = os.path.join(SCRIPT_DIR, args.data_dir)
#         else:
#             data_dir = args.data_dir
            
#         # Find all document files
#         input_files = []
#         for root, _, files in os.walk(data_dir):
#             for file in files:
#                 if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
#                     input_files.append(os.path.join(root, file))
        
#         if not input_files:
#             logger.error(f"No document files found in {data_dir}")
#             return
        
#         # Group documents by language
#         doc_groups = group_documents_by_language(input_files)
        
#         if not doc_groups:
#             logger.error("Could not identify any valid document groups with English version")
#             return
        
#         logger.info(f"Found {len(doc_groups)} document groups to process")
        
#         # Process each document group
#         for doc_name, doc_group in doc_groups.items():
#             process_multilingual_document_set(
#                 doc_group=doc_group,
#                 output_dir=output_dir,
#                 model=model,
#                 start_page=args.start_page,
#                 end_page=args.end_page,
#                 correction_thresholds=correction_thresholds,
#                 prompts=prompts,
#                 csv_fields=MULTILINGUAL_CSV_FIELDS
#             )

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
Efficient Multilingual Museum Artifact Text Extraction System
This script implements a two-phase approach:
1. Process English documents fully (OCR + correction + extraction)
2. For each artifact found in English, extract just the name in Arabic/French
3. Create a consolidated database with English metadata + all language names
"""
import os
import argparse
import logging
import sys
from dotenv import load_dotenv
import re

# Add the script directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Import configuration
from config import (
    BASE_DIR, SELECTED_MODEL, 
    EN_DOCUMENT_PATH, AR_DOCUMENT_PATH, FR_DOCUMENT_PATH,
    CORRECTION_THRESHOLDS, MULTILINGUAL_CSV_FIELDS,
    logger
)

# Import modules
from modules.data_utils import group_documents_by_language
from modules.processors import process_multilingual_document_set

# Import prompts
from prompts import (
    OCRPrompt, OCRCorrectionPrompt, 
    ArtifactExtractionPrompt, MultilingualNameExtractionPrompt, 
    cross_language_validation_prompt
)

def main():
    # Load environment variables
    load_dotenv(dotenv_path="/home/alaa.elsetohy/Desktop/internship/SCAI/config/.env")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Efficient multilingual museum artifact extraction")
    parser.add_argument("--input_files", nargs='+', help="List of input files (different language versions)")
    parser.add_argument("--data_dir", default=os.path.join(SCRIPT_DIR, "data_multilin"), 
                        help="Directory containing document files")
    parser.add_argument("--output_dir", default="clean_code/results_with_mistral", 
                        help="Directory to save results")
    parser.add_argument("--start_page", type=int, default=1, help="Page to start processing from")
    parser.add_argument("--end_page", type=int, default=None, help="Page to end processing at")
    parser.add_argument("--use_global_paths", action="store_true", 
                        help="Use the global document paths defined in the script")
    parser.add_argument("--correction_threshold", type=float, default=None,
                        help="Override the default language-specific correction thresholds")
    
    parser.add_argument("--model", default=SELECTED_MODEL, 
                    choices=["gpt-4", "gpt-4o", "gpt-4o-mini", "gemini", "mistral-ocr"],
                    help="Model to use for text analysis")
    parser.add_argument("--ocr_model", default="mistral-ocr",
                        choices=["gpt-4", "gpt-4o", "gpt-4o-mini", "gemini", "mistral-ocr"],
                        help="Specific model to use for OCR (if different from primary model)")
    parser.add_argument("--extraction_model", default="gpt-4o",
                        choices=["gpt-4", "gpt-4o", "gpt-4o-mini", "gemini"],
                        help="Specific model to use for artifact extraction (if different from primary model)")

    args = parser.parse_args()
    
    # Check if Mistral API key is available (strip any whitespace from env var)
    if args.ocr_model == "mistral-ocr":
        mistral_api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        if not mistral_api_key:
            logger.error("Mistral API key not found in environment variables. Please add MISTRAL_API_KEY to your .env file.")
            return
        else:
            # Ensure the key is properly set without whitespace
            os.environ["MISTRAL_API_KEY"] = mistral_api_key
            logger.info("Mistral API key found and configured.")
    
    # Prepare the output directory
    output_dir = os.path.join(BASE_DIR, args.output_dir)
    
    # Use model specified in args or default
    model = args.model or SELECTED_MODEL
    ocr_model = args.ocr_model or model
    extraction_model = args.extraction_model or model
    
    logger.info(f"Primary model: {model}")
    if ocr_model != model:
        logger.info(f"OCR model: {ocr_model}")
    if extraction_model != model:
        logger.info(f"Extraction model: {extraction_model}")
    
    logger.info(f"Mode: Two-Phase Multilingual Processing (English First, Then Align)")
    logger.info(f"Output directory: {output_dir}")
    
    # Set up correction thresholds
    correction_thresholds = CORRECTION_THRESHOLDS.copy()
    if args.correction_threshold is not None:
        # Override all thresholds with the manual value
        for lang in correction_thresholds:
            correction_thresholds[lang] = args.correction_threshold
    
    logger.info(f"OCR correction thresholds: EN={correction_thresholds['EN']:.4f}, "
                f"FR={correction_thresholds['FR']:.4f}, AR={correction_thresholds['AR']:.4f}")
    
    # Set up prompts
    prompts = {
        "ocr": OCRPrompt(),
        "correction": OCRCorrectionPrompt(),
        "artifact": ArtifactExtractionPrompt(),
        "multilingual": MultilingualNameExtractionPrompt(),
        "validation": cross_language_validation_prompt
    }
    
    # If using global paths defined at the top of the script
    if args.use_global_paths or (not args.input_files and EN_DOCUMENT_PATH):
        logger.info("Using global document paths defined in the script")
        
        # Create a document group from the global paths
        doc_group = {
            "EN": EN_DOCUMENT_PATH if os.path.exists(EN_DOCUMENT_PATH) else None,
            "AR": AR_DOCUMENT_PATH if os.path.exists(AR_DOCUMENT_PATH) else None,
            "FR": FR_DOCUMENT_PATH if os.path.exists(FR_DOCUMENT_PATH) else None
        }
        
        # Validate paths
        if not doc_group["EN"]:
            logger.error("English document path is not valid. English is required.")
            return
        
        # Log which documents are being processed
        logger.info(f"Processing English document: {doc_group['EN']}")
        if doc_group["AR"]:
            logger.info(f"Processing Arabic document: {doc_group['AR']}")
        if doc_group["FR"]:
            logger.info(f"Processing French document: {doc_group['FR']}")
        
        # Process the document set
        process_multilingual_document_set(
            doc_group=doc_group,
            output_dir=output_dir,
            model=model,
            start_page=args.start_page,
            end_page=args.end_page,
            correction_thresholds=correction_thresholds,
            prompts=prompts,
            csv_fields=MULTILINGUAL_CSV_FIELDS,
            ocr_model=ocr_model,
            extraction_model=extraction_model
        )
        
    # If input files provided, process those
    elif args.input_files:
        # Convert relative input file paths to absolute paths if needed
        absolute_input_files = []
        for file_path in args.input_files:
            if not os.path.isabs(file_path):
                file_path = os.path.join(SCRIPT_DIR, file_path)
            absolute_input_files.append(file_path)
        
        # Group documents by language
        doc_groups = group_documents_by_language(absolute_input_files)
        
        if not doc_groups:
            logger.error("Could not identify any valid document groups with English version")
            return
        
        logger.info(f"Found {len(doc_groups)} document groups to process")
        
        # Process each document group
        for doc_name, doc_group in doc_groups.items():
            process_multilingual_document_set(
                doc_group=doc_group,
                output_dir=output_dir,
                model=model,
                start_page=args.start_page,
                end_page=args.end_page,
                correction_thresholds=correction_thresholds,
                prompts=prompts,
                csv_fields=MULTILINGUAL_CSV_FIELDS,
                ocr_model=ocr_model,
                extraction_model=extraction_model
            )
    
    # Otherwise search the data directory for documents
    else:
        # Make data_dir absolute if it's relative
        if not os.path.isabs(args.data_dir):
            data_dir = os.path.join(SCRIPT_DIR, args.data_dir)
        else:
            data_dir = args.data_dir
            
        # Find all document files
        input_files = []
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    input_files.append(os.path.join(root, file))
        
        if not input_files:
            logger.error(f"No document files found in {data_dir}")
            return
        
        # Group documents by language
        doc_groups = group_documents_by_language(input_files)
        
        if not doc_groups:
            logger.error("Could not identify any valid document groups with English version")
            return
        
        logger.info(f"Found {len(doc_groups)} document groups to process")
        
        # Process each document group
        for doc_name, doc_group in doc_groups.items():
            process_multilingual_document_set(
                doc_group=doc_group,
                output_dir=output_dir,
                model=model,
                start_page=args.start_page,
                end_page=args.end_page,
                correction_thresholds=correction_thresholds,
                prompts=prompts,
                csv_fields=MULTILINGUAL_CSV_FIELDS,
                ocr_model=ocr_model,
                extraction_model=extraction_model
            )

if __name__ == "__main__":
    main()