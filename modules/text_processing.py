"""Text processing functions for similarity calculation and parsing structured data"""
import re
import json
import logging

logger = logging.getLogger(__name__)

def calculate_text_difference(text1, text2):
    """
    Calculate similarity between texts using character-level Levenshtein distance.
    Returns a score between 0 and 1, where:
    - 0 means texts are identical
    - 1 means texts are completely different
    
    This metric is more sensitive to small edits and works well across different languages.
    """
    # If both texts are empty, they're identical
    if not text1 and not text2:
        return 0
    
    # If one text is empty and the other isn't, they're completely different
    if not text1 or not text2:
        return 1
    
    # Initialize the Levenshtein distance matrix
    len1, len2 = len(text1), len(text2)
    dp = [[0 for _ in range(len2 + 1)] for _ in range(len1 + 1)]
    
    # Base cases: transforming to/from empty string
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
    
    # Fill the matrix
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if text1[i-1] == text2[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      # deletion
                dp[i][j-1] + 1,      # insertion
                dp[i-1][j-1] + cost  # substitution
            )
    
    # Calculate the Levenshtein distance
    edit_distance = dp[len1][len2]
    
    # Normalize by the length of the longer text to get a score between 0 and 1
    max_length = max(len1, len2)
    if max_length == 0:
        return 0  # Both strings are empty
    
    normalized_distance = edit_distance / max_length
    
    return normalized_distance

def parse_artifacts_from_text(text, page_num, document_name):
    """Parse JSON artifacts from model response text with robust error handling."""
    # First, check for explicit "no artifacts" indicator
    if "NO_ARTIFACTS_MENTIONED" in text or "NO_ARTIFACTS_DETECTED" in text:
        logger.info(f"No artifacts mentioned on page {page_num}")
        return []
    
    # Extract code blocks if present
    code_blocks = re.findall(r'```(?:json)?\s*\n([\s\S]*?)\n\s*```', text)
    
    if code_blocks:
        cleaned_text = code_blocks[0]
    else:
        cleaned_text = text
    
    # Try several JSON extraction methods
    try:
        # Method 1: Direct JSON parsing of the entire text
        try:
            # Check if the entire text is valid JSON
            parsed_json = json.loads(cleaned_text)
            if isinstance(parsed_json, list):
                for artifact in parsed_json:
                    artifact["source_page"] = page_num
                    artifact["source_document"] = document_name
                return parsed_json
            elif isinstance(parsed_json, dict):
                parsed_json["source_page"] = page_num
                parsed_json["source_document"] = document_name
                return [parsed_json]
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract array with regex
        array_match = re.search(r'\[([\s\S]*)\]', cleaned_text)
        if array_match:
            try:
                array_text = '[' + array_match.group(1) + ']'
                # Try to fix common JSON formatting issues
                array_text = array_text.replace('"\n', '",\n')
                array_text = re.sub(r',(\s*[\]}])', r'\1', array_text)  # Remove trailing commas
                
                parsed_json = json.loads(array_text)
                for artifact in parsed_json:
                    artifact["source_page"] = page_num
                    artifact["source_document"] = document_name
                return parsed_json
            except json.JSONDecodeError:
                pass
        
        # Method 3: Extract individual objects
        object_matches = re.findall(r'{\s*"[^}]*}', cleaned_text)
        if object_matches:
            result = []
            for obj_text in object_matches:
                try:
                    # Add missing comma to end of string values if needed
                    fixed_obj = re.sub(r'"([^"]*)"(\s*")', r'"\1",\2', obj_text)
                    # Remove trailing commas
                    fixed_obj = re.sub(r',(\s*})', r'\1', fixed_obj)
                    
                    obj = json.loads(fixed_obj)
                    obj["source_page"] = page_num
                    obj["source_document"] = document_name
                    result.append(obj)
                except json.JSONDecodeError:
                    continue
            
            if result:
                return result
        
        # If we get here, check if the text actually mentions "no artifacts"
        no_artifact_indicators = ["no artifacts", "no artifact", "not mentioning any artifacts", 
                                 "does not mention any artifacts", "no museum artifacts"]
        
        for indicator in no_artifact_indicators:
            if indicator.lower() in cleaned_text.lower():
                logger.info(f"No artifacts mentioned on page {page_num} (from text)")
                return []
            
        # Last resort: we couldn't parse valid artifacts
        logger.warning(f"Failed to parse any valid artifacts from page {page_num}")
        return [{
            "error": "Failed to parse JSON response",
            "raw_text": text[:300] + ("..." if len(text) > 300 else ""),
            "source_page": page_num,
            "source_document": document_name,
        }]
            
    except Exception as e:
        logger.warning(f"Error during JSON extraction on page {page_num}: {str(e)}")
        return [{
            "error": f"JSON processing error: {str(e)}",
            "raw_text": text[:300] + ("..." if len(text) > 300 else ""),
            "source_page": page_num,
            "source_document": document_name,
        }]

def parse_multilingual_names(text, artifacts_en, page_num, document_name):
    """Parse multilingual artifact names from model response."""
    # Extract code blocks if present
    code_blocks = re.findall(r'```(?:json)?\s*\n([\s\S]*?)\n\s*```', text)
    
    if code_blocks:
        cleaned_text = code_blocks[0]
    else:
        cleaned_text = text
    
    try:
        # Try to parse the JSON response
        parsed_json = None
        try:
            parsed_json = json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Try to extract array with regex
            array_match = re.search(r'\[([\s\S]*)\]', cleaned_text)
            if array_match:
                array_text = '[' + array_match.group(1) + ']'
                # Try to fix common JSON formatting issues
                array_text = array_text.replace('"\n', '",\n')
                array_text = re.sub(r',(\s*[\]}])', r'\1', array_text)  # Remove trailing commas
                parsed_json = json.loads(array_text)
        
        if not parsed_json:
            logger.warning(f"Failed to parse multilingual names for page {page_num}")
            return []
        
        # Check if we have a list
        if not isinstance(parsed_json, list):
            parsed_json = [parsed_json]
        
        return parsed_json
    except Exception as e:
        logger.warning(f"Error parsing multilingual names for page {page_num}: {e}")
        return []