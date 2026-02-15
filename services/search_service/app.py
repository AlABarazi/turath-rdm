
import os
import logging
import glob
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from bs4 import BeautifulSoup

import concurrent.futures
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
HOCR_BASE_DIR = os.environ.get('HOCR_BASE_DIR', '/hocr_mount/books')
SEARCH_SERVICE_BASE_URL = os.environ.get('SEARCH_SERVICE_BASE_URL', 'https://127.0.0.1:5001')
IIIF_SERVER_BASE_URL = os.environ.get('IIIF_SERVER_BASE_URL', 'https://127.0.0.1:5000')
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))

def get_hocr_files(record_pid):
    """Get sorted list of HOCR files for a record."""
    record_dir = os.path.join(HOCR_BASE_DIR, record_pid, 'hocr')
    if not os.path.exists(record_dir):
        return []
    
    files = glob.glob(os.path.join(record_dir, '*.hocr'))
    # Sort by filename (assuming 001.hocr, 002.hocr, etc.)
    files.sort()
    return files

def parse_hocr_file_wrapper(args):
    """Wrapper for parse_hocr_file to be used with ProcessPoolExecutor."""
    return parse_hocr_file(*args)

def parse_hocr_file(file_path, page_index, query):
    """Parse a single HOCR file and find matches (supporting phrases)."""
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
            
        # Find all words
        words = soup.find_all('span', class_='ocrx_word')
        if not words:
            return []

        # 1. Build Full Text & Map
        full_text = ""
        word_map = [] 
        
        for w in words:
            text = w.get_text().strip()
            if not text:
                continue
            
            # Parse bbox
            title = w.get('title', '')
            bbox_coords = None # (x1, y1, x2, y2)
            
            if 'bbox' in title:
                parts = title.split(';')
                for part in parts:
                    if 'bbox' in part:
                        try:
                            coords = part.replace('bbox', '').strip().split()
                            if len(coords) == 4:
                                bbox_coords = tuple(map(int, coords))
                                break
                        except ValueError:
                            pass
            
            if bbox_coords:
                start = len(full_text)
                full_text += text + " " # Add space
                end = len(full_text) - 1 # Index of last char of word
                
                word_map.append({
                    'start': start, 
                    'end': end, 
                    'bbox': bbox_coords,
                    'text': text
                })

        # 2. Search for query in full text
        if not query or not full_text:
            return []

        # Case-insensitive search
        for m in re.finditer(re.escape(query), full_text, re.IGNORECASE):
            match_start, match_end = m.span()
            matched_text = m.group()
            
            # 3. Find overlapping words
            # A word is part of the match if it overlaps with the match range
            covered_words = [w for w in word_map if w['end'] >= match_start and w['start'] < match_end]
            
            if covered_words:
                # Calculate union bbox
                min_x1 = min(w['bbox'][0] for w in covered_words)
                min_y1 = min(w['bbox'][1] for w in covered_words)
                max_x2 = max(w['bbox'][2] for w in covered_words)
                max_y2 = max(w['bbox'][3] for w in covered_words)
                
                w_final = max_x2 - min_x1
                h_final = max_y2 - min_y1
                bbox_str = f"{min_x1},{min_y1},{w_final},{h_final}"
                
                # Context (surrounding text)
                context_start = max(0, match_start - 30)
                context_end = min(len(full_text), match_end + 30)
                
                prefix = "..." if context_start > 0 else ""
                suffix = "..." if context_end < len(full_text) else ""
                
                text_before = full_text[context_start:match_start]
                text_after = full_text[match_end:context_end]
                
                context_html = f"{prefix}{text_before}<span class='highlight'>{matched_text}</span>{text_after}{suffix}"

                matches.append({
                    'text': matched_text,
                    'context': context_html,
                    'bbox': bbox_str,
                    'page': page_index + 1
                })
                    
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        
    return matches

def parse_hocr_words(file_path):
    """Extract all words with bounding boxes from HOCR file."""
    words_data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
            
        # Find all words
        words = soup.find_all('span', class_='ocrx_word')
        
        for word in words:
            text = word.get_text().strip()
            if not text:
                continue
                
            # Get bounding box
            title = word.get('title', '')
            bbox = None
            if 'bbox' in title:
                parts = title.split(';')
                for part in parts:
                    if 'bbox' in part:
                        coords = part.replace('bbox', '').strip().split()
                        if len(coords) == 4:
                            x1, y1, x2, y2 = map(int, coords)
                            w = x2 - x1
                            h = y2 - y1
                            bbox = f"{x1},{y1},{w},{h}"
                            break
            
            if bbox:
                words_data.append({
                    'text': text,
                    'bbox': bbox
                })
    except Exception as e:
        logger.error(f"Error parsing words from {file_path}: {e}")
        
    return words_data

