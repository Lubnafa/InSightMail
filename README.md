# InSightMail 📧

> **Your AI-powered job search copilot that runs 100% locally**

Transform your job search chaos into organized insights. InSightMail automatically processes your Gmail exports, classifies job-related emails using local AI, and provides intelligent analytics about your hiring progress—all while keeping your data private on your own machine.

---

## 🎯 Why InSightMail?

**The Problem**: Job searching generates hundreds of emails across multiple platforms. Tracking which companies responded, when to follow up, and analyzing your success rates becomes overwhelming.

**The Solution**: InSightMail uses local AI to automatically organize your job search emails, providing clear insights into your application pipeline without compromising your privacy or costing you money.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **100% Local AI** | Uses Ollama (Mistral/Phi-3) - no cloud APIs, no costs, complete privacy |
| 📧 **Multi-Account Support** | Process emails from multiple Gmail accounts simultaneously |
| 🎯 **Smart Classification** | Auto-categorizes emails: Applications • Recruiter Outreach • Interviews • Offers • Rejections |
| 🔍 **AI-Powered Search** | "Ask My Inbox" - natural language queries across your entire email history |
| 📊 **Visual Analytics** | Interactive dashboards showing pipeline conversion, response rates, and trends |
| ⚡ **Real-time Processing** | Background processing with live updates as emails are analyzed |
| 🔒 **Privacy First** | All processing happens locally - your emails never leave your machine |

## 🏗️ Technical Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │───▶│     FastAPI     │───▶│     Ollama      │
│   Frontend      │    │     Backend     │    │   Local LLM     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │     SQLite      │              │
         │              │   Database      │              │
         │              └─────────────────┘              │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │    ChromaDB     │
                        │  Vector Store   │
                        └─────────────────┘
```

**Core Technologies:**
- **Backend**: FastAPI with async processing
- **Frontend**: Streamlit with interactive components  
- **Database**: SQLite for structured data
- **Vector Search**: ChromaDB for semantic similarity
- **LLM**: Ollama (local inference)
- **Embeddings**: SentenceTransformers
- **Email Processing**: Custom parsers for JSON/EML/MBOX formats

## 🚀 Quick Start

Get InSightMail running in under 5 minutes:

### 1️⃣ Prerequisites

```bash
# 1. Install Ollama (https://ollama.ai)
# Download and install Ollama for your platform

# 2. Pull an AI model (choose one)
ollama pull mistral:7b      # Recommended: Best performance
ollama pull phi3:mini       # Alternative: Fastest, good for lower-end hardware

# 3. Verify installation
ollama list                 # Should show your downloaded model
```

**Requirements**: Python 3.9+ and Ollama

### 2️⃣ Install InSightMail

```bash
# Clone the repository
git clone https://github.com/yourusername/InSightMail.git
cd InSightMail

# Install Python dependencies
pip install -r requirements.txt

# Initialize the database
cd backend
python -c "from db import db_manager; db_manager.create_tables()"
```

### 3️⃣ Start the Application

```bash
# Terminal 1: Start the backend API
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend dashboard
cd frontend
streamlit run app.py --server.port 8501
```

### 4️⃣ Access InSightMail

Open your browser and navigate to:
- 🖥️ **Dashboard**: http://localhost:8501
- 📚 **API Docs**: http://localhost:8000/docs

### 5️⃣ Try It Out

1. **Load Sample Data**: Upload `data/samples/sample_gmail.json` via the Email Upload page
2. **Explore Dashboard**: View your job pipeline and analytics
3. **Search Emails**: Try "Ask My Inbox" with queries like "Show me interview emails"

---

## 📧 Getting Your Gmail Data

InSightMail supports multiple ways to import your job search emails:

### 🥇 Google Takeout (Easiest)

1. Visit [Google Takeout](https://takeout.google.com)
2. Select **"Mail"** → Choose **"All messages included"**
3. Export as **JSON** or **EML** format
4. Download and extract the files

### 🔍 Gmail Search Export (Targeted)

1. In Gmail, use this search: `(recruiter OR interview OR application OR offer OR job OR hiring)`
2. Export results using a browser extension (like "Email Extractor")
3. Save as JSON or EML files

### ⚙️ Gmail API (Advanced Users)

Set up Gmail API credentials and use the built-in integration for real-time sync.

---

## 📱 How to Use InSightMail

### 📤 Upload & Process Emails

1. **Navigate** to "Email Upload" in the sidebar
2. **Enter** your Gmail account email (e.g., `your.email@gmail.com`)
3. **Upload** your exported files (supports JSON, EML, MBOX formats)
4. **Wait** for AI processing (progress shown in real-time)

### 📊 View Your Job Pipeline

- **Track Progress**: See emails flow through: Applied → Response → Interview → Offer
- **Conversion Rates**: Understand your success rates at each stage  
- **Follow-up Opportunities**: Identify applications that need attention

### 🔍 Search Your Inbox

Use **"Ask My Inbox"** with natural language:

> *"How many interviews did I have this month?"*  
> *"Show me rejection emails from tech companies"*  
> *"Which applications haven't received responses?"*  
> *"Find all emails about remote positions"*

### 📈 Analytics & Insights

Get actionable intelligence:
- **Response Rates**: Track which strategies work best
- **Timeline Analysis**: Understand hiring patterns and optimal timing
- **Company Insights**: See which employers are most responsive
- **Performance Trends**: Monitor improvement over time

## ⚙️ Configuration

### Model Selection

Choose the right AI model for your hardware:

| Model | Performance | Speed | Memory | Best For |
|-------|-------------|-------|---------|----------|
| `mistral:7b` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 8GB+ | **Recommended**: Best accuracy |
| `phi3:mini` | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 4GB+ | Fast processing, lower-end hardware |
| `llama3.2:3b` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 6GB+ | Good balance |

```bash
# Switch models anytime
ollama pull phi3:mini
# Update your .env file or restart with new model
```

### Environment Variables

Copy `env.example` to `.env` and customize:

```bash
# LLM Configuration  
OLLAMA_MODEL=mistral:7b              # Primary model
OLLAMA_BACKUP_MODEL=phi3:mini        # Fallback if primary fails

