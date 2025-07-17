#!/usr/bin/env python3
"""Configuration settings for multilingual museum artifact extraction"""
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Memory optimization - set expandable segments
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Base directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Default model
SELECTED_MODEL = "gpt-4o"

# Default document paths
EN_DOCUMENT_PATH = os.path.join(SCRIPT_DIR, "data_multilin", "LAD_Orsay_ENG_BAT_final.pdf")
AR_DOCUMENT_PATH = os.path.join(SCRIPT_DIR, "data_multilin", "LAD_Orsay_AR_final_BAT.pdf")
FR_DOCUMENT_PATH = os.path.join(SCRIPT_DIR, "data_multilin", "LAD_Orsay_FR_BAT_final.pdf")

# Language-specific correction thresholds
CORRECTION_THRESHOLDS = {
    "EN": 0.05,  # English - baseline
    "FR": 0.07,  # French - slightly higher to account for diacritics
    "AR": 0.10   # Arabic - higher due to complex script characteristics
}

# CSV field mapping for multilingual output
MULTILINGUAL_CSV_FIELDS = [
    "Name_EN", "Name_AR", "Name_FR", "Creator", "Creation Date", 
    "Materials", "Origin", "Description", "Category", 
    "source_page", "source_document", "Name_validation"
]