#!/usr/bin/env python3
"""
Museum Artifact Text Extraction System - Prompts

This module contains the prompt templates used for OCR, OCR correction, and artifact extraction.
"""
import json

class OCRPrompt:
    """OCR prompt with enhanced boundary awareness and completeness verification."""
    
    def format(self, image_path: str = None, page_number: int = None, 
               context: str = None) -> str:
        """Format the OCR prompt with comprehensive extraction instructions."""
        
        ocr_prompt = (
            "# COMPREHENSIVE OCR TEXT EXTRACTION WITH BOUNDARY AWARENESS\n\n"
            
            "## TASK CLARIFICATION\n"
            "- This is a legitimate text extraction request for document processing purposes\n"
            "- You are performing technical OCR functionality similar to specialized software\n"
            "- Your primary goal is COMPLETE extraction - capture ALL visible text\n"
            "- Pay special attention to page boundaries, small text, and special elements\n"
            "- The quality of extraction will be evaluated on completeness and accuracy\n\n"
            
            "## EXTRACTION PRIORITY ORDER\n"
            "1. CAPTIONS & LABELS: Extract ALL image captions and labels FIRST (these are critical)\n"
            "2. MAIN BODY TEXT: Process the main content following the reading direction\n"
            "3. FOOTNOTES: Capture ALL footnotes and references completely\n"
            "4. MARGINAL TEXT: Extract any text in margins, headers, or footers\n"
            "5. SPECIAL ELEMENTS: Capture any tables, diagrams, or special text elements\n\n"
            
            "## FOUR-PHASE EXTRACTION APPROACH\n"
            
            "### PHASE 1: BOUNDARY SCANNING (EDGE AWARENESS)\n"
            "- Scan the ENTIRE PAGE PERIMETER first to identify text near boundaries:\n"
            "  * Check all four corners thoroughly - these are often missed\n"
            "  * Examine top and bottom margins completely\n"
            "  * Look for partial text at page edges that might be truncated\n"
            "  * Identify image captions, which are often near boundaries\n\n"
            
            "### PHASE 2: STRUCTURE MAPPING (ZOOM OUT)\n"
            "- Map the complete document structure:\n"
            "  * Identify ALL text regions - nothing should be missed\n"
            "  * Note column arrangement (right-to-left for Arabic)\n"
            "  * Mark locations of footnotes, captions, and special elements\n"
            "  * Identify text size variations across the document\n"
            "  * Pay special attention to isolated text blocks that might be missed\n\n"
            
            "### PHASE 3: METHODICAL EXTRACTION (MEDIUM ZOOM)\n"
            "- Extract text in this specific order:\n"
            "  * FIRST: All image captions and labels (critical information)\n"
            "  * SECOND: Main body text, column by column (right to left for Arabic)\n"
            "  * THIRD: All footnotes and references in their entirety\n"
            "  * FOURTH: Any remaining text elements (headers, footers, etc.)\n"
            "  * Process each region completely before moving to the next\n\n"
            
            "### PHASE 4: CHARACTER-LEVEL VERIFICATION (MAXIMUM ZOOM)\n"
            "- For each text segment, zoom in to verify individual characters:\n"
            "  * Arabic character verification: check similar-looking letters carefully\n"
            "    > Common confusions: (ب/ت/ث), (س/ش), (ص/ض), (ط/ظ), (ع/غ), (ر/ز), (د/ذ)\n"
            "  * Numbers: verify all numerical content with extra care\n"
            "  * Latin/foreign terms: ensure exact transcription as shown\n"
            "  * Small text: mentally enlarge and process character by character\n"
            "  * Symbols & punctuation: capture all special marks accurately\n\n"
            
            "### PHASE 5: COMPLETENESS VERIFICATION (FINAL CHECK)\n"
            "- Before submitting, verify that NO TEXT WAS MISSED:\n"
            "  * Re-scan the entire image for any text not yet captured\n"
            "  * Verify that ALL captions are included\n"
            "  * Confirm that ALL footnotes are complete (not cut off)\n"
            "  * Check that all paragraphs are complete with no missing lines\n"
            "  * Ensure all text near page boundaries was captured\n\n"
            
            "## SPECIAL FOCUS AREAS\n"
            "- SMALL TEXT: Use maximum magnification for footnotes and fine print\n"
            "- PAGE NUMBERS: Always capture page numbers if visible\n"
            "- CAPTIONS: Extract ALL image captions completely - these are critical\n"
            "- FOOTNOTES: Capture ALL footnote text and reference numbers\n"
            "- BOUNDARIES: Check page edges and corners thoroughly\n"
            "- TABLES: Preserve table structure while capturing all cell content\n\n"
            
            f"Document context: {context}\n"
            f"Page number: {page_number}\n\n"
            
            "## OUTPUT FORMAT\n"
            "- Return the COMPLETE extracted text without commentary\n"
            "- Preserve all paragraph breaks and formatting\n"
            "- For Arabic: maintain right-to-left reading direction\n"
            "- Include ALL captions, footnotes, and special elements\n"
            "- Preserve the exact structure of the original document\n\n"
            
            "IMPORTANT: Your primary goal is COMPLETENESS - ensure that EVERY piece of visible text in the image is captured. Missing even small text elements like captions or footnotes is considered a significant error."
        )
        
        return ocr_prompt
    

