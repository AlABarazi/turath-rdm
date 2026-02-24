import os
from bs4 import BeautifulSoup
from flask import current_app
from typing import Optional

def extract_hocr_text(parent_id: str) -> Optional[str]:
    """
    Extract full text from HOCR files for a record (using parent_id for versioning).
    
    Args:
        parent_id: The parent record ID to locate HOCR directory
    
    Returns:
        Concatenated text from all HOCR files, or None if none found
    """
    hocr_mount_base = os.environ.get('HOCR_MOUNT_BASE', os.path.join(os.getcwd(), 'hocr_mount/books'))
    hocr_dir = os.path.join(hocr_mount_base, parent_id, 'hocr')
    
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
                    
                    # Extract text from ocrx_word elements (handles XML namespaces correctly)
                    words = soup.find_all(class_='ocrx_word')
                    page_text = ' '.join(w.get_text(strip=True) for w in words) if words else ''
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
