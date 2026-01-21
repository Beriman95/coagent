#!/usr/bin/env python3
"""
CoAgent MVP - AI-Powered Support Assistant

An intelligent L1 support assistant using:
- OpenAI GPT-4 for natural language understanding
- RAG (Retrieval-Augmented Generation) for knowledge retrieval
- Real-time hot-reload for dynamic knowledge updates
- Slack integration for team collaboration
"""
import os
import json
import chromadb
import threading
import time
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from sentence_transformers import SentenceTransformer

# Import prompts
from prompts_mvp import build_system_prompt, build_user_prompt, format_context

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../.env')  # Parent directory
except ImportError:
    pass

def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

SLACK_BOT_TOKEN = require_env("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = require_env("SLACK_APP_TOKEN")
OPENAI_API_KEY = require_env("OPENAI_API_KEY")

# =============================================================================
# INITIALIZE COMPONENTS
# =============================================================================

print("🚀 CoAgent MVP Starting...")

# OpenAI Client
openai_client = OpenAI(api_key=OPENAI_API_KEY)
print("  ✅ OpenAI client ready")

# ChromaDB - Use parent directory's database
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
db_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Load Embedding Model (same as sync pipeline uses)
print("  ⏳ Loading embedding model...")
EMBEDDING_MODEL = SentenceTransformer('intfloat/multilingual-e5-base')
print("  ✅ Embedding model ready")

# Get collections
try:
    kb_collection = db_client.get_collection("coagent_knowledge")
    print(f"  ✅ KB collection: {kb_collection.count()} documents")
except:
    kb_collection = None
    print("  ⚠️ KB collection not found")

try:
    ticket_collection = db_client.get_collection("support_tickets")
    print(f"  ✅ Ticket collection: {ticket_collection.count()} documents")
except:
    ticket_collection = None
    print("  ⚠️ Ticket collection not found")

# =============================================================================
# DATA LOADING & HOT-RELOAD
# =============================================================================

# Global Caches
SOP_CACHE = []
FEES_CACHE = []
RULES_CACHE = []

def load_sops():
    global SOP_CACHE
    SOP_CACHE = []
    try:
        # Load example SOPs from examples directory
        sop_path = os.path.join(os.path.dirname(__file__), "..", "examples", "example_sops.json")
        if os.path.exists(sop_path):
            with open(sop_path, 'r', encoding='utf-8') as f:
                sops = json.load(f)
                SOP_CACHE.extend(sops)
                print(f"  ✅ Loaded {len(SOP_CACHE)} SOPs")
        else:
            print("  ⚠️ No SOPs file found")
    except Exception as e:
        print(f"  ❌ Error loading SOPs: {e}")

def load_fees():
    global FEES_CACHE
    FEES_CACHE = []
    try:
        fees_path = os.path.join(os.path.dirname(__file__), "..", "examples", "example_fees.json")
        if os.path.exists(fees_path):
            with open(fees_path, 'r', encoding='utf-8') as f:
                FEES_CACHE = json.load(f)
                print(f"  ✅ Loaded {len(FEES_CACHE)} fee entries")
        else:
            print("  ⚠️ No fees file found")
    except Exception as e:
        print(f"  ❌ Error loading fees: {e}")

def load_rules():
    global RULES_CACHE
    RULES_CACHE = []
    try:
        rules_path = os.path.join(os.path.dirname(__file__), "..", "examples", "example_rules.json")
        if os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8') as f:
                RULES_CACHE = json.load(f)
                print(f"  ✅ Loaded {len(RULES_CACHE)} behavioral rules")
        else:
            print("  ⚠️ No rules file found")
    except Exception as e:
        print(f"  ❌ Error loading rules: {e}")

# Initial data load
print("⏳ Loading initial data...")
load_sops()
load_fees()
load_rules()
print("✅ Initial data loaded")

# File watching for hot-reload
def watch_config_files():
    """Watch config files and reload on changes"""
    sop_path = os.path.join(os.path.dirname(__file__), "..", "examples", "example_sops.json")
    fees_path = os.path.join(os.path.dirname(__file__), "..", "examples", "example_fees.json")
    rules_path = os.path.join(os.path.dirname(__file__), "..", "examples", "example_rules.json")
    
    last_sop_mtime = os.path.getmtime(sop_path) if os.path.exists(sop_path) else 0
    last_fees_mtime = os.path.getmtime(fees_path) if os.path.exists(fees_path) else 0
    last_rules_mtime = os.path.getmtime(rules_path) if os.path.exists(rules_path) else 0
    
    while True:
        time.sleep(5)  # Check every 5 seconds
        
        try:
            if os.path.exists(sop_path):
                current_mtime = os.path.getmtime(sop_path)
                if current_mtime > last_sop_mtime:
                    print("🔄 SOPs file changed, reloading...")
                    load_sops()
                    last_sop_mtime = current_mtime
                    
            if os.path.exists(fees_path):
                current_mtime = os.path.getmtime(fees_path)
                if current_mtime > last_fees_mtime:
                    print("🔄 Fees file changed, reloading...")
                    load_fees()
                    last_fees_mtime = current_mtime
                    
            if os.path.exists(rules_path):
                current_mtime = os.path.getmtime(rules_path)
                if current_mtime > last_rules_mtime:
                    print("🔄 Rules file changed, reloading...")
                    load_rules()
                    last_rules_mtime = current_mtime
        except Exception as e:
            print(f"⚠️ Error in config file watcher: {e}")

# Start file watcher thread
watcher_thread = threading.Thread(target=watch_config_files, daemon=True)
watcher_thread.start()
print("✅ File watcher started (hot-reload enabled)")

# =============================================================================
# SEARCH & RETRIEVAL
# =============================================================================

def search_documents(query: str, top_k: int = 5) -> list:
    """
    Search for relevant documents across SOPs and knowledge base
    
    Args:
        query: User's question/request
        top_k: Number of results to return
        
    Returns:
        List of relevant documents with metadata
    """
    results = []
    injected_sop_titles = set()
    
    # 1. KEYWORD MATCHING (Priority: inject matching SOPs)
    query_lower = query.lower()
    for sop in SOP_CACHE:
        keywords = sop.get('keywords', [])
        title_lower = sop.get('title', '').lower()
        
        # Match if any keyword appears in query (4+ chars)
        for kw in keywords:
            if len(kw) >= 4 and kw.lower() in query_lower:
                results.append({
                    'content': sop.get('content', ''),
                    'metadata': {
                        'title': sop.get('title', 'Untitled SOP'),
                        'source': 'sop',
                        'category': sop.get('category', 'General'),
                        'id': sop.get('id', 'unknown')
                    },
                    'score': 'keyword_match'
                })
                injected_sop_titles.add(sop.get('title', '').lower())
                break
    
    # 2. VECTOR SEARCH (if no keyword match, use semantic search)
    if len(results) == 0:
        try:
            # Generate query embedding using the same model
            query_embedding = EMBEDDING_MODEL.encode([query])[0].tolist()
            
            # Search KB collection
            if kb_collection:
                kb_results = kb_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, kb_collection.count())
                )
                
                if kb_results and kb_results['documents']:
                    for i, doc in enumerate(kb_results['documents'][0]):
                        # Skip if SOP with same title already injected
                        meta = kb_results['metadatas'][0][i]
                        if meta.get('title', '').lower() in injected_sop_titles:
                            continue
                            
                        results.append({
                            'content': doc,
                            'metadata': meta,
                            'score': kb_results['distances'][0][i] if 'distances' in kb_results else 0
                        })
            
            # Search ticket collection
            if ticket_collection and len(results) < top_k:
                ticket_results = ticket_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(3, ticket_collection.count())
                )
                
                if ticket_results and ticket_results['documents']:
                    for i, doc in enumerate(ticket_results['documents'][0]):
                        # Skip if SOP with same title already injected
                        meta = ticket_results['metadatas'][0][i]
                        if meta.get('title', '').lower() in injected_sop_titles:
                            continue
                            
                        results.append({
                            'content': doc,
                            'metadata': meta,
                            'score': ticket_results['distances'][0][i] if 'distances' in ticket_results else 0
                        })
        except Exception as e:
            print(f"❌ Vector search error: {e}")
    
    return results[:top_k]