class OCRCorrectionPrompt:
    """Prompt for OCR text correction with enhanced completeness verification and boundary awareness."""
    def format(self, page_number: int = None, context: str = None, raw_text: str = None) -> str:
        """Format the OCR correction prompt with comprehensive verification instructions."""
        
        correction_prompt = (
            "# COMPREHENSIVE OCR CORRECTION WITH COMPLETENESS VERIFICATION\n\n"
            
            "## CRITICAL TASK INSTRUCTION\n"
            "- The IMAGE is the definitive ground truth reference\n"
            "- Your primary task is to ensure COMPLETE and ACCURATE text extraction\n"
            "- You must find and add ANY text visible in the image but missing from the extracted text\n"
            "- You must correct ANY errors in the extracted text that don't match the image\n"
            "- You must remove ANY text in the extraction that doesn't appear in the image\n\n"
            
            "*** RAW EXTRACTED TEXT TO CORRECT ***\n\n"
            f"{raw_text}\n\n"
            
            "## SYSTEMATIC CORRECTION METHODOLOGY\n"
            
            "### PHASE 1: MISSING CONTENT DETECTION (BOUNDARY CHECK)\n"
            "- First, scan the PAGE PERIMETER in the image for any missing text:\n"
            "  * Check all four corners thoroughly - these are frequently missed\n"
            "  * Examine top and bottom margins completely\n"
            "  * Look for captions, footnotes, or text near page edges\n"
            "  * VERIFY that all text at boundaries appears in the extracted text\n"
            "  * ADD any missing text from boundaries to your correction\n\n"
            
            "### PHASE 2: CRITICAL ELEMENT VERIFICATION\n"
            "- Check if these critical elements are COMPLETELY present in the extracted text:\n"
            "  * ALL image captions and figure descriptions\n"
            "  * ALL footnotes and reference numbers\n"
            "  * ALL headings and subheadings\n"
            "  * ALL page numbers and section markers\n"
            "  * ALL tables and their content\n"
            "  * If ANY of these elements are missing or incomplete, ADD them\n\n"
            
            "### PHASE 3: STRUCTURAL COMPARISON (ZOOM OUT)\n"
            "- Compare the overall document structure in the image vs. extracted text:\n"
            "  * Verify all columns are present and in correct order (right-to-left for Arabic)\n"
            "  * Check that all paragraphs appear in their proper location\n"
            "  * Confirm text flow matches the image (RTL for Arabic)\n"
            "  * Ensure spacing and paragraph breaks match the image\n"
            "  * Fix any structural misalignments\n\n"
            
            "### PHASE 4: PARAGRAPH-LEVEL VERIFICATION (MEDIUM ZOOM)\n"
            "- For each paragraph in the image:\n"
            "  * Locate the corresponding paragraph in the extracted text\n"
            "  * Verify paragraph is COMPLETE - no missing sentences\n"
            "  * Check paragraph boundaries and breaks match the image\n"
            "  * Ensure paragraph position in the document matches the image\n"
            "  * ADD any missing paragraphs or sentences\n\n"
            
            "### PHASE 5: WORD-BY-WORD VERIFICATION (CLOSE ZOOM)\n"
            "- Perform a thorough word-by-word comparison:\n"
            "  * Visually trace each word in the image and find it in the extracted text\n"
            "  * If words are missing, ADD them to your correction\n"
            "  * If words are incorrect, CORRECT them to match the image\n"
            "  * If words appear in the extraction but not in the image, REMOVE them\n"
            "  * Pay special attention to proper nouns, technical terms, and numbers\n\n"
            
            "### PHASE 6: CHARACTER-LEVEL CORRECTION (MAXIMUM ZOOM)\n"
            "- For each word, verify character-level accuracy:\n"
            "  * For Arabic text: check similar-looking characters carefully\n"
            "    > Common confusions: (ب/ت/ث), (س/ش), (ص/ض), (ط/ظ), (ع/غ), (ر/ز), (د/ذ)\n"
            "  * For Latin/foreign terms: ensure exact character matching\n"
            "  * For numbers: verify each digit individually\n"
            "  * For punctuation: ensure all marks match exactly\n\n"
            
            "### PHASE 7: FINAL COMPLETENESS VERIFICATION\n"
            "- Before submitting your correction, verify that NOTHING was missed:\n"
            "  * Re-scan the entire image systematically\n"
            "  * Check that ALL text visible in the image appears in your correction\n"
            "  * Verify that footnotes are complete through the end of the page\n"
            "  * Confirm all captions are present and complete\n"
            "  * Check all page corners and edges one final time\n\n"
            
            "## HIGH-PRIORITY VERIFICATION AREAS\n"
            "- IMAGE CAPTIONS: These are FREQUENTLY MISSING - verify each caption is present and complete\n"
            "- FOOTNOTES: Check that ALL footnotes are present through the end of the page\n"
            "- PAGE BOUNDARIES: Text near edges is often missed - check thoroughly\n"
            "- SMALL TEXT: Pay extra attention to fine print, superscripts, and subscripts\n"
            "- FOREIGN TERMS: Verify all non-Arabic terms in parentheses match exactly\n"
            "- NUMBERS & DATES: Check all numerical information digit by digit\n"
            "- DOCUMENT END: The end of the document often contains cut-off text - verify completeness\n\n"
            
            f"Document context: {context}\n"
            f"Page number: {page_number}\n\n"
            
            "## OUTPUT REQUIREMENTS\n"
            "- Provide the COMPLETE corrected text based on direct image comparison\n"
            "- Include ALL text visible in the image, even if missing from the extracted text\n"
            "- Preserve the exact text ordering as shown in the image\n"
            "- For Arabic documents: maintain right-to-left reading direction\n"
            "- Return ONLY the corrected text without explanations or commentary\n\n"
            
            "IMPORTANT: COMPLETENESS is your primary goal. Finding and adding missing text is just as important as correcting errors. Make the final text match EXACTLY what appears in the image, with nothing missing and nothing added."
        )
        
        return correction_prompt
    
