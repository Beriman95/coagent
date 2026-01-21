"""
CoAgent Admin API - Flask Backend
Manages SOPs, KB, and provides monitoring endpoints
"""

from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import json
import os
from datetime import datetime
from functools import wraps

# Load environment
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'coagent-admin-secret-key')
CORS(app)

# ChromaDB setup
CHROMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
embedding_fn = OpenAIEmbeddingFunction(
    api_key=os.environ.get('OPENAI_API_KEY'),
    model_name='text-embedding-3-small'
)

def get_collection():
    """Get ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection('rackhost_knowledge', embedding_function=embedding_fn)


def atomic_write_json(path, data):
    """
    Write JSON data to a file atomically.
    1. Write to .tmp file
    2. Flush and Sync to disk
    3. Rename (Atomic) to target file
    """
    tmp_path = path + '.tmp'
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e



# =============================================================================
# SLACK OAUTH (Simplified for now - can be enhanced)
# =============================================================================

ALLOWED_USERS = os.environ.get('ADMIN_ALLOWED_USERS', '').split(',')

def require_auth(f):
    """Simple auth decorator - check if user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# API ROUTES - SOPs
# =============================================================================

# =============================================================================
# API ROUTES - SOPs
# =============================================================================

SOP_PATHS = [
    os.path.join(os.path.dirname(__file__), '..', 'colleague_sops.json'),
    os.path.join(os.path.dirname(__file__), '..', 'new_technical_sops.json')
]