# Database
DATABASE_URL=sqlite:///data/insightmail.db

# Embeddings (for search)
EMBEDDING_MODEL=all-MiniLM-L6-v2     # Lightweight and fast
```

## 🧪 Testing & Validation

### Quick Test with Sample Data

```bash
# Use included sample data to verify everything works
cd backend
python -c "
from email_parser import EmailParser
parser = EmailParser()
emails = parser.batch_parse_files(['../data/samples/sample_gmail.json'], 'demo@gmail.com')
print(f'✅ Loaded {len(emails)} sample emails')
"
```

### Run Test Suite

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests  
pytest tests/ -v

# Test specific components
pytest tests/test_parser.py    # Email parsing
pytest tests/test_rag.py       # Search functionality  
pytest tests/test_llm.py       # AI classification
```

## 🐳 Docker Deployment

Deploy with Docker for easy setup:

```bash
# Quick deployment
docker-compose up -d

# Manual build  
docker build -t insightmail .
docker run -p 8501:8501 -p 8000:8000 insightmail

# Access the application
# Dashboard: http://localhost:8501
# API: http://localhost:8000
```

## 🔌 API Reference

InSightMail provides a comprehensive REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System status and health check |
| `/emails/upload` | POST | Upload Gmail export files |
| `/emails` | GET | List processed emails with filters |
| `/query` | POST | RAG-powered natural language search |
| `/stats` | GET | Job pipeline statistics |
| `/summary` | GET | AI-generated inbox insights |

**Interactive Documentation**: http://localhost:8000/docs

## 🛠️ Project Structure

```
InSightMail/
├── 🔧 backend/                 # FastAPI backend
│   ├── main.py                # API routes & endpoints
│   ├── db.py                  # Database models (SQLAlchemy)
│   ├── email_parser.py        # Gmail export processing
│   ├── llm_adapter.py         # Ollama LLM interface
│   ├── rag_pipeline.py        # Vector search with ChromaDB
│   └── summarizer_chain.py    # AI classification & summarization
├── 🎨 frontend/               # Streamlit dashboard
│   ├── app.py                 # Main application
│   └── components/            # Modular UI components
├── 🧪 tests/                  # Comprehensive test suite
├── 📊 data/                   # Data storage
│   ├── samples/               # Sample Gmail exports
│   ├── embeddings/            # ChromaDB vector store
│   └── tokens/                # Authentication tokens
├── 📋 requirements.txt        # Python dependencies
└── 🐳 docker-compose.yml     # Container orchestration
```

## 🐛 Troubleshooting

### Quick Fixes

| Problem | Solution |
|---------|----------|
| 🔴 **Ollama not responding** | Run `ollama serve` and ensure model is pulled: `ollama list` |
| 📧 **No emails processed** | Check file format (JSON/EML/MBOX) and verify account email matches |
| 🤖 **Classification failing** | Try `ollama pull phi3:mini` or check `ollama ps` for active models |
| 🐌 **Slow performance** | Switch to `phi3:mini` model or close other applications |
| 🔍 **Search not working** | Wait for embeddings to generate, check ChromaDB initialization |

### Performance Tips

- **Start Small**: Use `phi3:mini` initially, upgrade to `mistral:7b` when comfortable
- **Memory**: 8GB+ RAM recommended for `mistral:7b`, 4GB sufficient for `phi3:mini`
- **Storage**: SSD improves database performance significantly
- **Batch Size**: Adjust email processing batches based on your hardware

### Getting Help

- 📋 **Check Logs**: Backend terminal shows detailed processing information
- 🏥 **Health Check**: Visit http://localhost:8000/health for system status
- 📚 **Sample Data**: Test with included samples first before your own emails

---

## 🚀 What's Next?

InSightMail is actively developed with upcoming features:

- 📱 **Mobile App**: iOS/Android companion app
- 🔗 **Platform Integration**: LinkedIn, Indeed, AngelList connectors  
- 🤝 **Team Features**: Share insights with career coaches
- 📊 **Advanced Analytics**: Predictive modeling and trend analysis
- 🔄 **Real-time Sync**: Live Gmail integration without exports

---

## 📄 License & Acknowledgments

**License**: MIT License - see [LICENSE](LICENSE) file

**Built with**: [Ollama](https://ollama.ai) • [ChromaDB](https://www.trychroma.com/) • [FastAPI](https://fastapi.tiangolo.com/) • [Streamlit](https://streamlit.io/) • [SentenceTransformers](https://www.sbert.net/)

## 💬 Community & Support

- 🐛 **Report Issues**: [GitHub Issues](https://github.com/yourusername/InSightMail/issues)
- 💭 **Join Discussion**: [GitHub Discussions](https://github.com/yourusername/InSightMail/discussions)  
- 📖 **Documentation**: [Project Wiki](https://github.com/yourusername/InSightMail/wiki)

---

<div align="center">

**🎯 Built with ❤️ for job seekers who value privacy and want data-driven insights into their search process**

*Take control of your job search. Your emails, your insights, your success.*

[⭐ Star on GitHub](https://github.com/yourusername/InSightMail) • [📧 Try the Demo](http://localhost:8501) • [🤝 Contribute](CONTRIBUTING.md)

</div>
