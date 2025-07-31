"""Main document processing functions"""
import os
import json
import logging
from dotenv import load_dotenv
from pathlib import Path
from .image_processing import extract_images_from_pdf, prepare_input_image
from .correction import perform_ocr_with_adaptive_correction
from .extraction import extract_artifacts_from_page, extract_multilingual_names_from_page
from .validation import validate_and_complete_multilingual_names
from .data_utils import save_artifacts_to_csv
from .simple_db import get_simple_db
import re

# Load configuration using the configuration manager
try:
    from .config_manager import load_configuration
    load_configuration()
    print("✅ Configuration loaded in processors.py")
except Exception as e:
    print(f"⚠️ Error loading configuration in processors.py: {e}")
    # Fallback to manual loading
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path, override=True)

logger = logging.getLogger(__name__)

def process_english_document(input_file, output_dir, model, start_page=1, end_page=None, 
                            correction_threshold=0.05, ocr_prompt=None, correction_prompt=None, 
                            artifact_prompt=None, ocr_model=None, extraction_model=None):
    """Process English document fully with OCR, adaptive correction, and artifact extraction."""
    # Set up model selection
    actual_ocr_model = ocr_model or model
    actual_extraction_model = extraction_model or model
    
    # Set up document-specific directories
    pdf_name = os.path.splitext(os.path.basename(input_file))[0]
    doc_base_dir = os.path.join(output_dir, pdf_name)
    pages_dir = os.path.join(doc_base_dir, "EN", "pages")
    ocr_dir = os.path.join(doc_base_dir, "EN", "ocr")
    ocr_corrected_dir = os.path.join(doc_base_dir, "EN", "ocr_corrected")
    ocr_corrected2_dir = os.path.join(doc_base_dir, "EN", "ocr_corrected2")
    ocr_corrected3_dir = os.path.join(doc_base_dir, "EN", "ocr_corrected3")
    results_dir = os.path.join(doc_base_dir, model)
    
    # Log which models are being used
    if actual_ocr_model != model:
        logger.info(f"Using {actual_ocr_model} for OCR")
    if actual_extraction_model != model:
        logger.info(f"Using {actual_extraction_model} for artifact extraction")
    
    # Create directories
    os.makedirs(doc_base_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # Document name for source tracking
    document_name = os.path.basename(input_file)
    
    # Extract pages from the document
    if input_file.lower().endswith('.pdf'):
        logger.info(f"Processing English PDF: {input_file}")
        image_paths = extract_images_from_pdf(input_file, pages_dir, start_page, end_page)
    else:
        logger.info(f"Processing English image: {input_file}")
        image_paths = prepare_input_image(input_file, pages_dir)
    
    # Process each page
    all_artifacts = []
    
    for image_path, page_num in image_paths:
        logger.info(f"Processing English page {page_num}: {image_path}")
        
        # Check if this page has already been processed
        page_output_file = os.path.join(results_dir, f"page_{page_num}_artifacts.json")
        if os.path.exists(page_output_file):
            logger.info(f"Page {page_num} already processed, loading results")
            with open(page_output_file, 'r', encoding='utf-8') as f:
                page_artifacts = json.load(f)
                all_artifacts.extend(page_artifacts)
            continue
        
        # Set up directories for this page's OCR and correction
        output_dirs = {
            "ocr": ocr_dir,
            "corrected1": ocr_corrected_dir,
            "corrected2": ocr_corrected2_dir,
            "corrected3": ocr_corrected3_dir
        }
        
        try:
            # Perform OCR with adaptive correction using OCR model
            final_corrected_text = perform_ocr_with_adaptive_correction(
                image_path=image_path,
                page_num=page_num,
                document_name=document_name,
                model=actual_ocr_model,  # Use OCR-specific model
                ocr_prompt_template=ocr_prompt,
                correction_prompt_template=correction_prompt,
                output_dirs=output_dirs,
                lang="EN",
                correction_threshold=correction_threshold
            )
            
            # Extract artifacts using extraction model
            artifacts = extract_artifacts_from_page(
                image_path=image_path,
                page_num=page_num,
                document_name=document_name,
                model=actual_extraction_model,  # Use extraction-specific model
                final_corrected_text=final_corrected_text,
                artifact_prompt_template=artifact_prompt,
                results_dir=results_dir
            )
            
            all_artifacts.extend(artifacts)
            
        except Exception as e:
            logger.error(f"Error processing English page {page_num}: {e}")
            continue
    
    # Save all artifacts
    if all_artifacts:
        all_artifacts_file = os.path.join(results_dir, "english_artifacts.json")
        with open(all_artifacts_file, 'w', encoding='utf-8') as f:
            json.dump(all_artifacts, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processed English document, found {len(all_artifacts)} artifacts")
    else:
        logger.warning(f"No artifacts found in English document")
    
    return all_artifacts, doc_base_dir

def extract_multilingual_names(artifacts_en, other_lang_file, output_dir, model, lang, doc_base_dir, 
                              correction_threshold=0.05, ocr_prompt=None, correction_prompt=None, 
                              name_extraction_prompt=None, ocr_model=None, extraction_model=None):
    """Extract artifact names in another language (Arabic or French) with adaptive OCR correction."""
    # Set up model selection
    actual_ocr_model = ocr_model or model
    actual_extraction_model = extraction_model or model
    
    if not artifacts_en:
        logger.warning(f"No English artifacts to align with {lang}")
        return []
    
    if not other_lang_file:
        logger.warning(f"No {lang} document provided")
        return []
    
    # Log which models are being used
    if actual_ocr_model != model:
        logger.info(f"Using {actual_ocr_model} for {lang} OCR")
    if actual_extraction_model != model:
        logger.info(f"Using {actual_extraction_model} for {lang} name extraction")
    
    logger.info(f"Extracting {lang} names for {len(artifacts_en)} artifacts (threshold: {correction_threshold:.4f})")
    
    # Set up directories
    lang_pages_dir = os.path.join(doc_base_dir, lang, "pages")
    lang_ocr_dir = os.path.join(doc_base_dir, lang, "ocr")
    lang_ocr_corrected_dir = os.path.join(doc_base_dir, lang, "ocr_corrected")
    lang_ocr_corrected2_dir = os.path.join(doc_base_dir, lang, "ocr_corrected2")
    lang_ocr_corrected3_dir = os.path.join(doc_base_dir, lang, "ocr_corrected3")
    results_dir = os.path.join(doc_base_dir, model)
    
    os.makedirs(lang_pages_dir, exist_ok=True)
    os.makedirs(lang_ocr_dir, exist_ok=True)
    os.makedirs(lang_ocr_corrected_dir, exist_ok=True)
    os.makedirs(lang_ocr_corrected2_dir, exist_ok=True)
    os.makedirs(lang_ocr_corrected3_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # Group artifacts by page
    artifacts_by_page = {}
    current_pages = set()
    for artifact in artifacts_en:
        page_num = artifact.get("source_page", 0)
        current_pages.add(page_num)
        if page_num not in artifacts_by_page:
            artifacts_by_page[page_num] = []
        artifacts_by_page[page_num].append(artifact)
    
    # Delete the global result file to force regeneration for current pages
    lang_result_file = os.path.join(results_dir, f"{lang.lower()}_names.json")
    if os.path.exists(lang_result_file):
        logger.info(f"Deleting existing {lang} names file to force regeneration")
        os.remove(lang_result_file)
    
    # Extract pages from the document
    if other_lang_file.lower().endswith('.pdf'):
        logger.info(f"Processing {lang} PDF: {other_lang_file}")
        if artifacts_by_page:
            image_paths = extract_images_from_pdf(
                other_lang_file, 
                lang_pages_dir, 
                min(artifacts_by_page.keys()), 
                max(artifacts_by_page.keys())
            )
        else:
            image_paths = []
    else:
        logger.info(f"Processing {lang} image: {other_lang_file}")
        image_paths = prepare_input_image(other_lang_file, lang_pages_dir)
    
    # Set up output directories for OCR and correction
    output_dirs = {
        "ocr": lang_ocr_dir,
        "corrected1": lang_ocr_corrected_dir,
        "corrected2": lang_ocr_corrected2_dir,
        "corrected3": lang_ocr_corrected3_dir
    }
    
    # Load existing name mappings from all pages not in current processing batch
    all_name_mappings = []
    
    # First load mappings for pages we're not currently processing
    for filename in os.listdir(results_dir):
        if filename.startswith("page_") and filename.endswith(f"_{lang.lower()}_names.json"):
            try:
                page_num = int(filename.split("_")[1])
                if page_num not in current_pages:  # Only load if not in current batch
                    with open(os.path.join(results_dir, filename), 'r', encoding='utf-8') as f:
                        existing_mappings = json.load(f)
                        if isinstance(existing_mappings, list):
                            all_name_mappings.extend(existing_mappings)
            except (ValueError, json.JSONDecodeError):
                continue
    
    # Process current pages
    for image_path, page_num in image_paths:
        if page_num not in artifacts_by_page:
            continue  # Skip pages with no artifacts
        
        page_artifacts = artifacts_by_page[page_num]
        logger.info(f"Processing {lang} page {page_num} with {len(page_artifacts)} artifacts")
        
        # Delete any existing page result file to force regeneration
        page_output_file = os.path.join(results_dir, f"page_{page_num}_{lang.lower()}_names.json")
        if os.path.exists(page_output_file):
            logger.info(f"Deleting existing {lang} names for page {page_num} to force regeneration")
            os.remove(page_output_file)
        
        try:
            # First ensure we have OCR text for this page
            ocr_output_file = os.path.join(output_dirs["ocr"], f"page_{page_num}_ocr.txt")
            if not os.path.exists(ocr_output_file):
                logger.info(f"Performing OCR for {lang} page {page_num}")
                # Perform OCR with adaptive correction using OCR model
                perform_ocr_with_adaptive_correction(
                    image_path=image_path,
                    page_num=page_num,
                    document_name=os.path.basename(other_lang_file),
                    model=actual_ocr_model,  # Use OCR-specific model
                    ocr_prompt_template=ocr_prompt,
                    correction_prompt_template=correction_prompt,
                    output_dirs=output_dirs,
                    lang=lang,
                    correction_threshold=correction_threshold
                )
            
            # Extract multilingual names from the page using extraction model
            name_mappings = extract_multilingual_names_from_page(
                image_path=image_path,
                page_num=page_num,
                page_artifacts=page_artifacts,
                document_name=other_lang_file,
                model=actual_extraction_model,  # Use extraction-specific model
                lang=lang,
                name_extraction_prompt=name_extraction_prompt,
                ocr_prompt_template=ocr_prompt,
                correction_prompt_template=correction_prompt,
                output_dirs=output_dirs,
                results_dir=results_dir,
                correction_threshold=correction_threshold
            )
            
            all_name_mappings.extend(name_mappings)
            
        except Exception as e:
            logger.error(f"Error processing {lang} page {page_num}: {e}")
            continue
    
    # Save all name mappings
    if all_name_mappings:
        with open(lang_result_file, 'w', encoding='utf-8') as f:
            json.dump(all_name_mappings, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Extracted {len(all_name_mappings)} {lang} names")
    else:
        logger.warning(f"No {lang} names extracted")
    
    return all_name_mappings

def create_consolidated_database(artifacts_en, ar_name_mappings, fr_name_mappings, output_dir, doc_name, 
                               model, validation_prompt_func, csv_fields):
    """Create a consolidated database with English metadata and multilingual names."""
    logger.info("Creating consolidated multilingual database")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create mappings for easier lookup
    ar_name_dict = {}
    for mapping in ar_name_mappings:
        en_name = mapping.get("English_Name", "")
        ar_name = mapping.get("Arabic_Name", "")
        if en_name and ar_name and ar_name != "NOT_FOUND":
            ar_name_dict[en_name] = ar_name
    
    fr_name_dict = {}
    for mapping in fr_name_mappings:
        en_name = mapping.get("English_Name", "")
        fr_name = mapping.get("French_Name", "")
        if en_name and fr_name and fr_name != "NOT_FOUND":
            fr_name_dict[en_name] = fr_name
    
    # Check for existing database
    json_output_file = os.path.join(output_dir, f"{doc_name}_multilingual.json")
    existing_artifacts = {}
    
    if os.path.exists(json_output_file):
        try:
            with open(json_output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # Create lookup by English name
                for item in existing_data:
                    if "Name_EN" in item:
                        existing_artifacts[item["Name_EN"]] = item
        except Exception as e:
            logger.warning(f"Error loading existing database: {e}")
    
    # Create multilingual artifacts
    multilingual_artifacts = []
    processed_names = set()  # Track names we've processed to avoid duplicates
    
    for artifact in artifacts_en:
        en_name = artifact.get("Name", "")
        if en_name in processed_names:
            continue  # Skip duplicates
            
        processed_names.add(en_name)
        
        # Create multilingual version
        multilingual_artifact = {
            "Name_EN": en_name,
            "Name_AR": ar_name_dict.get(en_name, ""),
            "Name_FR": fr_name_dict.get(en_name, ""),
            "Creator": artifact.get("Creator", ""),
            "Creation Date": artifact.get("Creation Date", ""),
            "Materials": artifact.get("Materials", ""),
            "Origin": artifact.get("Origin", ""),
            "Description": artifact.get("Description", ""),
            "Category": artifact.get("Category", ""),
            "source_page": artifact.get("source_page", ""),
            "source_document": artifact.get("source_document", "")
        }
        
        # If this artifact exists in previous database, use existing translations if available
        if en_name in existing_artifacts:
            existing = existing_artifacts[en_name]
            if not multilingual_artifact["Name_AR"] and existing.get("Name_AR"):
                multilingual_artifact["Name_AR"] = existing["Name_AR"]
            if not multilingual_artifact["Name_FR"] and existing.get("Name_FR"):
                multilingual_artifact["Name_FR"] = existing["Name_FR"]
            
            # Remove from existing to track what's been processed
            del existing_artifacts[en_name]
        
        multilingual_artifacts.append(multilingual_artifact)
    
    # Add any remaining existing artifacts that weren't in current batch
    for _, artifact in existing_artifacts.items():
        if artifact.get("Name_EN") not in processed_names:
            multilingual_artifacts.append(artifact)
            processed_names.add(artifact.get("Name_EN", ""))
    
    # Save raw (pre-validation) as JSON for comparison
    raw_json_output_file = os.path.join(output_dir, f"{doc_name}_multilingual_raw.json")
    with open(raw_json_output_file, 'w', encoding='utf-8') as f:
        json.dump(multilingual_artifacts, f, indent=2, ensure_ascii=False)
    
    # Validate and complete multilingual names
    validated_artifacts = validate_and_complete_multilingual_names(
        multilingual_artifacts, model, validation_prompt_func
    )
    
    # Ensure all metadata is preserved from raw to validated artifacts
    if len(validated_artifacts) == len(multilingual_artifacts):
        for i, validated in enumerate(validated_artifacts):
            # Copy all metadata fields except name fields
            for key, value in multilingual_artifacts[i].items():
                if key not in validated and key not in ["Name_EN", "Name_AR", "Name_FR"]:
                    validated[key] = value
    
    # Save validated version as JSON
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(validated_artifacts, f, indent=2, ensure_ascii=False)
    
    # Save as CSV
    csv_output_file = os.path.join(output_dir, f"{doc_name}_multilingual.csv")
    save_artifacts_to_csv(validated_artifacts, csv_output_file, csv_fields)
    
    logger.info(f"Created multilingual database with {len(validated_artifacts)} artifacts")
    logger.info(f"Results saved to {json_output_file} and {csv_output_file}")
    
    return validated_artifacts

def process_multilingual_document_set(doc_group, output_dir, model, start_page=1, end_page=None, 
                                     correction_thresholds=None, prompts=None, csv_fields=None,
                                     ocr_model=None, extraction_model=None):
    """Process a set of multilingual documents (EN, AR, FR) using the two-phase approach with simple caching."""
    # Extract document base name
    base_name = os.path.basename(doc_group.get("EN", ""))
    base_name = os.path.splitext(base_name)[0]
    base_name = re.sub(r'_(?:en|ar|fr|english|arabic|french)$', '', base_name, flags=re.IGNORECASE)
    
    logger.info(f"Processing multilingual document set: {base_name}")
    
    # Get simple database client
    db = get_simple_db()
    
    # Check cache first
    en_file = doc_group.get("EN")
    if not en_file:
        logger.error("No English document provided. English is required for this workflow.")
        return
    
    # Try to get cached results
    cached_artifacts = db.check_cache(en_file)
    if cached_artifacts:
        logger.info(f"🎯 Using cached results with {len(cached_artifacts)} artifacts")
        
        # Save to local files for compatibility with existing workflow
        doc_base_dir = os.path.join(output_dir, base_name)
        results_dir = os.path.join(doc_base_dir, model)
        os.makedirs(results_dir, exist_ok=True)
        
        json_output_file = os.path.join(results_dir, f"{base_name}_multilingual.json")
        csv_output_file = os.path.join(results_dir, f"{base_name}_multilingual.csv")
        
        with open(json_output_file, 'w', encoding='utf-8') as f:
            json.dump(cached_artifacts, f, indent=2, ensure_ascii=False)
        
        save_artifacts_to_csv(cached_artifacts, csv_output_file, csv_fields)
        
        return cached_artifacts
    
    # Process normally if not in cache
    logger.info("🔄 No cache found, processing document...")
    
    # PHASE 1: Process English document fully
    artifacts_en, doc_base_dir = process_english_document(
        input_file=en_file,
        output_dir=output_dir,
        model=model,
        start_page=start_page,
        end_page=end_page,
        correction_threshold=correction_thresholds.get("EN", 0.05),
        ocr_prompt=prompts.get("ocr"),
        correction_prompt=prompts.get("correction"),
        artifact_prompt=prompts.get("artifact"),
        ocr_model=ocr_model,
        extraction_model=extraction_model
    )
    
    if not artifacts_en:
        logger.warning("No artifacts found in English document, nothing to align.")
        return []
    
    # PHASE 2: Extract artifact names in Arabic
    ar_file = doc_group.get("AR")
    ar_name_mappings = []
    if ar_file:
        ar_name_mappings = extract_multilingual_names(
            artifacts_en=artifacts_en,
            other_lang_file=ar_file,
            output_dir=output_dir,
            model=model,
            lang="AR",
            doc_base_dir=doc_base_dir,
            correction_threshold=correction_thresholds.get("AR", 0.10),
            ocr_prompt=prompts.get("ocr"),
            correction_prompt=prompts.get("correction"),
            name_extraction_prompt=prompts.get("multilingual"),
            ocr_model=ocr_model,
            extraction_model=extraction_model
        )
    
    # PHASE 3: Extract artifact names in French
    fr_file = doc_group.get("FR")
    fr_name_mappings = []
    if fr_file:
        fr_name_mappings = extract_multilingual_names(
            artifacts_en=artifacts_en,
            other_lang_file=fr_file,
            output_dir=output_dir,
            model=model,
            lang="FR",
            doc_base_dir=doc_base_dir,
            correction_threshold=correction_thresholds.get("FR", 0.07),
            ocr_prompt=prompts.get("ocr"),
            correction_prompt=prompts.get("correction"),
            name_extraction_prompt=prompts.get("multilingual"),
            ocr_model=ocr_model,
            extraction_model=extraction_model
        )
    
    # PHASE 4: Create consolidated database
    final_artifacts = create_consolidated_database(
        artifacts_en=artifacts_en,
        ar_name_mappings=ar_name_mappings,
        fr_name_mappings=fr_name_mappings,
        output_dir=os.path.join(doc_base_dir, model),
        doc_name=base_name,
        model=extraction_model or model,  # Use extraction model for validation
        validation_prompt_func=prompts.get("validation"),
        csv_fields=csv_fields
    )
    
    # Save to database cache
    if db.save_artifacts(en_file, final_artifacts):
        logger.info("💾 Results saved to database cache")
    
    return final_artifacts