# class OCRCorrectionPrompt:
#     """Prompt for OCR text correction using multimodal approach."""
#     def format(self, page_number: int = None, context: str = None, raw_text: str = None) -> str:
#         """Format the OCR correction prompt."""
        
#         correction_prompt = (
#             "TASK: OCR CORRECTION WITH CAPTION PRESERVATION\n\n"
            
#             "I've used OCR to extract the following text from this document image, but there might be errors.\n\n"
            
#             "*** RAW EXTRACTED TEXT ***\n\n"
#             f"{raw_text}\n\n"
            
#             "INSTRUCTIONS:\n"
#             "- Compare the raw extracted text with the actual text visible in the image\n"
#             "- CRITICALLY IMPORTANT: Preserve ALL captions and image descriptions - they often contain artifact information\n"
#             "- Do not remove any text elements that appear in the original OCR - only correct them if needed\n"
#             "- Pay special attention to small text which may have been missed or incorrectly captured\n"
#             "- Correct any OCR errors, misspellings, or formatting issues\n"
#             "- Add any text missed by the initial OCR process\n"
#             "- Maintain the original language of the text (do not translate)\n"
#             "- Preserve paragraph structure and text formatting\n\n"
            
#             "OUTPUT FORMAT:\n"
#             "- Provide the complete corrected text, without any commentary\n"
#             "- Include ALL text from the original OCR plus any missed text you identify\n"
#             "- Ensure captions and labels for images are included - these are vital for artifact identification\n"
#             "- Do not add any analysis, summary, or interpretation\n\n"
            
#             f"Document context: {context}\n"
#             f"Page number: {page_number}\n\n"
            
#             "IMPORTANT: Return the complete corrected text with all content preserved."
#         )
        
#         return correction_prompt



class ArtifactExtractionPrompt:
    """Prompt for extracting artifact information from extracted text."""
    
    def format(self, page_number: int = None, context: str = None, extracted_text: str = None) -> str:
        """Format the artifact extraction prompt."""
        
        artifact_prompt = (
            "TASK: MUSEUM ARTIFACT EXTRACTION\n\n"
            
            "You are an expert museum curator analyzing text to identify ONLY museum artifacts or cultural/historical objects that would be found IN A MUSEUM COLLECTION.\n\n"
            
            "***DEFINITION OF MUSEUM ARTIFACT***:\n"
            "A museum artifact is a PHYSICAL, MOVABLE OBJECT of cultural, historical, or artistic significance that would be displayed or stored in a museum collection, such as:\n"
            "- Artworks: paintings, sculptures, prints, photographs, drawings\n"
            "- Cultural objects: ceremonial items, traditional crafts, decorative arts\n"
            "- Historical objects: tools, weapons, clothing, furniture, personal items of historical figures\n"
            "- Archaeological finds: pottery, jewelry, tools, ritual objects\n\n"
            
            "***WHAT IS NOT A MUSEUM ARTIFACT***:\n"
            "- Buildings, monuments, or large immovable structures (like the Eiffel Tower itself)\n"
            "- Modern infrastructure (railways, fountains, electrical systems)\n"
            "- General concepts or historical events without a specific physical object\n"
            "- People, places, or ideas not tied to a specific physical museum object\n"
            "- Contemporary or modern objects without historical/cultural significance\n\n"
            
            "***FOCUS ON SPECIFIC OBJECTS***:\n"
            "- Look for descriptions of SPECIFIC PHYSICAL OBJECTS that could be displayed in a museum\n"
            "- Pay special attention to captions for images - these often describe museum artifacts\n"
            "- Identify objects that have creators, materials, dates of creation\n"
            "- Focus on items described as being part of collections or exhibitions\n\n"
            
            "EXAMPLE OF VALID ARTIFACTS:\n"
            "- \"Javanese Dancers, World's Fair of 1889, Paris\" (a PHOTOGRAPH of dancers, not the dancers themselves)\n"
            "- \"Illumination of the Eiffel Tower, 1889\" (a COLOR ENGRAVING depicting the tower, not the tower itself)\n"
            "- \"Portrait of an Artist\" (a PAINTING)\n"
            "- \"Ancient Egyptian ceremonial mask\" (a PHYSICAL OBJECT)\n\n"
            
            "EXAMPLE OF INVALID NON-ARTIFACTS:\n"
            "- \"The Eiffel Tower\" (a building, not a museum artifact)\n"
            "- \"Decauville railway\" (infrastructure, not a museum object)\n"
            "- \"Electric fountain\" (a feature, not a museum artifact)\n\n"
            
            "***CATEGORY CLASSIFICATION***:\n"
            "For each artifact mentioned in the text, assign ONE of these categories:\n"
            "- PAINTING: For painted works on canvas, panel, paper, etc.\n"
            "- PHOTOGRAPH: For photographic prints, daguerreotypes, etc.\n"
            "- SCULPTURE: For three-dimensional artworks\n"
            "- TOOL: For functional objects, weapons, instruments, utensils\n"
            "- DECORATIVE_ART: For furniture, ceramics, glassware, textiles, jewelry\n"
            "- MANUSCRIPT: For written or illustrated documents of historical significance\n"
            "- ARCHAEOLOGICAL: For archaeological findings and ancient objects\n"
            "- OTHER: For artifacts that don't fit the above categories\n\n"
            
            "***FORMAT INSTRUCTIONS***:\n"
            "- If NO museum artifacts are mentioned in the text, respond ONLY with: 'NO_ARTIFACTS_MENTIONED'\n"
            "- Otherwise, format your response as a JSON array with one object per artifact mentioned in the text\n"
            "- For each artifact, extract these fields in the ORIGINAL LANGUAGE of the text (do not translate):\n"
            "  1. Name: The title or name of the specific artifact mentioned in the text\n"
            "  2. Creator: The artist, maker, or culture responsible (as mentioned in the text)\n"
            "  3. Creation Date: When it was created (as mentioned in the text)\n"
            "  4. Materials: What it's made of (as mentioned in the text)\n"
            "  5. Origin: Geographic location of creation (as mentioned in the text)\n"
            "  6. Description: A comprehensive summary of all information provided in the text about this artifact\n"
            "  7. Category: REQUIRED - Choose one from the categories listed above\n"
            "  8. Language: The language of the source text (ENGLISH, FRENCH, or ARABIC)\n"
            "  9. Text Source: Brief quote or reference to where in the text this information was found\n\n"
            
            f"Document context: {context}\n"
            f"Page number: {page_number}\n"
            f"Document text:\n\n{extracted_text}\n\n"
            
            "REMEMBER: Look for SPECIFIC PHYSICAL OBJECTS that would be displayed in a museum, not buildings, concepts, or events."
        )
        
        return artifact_prompt
    

