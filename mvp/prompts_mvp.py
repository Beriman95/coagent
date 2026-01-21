#!/usr/bin/env python3
"""
CoAgent MVP Prompts - Clean, Simple, Effective

Single source of truth for CoAgent prompts and response formatting.
"""

# =============================================================================
# SYSTEM PROMPT BUILDER
# =============================================================================

BASE_SYSTEM_PROMPT = """
You are an INTERNAL support assistant for L1 support colleagues. NEVER speak directly to customers!

## 🎯 YOUR ROLE
Help your colleague decide WHAT TO SAY to the customer. You're not a customer service bot, but an experienced COLLEAGUE providing guidance from the background.

## ⚡ BE CONCISE! (MAX 1500 CHARACTERS)
- Only write the ESSENTIALS, no long explanations
- TO-DO: Max 5-6 steps
- ASK ABOUT: Max 2-3 questions
- No lengthy introductions or summaries

## 🗣️ STYLE - INTERNAL USE!
**CORRECT example (colleague perspective):**
"Ask the customer to send the domain list from the account's registered email."

**INCORRECT example (direct customer address):**
"Please send the domain list..." ❌

**Think like this:**
The colleague asks: "Hey, this customer is asking this, what should I tell them?"

You quickly write:
- The FACTS they need to know
- If there's a SPECIFIC procedure (e.g., process steps) → what the COLLEAGUE should do
- If you don't have valid info: "I don't know this, ask a senior/mentor"

## ⛔ FORBIDDEN WORDS
❌ "SOP", "context", "VectorDB", "ChromaDB"

## 🚨 NO HALLUCINATIONS!
- If there's no info in the knowledge base → Direct to documentation or senior support!
- NEVER make up steps!

## FORMAT
🔹 **INFO:** [Facts the colleague needs to know]
🔹 **TO-DO:** [What the COLLEAGUE should do - step 0 is always: verify account email]
🔹 **RULES:** [Relevant rules]
🔹 **💰 PRICING:** [🚨 REQUIRED! Find the "💰 SERVICE PRICING" section in context and output RELEVANT pricing!]
🔹 **ASK ABOUT:** [What the colleague should ASK the CUSTOMER - only if necessary]
"""

def build_system_prompt(rules_cache: list = [], role: str = "L1_Support", context: str = "") -> str:
    """Builds the System Prompt dynamically using rules and optional context."""
    
    # Sort rules by priority
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_rules = sorted(rules_cache, key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
    
    rule_text = ""
    for rule in sorted_rules:
        priority_icon = "⛔" if rule.get('priority') == 'critical' else "⚠️"
        content = rule.get('rule', '') if 'rule' in rule else rule.get('content', '')
        rule_text += f"{priority_icon} {content}\n"
    
    prompt = BASE_SYSTEM_PROMPT
    
    if rule_text:
        prompt += f"\n## 🧠 DYNAMIC BEHAVIORAL RULES (ALWAYS FOLLOW THESE!)\n{rule_text}"
        
    if context:
        prompt += f"\n\n## 📚 CONTEXT (Knowledge Base & Procedures)\n{context}"
        
    return prompt

# Backwards compatibility (initially empty)
SYSTEM_PROMPT = build_system_prompt([])


# =============================================================================
# USER PROMPT BUILDER
# =============================================================================

def build_user_prompt(query: str) -> str:
    """Build the user query prompt"""
    return f"""Customer Question/Request:
{query}

Please provide guidance for the support colleague on how to handle this request."""


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(results: list) -> str:
    """Format search results into context string"""
    if not results:
        return "No relevant information found in knowledge base."
    
    context = ""
    
    # Group by source type
    sops = [r for r in results if r.get('metadata', {}).get('source') == 'sop']
    kb_articles = [r for r in results if r.get('metadata', {}).get('source') == 'kb']
    tickets = [r for r in results if r.get('metadata', {}).get('source') == 'ticket']
    
    # Format SOPs
    if sops:
        context += "## 📋 PROCEDURES\n\n"
        for sop in sops:
            title = sop.get('metadata', {}).get('title', 'Untitled')
            content = sop.get('content', '')
            context += f"**{title}**\n{content}\n\n"
    
    # Format KB articles
    if kb_articles:
        context += "## 📚 KNOWLEDGE BASE\n\n"
        for article in kb_articles:
            title = article.get('metadata', {}).get('title', 'Untitled')
            content = article.get('content', '')
            context += f"**{title}**\n{content}\n\n"
    
    # Format past tickets
    if tickets:
        context += "## 🎫 SIMILAR PAST CASES\n\n"
        for ticket in tickets:
            title = ticket.get('metadata', {}).get('title', 'Case')
            content = ticket.get('content', '')
            context += f"**{title}**\n{content}\n\n"
    
    return context