def format_sop(sop: dict) -> str:
    """Format a single SOP for display"""
    title = sop.get('title', 'Untitled')
    category = sop.get('category', 'General')
    
    # Check if raw content exists (simple SOPs)
    if 'content' in sop:
        return f"📋 **{title}** ({category})\n{sop['content']}\n"
    
    # Otherwise build from structured format
    formatted = f"📋 **{title}** ({category})\n\n"
    
    if 'steps' in sop:
        formatted += "**Steps:**\n"
        for i, step in enumerate(sop['steps'], 1):
            formatted += f"{i}. {step}\n"
        formatted += "\n"
        
    if 'tips' in sop:
        formatted += "**Tips:**\n"
        for tip in sop['tips']:
            formatted += f"- {tip}\n"
            
    return formatted

def format_fees() -> str:
    """Format fees for inclusion in context"""
    if not FEES_CACHE:
        return ""
    
    fee_text = "💰 **SERVICE PRICING**\n\n"
    for fee in FEES_CACHE:
        service = fee.get('service', 'Unknown Service')
        base = fee.get('base_fee', 0)
        hourly = fee.get('hourly_rate', 0)
        currency = fee.get('currency', 'USD')
        desc = fee.get('description', '')
        
        fee_text += f"**{service}**\n"
        fee_text += f"- Base Fee: {base} {currency}\n"
        fee_text += f"- Hourly Rate: {hourly} {currency}\n"
        if desc:
            fee_text += f"- {desc}\n"
        fee_text += "\n"
    
    return fee_text

