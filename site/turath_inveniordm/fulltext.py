import os
from bs4 import BeautifulSoup
from flask import current_app

def extract_hocr_text(parent_id):
    """
    Extract full text from HOCR files for a given parent ID.
    Returns a single string containing all text from all pages.
    """
    # Locate HOCR directory (keep in sync with signals.py HOCR_MOUNT_BASE)
    base_path = os.environ.get(
        'HOCR_MOUNT_BASE',
        current_app.config.get('HOCR_MOUNT_PATH', os.path.abspath('hocr_mount')),
    )
    hocr_dir = os.path.join(base_path, parent_id, 'hocr')
    
    if not os.path.exists(hocr_dir):
        current_app.logger.warning(f"Fulltext extraction: HOCR dir not found at {hocr_dir}")
        return None
        
    text_content = []
    
    try:
        # Sort files to ensure page order (001.hocr, 002.hocr)
        files = sorted([f for f in os.listdir(hocr_dir) if f.endswith('.hocr')])
        
        if not files:
            return None

        current_app.logger.info(f"Extracting text from {len(files)} HOCR files for parent {parent_id}")

        for filename in files:
            file_path = os.path.join(hocr_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Use html.parser (built-in, always available)
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract text, stripping tags but keeping spaces
                    # We add a newline after each page to separate them
                    page_text = soup.get_text(' ', strip=True)
                    if page_text:
                        text_content.append(page_text)
                        current_app.logger.debug(f"Extracted {len(page_text)} chars from {filename}")
                    else:
                        current_app.logger.warning(f"No text in {filename}")
            except Exception as e:
                current_app.logger.error(f"Failed to parse HOCR file {file_path}: {e}")
                continue
                
    except Exception as e:
        current_app.logger.error(f"Error accessing HOCR directory {hocr_dir}: {e}")
        return None
            
    return "\n".join(text_content)
