import os
from bs4 import BeautifulSoup
from flask import current_app

def extract_hocr_text(record_pid):
    """
    Extract full text from HOCR files for a given record PID.
    Returns a single string containing all text from all pages.
    """
    # Locate HOCR directory
    # Default to relative 'hocr_mount' if config not set, matching signals.py logic
    base_path = current_app.config.get('HOCR_MOUNT_PATH', os.path.abspath('hocr_mount'))
    hocr_dir = os.path.join(base_path, 'books', record_pid, 'hocr')
    
    if not os.path.exists(hocr_dir):
        current_app.logger.warning(f"Fulltext extraction: HOCR dir not found at {hocr_dir}")
        return None
        
    text_content = []
    
    try:
        # Sort files to ensure page order (001.hocr, 002.hocr)
        files = sorted([f for f in os.listdir(hocr_dir) if f.endswith('.hocr')])
        
        if not files:
            return None

        current_app.logger.info(f"Extracting text from {len(files)} HOCR files for {record_pid}")

        for filename in files:
            file_path = os.path.join(hocr_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Use lxml for speed if available, else html.parser
                    # We try-except the parser choice if needed, but lxml is standard in our envs
                    soup = BeautifulSoup(f, 'lxml')
                    
                    # Extract text, stripping tags but keeping spaces
                    # We add a newline after each page to separate them
                    page_text = soup.get_text(' ', strip=True)
                    text_content.append(page_text)
            except Exception as e:
                current_app.logger.error(f"Failed to parse HOCR file {file_path}: {e}")
                continue
                
    except Exception as e:
        current_app.logger.error(f"Error accessing HOCR directory {hocr_dir}: {e}")
        return None
            
    return "\n".join(text_content)