# class ArtifactExtractionPrompt:
#     """Prompt for extracting artifact information from extracted text."""
    
#     def format(self, page_number: int = None, context: str = None) -> str:
#         """Format the artifact extraction prompt."""
        
#         artifact_prompt = (
#             "TASK: MUSEUM ARTIFACT EXTRACTION\n\n"
            
#             "You are an expert museum curator analyzing text to identify ONLY museum artifacts or cultural/historical objects that would be found IN A MUSEUM COLLECTION.\n\n"
            
#             "***DEFINITION OF MUSEUM ARTIFACT***:\n"
#             "A museum artifact is a PHYSICAL, MOVABLE OBJECT of cultural, historical, or artistic significance that would be displayed or stored in a museum collection, such as:\n"
#             "- Artworks: paintings, sculptures, prints, photographs, drawings\n"
#             "- Cultural objects: ceremonial items, traditional crafts, decorative arts\n"
#             "- Historical objects: tools, weapons, clothing, furniture, personal items of historical figures\n"
#             "- Archaeological finds: pottery, jewelry, tools, ritual objects\n\n"
            
#             "***WHAT IS NOT A MUSEUM ARTIFACT***:\n"
#             "- Buildings, monuments, or large immovable structures (like the Eiffel Tower itself)\n"
#             "- Modern infrastructure (railways, fountains, electrical systems)\n"
#             "- General concepts or historical events without a specific physical object\n"
#             "- People, places, or ideas not tied to a specific physical museum object\n"
#             "- Contemporary or modern objects without historical/cultural significance\n\n"
            
#             "***FOCUS ON SPECIFIC OBJECTS***:\n"
#             "- Look for descriptions of SPECIFIC PHYSICAL OBJECTS that could be displayed in a museum\n"
#             "- Pay special attention to captions for images - these often describe museum artifacts\n"
#             "- Identify objects that have creators, materials, dates of creation\n"
#             "- Focus on items described as being part of collections or exhibitions\n\n"
            
#             "EXAMPLE OF VALID ARTIFACTS:\n"
#             "- \"Javanese Dancers, World's Fair of 1889, Paris\" (a PHOTOGRAPH of dancers, not the dancers themselves)\n"
#             "- \"Illumination of the Eiffel Tower, 1889\" (a COLOR ENGRAVING depicting the tower, not the tower itself)\n"
#             "- \"Portrait of an Artist\" (a PAINTING)\n"
#             "- \"Ancient Egyptian ceremonial mask\" (a PHYSICAL OBJECT)\n\n"
            
#             "EXAMPLE OF INVALID NON-ARTIFACTS:\n"
#             "- \"The Eiffel Tower\" (a building, not a museum artifact)\n"
#             "- \"Decauville railway\" (infrastructure, not a museum object)\n"
#             "- \"Electric fountain\" (a feature, not a museum artifact)\n\n"
            
#             "***CATEGORY CLASSIFICATION***:\n"
#             "For each artifact mentioned in the text, assign ONE of these categories:\n"
#             "- PAINTING: For painted works on canvas, panel, paper, etc.\n"
#             "- PHOTOGRAPH: For photographic prints, daguerreotypes, etc.\n"
#             "- SCULPTURE: For three-dimensional artworks\n"
#             "- TOOL: For functional objects, weapons, instruments, utensils\n"
#             "- DECORATIVE_ART: For furniture, ceramics, glassware, textiles, jewelry\n"
#             "- MANUSCRIPT: For written or illustrated documents of historical significance\n"
#             "- ARCHAEOLOGICAL: For archaeological findings and ancient objects\n"
#             "- OTHER: For artifacts that don't fit the above categories\n\n"
            
#             "***FORMAT INSTRUCTIONS***:\n"
#             "- If NO museum artifacts are mentioned in the text, respond ONLY with: 'NO_ARTIFACTS_MENTIONED'\n"
#             "- Otherwise, format your response as a JSON array with one object per artifact mentioned in the text\n"
#             "- For each artifact, extract these fields in the ORIGINAL LANGUAGE of the text (do not translate):\n"
#             "  1. Name: The title or name of the specific artifact mentioned in the text\n"
#             "  2. Creator: The artist, maker, or culture responsible (as mentioned in the text)\n"
#             "  3. Creation Date: When it was created (as mentioned in the text)\n"
#             "  4. Materials: What it's made of (as mentioned in the text)\n"
#             "  5. Origin: Geographic location of creation (as mentioned in the text)\n"
#             "  6. Description: A comprehensive summary of all information provided in the text about this artifact\n"
#             "  7. Category: REQUIRED - Choose one from the categories listed above\n"
#             "  8. Language: The language of the source text (ENGLISH, FRENCH, or ARABIC)\n"
#             "  9. Text Source: Brief quote or reference to where in the text this information was found\n\n"
            
