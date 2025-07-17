# Multilingual Museum Artifact Extractor

A specialized system for extracting artifact information from multilingual museum catalogs and documents. This tool processes documents in English, Arabic, and French, extracting detailed artifact metadata and aligning names across languages.

## Features

- **Multilingual Support**: Process documents in English, Arabic, and French
- **OCR with Correction**: Uses advanced OCR with adaptive correction for accurate text extraction
- **AI-Powered Extraction**: Leverages AI models to identify and extract artifact information
- **Cross-Language Alignment**: Aligns artifact names across different language versions
- **Flexible Model Selection**: Choose between different AI models (Mistral OCR, GPT-4o, Gemini)

## Project Structure

- `modules/`: Core processing modules
  - `api_calls.py`: API interaction with AI services
  - `correction.py`: OCR text correction algorithms
  - `data_utils.py`: Data handling utilities
  - `extraction.py`: Artifact extraction logic
  - `image_processing.py`: Image preparation and processing
  - `processors.py`: Main document processing pipelines
  - `text_processing.py`: Text analysis and processing
  - `validation.py`: Cross-language validation

- `prompts/`: AI prompt templates
- `config.py`: Configuration settings
- `main.py`: Command line interface
