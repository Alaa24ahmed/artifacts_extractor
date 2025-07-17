"""Name validation functions for cross-language verification"""
import re
import json
import logging
from .api_calls import call_api_for_model, extract_content_from_response

logger = logging.getLogger(__name__)

def validate_and_complete_multilingual_names(artifacts, model, validation_prompt_func):
    """Cross-validate and complete multilingual artifact names."""
    if not artifacts:
        logger.warning("No artifacts to validate")
        return artifacts
        
    logger.info(f"Validating and completing multilingual names for {len(artifacts)} artifacts")
    
    # Generate the validation prompt
    validation_prompt = validation_prompt_func(artifacts)
    
    try:
        # Call the model
        validation_response = call_api_for_model(model, "text", prompt=validation_prompt)
        validation_text = extract_content_from_response(validation_response, model)
        
        # Parse the validated artifacts
        validated_artifacts = []
        try:
            # Extract JSON from the response
            code_blocks = re.findall(r'```(?:json)?\s*\n([\s\S]*?)\n\s*```', validation_text)
            if code_blocks:
                validated_artifacts = json.loads(code_blocks[0])
            else:
                # Try direct parsing
                validated_artifacts = json.loads(validation_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation result: {e}")
            return artifacts  # Return original artifacts on error
            
        logger.info(f"Successfully validated and completed {len(validated_artifacts)} artifact names")
        return validated_artifacts
    except Exception as e:
        logger.error(f"Error during name validation: {e}")
        return artifacts  # Return original artifacts on error