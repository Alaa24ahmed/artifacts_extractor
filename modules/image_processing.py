"""Image processing functions for extracting content from PDFs and images"""
import os
import logging
from shutil import copy
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def extract_images_from_pdf(pdf_path, output_dir, start_page=1, end_page=None):
    """Extract images from PDF and save them to the output directory."""
    doc = fitz.open(pdf_path)
    
    # Handle page range
    total_pages = len(doc)
    start_page = max(1, min(start_page, total_pages))  # Ensure start page is valid (1-indexed)
    
    if end_page is None:
        end_page = total_pages
    else:
        end_page = max(start_page, min(end_page, total_pages))  # Ensure end page is valid
        
    logger.info(f"Processing PDF pages {start_page} to {end_page} (of {total_pages} total pages)")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    image_paths = []
    for page_num in range(start_page - 1, end_page):  # Convert to 0-indexed for PyMuPDF
        page = doc.load_page(page_num)
        # Higher resolution matrix (600 DPI instead of 300 DPI)
        pix = page.get_pixmap(matrix=fitz.Matrix(600/72, 600/72))
        image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(image_path)
        image_paths.append((image_path, page_num + 1))
    
    doc.close()  # Close the document to free resources
    return image_paths

def prepare_input_image(input_file, pages_dir):
    """Prepare a single image input file for processing."""
    dest_path = os.path.join(pages_dir, os.path.basename(input_file))
    if not os.path.exists(dest_path):
        copy(input_file, dest_path)
    return [(dest_path, 1)]  # Single image with page number 1