@app.route('/annotations/<record_pid>/<page_id>', methods=['GET'])
def annotations(record_pid, page_id):
    """IIIF Annotation List API endpoint (for text overlay)."""
    # page_id format expected: p001, p002, etc.
    try:
        # Extract page number from pXXX
        page_num_str = page_id.replace('p', '')
        # Filename format: 001.hocr
        filename = f"{page_num_str}.hocr"
    except:
        abort(400, "Invalid page_id format. Expected pXXX (e.g., p001)")

    file_path = os.path.join(HOCR_BASE_DIR, record_pid, 'hocr', filename)
    logger.info(f"Looking for annotation file: {file_path}")
    
    if not os.path.exists(file_path):
        # Try finding file without zero padding if strict match failed
        logger.warning(f"File not found at {file_path}. Checking directory content...")
        try:
            dir_path = os.path.join(HOCR_BASE_DIR, record_pid, 'hocr')
            if os.path.exists(dir_path):
                logger.info(f"Directory content: {os.listdir(dir_path)}")
        except:
            pass
        abort(404, f"Page HOCR file not found: {filename}")

    words = parse_hocr_words(file_path)
    
    resources = []
    canvas_id = f"{IIIF_SERVER_BASE_URL}/records/{record_pid}/canvas/{page_id}"
    
    for i, word in enumerate(words):
        annotation_id = f"{SEARCH_SERVICE_BASE_URL}/annotations/{record_pid}/{page_id}/{i}"
        resources.append({
            "@id": annotation_id,
            "@type": "oa:Annotation",
            "motivation": "sc:painting",
            "resource": {
                "@type": "cnt:ContentAsText",
                "chars": word['text'],
                "format": "text/plain"
            },
            "on": f"{canvas_id}#xywh={word['bbox']}"
        })

    return jsonify({
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@id": f"{SEARCH_SERVICE_BASE_URL}/annotations/{record_pid}/{page_id}",
        "@type": "sc:AnnotationList",
        "resources": resources
    })

@app.route('/search/<record_pid>', methods=['GET'])
def search(record_pid):
    """IIIF Search API v1 endpoint."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({
            "@context": "http://iiif.io/api/search/1/context.json",
            "@id": f"{SEARCH_SERVICE_BASE_URL}/search/{record_pid}",
            "@type": "sc:AnnotationList",
            "resources": [],
            "hits": []
        })

    hocr_files = get_hocr_files(record_pid)
    if not hocr_files:
        # Return empty result if no files found (don't 404, just no results)
        logger.warning(f"No HOCR files found for {record_pid}")
        return jsonify({
            "@context": "http://iiif.io/api/search/1/context.json",
            "@id": f"{SEARCH_SERVICE_BASE_URL}/search/{record_pid}?q={query}",
            "@type": "sc:AnnotationList",
            "resources": [],
            "hits": []
        })

    all_matches = []
    
    # Search in files in parallel
    # Prepare arguments for each file: (file_path, index, query)
    search_args = [(f, i, query) for i, f in enumerate(hocr_files)]
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Use map to process files in parallel while maintaining order roughly
        # map returns an iterator of results
        results = executor.map(parse_hocr_file_wrapper, search_args)
        
        for file_matches in results:
            all_matches.extend(file_matches)
        
    # Construct IIIF response
    resources = []
    hits = []
    
    for i, match in enumerate(all_matches):
        page_num = match['page']
        # Format: p001, p002, etc. to match InvenioRDM canvas IDs
        canvas_id = f"{IIIF_SERVER_BASE_URL}/records/{record_pid}/canvas/p{page_num:03d}"
        annotation_id = f"{SEARCH_SERVICE_BASE_URL}/annotations/{record_pid}/{page_num}/{i}"
        
        # Annotation (the box on the image)
        resources.append({
            "@id": annotation_id,
            "@type": "oa:Annotation",
            "motivation": "sc:painting",
            "resource": {
                "@type": "cnt:ContentAsText",
                "chars": match['text']
            },
            "on": f"{canvas_id}#xywh={match['bbox']}"
        })
        
        # Hit (the search result in the sidebar)
        hits.append({
            "@type": "search:Hit",
            "annotations": [annotation_id],
            "match": match['text'],
            "before": match['context'].split("<span")[0],
            "after": match['context'].split("</span>")[1],
            "isMatching": True
        })

    return jsonify({
        "@context": "http://iiif.io/api/search/1/context.json",
        "@id": f"{SEARCH_SERVICE_BASE_URL}/search/{record_pid}?q={query}",
        "@type": "sc:AnnotationList",
        "resources": resources,
        "hits": hits
    })

@app.route('/autocomplete/<record_pid>', methods=['GET'])
def autocomplete(record_pid):
    """IIIF Autocomplete API v1 endpoint."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({
            "@context": "http://iiif.io/api/search/1/context.json",
            "@id": f"{SEARCH_SERVICE_BASE_URL}/autocomplete/{record_pid}",
            "@type": "search:TermList",
            "terms": []
        })
        
    # Basic implementation: just return the query as a suggestion if it's found
    # Real implementation would need an index or Trie for efficient prefix search
    
    hocr_files = get_hocr_files(record_pid)
    terms = []
    seen_terms = set()
    
    # Limit files to search for autocomplete performance
    # Just check first few files for now
    for file_path in hocr_files[:5]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'lxml')
                words = soup.find_all('span', class_='ocrx_word')
                for word in words:
                    text = word.get_text().strip()
                    if text.lower().startswith(query.lower()) and text not in seen_terms:
                        seen_terms.add(text)
                        terms.append({
                            "match": text,
                            "url": f"{SEARCH_SERVICE_BASE_URL}/search/{record_pid}?q={text}",
                            "count": 1 # Placeholder count
                        })
                        if len(terms) >= 10: # Limit suggestions
                            break
        except:
            continue
            
        if len(terms) >= 10:
            break
            
    return jsonify({
        "@context": "http://iiif.io/api/search/1/context.json",
        "@id": f"{SEARCH_SERVICE_BASE_URL}/autocomplete/{record_pid}?q={query}",
        "@type": "search:TermList",
        "terms": terms
    })

@app.route('/')
def health():
    return jsonify({"status": "ok", "service": "IIIF Search Service"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