@app.route('/api/sops', methods=['GET'])
@require_auth
def get_all_sops():
    """Get all SOPs from JSON files."""
    try:
        all_sops = []
        
        def extract_fee(content):
            """Extract fee from content like '3.000 Ft' or 'nettó 5.000 Ft'"""
            if not isinstance(content, str):
                return None
            import re
            patterns = [
                r'(\d{1,3}(?:\.\d{3})*)\s*Ft',  # 3.000 Ft
                r'nettó\s+(\d{1,3}(?:\.\d{3})*)\s*Ft',  # nettó 3.000 Ft
            ]
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(0)
            return None

        for path in SOP_PATHS:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both list and dict wrapper formats
                    sops_list = data.get('sops', []) if isinstance(data, dict) else data
                    # Add source file info for updates
                    for sop in sops_list:
                        sop['source_file'] = path
                        # Normalize fields
                        if 'content' not in sop and 'steps' in sop:
                            sop['content'] = json.dumps(sop['steps'], ensure_ascii=False)
                        
                        sop['fee'] = extract_fee(sop.get('content', ''))
                    all_sops.extend(sops_list)
        
        return jsonify({'success': True, 'sops': all_sops, 'count': len(all_sops)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sops/<sop_id>', methods=['GET'])
@require_auth
def get_sop(sop_id):
    """Get single SOP by ID."""
    try:
        found_sop = None
        for path in SOP_PATHS:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sops_list = data.get('sops', []) if isinstance(data, dict) else data
                    
                    for sop in sops_list:
                        if sop.get('id') == sop_id:
                            found_sop = sop
                            break
            if found_sop:
                break
        
        if not found_sop:
            return jsonify({'success': False, 'error': 'SOP not found'}), 404
        
        return jsonify({'success': True, 'sop': found_sop})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sops/<sop_id>', methods=['PUT'])
@require_auth
def update_sop(sop_id):
    """Update SOP in JSON file."""
    try:
        updated_data = request.json
        target_file = None
        
        # Find which file contains the SOP
        for path in SOP_PATHS:
            if not os.path.exists(path):
                continue
                
            with open(path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            sops_list = file_data.get('sops', []) if isinstance(file_data, dict) else file_data
            
            for i, sop in enumerate(sops_list):
                if sop.get('id') == sop_id:
                    # Found it! Update fields
                    sops_list[i].update(updated_data)
                    target_file = path
                    
                    # Save back to file using wrapper or list
                    if isinstance(file_data, dict):
                        file_data['sops'] = sops_list
                        save_data = file_data
                    else:
                        save_data = sops_list
                        
                    atomic_write_json(path, save_data)
                    break
            
            if target_file:
                break
        
        if not target_file:
             return jsonify({'success': False, 'error': 'SOP not found to update'}), 404
             
        return jsonify({'success': True, 'message': 'SOP updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sops', methods=['POST'])
@require_auth
def create_sop():
    """Create new SOP in new_technical_sops.json."""
    try:
        new_sop = request.json
        # Generate ID if missing
        if 'id' not in new_sop:
            new_sop['id'] = f"sop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        target_path = SOP_PATHS[1] # Default to technical sops
        
        if os.path.exists(target_path):
            with open(target_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
        else:
            file_data = {'sops': []}
            
        if isinstance(file_data, dict):
            file_data.setdefault('sops', []).append(new_sop)
            save_data = file_data
        else:
            file_data.append(new_sop)
            save_data = file_data
            
        atomic_write_json(target_path, save_data)
        
        return jsonify({'success': True, 'id': new_sop['id'], 'message': 'SOP created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sops/<sop_id>', methods=['DELETE'])
@require_auth
def delete_sop(sop_id):
    """Delete SOP from JSON file."""
    try:
        deleted = False
        for path in SOP_PATHS:
            if not os.path.exists(path):
                continue
                
            with open(path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            sops_list = file_data.get('sops', []) if isinstance(file_data, dict) else file_data
            original_len = len(sops_list)
            
            # Filter out the SOP
            new_list = [s for s in sops_list if s.get('id') != sop_id]
            
            if len(new_list) < original_len:
                deleted = True
                if isinstance(file_data, dict):
                    file_data['sops'] = new_list
                    save_data = file_data
                else:
                    save_data = new_list
                
                atomic_write_json(path, save_data)
                break
        
        if not deleted:
            return jsonify({'success': False, 'error': 'SOP not found'}), 404
            
        return jsonify({'success': True, 'message': 'SOP deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# API ROUTES - KB Articles
# =============================================================================

@app.route('/api/kb', methods=['GET'])
@require_auth
def get_all_kb():
    """Get KB articles from kb_chunks.json file."""
    try:
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'kb_chunks.json')
        
        if not os.path.exists(kb_path):
            return jsonify({'success': True, 'articles': [], 'count': 0, 'message': 'kb_chunks.json not found'})
        
        with open(kb_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        def extract_category(url):
            """Extract category from URL like /tudasbazis/domain/..."""
            if '/tudasbazis/' in url:
                parts = url.split('/tudasbazis/')
                if len(parts) > 1:
                    cat = parts[1].split('/')[0] if '/' in parts[1] else parts[1]
                    return cat if cat else 'altalanos'
            return 'altalanos'
        
        # Group by title to get unique articles (not individual chunks)
        articles_by_title = {}
        for chunk in chunks:
            title = chunk.get('title', 'N/A')
            url = chunk.get('url', '')
            if title not in articles_by_title:
                articles_by_title[title] = {
                    'id': chunk.get('id', ''),
                    'title': title,
                    'url': url,
                    'category': extract_category(url),
                    'source': chunk.get('source', 'rackhost.hu'),
                    'chunks': 1
                }
            else:
                articles_by_title[title]['chunks'] += 1
        
        articles = list(articles_by_title.values())
        
        return jsonify({'success': True, 'articles': articles, 'count': len(articles)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/kb/article/<path:title>', methods=['GET'])
@require_auth
def get_kb_article(title):
    """Get all chunks for a specific article by title."""
    try:
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'kb_chunks.json')
        
        if not os.path.exists(kb_path):
            return jsonify({'success': False, 'error': 'kb_chunks.json not found'}), 404
        
        with open(kb_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        # Find all chunks for this title (URL decoded)
        from urllib.parse import unquote
        decoded_title = unquote(title)
        article_chunks = [c for c in chunks if c.get('title', '') == decoded_title]
        
        if not article_chunks:
            return jsonify({'success': False, 'error': 'Article not found'}), 404
        
        # Sort by chunk_index
        article_chunks.sort(key=lambda x: x.get('chunk_index', 0))
        
        return jsonify({
            'success': True,
            'title': decoded_title,
            'url': article_chunks[0].get('url', ''),
            'chunks': article_chunks,
            'total_chunks': len(article_chunks)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/kb/sync', methods=['POST'])
@require_auth
def sync_kb():
    """Trigger KB sync (re-scrape rackhost.hu/tudasbazis). Runs in subprocess for security."""
    import subprocess
    import threading
    
    try:
        # Use full_sync_kb.py instead of just scraper to ensure DB update
        sync_script = os.path.join(os.path.dirname(__file__), '..', 'full_sync_kb.py')
        
        if not os.path.exists(sync_script):
            return jsonify({'success': False, 'error': 'full_sync_kb.py not found'}), 404
        
        status_path = os.path.join(os.path.dirname(__file__), '..', 'scrape_status.json')
        
        def run_scraper():
            try:
                with open(status_path, 'w') as f:
                    json.dump({'status': 'running', 'started': datetime.now().isoformat()}, f)
                
                # Run the full pipeline
                result = subprocess.run(
                    ['python3', sync_script],
                    capture_output=True, text=True, timeout=900,  # Increased timeout to 15 min
                    cwd=os.path.dirname(sync_script)
                )
                
                with open(status_path, 'w') as f:
                    json.dump({
                        'status': 'completed' if result.returncode == 0 else 'error',
                        'finished': datetime.now().isoformat(),
                        'returncode': result.returncode
                    }, f)
            except subprocess.TimeoutExpired:
                with open(status_path, 'w') as f:
                    json.dump({'status': 'timeout', 'finished': datetime.now().isoformat()}, f)
            except Exception as e:
                with open(status_path, 'w') as f:
                    json.dump({'status': 'error', 'error': str(e)}, f)
        
        thread = threading.Thread(target=run_scraper, daemon=True)
        thread.start()
        
        return jsonify({'success': True, 'message': 'Sync started. This may take several minutes.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/kb/sync/status', methods=['GET'])
@require_auth
def get_sync_status():
    """Get current KB sync status."""
    try:
        status_path = os.path.join(os.path.dirname(__file__), '..', 'scrape_status.json')
        if not os.path.exists(status_path):
            return jsonify({'success': True, 'status': 'idle'})
        with open(status_path, 'r') as f:
            status = json.load(f)
        return jsonify({'success': True, **status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# API ROUTES - Monitoring

# =============================================================================

@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    """Get monitoring statistics."""
    try:
        # Load query log
        log_path = os.path.join(os.path.dirname(__file__), '..', 'query_log.json')
        logs = []
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                logs = json.load(f)
        
        # Date filter
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        if date_from:
            logs = [l for l in logs if l.get('timestamp', '') >= date_from]
        if date_to:
            # Add end of day to include all entries from that day
            date_to_full = date_to + "T23:59:59" if "T" not in date_to else date_to
            logs = [l for l in logs if l.get('timestamp', '') <= date_to_full]
        
        # Calculate stats
        total_queries = len(logs)
        
        # Category distribution
        categories = {}
        for log in logs:
            cat = log.get('category', '') or 'Ismeretlen'
            if cat == '':
                cat = 'Ismeretlen'
            categories[cat] = categories.get(cat, 0) + 1
        
        # Response times (if logged)
        response_times = []
        for l in logs:
            if 'response_time_ms' in l:
                response_times.append(l['response_time_ms'] / 1000)
            elif 'response_time' in l:
                response_times.append(l['response_time'])
                
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_queries': total_queries,
                'categories': categories,
                'avg_response_time': round(avg_response_time, 2),
                'period': {'from': date_from, 'to': date_to}
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# API ROUTES - Fees
# =============================================================================

FEES_PATH = os.path.join(os.path.dirname(__file__), '..', 'fees.json')

@app.route('/api/fees', methods=['GET'])
@require_auth
def get_all_fees():
    """Get all fees from fees.json."""
    try:
        if not os.path.exists(FEES_PATH):
            return jsonify({'success': True, 'fees': [], 'count': 0})
        
        with open(FEES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({'success': True, 'fees': data.get('fees', []), 'count': len(data.get('fees', []))})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fees/<fee_id>', methods=['PUT'])
@require_auth
def update_fee(fee_id):
    """Update a fee."""
    try:
        with open(FEES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, fee in enumerate(data.get('fees', [])):
            if fee['id'] == fee_id:
                data['fees'][i].update(request.json)
                data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                break
        
        atomic_write_json(FEES_PATH, data)
        
        return jsonify({'success': True, 'message': 'Fee updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fees', methods=['POST'])
@require_auth
def create_fee():
    """Create new fee."""
    try:
        with open(FEES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        new_fee = request.json
        new_fee['id'] = f"fee_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        data['fees'].append(new_fee)
        data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        atomic_write_json(FEES_PATH, data)
        
        return jsonify({'success': True, 'id': new_fee['id'], 'message': 'Fee created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fees/<fee_id>', methods=['DELETE'])
@require_auth
def delete_fee(fee_id):
    """Delete fee."""
    try:
        with open(FEES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['fees'] = [f for f in data.get('fees', []) if f['id'] != fee_id]
        data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        atomic_write_json(FEES_PATH, data)
        
        return jsonify({'success': True, 'message': 'Fee deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# API ROUTES - Rules
# =============================================================================

RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'rules.json')

@app.route('/api/rules', methods=['GET'])
@require_auth
def get_all_rules():
    """Get all rules from rules.json."""
    try:
        if not os.path.exists(RULES_PATH):
            return jsonify({'success': True, 'rules': [], 'count': 0})
        
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({'success': True, 'rules': data.get('rules', []), 'count': len(data.get('rules', []))})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rules/<rule_id>', methods=['PUT'])
@require_auth
def update_rule(rule_id):
    """Update a rule."""
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, rule in enumerate(data.get('rules', [])):
            if rule['id'] == rule_id:
                data['rules'][i].update(request.json)
                data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                break
        
        atomic_write_json(RULES_PATH, data)
        
        return jsonify({'success': True, 'message': 'Rule updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rules', methods=['POST'])
@require_auth
def create_rule():
    """Create new rule."""
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        new_rule = request.json
        new_rule['id'] = f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        data['rules'].append(new_rule)
        data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        atomic_write_json(RULES_PATH, data)
        
        return jsonify({'success': True, 'id': new_rule['id'], 'message': 'Rule created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rules/<rule_id>', methods=['DELETE'])
@require_auth
def delete_rule(rule_id):
    """Delete rule."""
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['rules'] = [r for r in data.get('rules', []) if r['id'] != rule_id]
        data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        atomic_write_json(RULES_PATH, data)
        
        return jsonify({'success': True, 'message': 'Rule deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# WEB ROUTES
# =============================================================================

@app.route('/')
@require_auth
def index():
    """Main admin dashboard."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login page."""
    if request.method == 'POST':
        # For now, simple password auth
        # TODO: Implement Slack OAuth
        password = request.form.get('password')
        if password == os.environ.get('ADMIN_PASSWORD', 'rackhost2026'):
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Hibás jelszó')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout."""
    session.pop('logged_in', None)
    return redirect(url_for('login'))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=5001)
