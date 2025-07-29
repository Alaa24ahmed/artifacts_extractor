"""API interaction functions for calling vision and language models"""
import os
import base64
import requests
import logging
import re  # Added missing import
from pathlib import Path
from mistralai import Mistral

logger = logging.getLogger(__name__)

def encode_image_to_base64(image_path):
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def call_openai_api(image_path, prompt, model_name="gpt-4o"):
    """Call OpenAI's GPT-4 Vision API with the image and prompt."""
    try:
        import openai
        
        # Set API key from environment variable
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Create the messages with the image and prompt
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            }
        ]
        
        # Call the API with the selected model
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=4096
        )
        
        # Return response in a format compatible with our extraction function
        return {"content": [{"text": response.choices[0].message.content}]}
    
    except ImportError:
        logger.error("Error: OpenAI package not installed. Run 'pip install openai'")
        raise
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise

def call_openai_api_correction(image_path, raw_text, prompt_template, context, page_num, model_name="gpt-4o"):
    """Call OpenAI's GPT-4 Vision API for OCR correction with both image and raw text."""
    try:
        import openai
        
        # Set API key from environment variable
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Generate prompt with raw text
        prompt = prompt_template.format(
            page_number=page_num,
            context=context,
            raw_text=raw_text
        )
        
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Create the messages with both the image and text
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            }
        ]
        
        # Call the API with the selected model
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=4096
        )
        
        # Return response in a format compatible with our extraction function
        return {"content": [{"text": response.choices[0].message.content}]}
    
    except ImportError:
        logger.error("Error: OpenAI package not installed. Run 'pip install openai'")
        raise
    except Exception as e:
        logger.error(f"Error calling OpenAI API for correction: {e}")
        raise

def call_openai_api_text(text_content, prompt_template=None, model_name="gpt-4o"):
    """Call OpenAI's API with text-only prompt."""
    try:
        import openai
        
        # Set API key from environment variable
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Format the prompt if a template is provided
        if prompt_template:
            formatted_prompt = prompt_template.replace("{extracted_text}", text_content)
        else:
            formatted_prompt = text_content
        
        # Create the messages
        messages = [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]
        
        # Call the API with the selected model
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=4096
        )
        
        # Return response in a format compatible with our extraction function
        return {"content": [{"text": response.choices[0].message.content}]}
    
    except ImportError:
        logger.error("Error: OpenAI package not installed. Run 'pip install openai'")
        raise
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise

def call_gemini_api(image_path, prompt):
    """Call Gemini API with the image and prompt."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={os.getenv('GOOGLE_API_KEY')}"
    
    encoded_image = encode_image_to_base64(image_path)
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image
                    }
                }
            ]
        }]
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

def call_gemini_api_correction(image_path, raw_text, prompt_template, context, page_num):
    """Call Gemini API for OCR correction with both image and raw text."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={os.getenv('GOOGLE_API_KEY')}"
    
    # Generate prompt with raw text
    prompt = prompt_template.format(
        page_number=page_num,
        context=context,
        raw_text=raw_text
    )
    encoded_image = encode_image_to_base64(image_path)
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image
                    }
                }
            ]
        }]
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

def call_gemini_api_text(text_content, prompt_template=None):
    """Call Gemini API with text-only prompt."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={os.getenv('GOOGLE_API_KEY')}"
    
    # Format the prompt if a template is provided
    if prompt_template:
        formatted_prompt = prompt_template.replace("{extracted_text}", text_content)
    else:
        formatted_prompt = text_content
    
    payload = {
        "contents": [{
            "parts": [
                {"text": formatted_prompt}
            ]
        }]
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

# Add Mistral API initialization
def get_mistral_client():
    """Initialize and return a Mistral client."""
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    return Mistral(api_key=mistral_api_key)

def call_mistral_ocr(image_path):
    """Process a local PDF or image file using Mistral AI OCR."""
    logger.info(f"Processing with Mistral OCR: {image_path}")
    
    try:
        client = get_mistral_client()
        
        # Use file upload for all types - more reliable
        uploaded_file = client.files.upload(
            file={
                "file_name": os.path.basename(image_path),
                "content": open(image_path, "rb"),
            },
            purpose="ocr"
        )
        
        signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
        
        # Process the file via the signed URL
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url
            }
        )
        
        # Extract text from the response
        return extract_text_from_mistral_response(ocr_response)
        
    except Exception as e:
        logger.error(f"Error calling Mistral OCR API: {e}")
        raise

def extract_text_from_mistral_response(response):
    """Extract plain text from Mistral OCR response."""
    if not response:
        return ""
    
    # Get text from overall response
    text = response.text if hasattr(response, 'text') else ""
    
    # If no overall text but we have pages, combine their markdown
    if not text and hasattr(response, 'pages'):
        for page in response.pages:
            if hasattr(page, 'markdown'):
                # Clean markdown - remove images and formatting
                page_text = page.markdown
                # Remove markdown image syntax ![alt text](image.jpg)
                page_text = re.sub(r'!\[.*?\]\(.*?\)\n?', '', page_text)
                # Remove HTML img tags
                page_text = re.sub(r'<img[^>]*>', '', page_text)
                # Remove markdown formatting (bold, italic, etc.)
                page_text = re.sub(r'\*\*(.*?)\*\*', r'\1', page_text)
                page_text = re.sub(r'\*(.*?)\*', r'\1', page_text)
                page_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', page_text)
                page_text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', page_text, flags=re.MULTILINE)
                
                text += page_text + "\n\n"
    
    return text.strip()

def call_api_for_model(model, api_type, image_path=None, prompt=None, 
                       prompt_template=None, context=None, page_num=None, **kwargs):
    """Unified API call function that routes to the correct model and API type."""
    # Add support for Mistral OCR
    if model == "mistral-ocr" and api_type == "vision" and image_path:
        return {"content": [{"text": call_mistral_ocr(image_path)}]}
        
    elif api_type == "vision" and image_path:
        # Vision API calls (OCR)
        if model == "gemini":
            return call_gemini_api(image_path, prompt)
        elif model in ["gpt-4", "gpt-4o", "gpt-4o-mini"]:
            return call_openai_api(image_path, prompt, model_name=model)
    
    elif api_type == "correction" and image_path and prompt and prompt_template:
        # Correction API calls
        if model == "gemini":
            return call_gemini_api_correction(image_path, prompt, prompt_template, context, page_num)
        elif model in ["gpt-4", "gpt-4o", "gpt-4o-mini"]:
            return call_openai_api_correction(image_path, prompt, prompt_template, context, page_num, model_name=model)
    
    elif api_type == "text":
        # Text-only API calls
        if model == "gemini":
            return call_gemini_api_text(prompt, prompt_template)
        elif model in ["gpt-4", "gpt-4o", "gpt-4o-mini"]:
            return call_openai_api_text(prompt, prompt_template, model_name=model)
    
    raise ValueError(f"Invalid API call parameters: model={model}, api_type={api_type}")

def extract_content_from_response(response, model):
    """Extract the generated content from the model's response."""
    if model == "gemini":
        try:
            return response['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to extract content from Gemini response: {e}")
    
    elif model in ["gpt-4", "gpt-4o", "gpt-4o-mini", "mistral-ocr"]:  # Added mistral-ocr
        try:
            return response['content'][0]['text']
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to extract content from response: {e}")
    
    else:
        raise ValueError(f"Unsupported model: {model}")