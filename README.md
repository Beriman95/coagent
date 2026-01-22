# 🤖 CoAgent - AI-Powered Support Assistant

> Intelligent L1 support assistant powered by GPT-4, RAG (Retrieval-Augmented Generation), and real-time knowledge hot-reload

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991.svg)](https://openai.com/)

---

## ✨ Features

### 🧠 **Intelligent AI Assistant**
- **GPT-4o-mini** powered natural language understanding
- **RAG (Retrieval-Augmented Generation)** for accurate, context-aware responses
- **Multi-source knowledge**: SOPs, knowledge base articles, past tickets

### 🔥 **Hot-Reload System**
- **Zero-downtime updates** - modify SOPs, fees, and rules without restart
- **File watcher** automatically detects changes every 5 seconds
- Perfect for rapidly evolving support environments

### 🎨 **Premium Admin UI**
- **Glassmorphism design** with smooth animations
- Manage SOPs, fees, behavioral rules
- Real-time statistics and analytics
- Modern, responsive interface

### 🔌 **Slack Integration**
- Native Slack bot integration
- Responds to @mentions and direct messages
- Thread-based conversations

### 🔍 **Advanced Search**
- **Hybrid search strategy**: Keyword matching → Vector semantic search
- **SOP priority system** ensures critical procedures are always found
- Intelligent deduplication prevents conflicting information

---

## 🏗️ Architecture

```mermaid
graph LR
    %% Palette: 
    %% Agent/Ops: #2B2D42 (Dark Blue)
    %% AI/Tech: #6A0572 (Deep Purple)
    %% Admin/Gov: #0077B6 (Rackhost Blue)
    %% Knowledge: #264653 (Teal)
    subgraph Operations [" 👥 OPERATIONS "]
        Agent((Support Agent))
        Slack[Slack Interface]
    end
    subgraph Intelligence [" 🧠 AI ENGINE "]
        CoAgent[<b>CoAgent AI</b><br>Context-Aware Assistant]
        LLM[GPT-4o Model]
    end
    subgraph KnowledgeBase [" 📚 KNOWLEDGE ASSET "]
        Data[(<b>Unified Knowledge</b><br>SOPs + Vectors + Feedback)]
    end
    subgraph Governance [" 🛡️ GOVERNANCE "]
        Admin((Admin))
        Dashboard[Admin Dashboard]
    end
    %% Operational Flow
    Agent -->|Query| Slack
    Slack -->|Request| CoAgent
    CoAgent <-->|Reasoning| LLM
    CoAgent -->|Context Retrieval| Data
    CoAgent -->|Answer| Slack
    %% Improvement Loop (The "Flywheel")
    Agent -.->|Feedback| CoAgent
    CoAgent -.->|Log Issue| Data
    Admin -->|Review & Approve| Dashboard
    Dashboard -->|Update Standards| Data
    Data -.->|Instant Re-training| CoAgent
    %% Styling for "C-Level" Look
    linkStyle default stroke:#666,stroke-width:2px,fill:none
    
    style Operations fill:#EDF6F9,stroke:#2B2D42,stroke-width:0px
    style Agent fill:#2B2D42,stroke:#fff,color:#fff
    style Slack fill:#fff,stroke:#2B2D42,stroke-width:2px
    style Intelligence fill:#F2E2F5,stroke:#6A0572,stroke-width:0px
    style CoAgent fill:#6A0572,stroke:#fff,color:#fff,stroke-width:2px
    style LLM fill:#fff,stroke:#6A0572,stroke-width:1px,stroke-dasharray: 5 5
    style KnowledgeBase fill:#E6F4F1,stroke:#264653,stroke-width:0px
    style Data fill:#264653,stroke:#fff,color:#fff,stroke-width:2px
    style Governance fill:#E0F4FF,stroke:#0077B6,stroke-width:0px
    style Admin fill:#0077B6,stroke:#fff,color:#fff
    style Dashboard fill:#fff,stroke:#0077B6,stroke-width:2px

```

### Data Flow

1. **Support agent** sends query via Slack
2. **Hybrid search** checks:
   - Keyword matches in SOP cache (instant)
   - Vector similarity in ChromaDB (semantic)
3. **Context assembly** combines relevant SOPs, KB articles, fees, rules
4. **GPT-4o-mini** generates colleague-facing guidance
5. **Response** delivered via Slack thread

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- Slack workspace (optional, for bot integration)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/coagent.git
cd coagent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Edit `.env` and add your credentials:**
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token  # Optional
SLACK_APP_TOKEN=xapp-your-slack-app-token  # Optional
FLASK_SECRET_KEY=your-random-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password-here
```

3. **Initialize knowledge base:**
```bash
# The example data is already included in examples/
# To use your own data, replace files in examples/ directory
```

### Run CoAgent

```bash
# Start the main CoAgent
cd mvp
python coagent_mvp.py
```

### Run Admin UI

```bash
# In a separate terminal
cd admin
python app.py
```

Access Admin UI at: `http://localhost:5001`

---

## 📖 Usage

### Slack Bot

Once configured, mention the bot in any Slack channel:

```
@CoAgent How do I restart the server?
```

The bot will:
1. Search for relevant SOPs
2. Retrieve KB articles
3. Check past similar tickets
4. Generate step-by-step guidance

### Admin UI

**Manage SOPs:**
- Create new procedures
- Edit existing SOPs
- Add keywords for better matching
- Organize by category

**Configure Pricing:**
- Set base fees
- Define hourly rates
- Update service descriptions

**Behavioral Rules:**
- Define response tone
- Set escalation criteria
- Customize output format

---

## 📁 Project Structure

```
coagent/
├── mvp/                        # Core CoAgent
│   ├── coagent_mvp.py         # Main application
│   └── prompts_mvp.py         # Prompt engineering
│
├── admin/                      # Admin UI
│   ├── app.py                 # Flask application
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JS, assets
│
├── examples/                   # Sample data
│   ├── example_sops.json      # Procedure templates
│   ├── example_fees.json      # Pricing structure
│   ├── example_rules.json     # Behavioral rules
│   └── example_kb.json        # Knowledge base articles
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md        # Technical details
│   ├── DEPLOYMENT.md          # Production guide
│   └── API.md                 # Admin API docs
│
├── .env.example               # Environment template
├── .gitignore                 # Git exclusions
├── LICENSE                    # MIT License
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔧 Configuration

### Knowledge Base

CoAgent uses **ChromaDB** for vector storage. Collections:

- `coagent_knowledge` - KB articles
- `support_tickets` - Historical tickets

### Embedding Model

Default: `intfloat/multilingual-e5-base` (768 dimensions)

**Why this model?**
- Excellent multilingual support
- Efficient (runs on CPU)
- High quality semantic search

### LLM Configuration

```python
# In coagent_mvp.py
model="gpt-4o-mini"  # Fast, cost-effective
temperature=0.7       # Balanced creativity/consistency
max_tokens=1500      # Concise responses
```

---

## 🎨 Admin UI Features

### Modern Glassmorphism Design

- **Smooth animations** on all interactions
- **Premium color palette** with gradients
- **Responsive layout** for desktop/mobile
- **Dark mode ready**

### Real-time Statistics

- Total SOPs count
- Active rules
- Pricing entries
- System health

### Client-Side Search

- Instant filtering (no server round-trips)
- Search across title, content, keywords
- Highlight matching terms

---

## 🧪 Development

### Hot-Reload

The file watcher monitors:
- `examples/example_sops.json`
- `examples/example_fees.json`
- `examples/example_rules.json`

Changes are detected every 5 seconds and auto-reloaded. **No restart required!**

### Adding New SOPs

Edit `examples/example_sops.json`:

```json
{
  "id": "new_sop",
  "title": "New Procedure",
  "category": "Category",
  "keywords": ["keyword1", "keyword2"],
  "content": "Step-by-step instructions..."
}
```

### Custom Rules

Edit `examples/example_rules.json`:

```json
{
  "id": "custom_rule",
  "rule": "Always verify account ownership first",
  "priority": "critical",
  "example": "Ask for account email verification"
}
```

---

## 🐳 Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  coagent:
    build: ./mvp
    env_file: .env
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./examples:/app/examples
    restart: unless-stopped

  admin:
    build: ./admin
    env_file: .env
    ports:
      - "5001:5000"
    volumes:
      - ./examples:/app/examples
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## 📊 Performance

### Response Times

- **Keyword match**: < 50ms
- **Vector search**: 100-300ms
- **LLM generation**: 1-3 seconds
- **Total**: 1.5-3.5 seconds avg

### Resource Usage

- **Memory**: ~500MB (with embeddings loaded)
- **CPU**: < 5% idle, 20-40% during queries
- **Storage**: ~20MB (excluding vector DB)

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Fork & clone
git clone https://github.com/yourusername/coagent.git
cd coagent

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes, commit
git commit -m "Add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API
- **ChromaDB** for vector storage
- **Sentence Transformers** for embeddings
- **Slack** for bot platform

---

## 📧 Contact

**Berke Siakos**

- Portfolio: [Your Portfolio URL]
- LinkedIn: [Your LinkedIn]
- Email: [Your Email]

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐!

---

**Built with ❤️ for support teams everywhere**