# =============================================================================
# LLM QUERY
# =============================================================================

def get_response(user_query: str) -> str:
    """
    Get AI response for user query
    
    Args:
        user_query: The user's question/request
        
    Returns:
        AI-generated response
    """
    # Search for relevant context
    search_results = search_documents(user_query, top_k=5)
    
    # Build context string
    context = ""
    
    # Add SOPs
    sop_context = {r for r in search_results if r['metadata'].get('source') == 'sop'}
    if sop_context:
        context += "## 📋 RELEVANT PROCEDURES\n\n"
        for result in sop_context:
            context += result['content'] + "\n\n"
    
    # Add KB articles
    kb_context = {r for r in search_results if r['metadata'].get('source') == 'kb'}
    if kb_context:
        context += "## 📚 KNOWLEDGE BASE\n\n"
        for result in kb_context:
            title = result['metadata'].get('title', 'Untitled')
            context += f"**{title}**\n{result['content']}\n\n"
    
    # Add ticket examples
    ticket_context = {r for r in search_results if r['metadata'].get('source') == 'ticket'}
    if ticket_context:
        context += "## 🎫 SIMILAR PAST TICKETS\n\n"
        for result in ticket_context:
            context += result['content'] + "\n\n"
    
    # Add fees
    context += format_fees()
    
    # Build system prompt with context
    system_prompt = build_system_prompt(
        rules_cache=RULES_CACHE,
        role="L1_Support",
        context=context
    )
    
    # Build user prompt
    user_prompt = build_user_prompt(user_query)
    
    # Call OpenAI
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"

# =============================================================================
# SLACK BOT
# =============================================================================

app = App(token=SLACK_BOT_TOKEN)

@ app.event("app_mention")
def handle_mention(event, say):
    """Handle @mentions of the bot"""
    user_query = event['text']
    # Remove bot mention from query
    user_query = user_query.split('>', 1)[1].strip() if '>' in user_query else user_query
    
    # Get AI response
    response = get_response(user_query)
    
    # Reply in thread
    say(text=response, thread_ts=event['ts'])

@app.message("")
def handle_dm(message, say):
    """Handle direct messages"""
    user_query = message['text']
    
    # Get AI response
    response = get_response(user_query)
    
    # Reply
    say(text=response)

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n✅ CoAgent MVP is ready!")
    print("📱 Slack integration active")
    print("🔥 Hot-reload enabled")
    print("\n🚀 Starting Socket Mode...\n")
    
    # Start bot
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