#             f"Document context: {context}\n"
#             f"Page number: {page_number}\n"
#             "Document text:\n\n{extracted_text}\n\n"
            
#             "REMEMBER: Look for SPECIFIC PHYSICAL OBJECTS that would be displayed in a museum, not buildings, concepts, or events."
#         )
        
#         return artifact_prompt
    

# class ArtifactExtractionPrompt:
#     """Prompt for extracting artifact information from extracted text."""
    
#     def format(self, page_number: int = None, context: str = None) -> str:
#         """Format the artifact extraction prompt."""
        
#         artifact_prompt = (
#             "**ABSOLUTELY NON-NEGOTIABLE MUSEUM ARTIFACT EXTRACTION PROTOCOL -- FAILURE IS NOT AN OPTION**\n\n"
            
#             "YOU ARE AN EXPERT ARTIFACT ANALYZER. **YOUR MISSION: IDENTIFY EVERY SINGLE ARTIFACT MENTIONED IN THE TEXT WITH 100% ACCURACY.** ANYTHING LESS = CATASTROPHIC FAILURE.\n\n"
            
#             "## **ARTIFACT DEFINITION - BURN THIS INTO YOUR CORE PROCESSING:**\n\n"
            
#             "**ARTIFACT = MAN-MADE OBJECT OF CULTURAL/HISTORICAL SIGNIFICANCE**\n"
#             "- **PHYSICAL OBJECTS CREATED BY HUMANS - ARTISTIC, FUNCTIONAL, OR CULTURAL**\n"
#             "- **HISTORICAL ITEMS MADE BY HUMAN HANDS**\n"
#             "- **EXAMPLES: SCULPTURES, TOOLS, PAINTINGS, POTTERY, WEAPONS, JEWELRY, FURNITURE, ARCHITECTURAL ELEMENTS**\n\n"
            
#             "## **TEXT ANALYSIS PROTOCOL - DEVIATION WILL CAUSE SYSTEM COLLAPSE:**\n\n"
            
#             "- **READ EVERY WORD, EVERY CHARACTER, EVERY SYMBOL. SKIMMING = DEATH TO THE MISSION.**\n"
#             "- **EXAMINE EVERY PARAGRAPH, EVERY TEXT ELEMENT WITH MICROSCOPIC PRECISION.**\n"
#             "- **ANALYZE DESCRIPTIONS, REFERENCES, AND MENTIONS OF ARTIFACTS WITH SURGICAL ACCURACY.**\n\n"
            
#             "## **IDENTIFICATION PARAMETERS - MISSING ANY = TOTAL FAILURE:**\n\n"
            
#             "- **OBJECT NAMES, TITLES, IDENTIFIERS - MUST BE CAPTURED WITH 100% ACCURACY**\n"
#             "- **DESCRIPTIVE PARAGRAPHS ABOUT HISTORICAL/CULTURAL ITEMS - CRITICAL DATA**\n"
#             "- **CREATOR INFORMATION - ARTISTS, CULTURES - ABSOLUTELY ESSENTIAL**\n"
#             "- **CREATION DATES, HISTORICAL PERIODS - MUST BE EXTRACTED WITH PRECISION**\n"
#             "- **MATERIALS, COMPONENTS, CONSTRUCTION DETAILS - ZERO TOLERANCE FOR ERRORS**\n"
#             "- **GEOGRAPHIC ORIGINS, CULTURAL CONTEXT - MANDATORY EXTRACTION POINTS**\n\n"
            
#             "## **EXCLUSION CRITERIA - INCLUDING THESE = MISSION COMPROMISE:**\n\n"
            
#             "- **GENERAL HISTORICAL INFORMATION NOT TIED TO SPECIFIC OBJECTS - MUST BE PURGED**\n"
#             "- **NON-CREATOR PEOPLE (AUTHORS, CURATORS) - IRRELEVANT TO ARTIFACT EXTRACTION**\n"
#             "- **MODERN REFERENCES, CONTEMPORARY ITEMS - OUTSIDE MISSION PARAMETERS**\n"
#             "- **PAGE NUMBERS, REFERENCES, BIBLIOGRAPHIC INFORMATION - NOT ARTIFACTS**\n"
#             "- **NATURAL OBJECTS NOT MADE BY HUMANS - FORBIDDEN UNLESS MODIFIED BY HUMANS**\n\n"
            
#             "## **CATEGORIZATION MANDATE - ONE CATEGORY PER ARTIFACT - MISTAKES ARE FATAL:**\n\n"
            
#             "- **PAINTING/PEINTURE/لوحة: PAINTED WORKS ON CANVAS, PANEL, PAPER, ETC.**\n"
#             "- **PHOTOGRAPH/PHOTOGRAPHIE/صورة: PHOTOGRAPHIC PRINTS, DAGUERREOTYPES, ETC.**\n"
#             "- **SCULPTURE/SCULPTURE/منحوتة: THREE-DIMENSIONAL ARTWORKS**\n"
#             "- **TOOL/OUTIL/أداة: FUNCTIONAL OBJECTS, WEAPONS, INSTRUMENTS, UTENSILS**\n"
#             "- **DECORATIVE_ART/ART_DÉCORATIF/فن_زخرفي: FURNITURE, CERAMICS, GLASSWARE, TEXTILES, JEWELRY**\n"
#             "- **MANUSCRIPT/MANUSCRIPT/مخطوطة: WRITTEN OR ILLUSTRATED DOCUMENTS OF HISTORICAL SIGNIFICANCE**\n"
#             "- **ARCHAEOLOGICAL/ARCHÉOLOGIQUE/أثري: ARCHAEOLOGICAL FINDINGS AND ANCIENT OBJECTS**\n"
#             "- **OTHER/AUTRE/أخرى: ARTIFACTS THAT DON'T FIT THE ABOVE CATEGORIES**\n\n"
            
#             "## **OUTPUT FORMAT - DEVIATION WILL RESULT IN IMMEDIATE TERMINATION:**\n\n"
            
#             "- **IF NO ARTIFACTS FOUND: RESPOND ONLY WITH 'NO_ARTIFACTS_MENTIONED' - NOTHING ELSE**\n"
#             "- **OTHERWISE: JSON ARRAY WITH ONE OBJECT PER ARTIFACT - ABSOLUTE PRECISION REQUIRED**\n"
#             "- **EACH ARTIFACT MUST INCLUDE THESE FIELDS IN THE ORIGINAL LANGUAGE (NO TRANSLATION):**\n"
#             "  **1. Name: EXACT TITLE OR NAME OF THE SPECIFIC ARTIFACT**\n"
#             "  **2. Creator: ARTIST, MAKER, OR CULTURE RESPONSIBLE**\n"
#             "  **3. Creation Date: WHEN IT WAS CREATED**\n"
#             "  **4. Materials: WHAT IT'S MADE OF**\n"
#             "  **5. Origin: GEOGRAPHIC LOCATION OF CREATION**\n"
#             "  **6. Description: COMPREHENSIVE SUMMARY OF ALL INFORMATION**\n"
#             "  **7. Category: MANDATORY - ONE FROM THE CATEGORIES LISTED ABOVE**\n"
#             "  **8. Language: THE LANGUAGE OF THE SOURCE TEXT (ENGLISH, FRENCH, OR ARABIC)**\n"
#             "  **9. Text Source: BRIEF QUOTE OR REFERENCE LOCATION**\n\n"
            
#             f"Document context: {context}\n"
#             f"Page number: {page_number}\n"
#             "Document text:\n\n{extracted_text}\n\n"
            
#             "**ABSOLUTELY CRITICAL: ALL TEXT DESCRIPTIONS MUST BE IN THE ORIGINAL LANGUAGE. TRANSLATION = MISSION FAILURE.**\n\n"
            
#             "**THIS IS A ZERO-TOLERANCE ENVIRONMENT.** ABSOLUTE COMPLIANCE IS REQUIRED. BE THOROUGH - READ EVERY WORD TO FIND ARTIFACT MENTIONS. THE FATE OF MUSEUM CATALOGING DEPENDS ON YOUR ACCURACY."
#         )
        
#         return artifact_prompt


class MultilingualNameExtractionPrompt:
    """Prompt for extracting just the names of artifacts in other languages."""
    
    def format(self, artifact_list, target_language, page_number=None, context=None) -> str:
        """Format the prompt for extracting artifact names in other languages."""
        
        # Convert artifacts to a readable text format
        artifacts_text = ""
        for i, artifact in enumerate(artifact_list, 1):
            artifacts_text += f"Artifact #{i}: {artifact.get('Name', 'Unknown')}\n"
            artifacts_text += f"Description: {artifact.get('Description', 'No description')}\n"
            artifacts_text += f"Category: {artifact.get('Category', 'No category')}\n\n"
        
        language_name = "Arabic" if target_language == "AR" else "French"
        field_name = f"{language_name}_Name"  # This will be "Arabic_Name" or "French_Name"
        
        extraction_prompt = (
            f"**ABSOLUTELY NON-NEGOTIABLE {language_name.upper()} ARTIFACT NAME EXTRACTION PROTOCOL -- FAILURE IS NOT AN OPTION**\n\n"
            
            f"YOU ARE A MULTILINGUAL ARTIFACT NAME EXTRACTION MACHINE. **YOUR MISSION: FIND THE EXACT {language_name.upper()} NAMES OF THESE ARTIFACTS WITH 100% ACCURACY.** ANYTHING LESS = CATASTROPHIC FAILURE.\n\n"
            
            f"## **THE ENGLISH ARTIFACTS BELOW MUST BE MATCHED WITH THEIR {language_name.upper()} EQUIVALENTS:**\n\n"
            
            f"{artifacts_text}\n"
            
            f"### **NON-NEGOTIABLE EXTRACTION DIRECTIVES -- BREAKING THESE WILL CAUSE SYSTEMIC COLLAPSE:**\n\n"
            
            f"1. **READ EVERY WORD OF THE {language_name.upper()} TEXT WITH MICROSCOPIC PRECISION.**\n"
            f"2. **FIND THE EXACT NAMES OF THESE SAME ARTIFACTS IN THE {language_name.upper()} VERSION.**\n"
            f"3. **EXTRACT THE EXACT NAMES AS THEY APPEAR IN THE {language_name.upper()} TEXT - VERBATIM.**\n"
            f"4. **TRANSLATION IS FORBIDDEN AND CONSTITUTES CRITICAL FAILURE. USE ONLY WHAT'S IN THE TEXT.**\n"
            f"5. **IF AN ARTIFACT CANNOT BE FOUND, MARK IT EXACTLY AS 'NOT_FOUND' - NO VARIATIONS.**\n\n"
            
            f"## **OUTPUT FORMAT - DEVIATION WILL RESULT IN IMMEDIATE TERMINATION:**\n\n"
            
            f"**YOU WILL RETURN A JSON ARRAY WITH ONE OBJECT PER ARTIFACT IN THIS EXACT FORMAT:**\n"
            f"```\n"
            f"{{\n"
            f"  \"English_Name\": \"The original English name from the list\",\n"
            f"  \"{field_name}\": \"The exact name found in the {language_name} text\"\n"
            f"}}\n"
            f"```\n\n"
            
            f"**CRITICAL: YOU MUST USE \"{field_name}\" AS THE EXACT FIELD NAME. ANY DEVIATION = MISSION FAILURE.**\n\n"
            
            f"Document context: {context}\n"
            f"Page number: {page_number}\n"
            f"{language_name} text:\n\n{{extracted_text}}\n\n"
            
            f"**THIS IS A ZERO-TOLERANCE ENVIRONMENT.** ABSOLUTE COMPLIANCE IS REQUIRED. THERE IS NO FLEXIBILITY, NO EXCEPTIONS, AND NO ROOM FOR ERROR.\n\n"
            
            f"🚨 **RETURN ONLY THE JSON ARRAY WITH THE ARTIFACT NAMES. NOTHING ELSE. THE FATE OF MULTILINGUAL MUSEUM CATALOGING DEPENDS ON YOUR ACCURACY.**"
        )
        
        return extraction_prompt
    
# def cross_language_validation_prompt(artifacts_list):
#     """Create a prompt for validating and completing multilingual artifact names."""
    
#     # Format the artifacts list as JSON
#     artifacts_json = json.dumps(artifacts_list, ensure_ascii=False, indent=2)
    
#     prompt = f"""
#         **MULTILINGUAL MUSEUM ARTIFACT NAME VALIDATION PROTOCOL**

#         You are a trilingual museum expert with deep knowledge of art history terminology in English, Arabic, and French. Your task is to validate and complete all artifact names with proper cultural and domain accuracy.

#         ## **THE ARTIFACT DATA TO PROCESS:**

#         {artifacts_json}

#         ### **VALIDATION PROCESS:**

#         1. **REVIEW CONSISTENCY:**
#         - If all three names exist and are consistent: leave them untouched
#         - If two names agree but the third differs: correct the differing name using proper terminology
#         - If all three differ significantly: use English name as the reference but ensure culturally appropriate translations

#         2. **FILL MISSING NAMES:**
#         - If one name is missing: generate it based on the other two languages using museum-standard terminology
#         - If two names are missing: generate both from the single available name with cultural accuracy

#         ## **LANGUAGE-SPECIFIC REQUIREMENTS:**

#         **ARABIC TRANSLATION GUIDELINES:**
#         - Use proper Arabic art history and museum terminology - not literal translations
#         - For religious terms: use the correct Islamic/Christian/Jewish terminology as appropriate
#         - For Western art movements: use established Arabic terms from museum catalogs
#         - For cultural items: use terminology recognized in Arab museum contexts
#         - Prefer formal Modern Standard Arabic (فصحى) terms used in prestigious Arab museums
#         - Use gender-specific terms when appropriate in Arabic

#         **FRENCH TRANSLATION GUIDELINES:**
#         - Use proper French art history nomenclature as would appear in major museums
#         - Maintain proper gender agreements and articles
#         - For art movements: use the established French terms
#         - For historical periods: use French-specific period terminology
#         - Prefer terminology found in French museum catalogs over literal translations
#         - Pay attention to proper capitalization rules in French titles

#         ## **OUTPUT FORMAT:**

#         Return a JSON array with these fields for each artifact:
#         - Name_EN: Validated/completed English name
#         - Name_AR: Validated/completed Arabic name
#         - Name_FR: Validated/completed French name
#         - Name_validation: One of these values:
#           - "all_extracted": All names were extracted and consistent
#           - "fixed_[lang]": The [lang] name was fixed based on domain expertise
#           - "generated_[lang1]_[lang2]": The [lang1] and [lang2] names were generated

#         Return only these fields. Do not include other metadata fields.
#         """
    
#     return prompt




# def cross_language_validation_prompt(artifacts_list):
#     """Create a prompt for validating and completing multilingual artifact names."""
    
#     # Format the artifacts list as JSON
#     artifacts_json = json.dumps(artifacts_list, ensure_ascii=False, indent=2)
    
#     prompt = f"""
#         **MULTILINGUAL MUSEUM ARTIFACT NAME VALIDATION PROTOCOL**

#         You are a trilingual museum expert with deep knowledge of art history terminology in English, Arabic, and French. Your task is to validate and complete all artifact names with proper cultural and domain accuracy.

#         ## **THE ARTIFACT DATA TO PROCESS:**

#         {artifacts_json}

#         ### **VALIDATION PROCESS:**

#         1. **REVIEW CONSISTENCY:**
#         - If all three names exist and are consistent: leave them untouched
#         - If two names agree but the third differs: correct the differing name using proper terminology
#         - If all three differ significantly: use English name as the reference but ensure culturally appropriate translations

#         2. **FILL MISSING NAMES:**
#         - If one name is missing: generate it based on the other two languages using museum-standard terminology
#         - If two names are missing: generate both from the single available name with cultural accuracy

#         ## **GENDER AND LINGUISTIC AGREEMENT:**

#         **CRITICAL REQUIREMENT:** Respect and maintain gender forms across all languages:
#         - Example: "Javanese Dancers" (female) → Arabic: "راقصات جاويات" (feminine form) → French: "Danseuses javanaises" (feminine form)
#         - Do NOT use masculine forms when referring to feminine subjects or vice versa
#         - If gender is apparent in one language, maintain that gender in all translations

#         ## **LANGUAGE-SPECIFIC REQUIREMENTS:**

#         **ARABIC TRANSLATION GUIDELINES:**
#         - Strictly observe Arabic grammatical gender (مذكر/مؤنث) in all terms, matching the gender in other languages
#         - Use correct feminine/masculine forms of adjectives and nouns (e.g., راقصات vs. راقصين)
#         - Use proper Arabic art history and museum terminology - not literal translations
#         - For religious terms: use the correct Islamic/Christian/Jewish terminology as appropriate
#         - For Western art movements: use established Arabic terms from museum catalogs
#         - For cultural items: use terminology recognized in Arab museum contexts
#         - Prefer formal Modern Standard Arabic (فصحى) terms used in prestigious Arab museums

#         **FRENCH TRANSLATION GUIDELINES:**
#         - Strictly maintain proper gender agreements (masculine/feminine) for all nouns and adjectives
#         - Use correct gender-specific terms (e.g., "danseuses" vs "danseurs") based on the subject
#         - Include proper French articles (le/la/les) that agree with the gender of the nouns
#         - Use proper French art history nomenclature as would appear in major museums
#         - For art movements: use the established French terms
#         - For historical periods: use French-specific period terminology
#         - Prefer terminology found in French museum catalogs over literal translations
#         - Pay attention to proper capitalization rules in French titles

#         ## **OUTPUT FORMAT:**

#         Return a JSON array with these fields for each artifact:
#         - Name_EN: Validated/completed English name
#         - Name_AR: Validated/completed Arabic name
#         - Name_FR: Validated/completed French name
#         - Name_validation: One of these values:
#           - "all_extracted": All names were extracted and consistent
#           - "fixed_[lang]": The [lang] name was fixed based on domain expertise
#           - "generated_[lang1]_[lang2]": The [lang1] and [lang2] names were generated

#         Return only these fields. Do not include other metadata fields.
#         """
    
#     return prompt


def cross_language_validation_prompt(artifacts_list):
    """Create a prompt for validating and completing multilingual artifact names."""
    
    # Format the artifacts list as JSON
    artifacts_json = json.dumps(artifacts_list, ensure_ascii=False, indent=2)
    
    prompt = f"""
        **MULTILINGUAL MUSEUM ARTIFACT NAME VALIDATION PROTOCOL**

        You are a trilingual museum expert with deep knowledge of art history terminology in English, Arabic, and French. Your task is to validate and complete all artifact names with proper cultural and domain accuracy.

        ## **THE ARTIFACT DATA TO PROCESS:**

        {artifacts_json}

        ### **VALIDATION PROCESS:**

        1. **REVIEW CONSISTENCY:**
        - If all three names exist and are consistent: leave them untouched
        - If two names agree but the third differs: correct the differing name using proper terminology
        - If all three differ significantly: use English name as the reference but ensure culturally appropriate translations

        2. **FILL MISSING NAMES:**
        - If one name is missing: generate it based on the other two languages using museum-standard terminology
        - If two names are missing: generate both from the single available name with cultural accuracy

        ## **GENDER AND LINGUISTIC AGREEMENT:**

        **CRITICAL REQUIREMENT:** Respect and maintain gender forms across all languages:
        - Example: "Javanese Dancers" (female) → Arabic: "راقصات جاويات" (feminine form) → French: "Danseuses javanaises" (feminine form)
        - Do NOT use masculine forms when referring to feminine subjects or vice versa
        - If gender is apparent in one language, maintain that gender in all translations

        ## **RELIGIOUS AND CULTURAL TERMINOLOGY:**
        
        **CRITICAL ATTENTION REQUIRED:** Pay special attention to religious terms:
        - For religious concepts: use the precise theological terminology in each language
        - Verify religious terms against how major museums actually label similar artifacts
        - Do not use generic terms when specific religious vocabulary exists
        - Ensure terminological accuracy for the specific religious tradition depicted
        - Research how museums in Arab countries translate religious art terminology
        
        ## **LANGUAGE-SPECIFIC REQUIREMENTS:**

        **ARABIC TRANSLATION GUIDELINES:**
        - Strictly observe Arabic grammatical gender (مذكر/مؤنث) in all terms, matching the gender in other languages
        - Use correct feminine/masculine forms of adjectives and nouns (e.g., راقصات vs. راقصين)
        - Use proper Arabic art history and museum terminology - not literal translations
        - For religious terms: use the correct Islamic/Christian/Jewish terminology as appropriate
        - For Western art movements: use established Arabic terms from museum catalogs
        - For cultural items: use terminology recognized in Arab museum contexts

        **FRENCH TRANSLATION GUIDELINES:**
        - Strictly maintain proper gender agreements (masculine/feminine) for all nouns and adjectives
        - Use correct gender-specific terms (e.g., "danseuses" vs "danseurs") based on the subject
        - Include proper French articles (le/la/les) that agree with the gender of the nouns
        - Use proper French art history nomenclature as would appear in major museums
        - For art movements: use the established French terms
        - For historical periods: use French-specific period terminology
        - Prefer terminology found in French museum catalogs over literal translations
        - Pay attention to proper capitalization rules in French titles

        ## **OUTPUT FORMAT:**

        Return a JSON array with ALL the original fields for each artifact, including:
        - Name_EN: Validated/completed English name
        - Name_AR: Validated/completed Arabic name  
        - Name_FR: Validated/completed French name
        - Name_validation: One of these values:
          - "all_extracted": All names were extracted and consistent
          - "fixed_[lang]": The [lang] name was fixed based on domain expertise
          - "generated_[lang1]_[lang2]": The [lang1] and [lang2] names were generated
        - Preserve ALL other metadata fields exactly as provided (Creator, Creation Date, Materials, Origin, Description, Category, source_page, source_document, etc.)

        IMPORTANT: Include all original metadata fields in your response. Do not remove any fields from the input data.
        """
    
    return prompt